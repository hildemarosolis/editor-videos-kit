#!/usr/bin/env python3
"""Centro de la cara (YuNet) en el corte de un proyecto: mediana de varios fotogramas.
Uso: .venv/bin/python scripts/cara.py proyectos/<VIDEO>   (el python con OpenCV: kit.python_opencv())"""
import sys, statistics
import cv2
d = sys.argv[1]
cap = cv2.VideoCapture(f"{d}/assets/corte.mp4")
n = cap.get(cv2.CAP_PROP_FRAME_COUNT); fps = cap.get(cv2.CAP_PROP_FPS)
det = cv2.FaceDetectorYN.create("models/face_detection_yunet_2023mar.onnx", "", (1080, 1920), 0.7)
cx, cy, top = [], [], []
for k in range(1, 9):
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(n * k / 9)); ok, f = cap.read()
    if not ok: continue
    # YuNet falla con caras muy grandes (primeros planos a 1080p): se detecta a 1/3 y se reescala
    s = 3; small = cv2.resize(f, (f.shape[1] // s, f.shape[0] // s))
    det.setInputSize((small.shape[1], small.shape[0])); _, faces = det.detect(small)
    if faces is None: continue
    x, y, w, h = [v * s for v in max(faces, key=lambda r: r[2] * r[3])[:4]]
    cx.append(x + w / 2); cy.append(y + h / 2); top.append(y)
print(f"[{statistics.median(cx):.0f}, {statistics.median(cy):.0f}]  cabeza desde y≈{min(top):.0f}")
