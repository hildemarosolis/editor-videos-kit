"""Pegatina congelada (freeze-frame): al decir una frase, el plano se congela, la persona
sale recortada como una pegatina con borde blanco y una etiqueta con el nombre de lo que se presenta.
La voz sigue sonando; a los ~2,5 s el vídeo vuelve en seco.

Receta:
  "pegatina": [{"frase": "la toma de huellas", "nombre": "LA TIE", "rol": "toma de huellas",
                "despues_de": 0, "antes": 0.05, "dur": 2.5 | "hasta_frase": "...", "y": 1245}]
- `nombre` (obligatorio, hasta 24 caracteres): lo que se presenta (un trámite, un paso, una persona).
  `rol` (opcional): una línea corta debajo, sacada de lo que se dice.
- Una por idea nueva, separadas al menos 5 s. Cada una congela: no la pongas en una frase con gesto clave.
- La silueta sale de Vision sobre ese fotograma (gratis, sin `silueta.webm`). Se guarda en
  `assets/pegatina/` y no se recalcula si el segundo no cambia. SOLO MAC: Vision es de Apple (ver recorte.py);
  en Windows o Linux la pegatina se para con un aviso.
- `y`: arriba de la etiqueta (por defecto 1245, bajo los subtítulos). Si coincide con la caja «Comenta»,
  la etiqueta sube encima de la cabeza (y=170).
- No se combina con `impactos`, `zoom_lento` ni la pizarra en el mismo momento: congela el plano tal cual
  sale de `assets/corte.mp4`.
"""
import html
import subprocess
import sys
import tempfile
from pathlib import Path

import kit
from efectos import _find, _norm

ROOT = Path(__file__).resolve().parent.parent

CSS = """
      .pg-fondo { position: absolute; inset: 0; width: 1080px; height: 1920px; z-index: 7; overflow: hidden; background: #111; }
      .pg-fondo img { position: absolute; inset: 0; width: 1080px; height: 1920px; object-fit: cover;
                      filter: brightness(.42) saturate(.55) blur(7px); transform: scale(1.06); }
      .pg-fondo .puntos { position: absolute; inset: 0;
                          background-image: radial-gradient(rgba(255,200,0,.22) 2.2px, transparent 2.8px);
                          background-size: 28px 28px; }
      .pg-flash { position: absolute; inset: 0; width: 1080px; height: 1920px; z-index: 11; background: #fff;
                  opacity: 0; pointer-events: none; }
      .pg-stk { position: absolute; inset: 0; width: 1080px; height: 1920px; z-index: 8; pointer-events: none; }
      .pg-stk img { position: absolute; inset: 0; width: 1080px; height: 1920px;
                    filter: drop-shadow(0 22px 28px rgba(0,0,0,.6)); }
      .pg-tag { position: absolute; left: 0; width: 1080px; z-index: 9; display: flex; flex-direction: column;
                align-items: center; pointer-events: none; }
      .pg-nom { display: inline-block; background: var(--amarillo); color: #111; font-family: "Anton", sans-serif;
                line-height: 1; padding: 16px 36px 12px; text-transform: uppercase; border: 7px solid #fff;
                border-radius: 14px; box-shadow: 0 14px 26px rgba(0,0,0,.5); white-space: nowrap; }
      .pg-rol { display: inline-block; margin-top: 14px; background: #111; color: #fff; font: 40px/1 "Anton", sans-serif;
                letter-spacing: .06em; padding: 12px 22px 9px; text-transform: uppercase; border-radius: 8px;
                white-space: nowrap; }
"""


def _vision(frame_png, w, h):
    """Máscara gris (bytes w×h) de la persona en un fotograma, con el binario de recorte.py."""
    sys.path.insert(0, str(ROOT / "scripts"))
    from recorte import BIN, compilar
    compilar()
    with tempfile.TemporaryDirectory() as tmp:
        clip = Path(tmp) / "f.mp4"
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-loop", "1", "-i", str(frame_png),
                        "-frames:v", "3", "-r", "30", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "8", str(clip)],
                       check=True)
        out = subprocess.run([str(BIN), str(clip), "accurate"], capture_output=True, check=True).stdout
    if len(out) < w * h:
        raise SystemExit(f"pegatina: Vision no devolvió la máscara de {frame_png.name}")
    return out[:w * h]


LIMPIAR = """
import sys, numpy as np, cv2
m = np.frombuffer(sys.stdin.buffer.read(), np.uint8).reshape(1920, 1080)
# núcleo: donde Vision está segura (la persona sale a 255; un objeto blanco de la estantería, a ~100)
n, lab, st, _ = cv2.connectedComponentsWithStats((m > 200).astype(np.uint8), 8)
if n > 1:
    grande = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    nucleo = (lab == grande).astype(np.uint8)
    # se conserva el borde suave (pelo) cerca del núcleo; lo dudoso y suelto, fuera
    cerca = cv2.dilate(nucleo, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25)))
    quitado = int(((m > 100) & (cerca == 0)).sum())
    m = (m * cerca).astype(np.uint8)
    if quitado:
        sys.stderr.write(f"pegatina: {quitado} px dudosos fuera de la silueta\\n")
sys.stdout.buffer.write(m.tobytes())
"""


def _limpiar(mask):
    """Deja la silueta grande y quita manchas sueltas que Vision confunde con la persona (python con OpenCV,
    kit.python_opencv())."""
    try:
        r = subprocess.run([kit.python_opencv(), "-c", LIMPIAR], input=mask, capture_output=False,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError:  # el python de editor.json no existe
        r = None
    if r is None or r.returncode:
        print("pegatina: sin OpenCV (y numpy) en el python de kit.python_opencv(), la máscara va sin limpiar")
        return mask
    sys.stderr.write(r.stderr.decode(errors="replace"))
    return r.stdout


def _preparar(src, t, dst):
    """Fondo congelado (.jpg) y pegatina (.png con borde blanco) del fotograma en el segundo t."""
    dst.mkdir(parents=True, exist_ok=True)
    clave = f"t{int(round(t * 1000)):07d}"
    fondo, stk = dst / f"{clave}_fondo.jpg", dst / f"{clave}.png"
    if fondo.exists() and stk.exists():
        return fondo, stk
    with tempfile.TemporaryDirectory() as tmp:
        frame, mask = Path(tmp) / "frame.png", Path(tmp) / "mask.gray"
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{t:.3f}", "-i", str(src),
                        "-frames:v", "1", "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
                        str(frame)], check=True)
        mask.write_bytes(_limpiar(_vision(frame, 1080, 1920)))
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(frame), "-q:v", "3",
                        str(fondo)], check=True)
        # borde de pegatina: la máscara se ensancha ~18 px, se rellena de blanco y la persona va encima
        graph = ("[1:v]format=gray,split[m1][m2];"
                 "[m1]gblur=sigma=1.2[ms];"
                 "[m2]gblur=sigma=10,lut=y='if(gt(val,28),255,0)',gblur=sigma=1.6[md];"
                 "color=c=white:s=1080x1920:d=1,format=rgb24[w];[w][md]alphamerge[wb];"
                 "[0:v]format=rgb24[f];[f][ms]alphamerge[p];"
                 "[wb][p]overlay=format=auto,format=rgba[v]")
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(frame),
                        "-f", "rawvideo", "-pix_fmt", "gray", "-s", "1080x1920", "-i", str(mask),
                        "-filter_complex", graph, "-map", "[v]", "-frames:v", "1", str(stk)], check=True)
    return fondo, stk


def build_pegatina(cfg, words, total, d):
    d = Path(d)
    src = d / "assets/corte.mp4"
    seq = [(_norm(w["raw"]), w["t0"], w["t1"]) for w in words]
    cx, cy = cfg.get("centro_cara", [540, 620])
    comenta = cfg.get("_comenta")

    def at(frase, after=0.0):
        i = _find(seq, frase, after)
        if i is None:
            raise SystemExit(f"pegatina: no encuentro la frase «{frase}» (después de {after:.1f}s)")
        return seq[i][1]

    momentos = []
    for k, e in enumerate(cfg["pegatina"]):
        if not e.get("nombre"):
            raise SystemExit("pegatina: cada momento necesita «nombre»")
        if len(e["nombre"]) > 24:
            raise SystemExit(f"pegatina: «{e['nombre']}» pasa de 24 caracteres")
        t0 = max(0.0, at(e["frase"], e.get("despues_de", 0.0)) - e.get("antes", 0.05)) if e.get("frase") else e["t"]
        t1 = at(e["hasta_frase"], t0) if e.get("hasta_frase") else t0 + e.get("dur", 2.5)
        momentos.append([t0, min(t1, total), e, k])
    momentos.sort(key=lambda m: m[0])
    for a, b in zip(momentos, momentos[1:]):
        if b[0] - a[0] < 5.0:
            print(f"pegatina: aviso, «{a[2]['nombre']}» y «{b[2]['nombre']}» están a menos de 5 s")
        a[1] = min(a[1], b[0] - 0.1)  # una pegatina se acorta si la siguiente empieza antes

    parts, js, ev, win = [], [], [], []
    for t0, t1, e, n in momentos:  # n: orden en la receta (la página de revisión lo usa)
        dur = t1 - t0
        fondo, stk = _preparar(src, t0 + 0.04, d / "assets/pegatina")
        y = e.get("y", 1245)
        if comenta and comenta[0] < t1 and t0 < comenta[1] and "y" not in e:
            y = 170
            print(f"pegatina: «{e['nombre']}» coincide con «Comenta» → etiqueta arriba")
        px = min(e.get("px", 104), int(820 / (max(len(e["nombre"]), 1) * 0.47)))
        sid, data = f"pg{n}", f'data-start="{t0:.3f}" data-duration="{dur:.3f}"'
        tr = 60 + 4 * n
        rel = lambda p: p.relative_to(d).as_posix()  # noqa: E731
        g = cfg.get("_grade")  # después de un barrido de color, la pegatina va con el mismo color de cine
        tinte = f' style="filter:{g[2]} drop-shadow(0 22px 28px rgba(0,0,0,.6))"' if g and g[0] <= t0 < g[1] else ""
        fondo_f = f' style="filter:{g[2]} brightness(.42) saturate(.55) blur(7px)"' if tinte else ""
        parts.append(f'      <div class="clip pg-fondo" id="{sid}f" {data} data-track-index="{tr}">'
                     f'<img id="{sid}fi" src="{rel(fondo)}" alt=""{fondo_f}><div class="puntos"></div></div>')
        parts.append(f'      <div class="clip pg-stk" id="{sid}" {data} data-track-index="{tr + 1}" '
                     f'style="transform-origin:{cx}px {cy}px"><img src="{rel(stk)}" alt=""{tinte}></div>')
        rol = f'<div class="pg-rol" id="{sid}r">{html.escape(e["rol"])}</div>' if e.get("rol") else ""
        parts.append(f'      <div class="clip pg-tag" id="{sid}t" {data} data-track-index="{tr + 2}" style="top:{y}px">'
                     f'<div class="pg-nom" id="{sid}n" style="font-size:{px}px">{html.escape(e["nombre"])}</div>{rol}</div>')
        parts.append(f'      <div class="clip pg-flash" id="{sid}x" data-start="{t0:.3f}" data-duration="0.300" '
                     f'data-track-index="{tr + 3}"></div>')
        # foto: destello, el plano se congela y la persona se despega como pegatina
        js.append(f'tl.fromTo("#{sid}x",{{opacity:0.85}},{{opacity:0,duration:0.28,ease:"power2.out"}},{t0:.3f});')
        js.append(f'tl.fromTo("#{sid}fi",{{scale:1.06}},{{scale:1.13,duration:{dur:.3f},ease:"none"}},{t0:.3f});')
        js.append(f'tl.fromTo("#{sid}",{{scale:1,rotation:0,y:0}},{{scale:1.09,rotation:-3,y:-18,duration:0.45,'
                  f'ease:"back.out(2.2)"}},{t0 + 0.04:.3f});')
        # micromovimiento mientras dura: la pegatina se balancea un poco
        if dur > 1.2:
            js.append(f'tl.to("#{sid}",{{rotation:-1.4,y:-30,duration:{dur - 0.75:.3f},ease:"sine.inOut"}},{t0 + 0.5:.3f});')
        js.append(f'tl.fromTo("#{sid}n",{{opacity:0,scale:0.2,rotation:-24}},{{opacity:1,scale:1,rotation:-3,duration:0.42,'
                  f'ease:"back.out(2.6)"}},{t0 + 0.28:.3f});')
        if rol:
            js.append(f'tl.fromTo("#{sid}r",{{opacity:0,y:26}},{{opacity:1,y:0,duration:0.3,ease:"back.out(1.8)"}},'
                      f'{t0 + 0.46:.3f});')
        # vuelta en seco: la pegatina se vuelve a pegar al plano y el vídeo sigue
        js.append(f'tl.to("#{sid}",{{scale:1,rotation:0,y:0,duration:0.16,ease:"power2.in"}},{t1 - 0.16:.3f});')
        js.append(f'tl.to("#{sid}t",{{opacity:0,scale:0.7,duration:0.14,ease:"power2.in"}},{t1 - 0.16:.3f});')
        ev += [(t0, "obturador"), (t0 + 0.3, "pop"), (t1 - 0.05, "whoosh")]
        win.append((t0, t1))
        print(f"pegatina: «{e['nombre']}» {t0:6.2f}–{t1:6.2f}s")
    return CSS, "\n".join(parts), js, ev, win
