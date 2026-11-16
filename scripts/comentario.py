#!/usr/bin/env python3
"""Captura de un comentario público → PNG para la tarjeta del vídeo:
captura real, foto de perfil difuminada, nombre visible. Un DM nunca pasa por aquí.

  .venv/bin/python scripts/comentario.py <captura> <salida.png> [--recorte x0 y0 x1 y1] [--avatar cx cy r]

- --recorte: el trozo de la captura que se ve (en píxeles de la captura): sin los botones «Me gusta/Responder».
  Sin él, la captura entera.
- --tapar: rectángulos que se rellenan con el color de fondo (los botones al lado de la foto, que el recorte
  no puede quitar sin cortarla). Se puede repetir.
- --avatar: el círculo de la foto de perfil. Sin él se busca solo (el círculo más grande del tercio izquierdo);
  si no lo encuentra, falla: mejor parar que publicar una cara sin difuminar.
Lo llama efectos.py (pieza "comentarios" de la receta). Necesita OpenCV: el python de kit.python_opencv().
"""
import argparse
import sys

import cv2
import numpy as np


def buscar_avatar(img):
    """La foto de perfil: la mancha más grande y casi cuadrada pegada a la izquierda, sobre el color de fondo
    de la app (los círculos de Hough fallan con fotos oscuras o sin borde). Las letras son pequeñas y la
    burbuja de un mensaje es alargada, así que no cuentan."""
    h, w = img.shape[:2]
    borde = np.concatenate([img[0], img[-1], img[:, 0], img[:, -1]])
    fondo = np.median(borde, axis=0)
    mask = (np.abs(img.astype(int) - fondo).max(axis=2) > 28).astype(np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    n, _, st, _ = cv2.connectedComponentsWithStats(mask)
    lado, mejor = min(h, w), None
    for x, y, bw, bh, area in st[1:]:
        if x > w * 0.22 or not (0.8 < bw / bh < 1.25) or bw < lado * 0.12 or bw > lado * 0.75:
            continue
        if area / (bw * bh) < 0.45:  # un aro o un trazo, no una foto
            continue
        if mejor is None or bw > mejor[2]:
            mejor = (x, y, bw, bh)
    if not mejor:
        return None
    x, y, bw, bh = mejor
    return int(x + bw / 2), int(y + bh / 2), int(max(bw, bh) / 2)


def difuminar(img, cx, cy, r):
    """Pixelado fuerte + desenfoque dentro del círculo (un poco más grande, para tapar el borde de la foto)."""
    r2 = int(r * 1.08)
    x0, y0, x1, y1 = max(0, cx - r2), max(0, cy - r2), min(img.shape[1], cx + r2), min(img.shape[0], cy + r2)
    trozo = img[y0:y1, x0:x1]
    peq = cv2.resize(trozo, (6, 6), interpolation=cv2.INTER_LINEAR)
    pix = cv2.GaussianBlur(cv2.resize(peq, (x1 - x0, y1 - y0), interpolation=cv2.INTER_NEAREST), (0, 0), r2 / 4)
    mask = np.zeros(trozo.shape[:2], np.uint8)
    cv2.circle(mask, (cx - x0, cy - y0), r2, 255, -1)
    trozo[mask > 0] = pix[mask > 0]
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("captura")
    ap.add_argument("salida")
    ap.add_argument("--recorte", type=int, nargs=4, metavar=("X0", "Y0", "X1", "Y1"))
    ap.add_argument("--avatar", type=int, nargs=3, metavar=("CX", "CY", "R"))
    ap.add_argument("--tapar", type=int, nargs=4, action="append", default=[], metavar=("X0", "Y0", "X1", "Y1"),
                    help="rellena con el color de fondo (los botones que quedan al lado de la foto)")
    a = ap.parse_args()
    img = cv2.imread(a.captura)
    if img is None:
        sys.exit(f"no puedo leer {a.captura}")
    av = tuple(a.avatar) if a.avatar else buscar_avatar(img)
    if not av:
        sys.exit(f"{a.captura}: no encuentro la foto de perfil; pásala con --avatar cx cy r")
    img = difuminar(img, *av)
    borde = np.concatenate([img[0], img[-1], img[:, 0], img[:, -1]])
    for x0, y0, x1, y1 in a.tapar:
        img[y0:y1, x0:x1] = np.median(borde, axis=0)
    if a.recorte:
        x0, y0, x1, y1 = a.recorte
        img = img[y0:y1, x0:x1]
    cv2.imwrite(a.salida, img)
    print(f"comentario: {a.salida} ({img.shape[1]}×{img.shape[0]}, foto difuminada en {av})")


if __name__ == "__main__":
    main()
