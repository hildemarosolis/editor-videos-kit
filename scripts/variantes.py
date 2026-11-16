#!/usr/bin/env python3
"""Variantes de prueba de un vídeo: v1 color, v2 gancho, v3 zoom, v4 fuente.

Uso:
  python3 scripts/variantes.py --dir proyectos/MI_VIDEO --receta proyectos/MI_VIDEO/recetas/ranking.json [--solo v1_color,v3_zoom]

Lee <dir>/recetas/variantes.json ({nombre: cambios sobre la receta base}), genera cada
receta, la renderiza y deja el vídeo en out/ y en tu carpeta de entregas
(kit.carpeta("terminados"))/<fecha tema>/, cada una con su letra (scripts/terminados.py). Al terminar, deja index.html con la receta base.
"""
import argparse
import copy
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HF = ["npx", "--yes", "hyperframes@0.8.78"]


def merge(base, extra):
    out = copy.deepcopy(base)
    for k, v in extra.items():
        out[k] = merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def run(cmd, cwd=None, env=None):
    r = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"falló: {' '.join(map(str, cmd))}\n{r.stderr[-1500:]}")
    return r.stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--receta", required=True)
    ap.add_argument("--solo", default="")
    a = ap.parse_args()
    d, base_path = Path(a.dir), Path(a.receta)
    base = json.loads(base_path.read_text())
    variantes = json.loads((d / "recetas/variantes.json").read_text())
    elegidas = [v for v in variantes if not v.startswith("_") and (not a.solo or v in a.solo.split(","))]
    stem = d.name
    sys.path.insert(0, str(ROOT / "scripts"))
    from terminados import entregar as a_terminados  # cada variante, en la carpeta del tema con su letra
    (d / "recetas/variantes").mkdir(exist_ok=True)
    env = dict(__import__("os").environ, HYPERFRAMES_SKIP_SKILLS="1")
    env.pop("GEMINI_API_KEY", None)
    try:
        for name in elegidas:
            receta = merge(base, variantes[name])
            rp = d / "recetas/variantes" / f"{name}.json"
            rp.write_text(json.dumps(receta, ensure_ascii=False, indent=2))
            print(f"[{name}] generando…", flush=True)
            run([sys.executable, str(ROOT / "scripts/subtitulos.py"), "--dir", str(d), "--receta", str(rp)])
            lint = run(HF + ["lint", "--json"], cwd=d, env=env)
            errs = [f for f in (json.loads(lint).get("findings") or []) if f.get("severity") == "error"]
            if errs:
                sys.exit(f"[{name}] lint con errores: {[e.get('code') for e in errs]}")
            out = ROOT / "out" / f"{stem}_{name}.mp4"
            print(f"[{name}] renderizando…", flush=True)
            run(HF + ["render", "-o", str(out), "--quiet"], cwd=d, env=env)
            meas = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(out), "-vn", "-af", "ebur128", "-f", "null", "-"],
                                  capture_output=True, text=True).stderr
            lufs = float([l for l in meas.splitlines() if l.strip().startswith("I:")][-1].split()[1])
            if abs(lufs + 14) > 0.5:  # mismo arreglo que entregar.py
                mix = next(p for p in [d / "assets/audio_mix.m4a", d / "assets/audio.m4a"] if p.exists())
                fixed = out.with_name(out.stem + "_fix.mp4")
                run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(out), "-i", str(mix), "-map", "0:v",
                     "-map", "1:a", "-c", "copy", "-movflags", "+faststart", str(fixed)])
                fixed.replace(out)
            dst = a_terminados(out, dict(receta, variante=receta.get("variante", name)), rp, stem)
            print(f"[{name}] listo → {dst.parent.name}/{dst.name}", flush=True)
    finally:
        run([sys.executable, str(ROOT / "scripts/subtitulos.py"), "--dir", str(d), "--receta", str(base_path)])


if __name__ == "__main__":
    main()
