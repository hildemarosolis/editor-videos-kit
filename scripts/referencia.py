#!/usr/bin/env python3
"""Añade una referencia (un reel que te gusta) a referencias/refN para analizarla después.

  python3 scripts/referencia.py https://www.instagram.com/reel/XXXX/ --comentario "me gusta el gancho"
  python3 scripts/referencia.py ~/Downloads/grabacion.mp4 --comentario "…"

Deja:
  referencias/refN.mp4 (+ refN.info.json si viene de un enlace)
  referencias/refN_16k.wav, refN_frases.json (whisper por frases)
  referencias/refN/frames/{gancho_0-8s.png, completo.png}
  referencias/refN/NOTA.md (fuente, señales, comentario, transcripción): pendiente de analizar.
NO analiza ni escribe receta.json: eso se hace con el creador en sesión.
Sirve para lo que dejes en «0 Referencias» de tu carpeta de trabajo, o a mano.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kit  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
REFS = ROOT / "referencias"
MODEL = ROOT / "models/ggml-large-v3-turbo-q5_0.bin"


def run(cmd):
    return subprocess.run([str(c) for c in cmd], capture_output=True, text=True)


def siguiente():
    REFS.mkdir(exist_ok=True)
    nums = [int(m.group(1)) for p in REFS.iterdir() if (m := re.fullmatch(r"ref(\d+)", p.stem.split("_")[0]))]
    return f"ref{max(nums, default=0) + 1}"


def bajar(url, ref):
    r = run(["yt-dlp", "--no-playlist", "-q", "-f", "bv*+ba/b", "--merge-output-format", "mp4",
             "-o", REFS / f"{ref}.%(ext)s", "--write-info-json", url])
    video = REFS / f"{ref}.mp4"
    if not video.exists():
        for p in REFS.glob(f"{ref}.*"):
            p.unlink()
        raise RuntimeError(f"yt-dlp no pudo bajar {url}: {(r.stderr or r.stdout).strip()[-300:]}")
    return video


def copiar(src, ref):
    video = REFS / f"{ref}.mp4"
    r = run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", src, "-c", "copy",
             "-movflags", "+faststart", video])
    if r.returncode:  # contenedor raro: se guarda tal cual
        video = REFS / f"{ref}{Path(src).suffix.lower()}"
        shutil.copy2(src, video)
    return video


def senales(ref):
    info = REFS / f"{ref}.info.json"
    if not info.exists():
        return {}
    d = json.loads(info.read_text())
    return {k: d.get(k) for k in ["webpage_url", "uploader", "view_count", "like_count", "comment_count", "upload_date"]
            if d.get(k) is not None} | {"descripcion": (d.get("description") or d.get("title") or "")[:300]}


def procesar(video, ref, fuente, comentario):
    dur = float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", video]).stdout or 0)
    wav = REFS / f"{ref}_16k.wav"
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", video, "-vn", "-ac", "1", "-ar", "16000", wav])
    run(["whisper-cli", "-m", MODEL, "-f", wav, "-l", "auto", "-bs", "8", "-oj", "-of", REFS / f"{ref}_frases"])
    frases = REFS / f"{ref}_frases.json"
    lineas = []
    if frases.exists():
        for s in json.loads(frases.read_text())["transcription"]:
            if s["text"].strip():
                lineas.append(f"- `{s['timestamps']['from'][3:8]}` {s['text'].strip()}")
    fr = REFS / ref / "frames"
    fr.mkdir(parents=True, exist_ok=True)
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-t", "8", "-i", video,
         "-vf", "fps=2,scale=180:-2,tile=8x2:padding=3", "-frames:v", "1", fr / "gancho_0-8s.png"])
    if dur > 0:
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", video,
             "-vf", f"fps=22/{dur:.2f},scale=150:-2,tile=11x2:padding=3", "-frames:v", "1", fr / "completo.png"])
    s = senales(ref)
    datos = ", ".join(f"{k}: {v}" for k, v in s.items() if k not in ("descripcion", "webpage_url")) or "—"
    (REFS / ref / "NOTA.md").write_text(
        f"# {ref} — pendiente de analizar\n\n"
        f"- **Llegó:** {datetime.now():%d-%b-%Y %H:%M} por «0 Referencias»\n"
        f"- **Fuente:** {s.get('webpage_url') or fuente}\n"
        f"- **Señales:** {datos}\n"
        f"- **Duración:** {dur:.1f} s\n"
        f"- **Lo que dice {kit.nombre()}:** {comentario or '(sin comentario)'}\n"
        + (f"- **Descripción del post:** {s['descripcion']}\n" if s.get("descripcion") else "")
        + f"\nFotogramas en `frames/`. Siguiente paso: analizarla con {kit.nombre()} y escribir `receta.json` "
          f"(modelo M1–M7 o capa nueva, ver `subtitulos/recetas/README.md`).\n\n"
          f"## Transcripción\n\n" + ("\n".join(lineas) or "(sin voz)") + "\n")
    return ref


def nueva(fuente, comentario=""):
    """fuente = URL o ruta a un vídeo. Devuelve el nombre refN."""
    ref = siguiente()
    if re.match(r"https?://", str(fuente)):
        return procesar(bajar(fuente, ref), ref, fuente, comentario)
    return procesar(copiar(fuente, ref), ref, f"archivo {Path(fuente).name}", comentario)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("fuente", help="enlace del reel o ruta a un vídeo")
    ap.add_argument("--comentario", default="")
    a = ap.parse_args()
    try:
        ref = nueva(a.fuente, a.comentario)
    except RuntimeError as e:
        sys.exit(str(e))
    print(f"{ref}: lista en referencias/{ref}/NOTA.md")


if __name__ == "__main__":
    main()
