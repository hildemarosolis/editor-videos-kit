"""Ranking por niveles (tier-list): una tabla con filas (S, A, B… o las que se digan) arriba y tú
en la franja de abajo, como en la pizarra. Cada elemento cae en su fila al nombrarlo, con su bandera o su logo.

Receta:
  "niveles": {"tema": "¿TE LLEGA EL SMS?", "filas": ["SÍ", "NO"],
              "items": [{"nombre": "España", "fila": "SÍ", "frase": "España", "emoji": "🇪🇸"},
                        {"nombre": "ChatGPT", "fila": "A", "frase": "ChatGPT", "logo": "openai"},
                        {"nombre": "Mi foto", "fila": "B", "frase": "...", "imagen": "assets/x.png"}],
              "mantener": 2.0, "desde_frase": "...", "cara_y": 1360, "corte_y": 1100}
- `filas`: de arriba abajo, de 1 a 6, cada una de hasta 6 caracteres, con las letras, números o palabras que
  dices tú (si dices «top cinco», 1-5). Sin `filas`: S, A, B, C, D.
- `items`: hasta 4 por fila y 12 en total, nombres de hasta 14 caracteres. Cada uno cae al decir su `frase`
  (`despues_de` para la segunda vez que se dice algo). Icono: `emoji` (banderas), `logo` (nombre de Simple
  Icons 16.34.0, CC0; se baja una vez a `marca/logos/simple/`) o `imagen` (ruta dentro del proyecto).
- La tabla entra 0,6 s antes del primer elemento (o al decir `desde_frase`) y se va `mantener` s después del
  último. Mientras, los subtítulos suben a y=880 y tú bajas a la franja.
- No se usa en el mismo vídeo que la pizarra (las dos mueven el vídeo).
"""
import html
import shutil
import urllib.request
from pathlib import Path

from efectos import _find, _norm

ROOT = Path(__file__).resolve().parent.parent
SIMPLE = ROOT / "marca/logos/simple"
SIMPLE_URL = "https://cdn.jsdelivr.net/npm/simple-icons@16.34.0/icons/{}.svg"
COLORES = ["#FF5D5D", "#FF9F43", "#FFC800", "#7BD389", "#5DA9FF", "#B58CFF"]
TOP, BOT, L, ANCHO = 200, 850, 70, 940

CSS = """
      .nv-fondo {{ position: absolute; inset: 0; width: 1080px; height: 1920px; z-index: 0; opacity: 0; pointer-events: none;
                   background: radial-gradient(120% 60% at 50% 28%, #1d1d1d 0%, #0b0b0b 60%, #070707 100%); }}
      .nv-fondo::after {{ content: ""; position: absolute; inset: 0;
                          background-image: radial-gradient(rgba(255,200,0,.10) 2px, transparent 2.6px); background-size: 30px 30px; }}
      .nv-raya {{ position: absolute; left: 0; top: {BY}px; width: 1080px; height: 8px; margin-top: -4px; z-index: 5;
                  background: var(--amarillo); opacity: 0; }}
      .nv-tabla {{ position: absolute; left: {L}px; top: {TOP}px; width: {ANCHO}px; z-index: 6; opacity: 0; }}
      .nv-cab {{ display: flex; align-items: center; justify-content: space-between; height: 76px; margin-bottom: 14px; }}
      .nv-tema {{ font: 54px/1 "Anton", sans-serif; color: #fff; text-transform: uppercase; white-space: nowrap; }}
      .nv-pill {{ position: relative; height: 50px; min-width: 210px; border-radius: 25px; overflow: hidden;
                  font: 28px/50px "Anton", sans-serif; letter-spacing: .1em; text-align: center; text-transform: uppercase; }}
      .nv-pill span {{ position: absolute; inset: 0; padding: 0 20px; }}
      .nv-pill .p1 {{ background: #2a2a2a; color: #fff; }}
      .nv-pill .p2 {{ background: var(--amarillo); color: #111; opacity: 0; }}
      .nv-fila {{ display: flex; gap: 12px; margin-bottom: 12px; height: {RH}px; }}
      .nv-et {{ flex: none; width: {RH}px; height: {RH}px; border-radius: 16px; display: flex; align-items: center;
                justify-content: center; font: {EF}px/1 "Anton", sans-serif; color: #111; }}
      .nv-pista {{ flex: 1; border-radius: 16px; background: rgba(255,255,255,.07); border: 3px solid rgba(255,255,255,.10);
                   display: flex; align-items: center; gap: 10px; padding: 0 10px; }}
      .nv-chip {{ flex: none; width: {CWD}px; height: {CH}px; border-radius: 14px; background: #fff; opacity: 0;
                  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px;
                  box-shadow: 0 8px 18px rgba(0,0,0,.45); }}
      .nv-chip .ic {{ height: {IC}px; display: flex; align-items: center; justify-content: center; font-size: {IC}px; line-height: 1; }}
      .nv-chip .ic img {{ height: {IC}px; width: {IC}px; object-fit: contain; }}
      .nv-chip b {{ font: {NF}px/1 "Anton", sans-serif; font-weight: 400; color: #111; text-transform: uppercase; white-space: nowrap; }}
      .cap {{ top: var(--capy, {SUB}px) !important; }}
      #video {{ z-index: 1; }}
"""


def logo(nombre, d):
    """SVG de Simple Icons copiado a assets/logos/ (se baja una vez a marca/logos/simple/)."""
    src = SIMPLE / f"{nombre}.svg"
    if not src.exists():
        SIMPLE.mkdir(parents=True, exist_ok=True)
        try:
            with urllib.request.urlopen(SIMPLE_URL.format(nombre), timeout=20) as r:
                src.write_bytes(r.read())
        except Exception as e:  # noqa: BLE001
            raise SystemExit(f"niveles: no encuentro el logo «{nombre}» en Simple Icons 16.34.0 ({e})")
    dst = Path(d) / "assets/logos" / src.name
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return f"assets/logos/{src.name}"


def build_niveles(cfg, words, total, d):
    nv = cfg["niveles"]
    if cfg.get("pizarra"):
        raise SystemExit("niveles: no se usa con la pizarra en el mismo vídeo (las dos mueven el vídeo)")
    filas = nv.get("filas", ["S", "A", "B", "C", "D"])
    items = nv["items"]
    if not 1 <= len(filas) <= 6 or any(len(f) > 6 for f in filas):
        raise SystemExit("niveles: de 1 a 6 filas, cada una de hasta 6 caracteres")
    if len(items) > 12:
        raise SystemExit("niveles: como mucho 12 elementos")
    for it in items:
        if it.get("fila") not in filas:
            raise SystemExit(f"niveles: «{it.get('nombre')}» va a la fila «{it.get('fila')}», que no está en {filas}")
        if len(it["nombre"]) > 14:
            raise SystemExit(f"niveles: «{it['nombre']}» pasa de 14 caracteres")
    for f in filas:
        if sum(it["fila"] == f for it in items) > 4:
            raise SystemExit(f"niveles: la fila «{f}» tiene más de 4 elementos")

    seq = [(_norm(w["raw"]), w["t0"], w["t1"]) for w in words]

    def at(frase, after=0.0):
        i = _find(seq, frase, after)
        if i is None:
            raise SystemExit(f"niveles: no encuentro la frase «{frase}» (después de {after:.1f}s)")
        return seq[i][1]

    tiempos = [at(it["frase"], it.get("despues_de", 0.0)) for it in items]
    t_in = at(nv["desde_frase"]) - 0.1 if nv.get("desde_frase") else max(0.0, min(tiempos) - 0.6)
    t_last = max(tiempos)
    t_out = min(total, t_last + nv.get("mantener", 2.0))
    cx, cy = cfg.get("centro_cara", [540, 620])
    cara_y, by = nv.get("cara_y", 1360), nv.get("corte_y", 1100)
    vy = cara_y - cy
    sub_base = cfg.get("subtitulos", {}).get("top", 960)

    n = len(filas)
    rh = min(170, int((BOT - TOP - 90 - 12 * n) / n))
    ch = rh - 16
    ic = int(ch * 0.46)
    nf = max(22, int(ch * 0.22))
    cwd = min(200, int((ANCHO - rh - 12 - 20 - 30) / 4))  # caben 4 por fila
    alto_tabla = 90 + n * (rh + 12)
    top = TOP + max(0, (BOT - TOP - alto_tabla) // 2)  # centrada entre el borde de arriba y los subtítulos
    css = CSS.format(BY=by, L=L, TOP=top, ANCHO=ANCHO, RH=rh, EF=int(rh * 0.5), CWD=cwd, CH=ch, IC=ic, NF=nf, SUB=sub_base)

    chips = {f: [] for f in filas}
    for k, it in enumerate(items):
        if it.get("emoji"):
            icono = html.escape(it["emoji"])
        elif it.get("logo"):
            icono = f'<img src="{logo(it["logo"], d)}" alt="">'
        elif it.get("imagen"):
            icono = f'<img src="{html.escape(it["imagen"])}" alt="">'
        else:
            icono = ""
        # nombre: letra más pequeña si es largo (Anton ~0,47 em por carácter, caben ~170 px)
        px = min(nf, int((cwd - 20) / (max(len(it["nombre"]), 1) * 0.47)))
        chips[it["fila"]].append(f'<div class="nv-chip" id="nvc{k}"><div class="ic">{icono}</div>'
                                 f'<b style="font-size:{px}px">{html.escape(it["nombre"])}</b></div>')
    filas_html = "".join(f'<div class="nv-fila" id="nvf{j}"><div class="nv-et" style="background:{COLORES[j % 6]}">'
                         f'{html.escape(f)}</div><div class="nv-pista">{"".join(chips[f])}</div></div>'
                         for j, f in enumerate(filas))
    tema = nv.get("tema", "")
    tpx = min(54, int(640 / (max(len(tema), 1) * 0.47)))
    data = f'data-start="{t_in:.3f}" data-duration="{t_out - t_in + 0.5:.3f}"'
    parts = [f'      <div class="clip nv-fondo" id="nvb" {data} data-track-index="55"></div>',
             f'      <div class="clip nv-raya" id="nvr" {data} data-track-index="56"></div>',
             f'      <div class="clip nv-tabla" id="nv0" {data} data-track-index="57">'
             f'<div class="nv-cab"><div class="nv-tema" style="font-size:{tpx}px">{html.escape(tema)}</div>'
             f'<div class="nv-pill"><span class="p1" id="nvp1">{html.escape(nv.get("pill", "Clasificando"))}</span>'
             f'<span class="p2" id="nvp2">{html.escape(nv.get("pill_fin", "Clasificado"))}</span></div></div>'
             f'{filas_html}</div>']

    # el vídeo (y su copia con color de cine, si hay barrido) baja a la franja y vuelve
    videos = '"#video"' + (',"#bwv","#bwn"' if cfg.get("barrido") else "")
    franja = f'x:0,y:{vy},clipPath:"inset({by - vy}px 0px 0px 0px)"'
    lleno = 'x:0,y:0,clipPath:"inset(0px 0px 0px 0px)"'
    js = [f'gsap.set([{videos}],{{transformOrigin:"0px 0px"}});',
          f'tl.set("#root",{{"--capy":"{sub_base}px"}},0);',
          f'tl.to("#nvb",{{opacity:1,duration:0.3}},{t_in:.3f});',
          f'tl.to([{videos}],{{{franja},duration:0.5,ease:"power3.inOut"}},{t_in:.3f});',
          f'tl.to("#root",{{"--capy":"880px",duration:0.4}},{t_in:.3f});',
          f'tl.fromTo("#nvr",{{opacity:0,scaleX:0}},{{opacity:1,scaleX:1,duration:0.35,ease:"power2.out"}},{t_in + 0.3:.3f});',
          f'tl.fromTo("#nv0",{{opacity:0,y:-40}},{{opacity:1,y:0,duration:0.4,ease:"back.out(1.6)"}},{t_in + 0.15:.3f});']
    for j in range(n):  # las filas entran escalonadas
        js.append(f'tl.fromTo("#nvf{j}",{{opacity:0,x:-60}},{{opacity:1,x:0,duration:0.32,ease:"back.out(1.8)"}},'
                  f'{t_in + 0.25 + 0.07 * j:.3f});')
    ev = [(t_in, "whoosh")]
    for k, t in enumerate(tiempos):
        js.append(f'tl.fromTo("#nvc{k}",{{opacity:0,y:-140,scale:1.35,rotation:-8}},{{opacity:1,y:0,scale:1,rotation:0,'
                  f'duration:0.45,ease:"back.out(2.2)"}},{t - 0.05:.3f});')
        ev.append((t + 0.15, "pop"))
        print(f"niveles: «{items[k]['nombre']}» cae en «{items[k]['fila']}» a {t:6.2f}s")
    js.append(f'tl.to("#nvp1",{{opacity:0,duration:0.2}},{t_last + 0.6:.3f});')
    js.append(f'tl.fromTo("#nvp2",{{opacity:0,scale:0.6}},{{opacity:1,scale:1,duration:0.3,ease:"back.out(2.4)"}},{t_last + 0.6:.3f});')
    ev.append((t_last + 0.6, "tic"))
    # micromovimiento: la tabla flota un poco mientras está quieta
    js.append(f'tl.to("#nv0",{{y:-10,duration:{max(0.5, t_out - t_in - 0.6):.3f},ease:"sine.inOut"}},{t_in + 0.6:.3f});')
    # salida: la tabla sube y se va, el vídeo vuelve a pantalla completa
    js.append(f'tl.to("#nv0",{{opacity:0,y:-80,duration:0.35,ease:"power2.in"}},{t_out:.3f});')
    js.append(f'tl.to(["#nvr","#nvb"],{{opacity:0,duration:0.35}},{t_out + 0.1:.3f});')
    js.append(f'tl.to([{videos}],{{{lleno},duration:0.5,ease:"power3.inOut"}},{t_out:.3f});')
    js.append(f'tl.to("#root",{{"--capy":"{sub_base}px",duration:0.4}},{t_out:.3f});')
    ev.append((t_out, "whoosh"))
    print(f"niveles: tabla «{tema}» {t_in:6.2f}–{t_out + 0.5:6.2f}s")
    return css, "\n".join(parts), js, ev, [(t_in, t_out + 0.5)]
