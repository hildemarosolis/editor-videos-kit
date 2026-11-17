#!/usr/bin/env python3
"""Renderiza un proyecto con su receta y lo entrega en tu carpeta de trabajo.

  python3 scripts/entregar.py MI_VIDEO --receta proyectos/MI_VIDEO/recetas/m1.json --muestra        # para revisar
  python3 scripts/entregar.py MI_VIDEO --receta proyectos/MI_VIDEO/recetas/m1.json --usar-muestra   # tras el visto bueno

Lint (sin errores) → render 1080p → carpeta de entregas/<fecha tema>/ (kit.carpeta("terminados"), scripts/terminados.py),
con su .txt al lado (caption, portada y transcripción: scripts/textos.py) → mueve el original de la carpeta de
entrada (kit.carpeta("entrada")) a la de originales usados (kit.carpeta("originales")).
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kit  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
EDITOR = kit.carpeta_editor()
HF = ["npx", "--yes", "hyperframes@0.8.78"]


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode:
        sys.exit(f"falló: {' '.join(map(str, cmd))}\n{r.stderr[-1500:]}")
    return r.stdout


def pegar_outro(out, outro):
    """Pega el outro al final: destello blanco de 0,4 s + subida de aire y «boom» en el cambio.
    El outro va a −14 LUFS y el total pasa por un limitador, así que sigue en −14."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import sfx
    sfx.make_sounds(ROOT / "marca/sfx")
    x = 0.4
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                str(out)], capture_output=True, text=True).stdout)
    off = dur - x
    hit = int((off + x / 2) * 1000)
    rise = max(0, hit - int(sfx.SOUNDS["subida"][1] * 1000))
    graph = (f"[0:v][1:v]xfade=transition=fadewhite:duration={x}:offset={off:.3f},format=yuv420p[v];"
             f"[0:a][1:a]acrossfade=d={x}[ax];"
             f"[2:a]adelay={rise}|{rise},volume={sfx.SOUNDS['subida'][2]}[s1];"
             f"[3:a]adelay={hit}|{hit},volume={sfx.SOUNDS['boom'][2]}[s2];"
             f"[ax][s1][s2]amix=inputs=3:normalize=0:duration=first,alimiter=limit={sfx.LIMIT}:level=0[a]")
    joined = out.with_name(out.stem + "_outro.mp4")
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(out), "-i", str(outro),
         "-i", str(ROOT / "marca/sfx/subida.wav"), "-i", str(ROOT / "marca/sfx/boom.wav"),
         "-filter_complex", graph, "-map", "[v]", "-map", "[a]",
         "-c:v", "libx264", "-crf", "16", "-preset", "slow", "-c:a", "aac", "-b:a", "192k",
         "-ar", "48000", "-movflags", "+faststart", str(joined)])
    # el boom suma energía: se reajusta el total a −14 LUFS
    meas = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(joined), "-vn", "-af", "ebur128",
                           "-f", "null", "-"], capture_output=True, text=True).stderr
    lufs = float([l for l in meas.splitlines() if l.strip().startswith("I:")][-1].split()[1])
    fixed = out.with_name(out.stem + "_outro2.mp4")
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(joined), "-c:v", "copy",
         "-af", f"volume={-14 - lufs:.2f}dB,alimiter=limit={sfx.LIMIT}:level=0", "-c:a", "aac", "-b:a", "192k",
         "-ar", "48000", "-movflags", "+faststart", str(fixed)])
    joined.unlink()
    fixed.replace(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--receta", help="receta del short (no hace falta con --largo)")
    ap.add_argument("--muestra", action="store_true",
                    help="solo renderiza la muestra en out/ (+ copia ligera para el móvil); no toca la carpeta de entregas")
    ap.add_argument("--usar-muestra", action="store_true",
                    help="entrega la muestra ya aprobada sin volver a renderizar")
    ap.add_argument("--solo-texto", action="store_true",
                    help="con --usar-muestra: deja solo el .txt junto a un vídeo ya entregado (textos aprobados después)")
    ap.add_argument("--largo", action="store_true",
                    help="episodio largo horizontal (scripts/largo.py): con --usar-muestra entrega el montaje revisado")
    a = ap.parse_args()
    if a.largo:  # pasa por aquí para que la guarda de la carpeta de entregas (mod editor-videos) lo cubra igual
        if not a.usar_muestra:
            sys.exit("--largo va con --usar-muestra: se entrega el montaje que el creador revisó (largo.py montar + muestra)")
        sys.path.insert(0, str(ROOT / "scripts"))
        import largo
        return largo.entregar(a.video)
    if not a.receta:
        sys.exit("falta --receta")
    if a.solo_texto:
        if not a.usar_muestra:
            sys.exit("--solo-texto va con --usar-muestra: el texto también se entrega solo con el visto bueno")
        return solo_texto(a.video, a.receta)
    sys.path.insert(0, str(ROOT / "scripts"))
    from plantilla import comprobar
    comprobar(a.receta)  # sin huecos de plantilla
    cfg = json.loads(Path(a.receta).read_text())
    if not cfg.get("tema"):  # antes de renderizar, no después
        sys.exit(f"{a.receta}: falta «tema» en la receta (p. ej. \"tema\": \"Mi tema\")")
    d = ROOT / "proyectos" / a.video
    modelo = Path(a.receta).stem
    muestra = ROOT / "out" / f"{a.video}_{modelo}_muestra.mp4"
    out = ROOT / "out" / f"{a.video}_{modelo}_916.mp4"
    if a.usar_muestra:
        # lo que se entrega es exactamente lo que el creador vio; si la receta cambió después, no vale
        if not muestra.exists():
            sys.exit(f"no hay muestra: python3 scripts/entregar.py {a.video} --receta {a.receta} --muestra")
        if muestra.stat().st_mtime < Path(a.receta).stat().st_mtime:
            sys.exit(f"la muestra es anterior al último cambio de la receta: vuelve a sacarla con --muestra")
        shutil.copy2(muestra, out)
    else:
        destino = muestra if a.muestra else out
        renderizar(a.video, d, a.receta, destino)
        # outro de la receta (p. ej. «episodio completo en mi canal» en los shorts de un vídeo largo)
        if cfg.get("outro"):
            pegar_outro(destino, ROOT / cfg["outro"])
            print(f"{a.video}: outro {Path(cfg['outro']).name} añadido con destello y boom")
        if a.muestra:
            # copia ligera para verla en el móvil (el envío a otros dispositivos admite hasta 30 MB)
            ligera = muestra.with_name(muestra.stem + "_ligera.mp4")
            run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(muestra), "-vf", "scale=540:-2",
                 "-c:v", "libx264", "-crf", "26", "-preset", "fast", "-c:a", "aac", "-b:a", "96k", str(ligera)])
            print(f"{a.video}: muestra {muestra.relative_to(ROOT)} · ligera {ligera.relative_to(ROOT)} · {lufs_de(muestra)} LUFS")
            return
    # Solo se entrega la versión para publicar (decisión del 20-oct-2026: sin copias _movil),
    # en la carpeta de su tema y con nombre «fecha tema - letra variante» (22-oct-2026).
    from terminados import entregar as a_terminados
    from textos import texto
    txt = texto(a.video, a.receta)  # antes de copiar: si falla, no queda un vídeo sin su texto
    dst = a_terminados(out, cfg, a.receta, a.video)
    # al lado, con el mismo nombre en .txt: caption, portada y transcripción para publicar (25-oct-2026)
    # (la primera línea, el título, pasa a ser el nombre del archivo entregado)
    dst.with_suffix(".txt").write_text(dst.stem + txt[txt.index("\n"):])
    if not cfg.get("letra"):  # la receta se queda con su letra: si se vuelve a entregar, es la misma variante
        letra = dst.name.split(" - ")[1][0]
        Path(a.receta).write_text(json.dumps({"tema": cfg["tema"], "letra": letra,
                                              **{k: v for k, v in cfg.items() if k != "tema"}},
                                             ensure_ascii=False, indent=2) + "\n")
    orig = next(iter(kit.carpeta("entrada").glob(f"{a.video}.*")), None)
    if not orig:  # vídeo grabado con su guion: se mueve la carpeta entera (guion, comentarios y vídeo)
        v = next((v for v in kit.carpeta("entrada").glob(f"*/{a.video}.*")
                  if (v.parent / ".guion").exists() or (v.parent / "Guion.pdf").exists()), None)
        orig = v.parent if v else None
    if orig:
        shutil.move(str(orig), kit.carpeta("originales") / orig.name, copy_function=shutil.copyfile)
    print(f"{a.video}: entregado {dst.parent.name}/{dst.name}")
    avisar_efectos(a.video, a.receta)


def avisar_efectos(video, receta):
    """Qué efectos de la biblioteca lleva lo entregado y cuáles de los «elegidos» de la página se usaron.
    Claude los marca después en la página (ArtifactData update de elegidos/<código> con «usado_en»)."""
    try:
        import efectos_indice
        cods = efectos_indice.codigos(video, receta, ruta=receta) or []
    except Exception as ex:  # noqa: BLE001 — la entrega ya está hecha; esto solo informa
        print(f"  aviso: no pude leer los efectos ({ex})")
        return
    print(f"{video}: efectos {' '.join(cods) or 'ninguno'} (apuntados en _entregas.md)")
    f = ROOT / "proyectos" / video / "elegidos.json"
    if f.exists():
        eleg = json.loads(f.read_text()).get("elegidos", [])
        usados = [c for c in eleg if c in cods]
        if usados:
            print(f"  elegidos usados: {' '.join(usados)} → márcalos en la página con «usado_en»: «{video}»")
        if set(eleg) - set(usados):
            print(f"  elegidos que NO lleva: {' '.join(c for c in eleg if c not in cods)} (siguen para el próximo)")


def solo_texto(video, receta):
    """Escribe el .txt junto al vídeo que ya se entregó con esta receta (lo busca en _entregas.md)."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import terminados
    from textos import texto
    filas = [l.split("|") for l in terminados.REGISTRO.read_text().splitlines() if l.startswith("| 20")]
    hechas = [(f[2].strip(), f[3].strip()) for f in filas if f[4].strip() == video and f[5].strip() == Path(receta).name]
    if not hechas:
        sys.exit(f"{video}: no hay entrega de {Path(receta).name} en {terminados.REGISTRO.name}")
    carpeta, archivo = hechas[-1]
    mp4 = next((b / terminados.nfc(carpeta) / terminados.nfc(archivo) for b in (terminados.TERMINADOS, terminados.PUBLICADOS)
                if (b / terminados.nfc(carpeta) / terminados.nfc(archivo)).exists()), None)
    if not mp4:
        sys.exit(f"{video}: no encuentro {carpeta}/{archivo} ni en Terminados ni en Publicados")
    txt = texto(video, receta)
    mp4.with_suffix(".txt").write_text(mp4.stem + txt[txt.index("\n"):])
    print(f"{video}: texto → {mp4.parent.parent.name}/{carpeta}/{mp4.with_suffix('.txt').name}")


def lufs_de(f):
    meas = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(f), "-vn", "-af", "ebur128", "-f", "null", "-"],
                          capture_output=True, text=True).stderr
    return float([l for l in meas.splitlines() if l.strip().startswith("I:")][-1].split()[1])


def renderizar(video, d, receta, out):
    """Composición desde la receta, lint sin errores, render y volumen a −14 LUFS."""
    env = dict(os.environ, HYPERFRAMES_SKIP_SKILLS="1")
    env.pop("GEMINI_API_KEY", None)
    run([sys.executable, str(ROOT / "scripts/subtitulos.py"), "--dir", str(d), "--receta", receta])
    lint = json.loads(run(HF + ["lint", "--json"], cwd=d, env=env))
    errs = [f.get("code") for f in (lint.get("findings") or []) if f.get("severity") == "error"]
    if errs:
        sys.exit(f"{video}: lint con errores {errs}")
    run(HF + ["render", "-o", str(out), "--quiet"], cwd=d, env=env)
    # el render a veces baja el audio ~1,5 dB (pasó al renderizar 5 vídeos a la vez):
    # si se aleja de −14 LUFS, se sustituye por la mezcla original, que ya está a −14 y sincronizada.
    lufs = lufs_de(out)
    mix = next((p for p in [d / "assets/audio_mix.m4a", d / "assets/audio.m4a"] if p.exists()))
    if abs(lufs + 14) > 0.5:
        fixed = out.with_name(out.stem + "_fix.mp4")
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(out), "-i", str(mix), "-map", "0:v",
             "-map", "1:a", "-c", "copy", "-movflags", "+faststart", str(fixed)])
        fixed.replace(out)
        print(f"{video}: audio del render a {lufs} LUFS → sustituido por la mezcla")


if __name__ == "__main__":
    main()
