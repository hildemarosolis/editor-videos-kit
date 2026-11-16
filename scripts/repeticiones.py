#!/usr/bin/env python3
"""Busca tomas repetidas (te equivocas y repites la frase) en un vídeo en bruto.

  python3 scripts/repeticiones.py raw/MI_VIDEO.MOV [--ventana 15] [--min 6]

Transcribe palabra a palabra y avisa cuando una secuencia de --min palabras o más
se repite dentro de --ventana segundos. Propone quitar la PRIMERA aparición (la fallida)
con el formato de `preparar.py --quitar a-b`. Siempre hay que confirmarlo con el usuario.

Con --min 6 solo salen repeticiones largas: las cortas suelen ser intencionadas
(«se ha encarecido el alquiler, se ha encarecido la comida»). Aun así, una repetición
larga puede ser retórica («te van a recibir el caso. Perfecto, te van a recibir el caso»):
por eso son CANDIDATAS que confirma el usuario, nunca cortes automáticos.

Límite conocido: whisper a veces junta en una sola las dos tomas casi idénticas
(ya ha pasado); ahí solo lo detecta escuchar o mirar la boca en los fotogramas.
"""
import argparse
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STOP = {"de", "la", "el", "que", "y", "a", "en", "los", "las", "un", "una", "es", "lo", "por", "con", "se", "no", "te"}


def norm(s):
    return re.sub(r"[^\wáéíóúüñ]", "", s.lower())


def palabras(video):
    with tempfile.TemporaryDirectory() as t:
        wav, js = Path(t) / "a.wav", Path(t) / "a"
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(video), "-vn", "-ac", "1",
                        "-ar", "16000", str(wav)], check=True)
        subprocess.run(["whisper-cli", "-m", str(ROOT / "models/ggml-large-v3-turbo-q5_0.bin"), "-f", str(wav),
                        "-l", "es", "-bs", "8", "-ml", "1", "-sow", "-oj", "-of", str(js)], check=True, capture_output=True)
        segs = json.loads(Path(str(js) + ".json").read_text())["transcription"]
    return [(norm(s["text"]), s["offsets"]["from"] / 1000, s["offsets"]["to"] / 1000, s["text"].strip())
            for s in segs if norm(s["text"])]


def buscar(w, ventana, minimo):
    hallazgos, usado = [], set()
    for n in range(8, minimo - 1, -1):  # de la secuencia más larga a la más corta
        vistos = {}
        for i in range(len(w) - n + 1):
            clave = tuple(x[0] for x in w[i:i + n])
            if sum(1 for c in clave if c not in STOP) < 2:
                continue
            if clave in vistos:
                j = vistos[clave]
                if w[i][1] - w[j][1] <= ventana and not (set(range(j, j + n)) & usado):
                    a, b = w[j][1], w[i][1] - 0.05
                    hallazgos.append((a, b, " ".join(x[3] for x in w[j:j + n])))
                    usado |= set(range(j, i + n))
            vistos[clave] = i
    return sorted(hallazgos)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--ventana", type=float, default=15)
    ap.add_argument("--min", type=int, default=6)
    a = ap.parse_args()
    h = buscar(palabras(a.video), a.ventana, a.min)
    if not h:
        print(f"{Path(a.video).name}: sin repeticiones")
    for x, y, txt in h:
        print(f"{Path(a.video).name}: repetida «{txt}» → propuesta --quitar {x:.2f}-{y:.2f}")


if __name__ == "__main__":
    main()
