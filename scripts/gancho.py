"""Capa de gancho: titular arriba que se escribe solo,
antetítulo, etiquetas que aparecen al decir la palabra clave y corte seco a una
tarjeta de prueba con un número que sube. Lo usa scripts/subtitulos.py si existe
<dir>/gancho.json.
"""
import html
import re
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kit  # noqa: E402

# Iconos de línea (24x24, trazo); abstractos a propósito: nada de documentos ni sellos.
ICONS = {
    "pin": '<path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/>',
    "avion": '<path d="M2 13l20-8-6 16-3.5-6.5z"/><path d="M12.5 14.5L22 5"/>',
    "vuelta": '<path d="M4 12a8 8 0 1 0 2.4-5.7"/><path d="M4 3v5h5"/>',
}

STAR = '<svg viewBox="0 0 24 24"><path d="M12 2.5l2.9 6.2 6.8.8-5 4.7 1.3 6.7L12 17.6l-6 3.3 1.3-6.7-5-4.7 6.8-.8z"/></svg>'

CSS = """
      .gancho {{ position: absolute; inset: 0; z-index: 6; }}
      .g-ante {{ position: absolute; top: 200px; left: {L}px; width: {CW}px; text-align: center;
                 font: 36px/1 "Anton", sans-serif; letter-spacing: 0.32em; color: var(--amarillo);
                 -webkit-text-stroke: 7px #000; paint-order: stroke fill; }}
      .g-tit {{ position: absolute; top: 248px; left: {L}px; width: {CW}px; text-align: center;
                font: 100px/1 "Anton", sans-serif; text-transform: uppercase; color: var(--blanco);
                -webkit-text-stroke: 15px #000; paint-order: stroke fill; text-shadow: 0 6px 0 rgba(0,0,0,.55); }}
      .g-tit .acc {{ color: var(--amarillo); }}
      .g-tit .ch {{ opacity: 0; }}
      .g-tags {{ position: absolute; left: {TL}px; top: {TT}px; width: {TW}px;
                 display: flex; flex-direction: column; align-items: flex-start; gap: 22px; }}
      .g-tag {{ display: flex; align-items: center; gap: 14px; padding: 12px 22px 12px 16px;
                background: rgba(0,0,0,.74); border: 4px solid var(--amarillo); border-radius: 18px;
                font: 40px/1.05 "Anton", sans-serif; color: var(--blanco); text-transform: uppercase;
                opacity: 0; transform-origin: 0% 50%; }}
      .g-tag svg {{ width: 44px; height: 44px; flex: none; fill: none; stroke: var(--amarillo);
                    stroke-width: 2.2; stroke-linecap: round; stroke-linejoin: round; }}
      .prueba {{ position: absolute; inset: 0; z-index: 5;
                 background: radial-gradient(circle at 50% 36%, {GLOW} 0%, #0d0c08 58%, #000 100%); }}
      .p-ante {{ position: absolute; top: 330px; left: {L}px; width: {CW}px; text-align: center;
                 font: 40px/1 "Anton", sans-serif; letter-spacing: 0.3em; color: var(--blanco); }}
      .p-num {{ position: absolute; top: 400px; left: {L}px; width: {CW}px; text-align: center;
                font: 300px/1 "Anton", sans-serif; color: var(--amarillo);
                -webkit-text-stroke: 16px #000; paint-order: stroke fill; }}
      .logo {{ position: absolute; top: 185px; left: {L}px; width: {CW}px; z-index: 7;
                display: flex; justify-content: center; }}
      .logo .caja {{ background: #fff; border-radius: 26px; padding: 18px 26px;
                     box-shadow: 0 10px 0 rgba(0,0,0,.35), 0 0 0 5px var(--amarillo); }}
      .logo .caja img {{ display: block; width: 560px; height: auto; }}
      .logo .circulo img {{ display: block; width: 300px; height: 300px;
                            filter: drop-shadow(0 10px 0 rgba(0,0,0,.35)); }}
      .p-stars {{ position: absolute; top: 700px; left: {L}px; width: {CW}px; display: flex;
                   justify-content: center; gap: 14px; }}
      .p-stars svg {{ width: 74px; height: 74px; fill: var(--amarillo); stroke: #000; stroke-width: 1.2; }}
      .prueba:has(.p-stars) .p-txt {{ top: 810px; }}
      .p-lista {{ position: absolute; top: 420px; left: {L}px; width: {CW}px; list-style: none;
                  display: flex; flex-direction: column; gap: 34px; padding-left: 40px; }}
      .p-lista li {{ display: flex; align-items: center; gap: 26px; opacity: 0;
                     font: 70px/1 "Anton", sans-serif; color: var(--blanco); text-transform: uppercase; }}
      .p-lista svg {{ width: 70px; height: 70px; flex: none; fill: none; stroke: var(--amarillo);
                      stroke-width: 3.4; stroke-linecap: round; stroke-linejoin: round; }}
      .p-lista li.x svg {{ stroke: #E0242B; }}
      .p-lista li.tachado span {{ text-decoration: line-through; text-decoration-color: #E0242B;
                                  text-decoration-thickness: 8px; }}
      .impacto {{ position: absolute; inset: 0; z-index: 4; pointer-events: none;
                  background: radial-gradient(ellipse 60% 45% at {CX}px {CY}px, rgba(0,0,0,0) 55%, rgba(0,0,0,.55) 100%); }}
      .impacto svg {{ position: absolute; inset: 0; width: 100%; height: 100%; }}
      .p-flash {{ position: absolute; inset: 0; opacity: 0;
                  background: radial-gradient(circle at 70% 30%, #fff 0%, {FLASH} 30%, rgba(255,160,0,.0) 75%); }}
      .cuentas {{ position: absolute; left: 0; width: 1080px; z-index: 11;
                  background: linear-gradient(to bottom, rgba(255,255,255,0) 0%, rgba(255,255,255,.94) 16%,
                              rgba(255,255,255,.94) 84%, rgba(255,255,255,0) 100%); }}
      .cuentas ul {{ list-style: none; padding: 70px 0 0 {L}px; display: flex; flex-direction: column; gap: 18px; }}
      .cuentas li {{ display: flex; align-items: center; gap: 20px; opacity: 0;
                     font: 58px/1 "Anton", sans-serif; color: #111; text-transform: uppercase; }}
      .cuentas li svg {{ width: 58px; height: 58px; fill: none; stroke: #E0242B; stroke-width: 3.6;
                         stroke-linecap: round; stroke-linejoin: round; }}
      .cuentas .total {{ display: inline-block; margin: 26px 0 0 {L}px; padding: 10px 22px; opacity: 0;
                         background: #E0242B; color: #fff; font: 60px/1 "Anton", sans-serif; }}
      .p-txt {{ position: absolute; top: 740px; left: {L}px; width: {CW}px; text-align: center;
                font: 58px/1.08 "Anton", sans-serif; color: var(--blanco); text-transform: uppercase; }}
"""


def speed_lines(cx, cy, n, seed, color):
    """Cuñas radiales tipo cómic, deterministas (misma semilla, mismo dibujo)."""
    import math
    import random
    rnd = random.Random(seed)
    out = []
    for i in range(n):
        a = 2 * math.pi * (i + rnd.random() * 0.6) / n
        r0, r1, w = rnd.uniform(430, 620), 1500, rnd.uniform(0.010, 0.028)
        p = [(cx + r1 * math.cos(a - w), cy + r1 * math.sin(a - w)), (cx + r0 * math.cos(a), cy + r0 * math.sin(a)),
             (cx + r1 * math.cos(a + w), cy + r1 * math.sin(a + w))]
        out.append('<polygon points="' + " ".join(f"{x:.0f},{y:.0f}" for x, y in p) +
                   f'" fill="{color}" stroke="#000" stroke-width="3"/>')
    return "".join(out)


def anclar(cfg, words):
    """Convierte anclas por frase en segundos: así una receta sirve aunque cambie el corte."""
    from efectos import _find, _norm
    seq = [(_norm(w["raw"]), w["t0"], w["t1"]) for w in words]

    def at(frase, after=0.0):
        i = _find(seq, frase, after)
        if i is None:
            raise SystemExit(f"receta: no encuentro la frase «{frase}»")
        return seq[i][1]

    g = cfg.get("gancho")
    if g and "hasta_frase" in g:
        g["hasta"] = at(g["hasta_frase"]) - 0.05
    for d in cfg.get("datos", []):
        if "frase" in d:
            d["desde"] = at(d["frase"], d.get("despues_de", 0.0)) - d.get("antes", 0.1)
            d["hasta"] = d["desde"] + d.get("dur", 2.2)
        for it in d.get("items", []):
            if "frase" in it:
                it["t"] = at(it["frase"], d.get("desde", 0.0) - 1)
        if isinstance(d.get("total"), dict) and "frase" in d["total"]:
            d["total"]["t"] = at(d["total"]["frase"], d.get("desde", 0.0))
    zl = cfg.get("zoom_lento")
    if isinstance(zl, dict) and zl.get("tramos"):  # [{"desde_frase"|"desde", "hasta_frase"|"hasta", "despues_de"}]
        zl["_tramos"] = []
        for tr in zl["tramos"]:
            a = at(tr["desde_frase"], tr.get("despues_de", 0.0)) - 0.1 if tr.get("desde_frase") else tr.get("desde", 0.0)
            b = at(tr["hasta_frase"], a) - 0.15 if tr.get("hasta_frase") else tr.get("hasta", 1e9)
            zl["_tramos"].append((max(0.0, a), b))
    for im in cfg.get("impactos", []):
        if "frase" in im:
            im["t"] = at(im["frase"])
    return cfg


def suscriptores_yt(n):
    """Como lo escribe YouTube en español, truncando: 39769 → «39,7 mil»."""
    if n < 1000:
        return str(n)
    if n < 100_000:
        return f"{n // 100 / 10:.1f}".replace(".0", "").replace(".", ",") + " mil"
    if n < 1_000_000:
        return f"{n // 1000} mil"
    return f"{n // 100_000 / 10:.1f}".replace(".0", "").replace(".", ",") + " M"


BELL = ('<svg viewBox="0 0 24 24"><path fill="#fff" d="M12 22a2.5 2.5 0 0 0 2.45-2h-4.9A2.5 2.5 0 0 0 12 22zm7-6V11'
        'a7 7 0 0 0-5.5-6.84V3.5a1.5 1.5 0 0 0-3 0v.66A7 7 0 0 0 5 11v5l-2 2v1h18v-1z"/></svg>')
CHECK = ('<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="11" fill="#909090"/><path fill="none" stroke="#fff" '
         'stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" d="M7 12.5l3.2 3.2L17 9"/></svg>')


def tarjeta_youtube(n, t0, dur, y, dst):
    """Tarjeta de suscripción: foto, usuario y suscriptores de marca/canal.json; «Suscribirse» → «¡Suscrito!» + campana.
    marca/canal.json: {"youtube": {"usuario": "@tucanal", "suscriptores": 12345, "avatar": "avatar-youtube.jpg"}},
    con la foto en marca/tarjetas/."""
    raiz = Path(__file__).parent.parent / "marca"
    if not (raiz / "canal.json").exists():
        raise SystemExit("tarjeta de YouTube: falta marca/canal.json ({\"youtube\": {\"usuario\", \"suscriptores\", "
                         "\"avatar\"}}) y la foto en marca/tarjetas/; créalos o quita la tarjeta de la receta")
    yt = json.loads((raiz / "canal.json").read_text())["youtube"]
    if not (raiz / "tarjetas" / yt["avatar"]).exists():
        raise SystemExit(f"tarjeta de YouTube: falta la foto marca/tarjetas/{yt['avatar']}")
    shutil.copy2(raiz / "tarjetas" / yt["avatar"], dst / yt["avatar"])
    css = f"""
      .yt{n} {{ position: absolute; left: 70px; top: {y}px; width: 940px; height: 196px; z-index: 8; }}
      .yt{n} .fondo {{ position: absolute; inset: 0; background: #fff; border-radius: 34px; transform-origin: 98px 98px;
        box-shadow: 0 10px 30px rgba(0,0,0,.25); }}
      .yt{n} .foto {{ position: absolute; left: 29px; top: 29px; width: 138px; height: 138px; border-radius: 50%;
        object-fit: cover; }}
      .yt{n} .datos {{ position: absolute; left: 196px; top: 46px; font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; }}
      .yt{n} .usuario {{ font-size: 42px; font-weight: 500; color: #0f0f0f; letter-spacing: -0.5px; display: flex;
        align-items: center; gap: 10px; }}
      .yt{n} .usuario svg {{ width: 28px; height: 28px; }}
      .yt{n} .subs {{ font-size: 30px; color: #606060; margin-top: 6px; }}
      .yt{n} .boton {{ position: absolute; right: 36px; top: 58px; height: 80px; border-radius: 40px; padding: 0 34px;
        display: flex; align-items: center; font: 500 31px "Helvetica Neue", Helvetica, Arial, sans-serif; }}
      .yt{n} .b1 {{ background: #0f0f0f; color: #fff; }}
      .yt{n} .b2 {{ background: #f0f0f0; color: #0f0f0f; right: 132px; opacity: 0; }}
      .yt{n} .campana {{ position: absolute; right: 36px; top: 58px; width: 80px; height: 80px; border-radius: 50%;
        background: #0f0f0f; display: flex; align-items: center; justify-content: center; opacity: 0; }}
      .yt{n} .campana svg {{ width: 44px; height: 44px; }}
"""
    html_ = (f'      <div class="clip yt{n}" id="yt{n}" data-start="{t0:.3f}" data-duration="{dur:.3f}" data-track-index="{21 + n}">'
             f'<div class="fondo" id="yt{n}f"></div><img class="foto" id="yt{n}a" src="assets/tarjetas/{yt["avatar"]}">'
             f'<div class="datos" id="yt{n}d"><div class="usuario">{html.escape(yt["usuario"])}{CHECK}</div>'
             f'<div class="subs">{suscriptores_yt(yt["suscriptores"])} suscriptores</div></div>'
             f'<div class="boton b1" id="yt{n}b1">Suscribirse</div><div class="boton b2" id="yt{n}b2">¡Suscrito!</div>'
             f'<div class="campana" id="yt{n}c">{BELL}</div></div>')
    js = [f'tl.fromTo("#yt{n}a",{{scale:0}},{{scale:1,duration:0.35,ease:"back.out(2.2)"}},{t0:.3f});',
          f'tl.fromTo("#yt{n}f",{{scaleX:0.2,scaleY:0.2,opacity:0}},{{scaleX:1,scaleY:1,opacity:1,duration:0.4,'
          f'ease:"power3.out"}},{t0 + 0.55:.3f});',
          f'tl.fromTo(["#yt{n}d","#yt{n}b1"],{{opacity:0,x:-20}},{{opacity:1,x:0,duration:0.25}},{t0 + 0.8:.3f});',
          f'tl.to("#yt{n}b1",{{opacity:0,duration:0.12}},{t0 + 1.9:.3f});',
          f'tl.to("#yt{n}b2",{{opacity:1,duration:0.15}},{t0 + 1.9:.3f});',
          f'tl.fromTo("#yt{n}c",{{opacity:0,scale:0.5}},{{opacity:1,scale:1,duration:0.25,ease:"back.out(3)"}},{t0 + 2.1:.3f});',
          f'tl.fromTo("#yt{n}c svg",{{rotation:-18}},{{rotation:0,duration:0.5,ease:"elastic.out(1.2,0.3)"}},{t0 + 2.2:.3f});',
          f'tl.to("#yt{n}",{{opacity:0,duration:0.2}},{t0 + dur - 0.2:.3f});']
    return css, (html_, js), [(t0 + 0.55, "pop"), (t0 + 1.9, "tic")]

def build_hook(cfg_path, safe_l, cap_w, words=(), total=None, d="."):
    cfg = json.loads(Path(cfg_path).read_text())
    cfg["_duracion"] = total
    cfg["_dir"] = d
    cfg = anclar(cfg, words)
    g, p = cfg.get("gancho"), cfg.get("prueba")
    tx = g.get("etiquetas_x", 560) if g else 560
    cx, cy = cfg.get("centro_cara", [370, 620])
    # con otro acento en la receta (p. ej. el azul de un podcast) el resplandor de la tarjeta y el destello salen de ese color
    ac = cfg.get("acento") or (kit.acento() if kit.acento().upper() != kit.ACENTO_BASE else None)
    mezcla = lambda f, base: "#" + "".join(f"{round(int(ac[i:i + 2], 16) * f + base * (1 - f)):02x}" for i in (1, 3, 5))
    css = CSS.format(L=safe_l, CW=cap_w, CX=cx, CY=cy, TL=tx, TT=g.get("etiquetas_y", 500) if g else 500,
                     TW=safe_l + cap_w - tx, GLOW=mezcla(0.25, 0) if ac else "#3a2d00",
                     FLASH=mezcla(0.6, 255) if ac else "#ffe38a")
    parts, js = [], []
    hook_until = g["hasta"] if g else 0.0

    if g:
        # titular: un span por letra para escribirlo; las palabras de "acento" en amarillo
        letters, i = [], 0
        for word in g["titular"].split(" "):
            cls = "ch acc" if word in g.get("acento", []) else "ch"
            letters.append("".join(f'<span class="{cls}" id="gc{i + k}">{html.escape(ch)}</span>'
                                   for k, ch in enumerate(word)))
            i += len(word)
        t_type = g.get("escribe_desde", 0.05)
        for k in range(i):
            js.append(f'tl.set("#gc{k}",{{opacity:1}},{t_type + k * g.get("por_letra", 0.035):.3f});')

        tags = []
        for n, tag in enumerate(g["etiquetas"]):
            tags.append(f'<div class="g-tag" id="gt{n}"><svg viewBox="0 0 24 24">{ICONS[tag["icono"]]}</svg>'
                        f'<span>{html.escape(tag["texto"])}</span></div>')
            js.append(f'tl.fromTo("#gt{n}",{{opacity:0,scale:0.6,x:-30}},{{opacity:1,scale:1,x:0,duration:0.28,'
                      f'ease:"back.out(2)"}},{tag["t"]:.3f});')
        js.append(f'tl.fromTo("#gante",{{opacity:0,y:12}},{{opacity:1,y:0,duration:0.25}},{g["antetitulo_t"]:.3f});')
        # "baja": px que bajan antetítulo y titular cuando la cara queda alta en el plano
        b = g.get("baja", 0)
        st_a, st_t = (f' style="top:{200 + b}px"', f' style="top:{248 + b}px"') if b else ("", "")
        parts.append(f'      <div class="clip gancho" id="gancho" data-start="0" data-duration="{g["hasta"]:.3f}" '
                     f'data-track-index="3"><div class="g-ante" id="gante"{st_a}>{html.escape(g["antetitulo"])}</div>'
                     f'<h1 class="g-tit"{st_t}>{" ".join(letters)}</h1><div class="g-tags">{"".join(tags)}</div></div>')

    datos = cfg.get("datos", [])
    if p:
        datos = [p] + datos
    eventos = []  # (segundo, sonido) para la mezcla de efectos
    for n, d in enumerate(datos):
        t, dur = d["desde"], d["hasta"] - d["desde"]
        eventos.append((t, "whoosh"))
        if d.get("sonido"):  # p. ej. "caja" (registradora) cuando la tarjeta habla de dinero
            eventos.append((t + 0.1, d["sonido"]))
        flash = f'<div class="p-flash" id="dfl{n}"></div>' if d.get("destello") else ""
        if flash:
            js.append(f'tl.fromTo("#dfl{n}",{{opacity:0.95}},{{opacity:0,duration:0.45,ease:"power2.in"}},{t:.3f});')
        head = (f'      <div class="clip prueba" id="dato{n}" data-start="{t:.3f}" '
                f'data-duration="{dur:.3f}" data-track-index="4">' + flash +
                f'<div class="p-ante" id="dante{n}">{html.escape(d.get("antetitulo", ""))}</div>')
        if d.get("tipo") != "cuentas":
            js.append(f'tl.fromTo("#dante{n}",{{opacity:0,y:14}},{{opacity:1,y:0,duration:0.3}},{t + 0.05:.3f});')
        if d.get("tipo") == "cuentas":
            rows = []
            for k, it in enumerate(d["items"]):
                rows.append(f'<li id="d{n}i{k}"><svg viewBox="0 0 24 24"><path d="M4 12.5l5 5L20 6.5"/></svg>'
                            f'<span>{html.escape(it["texto"])}</span></li>')
                js.append(f'tl.fromTo("#d{n}i{k}",{{opacity:0,x:-30}},{{opacity:1,x:0,duration:0.2}},{it["t"]:.3f});')
                eventos.append((it["t"], "tic"))
            tot = ""
            if d.get("total"):
                tt = d["total"]
                tot = f'<div class="total" id="d{n}tot">{html.escape(tt["texto"])}</div>'
                js.append(f'tl.fromTo("#d{n}tot",{{opacity:0,scale:1.6}},{{opacity:1,scale:1,duration:0.18,'
                          f'ease:"power3.out"}},{tt["t"]:.3f});')
                eventos.append((tt["t"], "pop"))
            parts.append(f'      <div class="clip cuentas" id="dato{n}" data-start="{t:.3f}" data-duration="{dur:.3f}" '
                         f'data-track-index="4" style="top:{d.get("y", 600)}px;height:{d.get("alto", 440)}px">'
                         f'<ul>{"".join(rows)}</ul>{tot}</div>')
            js.append(f'tl.fromTo("#dato{n}",{{opacity:0}},{{opacity:1,duration:0.2}},{t:.3f});')
            # la banda ya dice esas palabras: los subtítulos se ocultan mientras está
            js.append(f'tl.set("#root",{{"--subs":0}},{t:.3f});tl.set("#root",{{"--subs":1}},{t + dur:.3f});')
            continue
        if d.get("tipo") == "lista":
            rows = []
            for k, it in enumerate(d["items"]):
                # «icono»: "x" → aspa roja en vez de visto; «tachado» → texto tachado en rojo
                cls = " ".join(c for c in ["x" if it.get("icono") == "x" else "", "tachado" if it.get("tachado") else ""] if c)
                icon = "M6 6l12 12M18 6L6 18" if it.get("icono") == "x" else "M4 12.5l5 5L20 6.5"
                rows.append(f'<li id="d{n}i{k}"{f' class="{cls}"' if cls else ""}><svg viewBox="0 0 24 24"><path d="{icon}"/></svg>'
                            f'<span>{html.escape(it["texto"])}</span></li>')
                js.append(f'tl.fromTo("#d{n}i{k}",{{opacity:0,x:-40}},{{opacity:1,x:0,duration:0.22,'
                          f'ease:"back.out(1.8)"}},{it["t"]:.3f});')
                eventos.append((it["t"], "tic"))
            parts.append(head + f'<ul class="p-lista">{"".join(rows)}</ul></div>')
            continue
        dec = d.get("decimales", 0)
        stars = ""
        if d.get("estrellas"):
            stars = '<div class="p-stars" id="dst{0}">{1}</div>'.format(n, STAR * d["estrellas"])
            js.append(f'tl.fromTo("#dst{n} svg",{{opacity:0,scale:0.3}},{{opacity:1,scale:1,duration:0.2,'
                      f'stagger:0.08,ease:"back.out(2.5)"}},{t + 0.3:.3f});')
        # miles con punto (1.814): toLocaleString('es') no agrupa los de 4 cifras
        fmt = (f'dc{n}.v.toFixed({dec}).replace(".",",")' if dec
               else f'String(Math.round(dc{n}.v)).replace(/\\B(?=(\\d{{3}})+(?!\\d))/g,".")')
        # el número cabe en una línea: con cifras largas («12.220 €») baja de 300 px (Anton ≈ 0,47 em por carácter)
        largo = len(f'{d["numero"]:,.{dec}f}') + len(d.get("sufijo", ""))
        px = min(300, int(cap_w * 0.96 / (largo * 0.47)))
        estilo = f' style="font-size:{px}px;top:{400 + (300 - px) // 2}px"' if px < 300 else ""
        parts.append(head + f'<div class="p-num"{estilo}><span id="dn{n}">0</span>{html.escape(d.get("sufijo", ""))}</div>'
                     f'{stars}<div class="p-txt" id="dtxt{n}">{html.escape(d["texto"])}</div></div>')
        js.append(f'const dc{n}={{v:0}};tl.fromTo(dc{n},{{v:0}},{{v:{d["numero"]},duration:{d.get("cuenta_s", 1.1)},'
                  f'ease:"power2.out",onUpdate:()=>{{document.getElementById("dn{n}").textContent={fmt}}}}},'
                  f'{t + 0.1:.3f});')
        js.append(f'tl.fromTo("#dtxt{n}",{{opacity:0,y:20}},{{opacity:1,y:0,duration:0.35}},{t + 0.4:.3f});')

    # zoom lento: acercamiento suave hacia la cara durante todo el vídeo (no se combina con impactos);
    # con "tramos" solo en esos tramos, para convivir con la pizarra y la pantalla partida
    zl = cfg.get("zoom_lento")
    if zl and total:
        if cfg.get("impactos"):
            raise SystemExit("receta: «zoom_lento» e «impactos» mueven el mismo vídeo; usa solo uno")
        if zl.get("_tramos"):
            # por tramos: se para donde otra pieza mueve el vídeo (pizarra, pantalla
            # partida). Escala desde la esquina y se compensa con x/y para acercarse a la cara: así esas piezas, que
            # también usan el origen 0 0, arrancan desde donde se quedó el zoom y no hay salto.
            s0, s1 = zl.get("de", 1.0), zl.get("a", 1.08)
            js.append('gsap.set("#video",{transformOrigin:"0px 0px"});')
            for a, b in zl["_tramos"]:
                b = min(b, total)
                js.append(f'tl.fromTo("#video",{{x:{(1 - s0) * cx:.1f},y:{(1 - s0) * cy:.1f},scale:{s0}}},'
                          f'{{x:{(1 - s1) * cx:.1f},y:{(1 - s1) * cy:.1f},scale:{s1},duration:{b - a:.3f},ease:"none",'
                          f'immediateRender:false}},{a:.3f});')
        else:
            js.append(f'gsap.set("#video",{{transformOrigin:"{cx}px {cy}px"}});')
            js.append(f'tl.fromTo("#video",{{scale:{zl.get("de", 1.0)}}},{{scale:{zl.get("a", 1.12)},duration:{total:.3f},ease:"none"}},0);')

    # impactos: zoom de golpe + líneas de velocidad que parpadean + temblor
    if cfg.get("impactos"):
        js.append(f'gsap.set("#video",{{transformOrigin:"{cx}px {cy}px"}});')
    for n, im in enumerate(cfg.get("impactos", [])):
        t0, dur = im["t"], im.get("dur", 1.0)
        onda = im.get("estilo") == "onda"  # sin rayos: ondas que salen de la cara + destello
        if onda:
            sets = (f'<rect id="im{n}f" width="1080" height="1920" fill="#fff" opacity="0"/>'
                    + "".join(f'<circle id="im{n}o{k}" cx="{cx}" cy="{cy}" r="80" fill="none" '
                              f'stroke="{col}" stroke-width="{w}" opacity="0"/>'
                              for k, (col, w) in enumerate([("#ffffff", 26), (cfg.get("acento", "#FFC800"), 18), ("#ffffff", 10)])))
        else:
            sets = "".join(f'<g id="im{n}s{s}" style="opacity:{1 if s == 0 else 0}">{speed_lines(cx, cy, 40, s + 3 * n, col)}</g>'
                           for s, col in enumerate(["#ffffff", cfg.get("acento", "#FFC800")]))
        parts.append(f'      <div class="clip impacto" id="imp{n}" data-start="{t0:.3f}" data-duration="{dur:.3f}" '
                     f'data-track-index="6"><svg viewBox="0 0 1080 1920">{sets}</svg></div>')
        if onda:
            js.append(f'tl.fromTo("#im{n}f",{{opacity:0.55}},{{opacity:0,duration:0.22,ease:"power2.out"}},{t0:.3f});')
            for k in range(3):
                js.append(f'tl.fromTo("#im{n}o{k}",{{attr:{{r:80}},opacity:0.95}},{{attr:{{r:1100}},opacity:0,'
                          f'duration:0.7,ease:"power2.out"}},{t0 + 0.09 * k:.3f});')
        js.append(f'tl.fromTo("#video",{{scale:1}},{{scale:{im.get("zoom", 1.22)},duration:0.12,ease:"power3.out"}},{t0:.3f});')
        js.append(f'tl.to("#video",{{scale:1,duration:0.2,ease:"power2.inOut"}},{t0 + dur - 0.2:.3f});')
        for k, dx in enumerate([14, -12, 9, -6, 3, 0]):
            js.append(f'tl.set("#video",{{x:{dx}}},{t0 + 0.04 * (k + 1):.3f});')
        k, tt = 0, (t0 + dur if onda else t0)
        while tt < t0 + dur:
            on = k % 2
            js.append(f'tl.set("#im{n}s0",{{opacity:{1 - on}}},{tt:.3f});tl.set("#im{n}s1",{{opacity:{on}}},{tt:.3f});')
            tt += 0.067
            k += 1
        eventos.append((t0, "impacto"))

    # logos: aparecen solos cuando se dice el nombre de la marca
    seq = [(re.sub(r"[^\wáéíóúüñ]", "", w["raw"].lower()), w["t0"]) for w in words]
    n_logo, logo_win = 0, []
    for lg in [dict(l, frase=f) for l in cfg.get("logos", []) for f in ([l["frase"]] + l.get("alias", []))]:
        frase = lg["frase"].lower().split()
        for i in range(len(seq) - len(frase) + 1):
            if [s for s, _ in seq[i:i + len(frase)]] != frase:
                continue
            t0 = seq[i][1]
            if t0 < hook_until:
                continue  # no pisar el titular del gancho
            dur = min(lg.get("dur", 2.6), (total or 1e9) - t0)
            if dur < 0.6:
                continue
            cls = "caja" if lg.get("fondo", "blanco") == "blanco" else "circulo"
            # "x"/"y" propios cuando el logo centrado tapa una cara
            pos = (f"left:{lg['x']}px;width:auto;" if "x" in lg else "") + (f"top:{lg['y']}px;" if "y" in lg else "")
            st = f' style="{pos}"' if pos else ""
            parts.append(f'      <div class="clip logo" id="logo{n_logo}"{st} data-start="{t0:.3f}" '
                         f'data-duration="{dur:.3f}" data-track-index="5"><div class="{cls}">'
                         f'<img src="assets/{lg["archivo"]}" alt="{html.escape(lg["frase"])}"></div></div>')
            js.append(f'tl.fromTo("#logo{n_logo}",{{opacity:0,scale:0.7,y:-20}},{{opacity:1,scale:1,y:0,'
                      f'duration:0.3,ease:"back.out(2)"}},{t0:.3f});')
            js.append(f'tl.to("#logo{n_logo}",{{opacity:0,y:-20,duration:0.2}},{t0 + dur - 0.2:.3f});')
            eventos.append((t0, "pop"))
            print(f"logo: {lg['frase']} a {t0:.2f}s")
            logo_win.append((t0, t0 + dur))
            n_logo += 1

    # tarjetas: al decir su frase. "tipo": "youtube" es la de suscripción, hecha aquí con los datos de
    # marca/canal.json (suscriptores al día); si no, un vídeo con transparencia de marca/tarjetas/*.webm
    for n, tj in enumerate(cfg.get("tarjetas", [])):
        frase = [re.sub(r"[^\wáéíóúüñ]", "", x) for x in tj["frase"].lower().split()]
        i = next((k for k in range(len(seq) - len(frase) + 1) if [s for s, _ in seq[k:k + len(frase)]] == frase), None)
        if i is None:
            raise SystemExit(f"tarjetas: no encuentro la frase «{tj['frase']}»")
        t0 = max(0.0, seq[i][1] - tj.get("antes", 0.0))
        dur = min(tj.get("dur", 3.0), (total or 1e9) - t0)
        dst = Path(cfg["_dir"]) / "assets/tarjetas"
        dst.mkdir(parents=True, exist_ok=True)
        if tj.get("tipo") == "youtube":
            c, cj, ev = tarjeta_youtube(n, t0, dur, tj.get("y", 1250), dst)
            css += c
            parts.append(cj[0])
            js += cj[1]
            eventos += ev
            print(f"tarjeta: YouTube a {t0:.2f}s ({dur:.1f}s)")
            continue
        src = Path(__file__).parent.parent / "marca/tarjetas" / tj["archivo"]
        if not src.exists():
            raise SystemExit(f"tarjetas: falta marca/tarjetas/{tj['archivo']} (vídeo con transparencia); ponlo ahí o quita la tarjeta")
        shutil.copy2(src, dst / src.name)
        ancho = tj.get("ancho", 960)
        parts.append(f'      <video id="tj{n}" class="clip" src="assets/tarjetas/{src.name}" data-start="{t0:.3f}" '
                     f'data-duration="{dur:.3f}" data-track-index="{21 + n}" data-has-audio="false" muted playsinline '
                     f'style="position:absolute;z-index:8;left:{(1080 - ancho) // 2}px;top:{tj.get("y", 1250)}px;'
                     f'width:{ancho}px"></video>')
        js.append(f'tl.to("#tj{n}",{{opacity:0,duration:0.2}},{t0 + dur - 0.2:.3f});')
        eventos.append((t0 + tj.get("sonido_t", 1.0), "pop"))
        print(f"tarjeta: {src.name} a {t0:.2f}s ({dur:.1f}s)")

    covered = [(d["desde"], d["hasta"]) for d in datos]
    if True:  # efectos siempre: la tarjeta «sígueme» va en todos los vídeos
        from efectos import build_efectos
        sub_top = cfg.get("subtitulos", {}).get("top", 960)
        # lo que ocupa la franja de arriba: la notificación de «comenta» espera a que acabe
        cfg["_ocupado_arriba"] = logo_win + [(d["desde"], d["hasta"]) for d in datos if "desde" in d]
        ecss, ehtml, ejs, eev = build_efectos(cfg, words, safe_l, cap_w, sub_top)
        css += ecss
        parts.append(ehtml)
        js += ejs
        eventos += eev
    if cfg.get("ranking"):
        from ranking import build_ranking
        rk = dict(cfg["ranking"], dur=cfg["_duracion"])
        if cfg.get("_seguir") and not cfg.get("_seguir_abajo"):
            rk["cta_hasta"] = cfg["_seguir"][0]  # la caja de comentario cede el sitio a la tarjeta «sígueme»
        # con «_seguir_abajo» en la receta, la caja se queda hasta el final y «sígueme» va abajo a la vez
        rcss, rhtml, rjs, rev, rtimes = build_ranking(rk, words)
        css += rcss
        parts.append(rhtml)
        js += rjs
        eventos += rev
        covered += [(a - 1.0, b) for a, b in rtimes.values()]
        for n, (a, b) in sorted(rtimes.items()):
            print(f"ranking: {n:>2} aparece {a:6.2f}s · vuela {b:6.2f}s")

    if cfg.get("barrido"):
        if cfg.get("pizarra"):
            raise SystemExit("barrido: no se usa con la pizarra en el mismo vídeo")
        from barrido import build_barrido
        bcss, bhtml, bjs, bev, bwin = build_barrido(cfg, words, total)
        css += bcss
        parts.append(bhtml)
        js += bjs
        eventos += bev
        cfg.setdefault("_arriba", []).extend(bwin)

    if cfg.get("detras"):
        from detras import build_detras
        dcss, dhtml, djs, dev, dwin = build_detras(cfg, words, total, cfg["_dir"])
        css += dcss
        parts.append(dhtml)
        js += djs
        eventos += dev
        cfg.setdefault("_arriba", []).extend(dwin)  # la tarjeta «sígueme» no se pone encima

    if cfg.get("pegatina"):
        from pegatina import build_pegatina
        gcss, ghtml, gjs, gev, gwin = build_pegatina(cfg, words, total, cfg["_dir"])
        css += gcss
        parts.append(ghtml)
        js += gjs
        eventos += gev
        cfg.setdefault("_arriba", []).extend(gwin)  # el plano congelado tapa todo: «sígueme» no va encima

    if cfg.get("prensa"):
        from prensa import build_prensa
        rcss, rhtml, rjs, rev, rwin = build_prensa(cfg, words, total, cfg["_dir"])
        css += rcss
        parts.append(rhtml)
        js += rjs
        eventos += rev
        cfg.setdefault("_arriba", []).extend(rwin)  # fotos y titulares arriba: «sígueme» baja

    if cfg.get("niveles"):
        from niveles import build_niveles
        ncss, nhtml, njs, nev, nwin = build_niveles(cfg, words, total, cfg["_dir"])
        css += ncss
        parts.append(nhtml)
        js += njs
        eventos += nev
        cfg.setdefault("_arriba", []).extend(nwin)  # la tabla ocupa la mitad de arriba

    if cfg.get("pizarra"):
        from pizarra import build_pizarra
        ocupado = sorted(logo_win + [w for w in (cfg.get("_comenta"), cfg.get("_seguir")) if w])
        pcss, phtml, pjs, pev, pwin = build_pizarra(cfg, words, total, ocupado)
        css += pcss
        parts.append(phtml)
        js += pjs
        eventos += pev
        covered += pwin

    sgw = cfg.get("_seguir")
    arriba = logo_win + cfg.get("_arriba", []) + [(d["desde"], d["hasta"]) for d in datos if "desde" in d]
    if sgw and (cfg.get("_seguir_abajo") or not cfg.get("pizarra") and any(a < sgw[1] and sgw[0] < b for a, b in arriba)):
        parts = [p.replace('class="clip seguir"', 'class="clip seguir abajo"') for p in parts]
        print("seguir: coincide con un logo, unas pastillas o una tarjeta → tarjeta abajo")

    # datos dichos en voz alta que aún no tienen tarjeta (para añadirlos a "datos")
    for w in words:
        if re.search(r"\d", w["raw"]) and not any(a - 0.5 <= w["t0"] <= b for a, b in covered):
            print(f"dato sin tarjeta: «{w['raw']}» a {w['t0']:.2f}s")
    return css, "\n".join(parts), "\n        ".join(js), sorted(eventos)
