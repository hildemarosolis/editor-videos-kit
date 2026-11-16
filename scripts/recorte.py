#!/usr/bin/env python3
"""Recorta la silueta de la persona en todo el vídeo (Vision de Apple, sin instalar nada). SOLO MAC: necesita
`swiftc` (Command Line Tools de Xcode: `xcode-select --install`); en Windows o Linux se para con un aviso.

  python3 scripts/recorte.py proyectos/<VIDEO> [--calidad accurate|balanced|fast]

Sale `assets/silueta.webm`: el vídeo con transparencia (VP9 + alfa) fuera de la persona. En la
composición va encima de los efectos «detrás de ti» (titular gigante, portada, gráfico) y debajo
de los subtítulos. Se compila `scripts/bin/recorte` desde `recorte.swift` la primera vez.
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SWIFT, BIN = ROOT / "scripts/recorte.swift", ROOT / "scripts/bin/recorte"


def compilar():
    if BIN.exists() and BIN.stat().st_mtime > SWIFT.stat().st_mtime:
        return
    if sys.platform != "darwin" or not shutil.which("swiftc"):
        sys.exit("recorte: la silueta usa Vision de Apple y solo funciona en un Mac con swiftc "
                 "(instálalo con: xcode-select --install)")
    BIN.parent.mkdir(exist_ok=True)
    tmp = BIN.parent / "main.swift"  # con este nombre swiftc admite código suelto y await arriba
    shutil.copy(SWIFT, tmp)
    try:
        subprocess.run(["swiftc", "-O", str(tmp), "-o", str(BIN)], check=True)
    finally:
        tmp.unlink()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--calidad", default="accurate")
    a = ap.parse_args()
    d = Path(a.dir)
    src, dst = d / "assets/corte.mp4", d / "assets/silueta.webm"
    compilar()
    w, h, fps = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                "stream=width,height,r_frame_rate", "-of", "csv=p=0", str(src)],
                               capture_output=True, text=True, check=True).stdout.strip().split(",")[:3]
    mask = subprocess.Popen([str(BIN), str(src), a.calidad], stdout=subprocess.PIPE)
    # la máscara se suaviza un poco en el borde; el vídeo original pone el color
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                    "-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{w}x{h}", "-r", fps, "-i", "-",
                    "-i", str(src), "-filter_complex",
                    "[0:v]gblur=sigma=1.4[m];[1:v][m]alphamerge,format=yuva420p[v]",
                    "-map", "[v]", "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "0", "-crf", "28",
                    "-row-mt", "1", "-deadline", "good", "-cpu-used", "4", "-auto-alt-ref", "0", "-an", str(dst)],
                   stdin=mask.stdout, check=True)
    if mask.wait():
        sys.exit("recorte: Vision falló")
    print(f"recorte: {dst}")


if __name__ == "__main__":
    main()
