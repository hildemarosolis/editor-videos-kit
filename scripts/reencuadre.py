#!/usr/bin/env python3
"""Reencuadre de un vídeo horizontal (16:9) a vertical 1080×1920, plano a plano (25-oct-2026).

  .venv/bin/python scripts/reencuadre.py <origen> <de> <a> <salida.mp4>

Pensado para entrevistas con tres cámaras (cerrado del invitado, cerrado del entrevistador y general con los dos):
- Busca caras con YuNet (10 fps a 640×360) y etiqueta cada muestra; CapCut monta con fundidos,
  así que el corte vertical va al centro de cada fundido. Cada plano se clasifica:
  · una cara de 165 px o más → «cerrado»: recorte 9:16 centrado en esa cara, fijo durante el plano;
  · dos caras o caras pequeñas → «general»: pantalla partida, la persona de la izquierda
    arriba y la de la derecha abajo, cada una en una mitad de 1080×960.
- El encuadre no se mueve dentro de un plano: así lo haría un editor y no marea.
- El logo del canal (arriba a la derecha, con su cara dibujada) se ignora: solo cuentan las caras
  por debajo del 18 % superior de la imagen.

Modo `--tres` (un podcast con dos personas en la mesa y el entrevistador aparte).
El tamaño de la cara no distingue los planos (el de las dos va de 113 a 178 px), así que se cuentan:
  · una cara → «cerrado» (el entrevistador);
  · dos caras → «general»: pantalla partida, la de la izquierda arriba y la de la derecha abajo;
  · tres caras → «tres»: arriba las dos de la mesa juntas, abajo la de la derecha (el entrevistador).
  .venv/bin/python scripts/reencuadre.py <origen> <de> <a> <salida.mp4> --tres

Modo `--general` (un paseo con cámara en mano): los dos de pie en un plano abierto todo el rato, con caras
de 160-200 px que bailan alrededor del umbral del primer plano. Sin él el encuadre salta de pantalla partida
a primer plano cada pocos segundos; con él es siempre pantalla partida (el de la izquierda arriba).

Con `--general`:
  · el recorte sale del tamaño real del origen (un 4K se recorta en 4K y se reduce, no se amplía un 1080p);
  · `--modos <json>` fija el encuadre por tramos, en segundos del origen: [[de, a, "dos"|"uno"|"izq"|"der"], …].
    «dos» = pantalla partida; «uno» = primer plano de la cara más grande; «izq»/«der» = primer plano que sigue
    a la persona de ese lado (p. ej. el invitado cuando habla él). Fuera de los tramos decide solo, como siempre.
"""
import json
import statistics
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kit  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
W, H = 1920, 1080               # origen
SW, SH = 640, 360               # tamaño para buscar caras
CERRADO_MIN = 165               # ancho de cara (px del origen) desde el que es un primer plano
FPS_CARAS = 10                  # muestras por segundo para clasificar los planos


def frames(src, de, dur, fps, w, h, gray=False):
    pix = "gray" if gray else "bgr24"
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{de:.3f}", "-t", f"{dur:.3f}", "-i", str(src),
           "-vf", f"fps={fps},scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", pix, "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    c = 1 if gray else 3
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w, c) if not gray else \
        np.frombuffer(raw, np.uint8).reshape(-1, h, w)


def caras(src, de, dur):
    det = cv2.FaceDetectorYN.create(str(ROOT / "models/face_detection_yunet_2023mar.onnx"), "", (SW, SH), 0.75)
    res = []
    for k, f in enumerate(frames(src, de, dur, FPS_CARAS, SW, SH)):
        _, fs = det.detect(np.ascontiguousarray(f))
        lst = []
        for r in (fs if fs is not None else []):
            x, y, w, h = r[:4]
            if y + h / 2 < SH * 0.18:   # logo del canal
                continue
            lst.append((float(x + w / 2) * W / SW, float(y + h / 2) * H / SH, float(w) * W / SW))
        res.append((k / FPS_CARAS, lst))
    return res


TRES = "--tres" in sys.argv
GENERAL = "--general" in sys.argv
MODOS = json.loads(Path(sys.argv[sys.argv.index("--modos") + 1]).read_text()) if "--modos" in sys.argv else []


def etiqueta(l):
    """C = primer plano, G = general (dos caras), T = los tres (solo en modo --tres)."""
    if not TRES:
        return "C" if max(c[2] for c in l) >= CERRADO_MIN else "G"
    l = [c for c in l if c[2] >= 60]
    if not l:
        return None
    # una cara grande con «caras» de menos de la mitad (fotos de la estantería, PODCAST_MARO_4) sigue siendo primer plano
    grande = max(c[2] for c in l)
    if grande >= 150 and all(c[2] < grande / 2 for c in l if c[2] != grande):
        return "C"
    return "C" if len(l) == 1 and l[0][2] >= 150 else ("G" if len(l) == 2 else ("T" if len(l) >= 3 else None))


def cortes_de_camara(src, de, dur):
    """Segundos (relativos) donde cambia el plano: salto grande entre fotogramas seguidos (10 por segundo)."""
    fs = frames(src, de, dur, FPS_CARAS, 160, 90, gray=True).astype(np.float32)
    dif = np.abs(np.diff(fs, axis=0)).mean(axis=(1, 2))
    umbral = max(18.0, float(np.median(dif)) * 4)
    cs, ult = [], -10
    for k, d in enumerate(dif):
        if d > umbral and k - ult > 5:   # como mucho un corte cada medio segundo
            cs.append((k + 1) / FPS_CARAS); ult = k
    return cs


def planos_general(src, de, a):
    """Modo --general: pantalla partida siempre, con las caras recolocadas en cada plano de cámara."""
    det, dur = caras(src, de, a - de), a - de
    bordes = [0.0] + cortes_de_camara(src, de, dur) + [dur]
    out = []
    for t0, t1 in zip(bordes, bordes[1:]):
        ls = [l for t, l in det if t0 <= t < t1 and l]
        izq = [c for l in ls for c in l if c[0] < W / 2 and c[2] >= 60]
        der = [c for l in ls for c in l if c[0] >= W / 2 and c[2] >= 60]
        med = lambda cs: [round(statistics.median(c[0] for c in cs)), round(statistics.median(c[1] for c in cs))] if cs else None
        out.append({"de": round(t0, 2), "a": round(t1, 2), "tipo": "general", "izq": med(izq), "der": med(der)})
    # un plano sin una de las caras (alguien de espaldas, un plano de recurso): la del plano anterior o siguiente
    for lado in ("izq", "der"):
        vistos = [p[lado] for p in out if p[lado]]
        defecto = vistos[0] if vistos else ([560, 470] if lado == "izq" else [1400, 520])
        ult = None
        for p in out:
            p[lado] = p[lado] or ult or defecto
            ult = p[lado]
    return out


def planos(src, de, a):
    if GENERAL:
        return planos_general(src, de, a)
    """Planos del tramo. CapCut monta con fundidos, así que no hay cortes secos que buscar: se etiqueta
    cada muestra (C = primer plano, G = general), se suaviza y el corte va al centro de cada fundido."""
    det = caras(src, de, a - de)
    eti, ult = [], "G"
    for _, l in det:
        e = "G" if GENERAL else ((etiqueta(l) or ult) if l else ult)
        eti.append(e); ult = e
    k = 2  # mediana de 5 muestras (0,5 s): quita parpadeos y fundidos cortos
    eti = [max("CGT", key=lambda x: eti[max(0, i - k):i + k + 1].count(x)) for i in range(len(eti))]
    tramos, i = [], 0
    while i < len(eti):
        j = i
        while j + 1 < len(eti) and eti[j + 1] == eti[i]:
            j += 1
        tramos.append([i, j, eti[i]]); i = j + 1
    # tramos de menos de 0,6 s se funden con el anterior
    limpio = []
    for t in tramos:
        if limpio and (t[1] - t[0] + 1) / FPS_CARAS < 0.6:
            limpio[-1][1] = t[1]
        elif limpio and limpio[-1][2] == t[2]:
            limpio[-1][1] = t[1]
        else:
            limpio.append(t)
    out, dur = [], a - de
    for n, (i, j, e) in enumerate(limpio):
        t0 = 0.0 if n == 0 else (i - 0.5) / FPS_CARAS
        t1 = dur if n == len(limpio) - 1 else (j + 0.5) / FPS_CARAS
        muestras = [l for (t, l), x in zip(det[i:j + 1], eti[i:j + 1]) if l]
        if e == "T":
            ts = [sorted(c for c in l if c[2] >= 60)[:3] for l in muestras if len([c for c in l if c[2] >= 60]) >= 3]
            md = lambda k: [round(statistics.median(t[k][0] for t in ts)), round(statistics.median(t[k][1] for t in ts))] if ts else None
            out.append({"de": round(t0, 2), "a": round(t1, 2), "tipo": "tres", "izq": md(0), "medio": md(1), "der": md(2)})
            continue
        if e == "C":
            umbral = 150 if TRES else CERRADO_MIN
            gr = [max(l, key=lambda c: c[2]) for l in muestras if max(c[2] for c in l) >= umbral]
            out.append({"de": round(t0, 2), "a": round(t1, 2), "tipo": "cerrado",
                        "cara": [round(statistics.median(c[0] for c in gr)), round(statistics.median(c[1] for c in gr))]})
        else:
            lim = 10 ** 6 if TRES else CERRADO_MIN
            dos = [l for l in muestras if len([c for c in l if c[2] >= 60]) == 2] if TRES else muestras
            izq = [c for l in dos for c in l if c[0] < W / 2 and c[2] < lim and c[2] >= 60]
            der = [c for l in dos for c in l if c[0] >= W / 2 and c[2] < lim and c[2] >= 60]
            med = lambda cs: [round(statistics.median(c[0] for c in cs)), round(statistics.median(c[1] for c in cs))] if cs else None
            out.append({"de": round(t0, 2), "a": round(t1, 2), "tipo": "general", "izq": med(izq), "der": med(der)})
    # plano general sin una de las dos caras: la posición típica de los demás planos generales
    gen = [p for p in out if p["tipo"] == "general"]
    for lado, defecto in (("izq", [560, 470]), ("der", [1400, 520])):
        vistos = [p[lado] for p in gen if p[lado]]
        tip = [statistics.median(v[0] for v in vistos), statistics.median(v[1] for v in vistos)] if vistos else defecto
        for p in gen:
            p[lado] = p[lado] or [round(tip[0]), round(tip[1])]
    for p in out:   # plano de tres sin muestras completas: posiciones típicas medidas en el podcast
        if p["tipo"] == "tres":
            p["izq"] = p["izq"] or [324, 404]; p["medio"] = p["medio"] or [914, 392]; p["der"] = p["der"] or [1356, 383]
    return out


def caja(cx, cy, w, h, alto=0.4):
    """Recorte w×h con la cara en el centro horizontal y a un 40 % desde arriba (o `alto`), dentro del origen."""
    x = min(max(cx - w / 2, 0), W - w)
    y = min(max(cy - h * alto, 0), H - h)
    return int(x) // 2 * 2, int(y) // 2 * 2


def render(src, de, a, ps, salida):
    fc, n = [], len(ps)
    for i, p in enumerate(ps):
        t0, t1 = p["de"], p["a"]   # relativos: la entrada ya empieza en «de» (-ss), ver abajo
        tr = f"[0:v]trim={t0:.4f}:{t1:.4f},setpts=PTS-STARTPTS"
        if p["tipo"] == "cerrado":
            cw = 608
            x, _ = caja(p["cara"][0], p["cara"][1], cw, H)
            fc.append(f"{tr},crop={cw}:{H}:{x}:0,scale=1080:1920:flags=lanczos,setsar=1[v{i}]")
        elif p["tipo"] == "tres":
            # arriba las dos de la mesa (un solo recorte que las abarca), abajo la de la derecha
            (xa, ya), (xb, yb), (xc, yc) = p["izq"], p["medio"], p["der"]
            ch1 = min(H, max(640, int((xb - xa + 420) * 8 / 9))) // 2 * 2; cw1 = int(ch1 * 9 / 8) // 2 * 2
            x1, y1 = caja((xa + xb) / 2, (ya + yb) / 2, cw1, ch1)
            ch2 = 600; cw2 = int(ch2 * 9 / 8) // 2 * 2
            x2, y2 = caja(xc, yc, cw2, ch2)
            fc.append(f"{tr},split[a{i}][b{i}]")
            fc.append(f"[a{i}]crop={cw1}:{ch1}:{x1}:{y1},scale=1080:960:flags=lanczos[t{i}]")
            fc.append(f"[b{i}]crop={cw2}:{ch2}:{x2}:{y2},scale=1080:960:flags=lanczos[u{i}]")
            fc.append(f"[t{i}][u{i}]vstack,drawbox=x=0:y=957:w=1080:h=6:color=black:t=fill,setsar=1[v{i}]")
        else:
            ch = 600; cw = int(ch * 9 / 8) // 2 * 2
            x1, y1 = caja(*p["izq"], cw, ch); x2, y2 = caja(*p["der"], cw, ch)
            fc.append(f"{tr},split[a{i}][b{i}]")
            fc.append(f"[a{i}]crop={cw}:{ch}:{x1}:{y1},scale=1080:960:flags=lanczos[t{i}]")
            fc.append(f"[b{i}]crop={cw}:{ch}:{x2}:{y2},scale=1080:960:flags=lanczos[u{i}]")
            fc.append(f"[t{i}][u{i}]vstack,drawbox=x=0:y=957:w=1080:h=6:color=black:t=fill,setsar=1[v{i}]")
    fc.append("".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[v]")
    fc.append(f"[0:a]atrim=0:{a - de:.4f},asetpts=PTS-STARTPTS[a]")
    # se lee solo el tramo (-ss/-t delante de -i, preciso al recodificar): con trim desde el principio de un
    # original de una hora, pasado el minuto 53 la pista de audio salía vacía
    cmd = ["ffmpeg", "-v", "error", "-y", "-ss", f"{de:.4f}", "-t", f"{a - de:.4f}", "-i", str(src),
           "-filter_complex", ";".join(fc),
           "-map", "[v]", "-map", "[a]", "-r", "30", *kit.h264("14M"),
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", str(salida)]
    subprocess.run(cmd, check=True)


def render_seguir(src, de, a, salida):
    """Modo --general: pantalla partida que sigue a cada cara con suavidad (cámara en mano, gente que se mueve).
    Posición de cada cara cada 0,1 s → se rellenan los huecos, se suaviza 1,5 s (y los cortes de cámara
    reinician el suavizado) y cada fotograma se recorta en Python. El audio va tal cual."""
    dur = a - de
    det = caras(src, de, dur)
    n = len(det)
    cortes = [int(round(c * FPS_CARAS)) for c in cortes_de_camara(src, de, dur)]
    pos = {"izq": [None] * n, "der": [None] * n, "sola": [None] * n}
    for k, (_, l) in enumerate(det):
        cs = [c for c in l if c[2] >= 60]
        if cs:
            c = max(cs, key=lambda c: c[2]); pos["sola"][k] = (c[0], c[1])
        for lado, ok in (("izq", lambda c: c[0] < W / 2), ("der", lambda c: c[0] >= W / 2)):
            cs = [c for c in l if ok(c) and c[2] >= 60]
            if cs:
                c = max(cs, key=lambda c: c[2]); pos[lado][k] = (c[0], c[1])
    # pantalla partida o primer plano, muestra a muestra: la cámara es una sola, en mano, y pasa
    # de los dos a uno solo con un barrido, no con un corte. Se decide por mayoría en 1,5 s y ningún modo dura
    # menos de 1,2 s; cada cambio de modo es un corte seco y reinicia el suavizado.
    def a_dos(l):   # dos caras grandes parecidas (las de las mesas del fondo no cuentan)
        cs = [c for c in l if c[2] >= 60]
        return len(cs) >= 2 and sorted(c[2] for c in cs)[-2] >= 0.45 * max(c[2] for c in cs)
    crudo = np.array([a_dos(l) for _, l in det], float)
    modo = np.array([crudo[max(0, k - 7):k + 8].mean() >= 0.4 for k in range(n)])
    cambia = True
    while cambia:   # tramos de menos de 1,2 s se funden con el anterior
        cambia = False
        ini = [0] + [k for k in range(1, n) if modo[k] != modo[k - 1]] + [n]
        for i0, i1 in zip(ini, ini[1:]):
            if i1 - i0 < 12 and i0 > 0:
                modo[i0:i1] = modo[i0 - 1]; cambia = True; break
    lado_uno = ["sola"] * n
    for t0, t1, m in MODOS:   # encuadre fijado a mano por tramos (segundos del origen)
        for k in range(n):
            if t0 <= de + k / FPS_CARAS < t1:
                modo[k] = m == "dos"
                lado_uno[k] = m if m in ("izq", "der") else "sola"
    ini = [0] + [k for k in range(1, n) if modo[k] != modo[k - 1] or lado_uno[k] != lado_uno[k - 1]] + [n]
    tramos = sorted(set(ini + [c for c in cortes if 0 < c < n]))
    suave = {}
    for lado, defecto in (("izq", (560, 470)), ("der", (1400, 520)), ("sola", (960, 470))):
        v = pos[lado]
        vistos = [x for x in v if x]
        ult = vistos[0] if vistos else defecto
        rel = []
        for x in v:   # huecos: la última posición vista
            ult = x or ult; rel.append(ult)
        arr = np.array(rel, np.float32)
        out = np.empty_like(arr)
        for i0, i1 in zip(tramos, tramos[1:]):   # suavizado de 1,5 s dentro de cada plano de cámara
            seg = arr[i0:i1]
            k = min(15, len(seg))
            ker = np.ones(k) / k
            for d in (0, 1):
                pad = np.pad(seg[:, d], (k // 2, k - 1 - k // 2), mode="edge")
                out[i0:i1, d] = np.convolve(pad, ker, "valid")
        suave[lado] = out
    ch = 600; cw = int(ch * 9 / 8) // 2 * 2
    fps = 30
    total = int(dur * fps)
    # se recorta en el tamaño real del origen: las posiciones van en 1920×1080 y se multiplican por S
    ow, oh = (int(v) for v in subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
              "stream=width,height", "-of", "csv=p=0", str(src)], capture_output=True, text=True,
              check=True).stdout.split()[0].split(",")[:2])   # la primera línea (los DJI traen grupos de pistas)
    S = ow / W
    if abs(oh / H - S) > 0.01:
        raise SystemExit(f"el origen no es 16:9 ({ow}×{oh})")
    def rec(im, x, y, w, h):
        return im[int(y * S):int((y + h) * S), int(x * S):int((x + w) * S)]
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{de:.4f}", "-t", f"{dur:.4f}", "-i", str(src),
                            "-vf", f"fps={fps}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "1080x1920",
                            "-r", str(fps), "-i", "-", "-ss", f"{de:.4f}", "-t", f"{dur:.4f}", "-i", str(src),
                            "-map", "0:v", "-map", "1:a", *kit.h264("14M"), "-pix_fmt", "yuv420p",
                            "-c:a", "aac", "-b:a", "192k", "-shortest", str(salida)], stdin=subprocess.PIPE)
    tam = ow * oh * 3
    for f in range(total + 2):
        buf = dec.stdout.read(tam)
        if len(buf) < tam:
            break
        im = np.frombuffer(buf, np.uint8).reshape(oh, ow, 3)
        k = min(n - 1, int(f / fps * FPS_CARAS))
        if modo[k]:
            mitades = []
            for lado in ("izq", "der"):
                x, y = caja(float(suave[lado][k][0]), float(suave[lado][k][1]), cw, ch, alto=0.47)   # sitio para el sombrero
                mitades.append(cv2.resize(rec(im, x, y, cw, ch), (1080, 960), interpolation=cv2.INTER_LANCZOS4))
            fr = np.vstack(mitades)
            fr[957:963] = 0
        else:
            lado = lado_uno[k]
            x, _ = caja(float(suave[lado][k][0]), float(suave[lado][k][1]), 608, H)
            fr = cv2.resize(rec(im, x, 0, 608, H), (1080, 1920), interpolation=cv2.INTER_LANCZOS4)
        enc.stdin.write(fr.tobytes())
    enc.stdin.close(); dec.stdout.close()
    enc.wait(); dec.wait()
    if enc.returncode:
        raise SystemExit(f"falló el render de {salida}")


def main():
    args = [x for i, x in enumerate(sys.argv[1:], 1) if not x.startswith("--") and sys.argv[i - 1] != "--modos"]
    src, de, a, salida = Path(args[0]).expanduser(), float(args[1]), float(args[2]), Path(args[3])
    salida.parent.mkdir(parents=True, exist_ok=True)
    if GENERAL:
        render_seguir(src, de, a, salida)
        print(f"→ {salida} (pantalla partida que sigue las caras)")
        return
    ps = planos(src, de, a)
    salida.with_suffix(".planos.json").write_text(json.dumps(ps, indent=1))
    for p in ps:
        print(f"{p['de']:7.2f}–{p['a']:7.2f}  {p['tipo']:8s} {p.get('cara') or (p['izq'], p.get('medio'), p['der'])}")
    render(src, de, a, ps, salida)
    print(f"→ {salida}")


if __name__ == "__main__":
    main()
