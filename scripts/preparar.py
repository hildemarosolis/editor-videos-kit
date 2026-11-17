#!/usr/bin/env python3
"""Prepara un vídeo de tu carpeta «1 Para editar» (kit.carpeta("entrada")) para montar con una receta.

  python3 scripts/preparar.py MI_VIDEO [--quitar 79.68-83.42 ...]

1. Si la carpeta está en iCloud (Mac), baja el vídeo si hace falta; lo copia a raw/ (fuera de git).
2. Corte de silencios + −14 LUFS + 9:16 SDR (scripts/prueba_corte.py).
3. Crea proyectos/<VIDEO>/ con los assets de base (de subtitulos/ y marca/), el corte y su audio.
4. Transcribe palabra a palabra (whisper -bs 8) → proyectos/<VIDEO>/palabras.json.
"""
import argparse
import json
import os
import shutil
import subprocess
import hashlib
import tempfile
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kit  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
INBOX = Path(os.environ.get("EDITOR_INBOX") or kit.carpeta("entrada"))  # EDITOR_INBOX: otra carpeta solo para pruebas
TEMPLATE = ROOT / "subtitulos"  # composición de base: de aquí salen hyperframes.json, package.json, Anton y GSAP
# una carpeta de trabajo por instalación: dos copias del editor no se pisan
WORK = Path(tempfile.gettempdir()) / f"editor-work-{hashlib.md5(str(ROOT).encode()).hexdigest()[:8]}"


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode:
        sys.exit(f"falló: {' '.join(map(str, cmd))}\n{r.stderr[-1500:]}")
    return r.stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--quitar", action="append", default=[])
    ap.add_argument("--sin-silencios", action="store_true", help="no recortar pausas (sketches, montajes)")
    a = ap.parse_args()
    name = a.video
    src = next(iter(INBOX.glob(f"{name}.*")), None)
    if not src:  # dentro de una carpeta de guion (vídeo grabado con su guion de «0 Guiones»)
        src = next((v for v in INBOX.glob(f"*/{name}.*") if (v.parent / ".guion").exists()
                    or (v.parent / "Guion.pdf").exists()), None)
    local = next(iter((ROOT / "raw").glob(f"{name}.*")), None)
    if not src and not local:
        sys.exit(f"no está {name} en {INBOX} ni en raw/")
    if src:
        if shutil.which("brctl"):  # Mac con «Optimizar almacenamiento»: el vídeo puede estar solo en iCloud
            subprocess.run(["brctl", "download", str(src)], capture_output=True)
        raw = ROOT / "raw" / src.name
        raw.parent.mkdir(exist_ok=True)
        if not raw.exists() or raw.stat().st_size != src.stat().st_size:
            shutil.copy2(src, raw)
    else:
        raw = local  # ya procesado antes: se rehace desde la copia local (p. ej. para quitar una toma)

    if not a.quitar:
        rep = subprocess.run([sys.executable, str(ROOT / "scripts/repeticiones.py"), str(raw)], capture_output=True, text=True)
        print(rep.stdout.strip() or rep.stderr.strip()[-300:])
    cmd = [sys.executable, str(ROOT / "scripts/prueba_corte.py"), str(raw), "--work", str(WORK / name), "--out", str(ROOT / "out")]
    for q in a.quitar:
        cmd += ["--quitar", q]
    if a.sin_silencios:
        cmd.append("--sin-silencios")
    print(run(cmd).strip().splitlines()[-1])

    d = ROOT / "proyectos" / name
    (d / "assets").mkdir(parents=True, exist_ok=True)
    (d / "recetas").mkdir(exist_ok=True)
    for f in ["hyperframes.json", "package.json"]:
        shutil.copy2(TEMPLATE / f, d / f)
    (d / "meta.json").write_text(json.dumps({"id": name.lower(), "name": name}, indent=2))
    for item in ["Anton-Regular.ttf", "gsap.min.js"]:  # sfx: los pone sfx.py con su banco
        shutil.copy2(TEMPLATE / "assets" / item, d / "assets" / item)
    (d / "assets/fuentes").mkdir(exist_ok=True)  # Oswald: los textos secundarios de la pizarra
    shutil.copy2(ROOT / "marca/fuentes/Oswald-Variable.ttf", d / "assets/fuentes/Oswald-Variable.ttf")
    logos = ROOT / "marca/logos"  # opcional: los logos de tus marcas (la receta los saca al nombrarlas)
    if logos.is_dir():
        (d / "assets/logos").mkdir(exist_ok=True)
        for f in logos.iterdir():
            if f.is_file() and f.suffix.lower() in (".png", ".svg", ".jpg"):
                shutil.copy2(f, d / "assets/logos" / f.name)
    shutil.copy2(ROOT / "out" / f"{name}_corte_916.mp4", d / "assets/corte.mp4")
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(d / "assets/corte.mp4"), "-vn", "-c:a", "copy",
         str(d / "assets/audio.m4a")])
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(d / "assets/corte.mp4"), "-vn", "-ac", "1",
         "-ar", "16000", str(d / "audio16k.wav")])
    run([kit.whisper_cli(), "-m", str(ROOT / "models/ggml-large-v3-turbo-q5_0.bin"), "-f", str(d / "audio16k.wav"),
         "-l", "es", "-bs", "8", "-ml", "1", "-sow", "-oj", "-of", str(d / "palabras")])
    words = json.loads((d / "palabras.json").read_text())["transcription"]
    print(f"{name}: {len([w for w in words if w['text'].strip()])} palabras → {d}")


if __name__ == "__main__":
    main()
