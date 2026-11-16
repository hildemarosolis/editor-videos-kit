"""Efectos «detrás de ti» (banco de efectos): van entre el vídeo y la persona recortada.

Necesitan `assets/silueta.webm` (scripts/recorte.py). La silueta se pone encima solo mientras
dura cada efecto, así no tapa logos, tarjetas ni pastillas el resto del vídeo.

Receta:
  "detras": [{"tipo": "titular", "texto": "EL DATO|QUE IMPORTA", "acento": ["IMPORTA"],
              "frase": "...", "despues_de": 0, "dur": 3.0 | "hasta_frase": "...", "y": 240, "px": 270}]
  ("|" parte la línea)
  "detras": [{"tipo": "revista", "cabecera": "REGULARIZACIÓN", "numero": "500.000", "numero_txt": "personas|pueden pedirla",
              "titular": "LO QUE|NADIE|TE CUENTA", "acento": ["NADIE"], "ante": "EL NÚMERO DE LA SEMANA",
              "fecha": "Nº 47 · OCT 2026", "frase": "...", "dur": 3.0}]
  Portada de revista: fondo aclarado como papel, cabecera gigante detrás de la cabeza,
  y delante el número grande, los titulares, la fecha y un código de barras.
  "detras": [{"tipo": "comparar", "valor_antes": "3 MESES", "valor_despues": "48 HORAS", "txt_antes": "hoy",
              "txt_despues": "la propuesta", "etiqueta_antes": "ANTES", "etiqueta_despues": "DESPUÉS",
              "frase": "...", "dur": 3.2, "fuente": "..."}]
  Antes y después a tu espalda (over-the-shoulder): una tarjeta de cristal sube por detrás de
  los hombros; a un lado el «antes» (se tacha) y al otro el «después» en amarillo. Valores de hasta 16 caracteres.
  Cada cifra es un dato: con su fuente.
"""
import html
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kit  # noqa: E402
from efectos import _find, _norm  # noqa: E402

CSS = """
      #silueta {{ position: absolute; inset: 0; width: 1080px; height: 1920px; object-fit: cover; z-index: 6;
                  opacity: 0; pointer-events: none; }}
      .dt-sombra {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1100px; z-index: 1;
                    background: linear-gradient(rgba(0,0,0,.62), rgba(0,0,0,.35) 60%, rgba(0,0,0,0)); }}
      .dt-tit {{ position: absolute; left: 0; width: 1080px; z-index: 2; text-align: center;
                 font-family: "Anton", sans-serif; line-height: .92; text-transform: uppercase; color: #fff;
                 text-shadow: 0 14px 40px rgba(0,0,0,.55); }}
      .dt-tit .l {{ display: inline-block; }}
      .dt-tit .acc {{ color: var(--amarillo); }}
      .rv-papel {{ position: absolute; inset: 0; width: 1080px; height: 1920px; z-index: 1; opacity: 0;
                   background: linear-gradient(rgba(247,242,232,.72), rgba(247,242,232,.5) 55%, rgba(247,242,232,.25)); }}
      .rv-cab {{ position: absolute; left: 0; width: 1080px; top: 150px; z-index: 2; text-align: center; white-space: nowrap;
                 font-family: "Anton", sans-serif; line-height: .86; color: #e2261b; letter-spacing: -.01em; }}
      .rv-delante {{ position: absolute; inset: 0; width: 1080px; height: 1920px; z-index: 7; pointer-events: none; opacity: 0;
                     font-family: "Anton", sans-serif; color: #111; }}
      .rv-top {{ position: absolute; left: 70px; right: 70px; top: 96px; display: flex; justify-content: space-between;
                 font: 30px/1 "Anton", sans-serif; letter-spacing: .14em; color: #111; text-transform: uppercase; }}
      .rv-num {{ position: absolute; left: 70px; top: 720px; width: 330px; }}
      .rv-num .ante {{ font: 30px/1.1 "Anton", sans-serif; letter-spacing: .12em; color: #e2261b; text-transform: uppercase; }}
      .rv-num b {{ display: block; font: 150px/0.95 "Anton", sans-serif; font-weight: 400; color: #e2261b; }}
      .rv-num .txt {{ font: 40px/1.1 "Anton", sans-serif; color: #111; text-transform: uppercase; }}
      .rv-tit {{ position: absolute; right: 70px; top: 760px; width: 330px; text-align: right;
                 font: 74px/0.95 "Anton", sans-serif; color: #111; text-transform: uppercase; }}
      .rv-tit .acc {{ color: #e2261b; }}
      .rv-barras {{ position: absolute; left: 70px; top: 1500px; width: 200px; height: 110px; background: #fff;
                    padding: 10px 12px; box-sizing: border-box; display: flex; gap: 3px; align-items: stretch; }}
      .rv-barras i {{ display: block; background: #111; }}
      .rv-marco {{ position: absolute; inset: 34px; border: 4px solid #111; }}
      .dt-cmp {{ position: absolute; left: 50px; width: 980px; z-index: 2; border-radius: 30px; overflow: hidden;
                 background: rgba(14,14,14,.72); border: 3px solid rgba(255,255,255,.14);
                 backdrop-filter: blur(12px); box-shadow: 0 24px 50px rgba(0,0,0,.45); }}
      .dt-cmp::before {{ content: ""; position: absolute; left: 0; top: 0; width: 100%; height: 10px; background: var(--amarillo); }}
      .dt-cmp .col {{ position: absolute; top: 46px; width: 320px; display: flex; flex-direction: column; gap: 10px; }}
      .dt-cmp .col.a {{ left: 34px; text-align: left; align-items: flex-start; }}
      .dt-cmp .col.d {{ right: 34px; text-align: right; align-items: flex-end; }}
      .dt-cmp .et {{ font: 32px/1 "Anton", sans-serif; letter-spacing: .14em; text-transform: uppercase; padding: 8px 14px 6px;
                     border-radius: 8px; }}
      .dt-cmp .a .et {{ background: #2c2c2c; color: #cfcfcf; }}
      .dt-cmp .d .et {{ background: var(--amarillo); color: #111; }}
      .dt-cmp .v {{ position: relative; font-family: "Anton", sans-serif; line-height: 1; text-transform: uppercase; white-space: nowrap; }}
      .dt-cmp .a .v {{ color: #e8e8e8; }}
      .dt-cmp .d .v {{ color: var(--amarillo); text-shadow: 0 0 30px rgba(255,200,0,.35); }}
      .dt-cmp .tacha {{ position: absolute; left: -6px; right: -6px; top: 52%; height: 10px; background: #ff4d4d;
                        transform-origin: 0 50%; transform: scaleX(0) rotate(-4deg); border-radius: 5px; }}
      .dt-cmp .tx {{ font: 34px/1.1 "Anton", sans-serif; color: #fff; opacity: .85; text-transform: uppercase; }}
"""


def _lineas(texto, acento):
    return "<br>".join(" ".join(f'<span class="acc">{html.escape(p)}</span>' if p in acento else html.escape(p)
                                for p in linea.split(" ")) for linea in texto.split("|"))


def _revista(e, sid, t0, t1, parts, js, ev):
    """Portada de revista: papel y cabecera detrás de la persona; número, titulares y código de barras delante."""
    dur = t1 - t0
    cab = e.get("cabecera", "")
    px = min(e.get("px", 300), int(1000 / (max(len(cab), 1) * 0.45)))  # Anton ~0,45 em por carácter
    barras = "".join(f'<i style="width:{w}px"></i>' for w in [3, 1, 2, 1, 3, 2, 1, 1, 3, 1, 2, 3, 1, 2, 1, 3, 1, 2, 2, 1, 3, 1])
    data = f'data-start="{t0:.3f}" data-duration="{dur:.3f}"'
    parts.append(f'      <div class="clip rv-papel" id="{sid}p" {data} data-track-index="24"></div>')
    # la cabecera va detrás de la cabeza: su mitad de abajo queda tapada por la coronilla (como en las revistas)
    cy = e.get("_cara_y", 620)
    top = e.get("y", max(110, int(cy - 150 - 0.55 * px * 0.86)))
    parts.append(f'      <div class="clip rv-cab" id="{sid}" {data} data-track-index="25" style="font-size:{px}px;top:{top}px">'
                 f'{html.escape(cab)}</div>')
    num = ""
    if e.get("numero"):
        num = (f'<div class="rv-num" id="{sid}n"><div class="ante">{html.escape(e.get("ante", ""))}</div>'
               f'<b>{html.escape(e["numero"])}</b><div class="txt">{_lineas(e.get("numero_txt", ""), [])}</div></div>')
    tit = f'<div class="rv-tit" id="{sid}t">{_lineas(e.get("titular", ""), e.get("acento", []))}</div>' if e.get("titular") else ""
    parts.append(f'      <div class="clip rv-delante" id="{sid}d" {data} data-track-index="26"><div class="rv-marco"></div>'
                 f'<div class="rv-top"><span>{html.escape(e.get("revista", kit.usuario()))}</span>'
                 f'<span>{html.escape(e.get("fecha", ""))}</span></div>{num}{tit}'
                 f'<div class="rv-barras" id="{sid}b">{barras}</div></div>')
    # entra como una portada: destello de papel, la cabecera cae, lo de delante se coloca
    js.append(f'tl.fromTo("#{sid}p",{{opacity:0}},{{opacity:1,duration:0.18}},{t0:.3f});')
    js.append(f'tl.fromTo("#{sid}",{{opacity:0,y:-120,scale:1.25}},{{opacity:1,y:0,scale:1,duration:0.32,'
              f'ease:"back.out(1.6)"}},{t0 + 0.05:.3f});')
    js.append(f'tl.fromTo("#{sid}d",{{opacity:0}},{{opacity:1,duration:0.15}},{t0 + 0.1:.3f});')
    if num:
        js.append(f'tl.fromTo("#{sid}n",{{opacity:0,x:-80}},{{opacity:1,x:0,duration:0.28,ease:"power3.out"}},{t0 + 0.3:.3f});')
    if tit:
        js.append(f'tl.fromTo("#{sid}t",{{opacity:0,x:80}},{{opacity:1,x:0,duration:0.28,ease:"power3.out"}},{t0 + 0.42:.3f});')
    js.append(f'tl.fromTo("#{sid}b",{{opacity:0,y:30}},{{opacity:1,y:0,duration:0.2}},{t0 + 0.55:.3f});')
    js.append(f'tl.fromTo("#{sid}",{{scale:1}},{{scale:1.03,duration:{dur:.3f},ease:"none"}},{t0 + 0.4:.3f});')
    js.append(f'tl.to(["#{sid}","#{sid}p","#{sid}d"],{{opacity:0,duration:0.2}},{t1 - 0.2:.3f});')
    js.append(f'tl.set("#silueta",{{opacity:1}},{t0:.3f});tl.set("#silueta",{{opacity:0}},{t1:.3f});')
    ev += [(t0, "impacto"), (t0 + 0.3, "whoosh")]
    print(f"detras: revista «{cab}» {t0:6.2f}–{t1:6.2f}s")


def _comparar(e, sid, t0, t1, parts, js, ev):
    """Antes y después en una tarjeta de cristal que sube por detrás de los hombros."""
    dur = t1 - t0
    for campo in ("valor_antes", "valor_despues"):
        if not e.get(campo) or len(e[campo]) > 16:
            raise SystemExit(f"detras comparar: «{campo}» es obligatorio y de hasta 16 caracteres")
    cy = e.get("_cara_y", 620)
    top = e.get("y", max(150, int(cy - 330)))
    alto = e.get("alto", 330)

    def px(t):
        return min(120, int(310 / (max(len(t), 1) * 0.47)))

    def col(c, et, v, tx, tacha=""):
        txt = f'<div class="tx">{html.escape(tx)}</div>' if tx else ""
        return (f'<div class="col {c}" id="{sid}{c}"><div class="et">{html.escape(et)}</div>'
                f'<div class="v" style="font-size:{px(v)}px">{html.escape(v)}{tacha}</div>{txt}</div>')

    a = col("a", e.get("etiqueta_antes", "ANTES"), e["valor_antes"], e.get("txt_antes", ""), f'<i class="tacha" id="{sid}x"></i>')
    b = col("d", e.get("etiqueta_despues", "DESPUÉS"), e["valor_despues"], e.get("txt_despues", ""))
    parts.append(f'      <div class="clip dt-sombra" id="{sid}s" data-start="{t0:.3f}" data-duration="{dur:.3f}" '
                 f'data-track-index="21"></div>')
    parts.append(f'      <div class="clip dt-cmp" id="{sid}" data-start="{t0:.3f}" data-duration="{dur:.3f}" data-track-index="22" '
                 f'style="top:{top}px;height:{alto}px">{a}{b}</div>')
    js.append(f'tl.fromTo("#{sid}s",{{opacity:0}},{{opacity:1,duration:0.25}},{t0:.3f});')
    js.append(f'tl.fromTo("#{sid}",{{opacity:0,y:260,scale:0.92}},{{opacity:1,y:0,scale:1,duration:0.5,ease:"back.out(1.5)"}},{t0:.3f});')
    js.append(f'tl.fromTo("#{sid}a",{{opacity:0,x:-50}},{{opacity:1,x:0,duration:0.3,ease:"back.out(1.8)"}},{t0 + 0.2:.3f});')
    js.append(f'tl.to("#{sid}x",{{scaleX:1,duration:0.25,ease:"power2.out"}},{t0 + 0.75:.3f});')
    js.append(f'tl.to("#{sid}a",{{opacity:0.55,duration:0.25}},{t0 + 0.85:.3f});')
    js.append(f'tl.fromTo("#{sid}d",{{opacity:0,scale:0.5}},{{opacity:1,scale:1,duration:0.4,ease:"back.out(2.4)"}},{t0 + 1.0:.3f});')
    js.append(f'tl.to("#{sid}",{{y:-12,duration:{max(0.4, dur - 1.0):.3f},ease:"sine.inOut"}},{t0 + 0.5:.3f});')
    js.append(f'tl.to(["#{sid}","#{sid}s"],{{opacity:0,duration:0.2}},{t1 - 0.2:.3f});')
    js.append(f'tl.set("#silueta",{{opacity:1}},{t0:.3f});tl.set("#silueta",{{opacity:0}},{t1:.3f});')
    ev += [(t0, "whoosh"), (t0 + 0.75, "tic"), (t0 + 1.0, "impacto")]
    print(f"detras: comparar «{e['valor_antes']}» → «{e['valor_despues']}» {t0:6.2f}–{t1:6.2f}s")


def build_detras(cfg, words, total, d):
    if not (Path(d) / "assets/silueta.webm").exists():
        raise SystemExit("detras: falta assets/silueta.webm → python3 scripts/recorte.py " + str(d))
    seq = [(_norm(w["raw"]), w["t0"], w["t1"]) for w in words]

    def at(frase, after=0.0):
        i = _find(seq, frase, after)
        if i is None:
            raise SystemExit(f"detras: no encuentro la frase «{frase}» (después de {after:.1f}s)")
        return seq[i][1]

    parts = [f'      <video id="silueta" class="clip" src="assets/silueta.webm" data-start="0" '
             f'data-duration="{total:.3f}" data-track-index="20" data-has-audio="false" muted playsinline></video>']
    js, ev, win = [], [], []
    for n, e in enumerate(cfg["detras"]):
        t0 = at(e["frase"], e.get("despues_de", 0.0)) - e.get("antes", 0.1) if e.get("frase") else e.get("t", 0.0)
        t0 = max(0.0, t0)
        t1 = at(e["hasta_frase"], t0) if e.get("hasta_frase") else t0 + e.get("dur", 3.0)
        t1 = min(t1, total)
        win.append((t0, t1))
        sid = f"dt{n}"
        if e.get("tipo") == "revista":
            _revista(dict(e, _cara_y=cfg.get("centro_cara", [540, 620])[1]), sid, t0, t1, parts, js, ev)
            continue
        if e.get("tipo") == "comparar":
            _comparar(dict(e, _cara_y=cfg.get("centro_cara", [540, 620])[1]), sid, t0, t1, parts, js, ev)
            continue
        # tamaño según la línea más larga: Anton mide ~0,47 em por carácter; caben ~980 px
        larga = max(len(x) for x in e["texto"].split("|"))
        px = min(e.get("px", 270), int(980 / (larga * 0.47)))
        lineas, k = [], 0
        for linea in e["texto"].split("|"):
            palabras = []
            for p in linea.split(" "):
                cls = "l acc" if p in e.get("acento", []) else "l"
                palabras.append("".join(f'<span class="{cls}" id="{sid}c{k + j}">{html.escape(ch)}</span>'
                                        for j, ch in enumerate(p)))
                k += len(p)
            lineas.append("&nbsp;".join(palabras))
        parts.append(f'      <div class="clip dt-sombra" id="{sid}s" data-start="{t0:.3f}" data-duration="{t1 - t0:.3f}" '
                     f'data-track-index="21"></div>')
        parts.append(f'      <div class="clip dt-tit" id="{sid}" data-start="{t0:.3f}" data-duration="{t1 - t0:.3f}" '
                     f'data-track-index="22" style="top:{e.get("y", 240)}px;font-size:{px}px">'
                     f'{"<br>".join(lineas)}</div>')
        js.append(f'tl.fromTo("#{sid}s",{{opacity:0}},{{opacity:1,duration:0.25}},{t0:.3f});')
        for j in range(k):
            js.append(f'tl.fromTo("#{sid}c{j}",{{opacity:0,y:-90,scale:1.4}},{{opacity:1,y:0,scale:1,duration:0.22,'
                      f'ease:"back.out(2)"}},{t0 + 0.04 * j:.3f});')
        js.append(f'tl.fromTo("#{sid}",{{scale:1}},{{scale:1.04,duration:{t1 - t0:.3f},ease:"none"}},{t0:.3f});')
        js.append(f'tl.to(["#{sid}","#{sid}s"],{{opacity:0,duration:0.2}},{t1 - 0.2:.3f});')
        # la persona recortada encima solo mientras dura el efecto
        js.append(f'tl.set("#silueta",{{opacity:1}},{t0:.3f});tl.set("#silueta",{{opacity:0}},{t1:.3f});')
        ev.append((t0, "impacto"))
        print(f"detras: «{e['texto']}» {t0:6.2f}–{t1:6.2f}s")
    return CSS.format(), "\n".join(parts), js, ev, win
