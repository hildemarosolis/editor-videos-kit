"""Modelo «Ranking 1-10»: columna fija de huecos 1-10 a la
izquierda; cada elemento aparece arriba (icono + nombre) al nombrarlo y vuela a su
hueco al decir «N de 10». El número 1 se revela con golpe y destello. Cierre con
caja de comentario que escribe la palabra clave.

Los tiempos salen solos de la transcripción: el elemento aparece cuando se dice su
`frase`, y vuela cuando se dice su número («5 de 10»). Para el 1 se usa `vuela_tras`.

`"aspecto": "completa"`: números 1-10 grandes a toda la altura de la
izquierda, que no se borran; el elemento sale grande en el centro (icono o `imagen` de
assets/) y se encoge hasta quedarse como miniatura al lado de su número.
`"orden": "numero_primero"`: para cuando se dice «Diez. …» antes de describirlo: el elemento
entra al decir su número y vuela justo antes del número siguiente.
"""
import html
import re

from efectos import sello

NUM_WORDS = {"uno": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6, "siete": 7,
             "ocho": 8, "nueve": 9, "diez": 10}

ICONS = {
    "pasaporte": '<rect x="5" y="2.5" width="14" height="19" rx="2"/><circle cx="12" cy="10" r="3.5"/><path d="M8.5 17h7"/>',
    "camisa": '<path d="M8 3l4 3 4-3 5 3-2 4-2-1v12H7V9L5 10 3 6z"/>',
    "cama": '<path d="M3 18V7M3 14h18v4M21 14v-3a3 3 0 0 0-3-3h-7v6"/><circle cx="7" cy="11" r="2"/>',
    "sobre": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/>',
    "avion": '<path d="M2 13l20-8-6 16-3.5-6.5z"/><path d="M12.5 14.5L22 5"/>',
    "escudo": '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/><path d="M9 12l2 2 4-4"/>',
    "euro": '<path d="M18 6.5A7 7 0 1 0 18 17.5"/><path d="M4 10h9M4 14h9"/>',
    "sello": '<circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="5"/><path d="M9.5 12h5"/>',
    "dialogo": '<path d="M4 5h16v10H9l-5 4z"/><path d="M8 9h8M8 12h5"/>',
    "check2": '<path d="M2 13l4 4 8-9"/><path d="M10 15l2 2 9-10"/>',
    # oficios (Top 5 con sueldo)
    "soldadura": '<path d="M4 20l7-7"/><path d="M11 13l3-3 3 3-3 3z"/><path d="M17 5l2-2M19 9h3M15 3V1"/>',
    "fontaneria": '<path d="M14 4a4 4 0 0 0-5 5L3 15l3 3 6-6a4 4 0 0 0 5-5l-3 3-3-3z"/>',
    "solar": '<rect x="3" y="11" width="18" height="9" rx="1"/><path d="M9 11v9M15 11v9M3 15.5h18"/><circle cx="12" cy="5" r="2.5"/>',
    "clima": '<path d="M12 2v20M4 7l16 10M20 7L4 17"/><path d="M9 3l3 2 3-2M9 21l3-2 3 2"/>',
    "electricidad": '<path d="M13 2L5 14h6l-1 8 8-12h-6z"/>',
}

CSS = """
      .rk-col {{ position: absolute; left: {X}px; top: {Y0}px; z-index: 6; }}
      .rk-slot {{ position: absolute; left: 0; width: {D}px; height: {D}px; border-radius: 50%;
                  border: 4px dashed var(--amarillo); background: rgba(0,0,0,.45);
                  display: flex; align-items: center; justify-content: center; opacity: 0; }}
      .rk-slot .n {{ font: {NF}px/1 "Anton", sans-serif; color: #fff; -webkit-text-stroke: 5px #000;
                     paint-order: stroke fill; }}
      .rk-slot svg {{ position: absolute; width: {IS}px; height: {IS}px; fill: none; stroke: #000;
                      stroke-width: 2.4; stroke-linecap: round; stroke-linejoin: round; opacity: 0; }}
      .rk-slot.lleno {{ background: var(--amarillo); border-style: solid; border-color: #000; }}
      .rk-slot.lleno .n {{ opacity: 0; }}
      .rk-slot.lleno svg {{ opacity: 1; }}
      .rk-item {{ position: absolute; left: 0; top: {TOP}px; width: 1080px; z-index: 7; opacity: 0;
                  display: flex; flex-direction: row; align-items: flex-start; justify-content: flex-start;
                  gap: 22px; padding-left: {IX}px; }}
      .rk-item .lab {{ margin-top: 22px; max-width: {LW}px; font: 58px/1.1 "Anton", sans-serif; color: #fff; text-transform: uppercase;
                       -webkit-text-stroke: 12px #000; paint-order: stroke fill; text-align: left; }}
      .rk-item .ico {{ flex: none; width: 112px; height: 112px; border-radius: 50%; background: var(--amarillo);
                       border: 6px solid #000; display: flex; align-items: center; justify-content: center; }}
      .rk-item .ico svg {{ width: 70px; height: 70px; fill: none; stroke: #000; stroke-width: 2.2;
                           stroke-linecap: round; stroke-linejoin: round; }}
      .rk-cta {{ position: absolute; left: {CTA_X}px; top: {CTA_Y}px; width: {CTA_W}px; z-index: 8; opacity: 0;
                 display: flex; align-items: center; gap: 18px; padding: 22px 26px; border-radius: 60px;
                 background: #fff; box-shadow: 0 10px 0 rgba(0,0,0,.35), 0 0 0 5px var(--amarillo); }}
      .rk-cta .ph {{ flex: 1; font: 50px/1 "Anton", sans-serif; color: #111; letter-spacing: .04em; }}
      .rk-cta .ph .c {{ opacity: 0; }}
      .rk-cta .ph .hint {{ color: #9a9a9a; }}
      .rk-cta .send {{ width: 76px; height: 76px; border-radius: 50%; background: #d9d9d9; flex: none;
                       display: flex; align-items: center; justify-content: center; }}
      .rk-cta .send svg {{ width: 44px; height: 44px; fill: none; stroke: #fff; stroke-width: 3;
                           stroke-linecap: round; stroke-linejoin: round; }}
"""
CSS_COMPLETA = """
      .rk-col {{ position: absolute; left: {X}px; top: {Y0}px; z-index: 6; }}
      .rk-row {{ position: absolute; left: 0; height: {D}px; display: flex; align-items: center; gap: 14px; opacity: 0; }}
      .rk-row .n {{ width: {NW}px; text-align: right; font: {NF}px/1 "Anton", sans-serif; color: #fff;
                    -webkit-text-stroke: 9px #000; paint-order: stroke fill; }}
      .rk-row .th {{ width: {D}px; height: {D}px; border-radius: 50%; background: var(--amarillo); border: 5px solid #000;
                     display: flex; align-items: center; justify-content: center; overflow: hidden; opacity: 0; }}
      .rk-row .th svg {{ width: 64%; height: 64%; fill: none; stroke: #000; stroke-width: 2.4;
                         stroke-linecap: round; stroke-linejoin: round; }}
      .rk-row .th img {{ width: 100%; height: 100%; object-fit: cover; }}
      .rk-big {{ position: absolute; left: {BX}px; top: {BY}px; width: {BS}px; z-index: 7; opacity: 0;
                 display: flex; flex-direction: column; align-items: center; gap: 18px; }}
      .rk-big .ico {{ width: {BS}px; height: {BS}px; border-radius: 50%; background: var(--amarillo); border: 9px solid #000;
                      display: flex; align-items: center; justify-content: center; overflow: hidden;
                      box-shadow: 0 14px 0 rgba(0,0,0,.35); }}
      .rk-big .ico svg {{ width: 62%; height: 62%; fill: none; stroke: #000; stroke-width: 2.2;
                          stroke-linecap: round; stroke-linejoin: round; }}
      .rk-big .ico img {{ width: 100%; height: 100%; object-fit: cover; }}
      .rk-big .lab {{ width: {LBW}px; text-align: center; font: {LBF}px/1.05 "Anton", sans-serif; color: #fff;
                      text-transform: uppercase; -webkit-text-stroke: 13px #000; paint-order: stroke fill; }}
      .rk-big .cred {{ margin-top: -10px; font: 22px/1.2 "Anton", sans-serif; letter-spacing: .03em; color: #fff;
                       opacity: .85; -webkit-text-stroke: 5px #000; paint-order: stroke fill; text-align: center; width: {LBW}px; }}
      .rk-tit {{ position: absolute; left: 60px; width: 960px; top: {TY}px; z-index: 6; text-align: center;
                 font: {TF}px/1.02 "Anton", sans-serif; color: #fff; text-transform: uppercase;
                 -webkit-text-stroke: 11px #000; paint-order: stroke fill; }}
      .rk-tit .acc {{ color: var(--amarillo); }}
"""


def _norm(s):
    return re.sub(r"[^\wáéíóúüñ]", "", s.lower())


def _num(tok):
    t = _norm(tok)
    return int(t) if t.isdigit() else NUM_WORDS.get(t)


def _canon(w):
    # whisper escribe a veces «cinco» y a veces «5»: para buscar frases cuentan igual (7-nov-2026)
    return str(NUM_WORDS[w]) if w in NUM_WORDS else w


def _find(seq, frase, after):
    f = [_canon(_norm(x)) for x in frase.split()]
    for i in range(len(seq) - len(f) + 1):
        if seq[i][1] >= after and [_canon(s) for s, _, _ in seq[i:i + len(f)]] == f:
            return i
    return None


def _tiempos(rk, seq, k, it, cursor):
    """(entra, vuela, número dicho) de un elemento, en segundos."""
    if rk.get("orden") == "numero_primero":
        # «Diez. …»: entra al decir su número; vuela antes del número siguiente (o tras `vuela_tras`)
        pre = rk.get("prefijo")  # p. ej. "puesto": solo vale «puesto 5», no «los 5 trabajos»

        def es(m, n):
            return _num(seq[m][0] or "x") == n and (not pre or (m > 0 and seq[m - 1][0] == pre))
        i = next((m for m in range(len(seq)) if seq[m][1] >= cursor and es(m, it["numero"])), None)
        if i is None:
            raise SystemExit(f"ranking: no encuentro el número {it['numero']} después de {cursor:.1f}s")
        t_in = seq[i - 1][1] if pre else seq[i][1]
        if it.get("vuela_tras"):
            j = _find(seq, it["vuela_tras"], t_in)
            return t_in, seq[j][1] - 0.3, t_in
        nxt = rk["items"][k + 1]["numero"] if k + 1 < len(rk["items"]) else None
        m2 = next((m for m in range(i + 1, len(seq)) if nxt is not None and es(m, nxt)), None)
        if m2 is not None:
            m2 = m2 - 1 if pre else m2
        return t_in, (seq[m2][1] - 0.55) if m2 is not None else min(t_in + 4.0, rk["dur"] - 1.0), t_in
    i = _find(seq, it["frase"], cursor)
    if i is None:
        raise SystemExit(f"ranking: no encuentro «{it['frase']}» después de {cursor:.1f}s")
    t_in = seq[i][1]
    if it.get("vuela_tras"):
        j = _find(seq, it["vuela_tras"], t_in)
        t_fly = seq[j + len(it["vuela_tras"].split()) - 1][2] + 0.15
        return t_in, t_fly, t_fly
    j = next((m for m in range(i, len(seq) - 2) if _num(seq[m][0] or "x") == it["numero"]
              and seq[m + 1][0] == "de" and _num(seq[m + 2][0] or "x") == 10), None)
    if j is None:
        raise SystemExit(f"ranking: no encuentro «{it['numero']} de 10» tras «{it['frase']}»")
    return t_in, seq[j + 2][2] + 0.1, seq[j][1]

CSS_TOP = """
      .tp-tit {{ position: absolute; left: 60px; width: 960px; top: {TY}px; z-index: 6; text-align: center;
                 font: 54px/1.05 "Anton", sans-serif; color: #fff; text-transform: uppercase;
                 -webkit-text-stroke: 10px #000; paint-order: stroke fill; }}
      .tp-col {{ position: absolute; left: {X}px; top: {Y0}px; z-index: 6; }}
      .tp-coin {{ position: absolute; left: 0; width: {D}px; height: {D}px; border-radius: 50%; opacity: 0;
                  background: radial-gradient(circle at 35% 30%, #fff3b0 0%, #f2c94c 35%, #b8860b 100%);
                  border: 5px solid #5a3e00; display: flex; align-items: center; justify-content: center; overflow: hidden;
                  box-shadow: 0 6px 0 rgba(0,0,0,.35); }}
      .tp-coin .n {{ font: {NF}px/1 "Anton", sans-serif; color: #5a3e00; }}
      .tp-coin .ic {{ position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
                      background: var(--amarillo); opacity: 0; }}
      .tp-coin .ic svg {{ width: 62%; height: 62%; fill: none; stroke: #000; stroke-width: 2.4; stroke-linecap: round; stroke-linejoin: round; }}
      .tp-coin .ic img {{ width: 100%; height: 100%; object-fit: cover; }}
      .tp-mid {{ position: absolute; left: 160px; width: 860px; top: {MY}px; z-index: 7; text-align: center; }}
      .tp-nn {{ font: 170px/1 "Anton", sans-serif; color: #fff; -webkit-text-stroke: 18px #000; paint-order: stroke fill;
                text-shadow: 0 12px 0 rgba(0,0,0,.4); }}
      .tp-of {{ font: 92px/1 "Anton", sans-serif; color: var(--amarillo); text-transform: uppercase;
                -webkit-text-stroke: 14px #000; paint-order: stroke fill; opacity: 0; }}
      .tp-su {{ margin-top: 10px; font: 120px/1 "Anton", sans-serif; color: var(--amarillo); white-space: nowrap;
                -webkit-text-stroke: 16px #000; paint-order: stroke fill; text-shadow: 0 10px 0 rgba(0,0,0,.4); opacity: 0; }}
      .tp-su small {{ font-size: 54px; color: #fff; }}
      .tp-foto {{ position: absolute; left: 0; width: 1080px; top: {FY}px; height: {FH}px; z-index: 5; overflow: hidden;
                  -webkit-mask-image: linear-gradient(to bottom, transparent 0, #000 90px); }}
      .tp-foto img {{ width: 100%; height: 100%; object-fit: cover; }}
      .tp-foto .ico {{ position: absolute; left: 50%; top: 55%; width: 300px; height: 300px; margin: -150px 0 0 -150px;
                       border-radius: 50%; background: var(--amarillo); border: 9px solid #000; display: flex;
                       align-items: center; justify-content: center; box-shadow: 0 14px 0 rgba(0,0,0,.35); }}
      .tp-foto .ico svg {{ width: 62%; height: 62%; fill: none; stroke: #000; stroke-width: 2.2; stroke-linecap: round; stroke-linejoin: round; }}
"""


def _miles(n):
    return f"{n:,}".replace(",", ".")


def build_top(rk, words):
    """Top N con sueldo: título fijo, monedas 1-N a la izquierda, «Nº5», oficio, sueldo que cuenta y
    foto (o icono) del oficio abajo; al acabar cada puesto su icono rellena la moneda."""
    seq = [(_norm(w["raw"]), w["t0"], w["t1"]) for w in words]
    N = rk.get("total", 5)
    D, gap, x, y0 = rk.get("slot", 96), rk.get("paso", 118), rk.get("x", 34), rk.get("y", 330)
    my, fy = rk.get("medio_y", 560), rk.get("foto_y", 1250)
    css = CSS_TOP.format(TY=rk.get("titulo_y", 120), X=x, Y0=y0, D=D, NF=int(D * 0.6), MY=my, FY=fy, FH=1920 - fy)
    parts, js, ev, times = [], [], [], {}
    if rk.get("titulo"):
        t0t = rk.get("titulo_desde", 0.0)
        parts.append(f'      <div class="clip tp-tit" id="tptit" data-start="{t0t:.3f}" data-duration="{rk["dur"] - t0t:.3f}" '
                     f'data-track-index="7">{html.escape(rk["titulo"])}</div>')
        js.append(f'tl.fromTo("#tptit",{{opacity:0,y:-20}},{{opacity:1,y:0,duration:0.3}},{t0t:.3f});')
    rk = dict(rk, orden="numero_primero")
    cursor, fill = 0.0, {}
    for k, it in enumerate(rk["items"]):
        t_in, t_fly, _ = _tiempos(rk, seq, k, it, cursor)
        cursor = t_fly
        n = it["numero"]
        times[n] = (t_in, t_fly)
        ico = (f'<img src="assets/{html.escape(it["imagen"])}">' if it.get("imagen")
               else f'<svg viewBox="0 0 24 24">{ICONS[it["icono"]]}</svg>')
        fill[n] = ico
        # sueldo: aparece al decir «entre» (o 1,4 s después del puesto) y cuenta hasta las cifras
        su = ""
        if it.get("sueldo"):
            de, a = it["sueldo"]
            j = _find(seq, it.get("sueldo_frase", "entre"), t_in)
            t_su = seq[j][1] if j is not None and seq[j][1] < t_fly else t_in + 1.4
            su = (f'<div class="tp-su" id="tpsu{k}"><span id="tpd{k}">0</span>–<span id="tpa{k}">0</span>'
                  f' €<small>/mes</small></div>')
            for sid, v in ((f"tpd{k}", de), (f"tpa{k}", a)):
                js.append(f'const c{sid}={{v:0}};tl.fromTo(c{sid},{{v:0}},{{v:{v},duration:0.7,ease:"power2.out",'
                          f'onUpdate:()=>{{document.getElementById("{sid}").textContent=Math.round(c{sid}.v)'
                          f'.toLocaleString("de-DE")}}}},{t_su + 0.1:.3f});')
            js.append(f'tl.fromTo("#tpsu{k}",{{opacity:0,scale:0.6}},{{opacity:1,scale:1,duration:0.25,ease:"back.out(2.4)"}},{t_su:.3f});')
            ev += [(t_su, "whoosh")]
        t_of = t_in + 0.9
        parts.append(f'      <div class="clip tp-mid" id="tpm{k}" data-start="{t_in:.3f}" data-duration="{t_fly + 0.3 - t_in:.3f}" '
                     f'data-track-index="8"><div class="tp-nn" id="tpn{k}">Nº{n}</div>'
                     f'<div class="tp-of" id="tpo{k}">{html.escape(it["texto"])}</div>{su}</div>')
        js.append(f'tl.fromTo("#tpn{k}",{{opacity:0,scale:1.8}},{{opacity:1,scale:1,duration:0.25,ease:"power3.out"}},{t_in:.3f});')
        js.append(f'tl.to("#tpn{k}",{{opacity:0,duration:0.15}},{t_of - 0.1:.3f});')
        js.append(f'tl.set("#tpn{k}",{{display:"none"}},{t_of:.3f});')
        js.append(f'tl.fromTo("#tpo{k}",{{opacity:0,y:30}},{{opacity:1,y:0,duration:0.25,ease:"back.out(2)"}},{t_of:.3f});')
        js.append(f'tl.to("#tpm{k}",{{opacity:0,duration:0.2}},{t_fly:.3f});')
        # foto (o icono grande) del oficio en la mitad de abajo
        foto = (f'<img src="assets/{html.escape(it["imagen"])}">' if it.get("imagen")
                else f'<div class="ico"><svg viewBox="0 0 24 24">{ICONS[it["icono"]]}</svg></div>')
        parts.append(f'      <div class="clip tp-foto" id="tpf{k}" data-start="{t_in + 0.3:.3f}" data-duration="{t_fly + 0.3 - t_in - 0.3:.3f}" '
                     f'data-track-index="9">{foto}</div>')
        js.append(f'tl.fromTo("#tpf{k}",{{y:300,opacity:0}},{{y:0,opacity:1,duration:0.4,ease:"power3.out"}},{t_in + 0.3:.3f});')
        js.append(f'tl.to("#tpf{k}",{{y:200,opacity:0,duration:0.25,ease:"power2.in"}},{t_fly:.3f});')
        # la moneda se rellena con el icono
        js.append(f'tl.set("#tpic{n}",{{opacity:1}},{t_fly + 0.2:.3f});')
        js.append(f'tl.fromTo("#tpc{n}",{{scale:1.4}},{{scale:1,duration:0.25,ease:"back.out(3)"}},{t_fly + 0.2:.3f});')
        ev += [(t_in, "impacto"), (t_of, "pop"), (t_fly + 0.2, "tic")]
    coins = []
    for n in range(1, N + 1):
        coins.append(f'<div class="tp-coin" id="tpc{n}" style="top:{(n - 1) * gap}px"><span class="n">{n}</span>'
                     f'<div class="ic" id="tpic{n}">{fill.get(n, "")}</div></div>')
        js.append(f'tl.fromTo("#tpc{n}",{{opacity:0,x:-40}},{{opacity:1,x:0,duration:0.2}},{rk.get("col_t", 1.0) + n * 0.07:.3f});')
    parts.insert(0, f'      <div class="clip tp-col" id="tpcol" data-start="0" data-duration="{rk["dur"]:.3f}" '
                    f'data-track-index="7">{"".join(coins)}</div>')
    return css, "\n".join(parts), js, ev, times


def build_ranking(rk, words):
    if rk.get("aspecto") == "top":
        return build_top(rk, words)
    seq = [(_norm(w["raw"]), w["t0"], w["t1"]) for w in words]
    completa = rk.get("aspecto") == "completa"
    if completa:
        D, gap, x, y0 = rk.get("slot", 112), rk.get("paso", 166), rk.get("x", 24), rk.get("y", 120)
    else:
        D, gap, x, y0 = rk.get("slot", 62), rk.get("paso", 90), rk.get("x", 112), rk.get("y", 330)
    ix = rk.get("item_x", 210)
    nw = rk.get("num_ancho", 150)  # ancho de la columna de números en el aspecto completo («10.»)
    bs, bcx, bcy = rk.get("grande", 380), rk.get("grande_x", 600), rk.get("grande_y", 560)
    css = CSS.format(X=x, Y0=y0, D=D, NF=int(D * 0.55), IS=int(D * 0.62), TOP=rk.get("item_y", 205),
                     IX=ix, LW=910 - ix - 112 - 22,
                     CTA_Y=rk.get("cta_y", 240), CTA_X=rk.get("cta_x", 150), CTA_W=rk.get("cta_w", 780))
    if completa:
        # el texto de debajo de la foto grande no se sale por los bordes aunque la foto vaya a un lado
        lbw = rk.get("grande_ancho") or min(760, 2 * min(bcx, 1080 - bcx) - 40)
        css += CSS_COMPLETA.format(X=x, Y0=y0, D=D, NW=nw, NF=int(D * 0.95), BX=bcx - bs // 2, BY=bcy - bs // 2, BS=bs,
                                   LBW=lbw, LBF=rk.get("grande_texto", 66), TY=rk.get("titulo_y", 120), TF=rk.get("titulo_px", 62))
        if rk.get("titulo"):  # título fijo arriba todo el vídeo; «|» parte la línea
            t0t = rk.get("titulo_desde", 0.0)
            lineas = "<br>".join(" ".join(f'<span class="acc">{html.escape(w)}</span>' if w in rk.get("titulo_acento", []) else html.escape(w)
                                          for w in l.split()) for l in rk["titulo"].split("|"))
            parts_tit = (f'      <div class="clip rk-tit" id="rktit" data-start="{t0t:.3f}" data-duration="{rk["dur"] - t0t:.3f}" '
                         f'data-track-index="7">{lineas}</div>')
    parts, js, ev, times = [], [], [], {}
    if completa and rk.get("titulo"):
        parts.append(parts_tit)
        js.append(f'tl.fromTo("#rktit",{{opacity:0,y:-40}},{{opacity:1,y:0,duration:0.4,ease:"back.out(1.8)"}},{rk.get("titulo_desde", 0.0):.3f});')

    if rk.get("pulso_1_t") is not None:
        t = rk["pulso_1_t"]
        js.append(f'tl.fromTo("#rks1",{{scale:1}},{{scale:1.35,duration:0.18,yoyo:true,repeat:3,ease:"power1.inOut"}},{t:.3f});')
        ev.append((t, "tic"))

    cursor, slot_icon = 0.0, {}
    if rk.get("zoom_ritmo"):
        js.append(f'gsap.set("#video",{{transformOrigin:"{rk.get("centro", "540px 760px")}"}});tl.set("#video",{{scale:1}},0);')
    for k, it in enumerate(rk["items"]):
        t_in, t_fly, t_num = _tiempos(rk, seq, k, it, cursor)
        cursor = t_fly
        times[it["numero"]] = (t_in, t_fly)
        n = it["numero"]
        # contenido: foto de assets/ (`imagen`) o icono de línea
        ico = (f'<img src="assets/{html.escape(it["imagen"])}">' if it.get("imagen")
               else f'<svg viewBox="0 0 24 24">{ICONS[it["icono"]]}</svg>')
        if completa:
            # grande en el centro → se encoge hasta la miniatura junto a su número (posiciones fijas)
            parts.append(f'      <div class="clip rk-big" id="rki{k}" data-start="{t_in:.3f}" '
                         f'data-duration="{t_fly + 0.5 - t_in:.3f}" data-track-index="8">'
                         f'<div class="ico" id="rkc{k}">{ico}</div>'
                         f'<div class="lab" id="rkl{k}">{html.escape(it["texto"])}</div>'
                         + (f'<div class="cred" id="rkf{k}">{html.escape(it["credito"])}</div>' if it.get("credito") else "")
                         + '</div>')
            tx, ty = x + nw + 14 + D / 2, y0 + (n - 1) * gap + D / 2
            js.append(f'tl.fromTo("#rki{k}",{{opacity:0,scale:0.4}},{{opacity:1,scale:1,duration:0.3,ease:"back.out(2)"}},{t_in:.3f});')
            js.append(f'tl.to("#rkl{k}",{{opacity:0,duration:0.15}},{t_fly:.3f});')
            if it.get("credito"):
                js.append(f'tl.to("#rkf{k}",{{opacity:0,duration:0.15}},{t_fly:.3f});')
            js.append(f'tl.to("#rkc{k}",{{x:{tx - bcx:.0f},y:{ty - bcy:.0f},scale:{D / bs:.3f},duration:0.5,'
                      f'ease:"power3.in"}},{t_fly:.3f});')
            js.append(f'tl.set("#rkc{k}",{{opacity:0}},{t_fly + 0.5:.3f});')
            js.append(f'tl.set("#rkth{n}",{{opacity:1}},{t_fly + 0.5:.3f});')
            js.append(f'tl.set("#rkn{n}",{{color:"{rk.get("color", "#FFC800")}"}},{t_fly + 0.5:.3f});')
            js.append(f'tl.fromTo("#rkr{n}",{{scale:1.25}},{{scale:1,duration:0.25,ease:"back.out(3)"}},{t_fly + 0.5:.3f});')
            slot_icon[n] = ico
        else:
            parts.append(f'      <div class="clip rk-item" id="rki{k}" data-start="{t_in:.3f}" '
                         f'data-duration="{t_fly + 0.5 - t_in:.3f}" data-track-index="8">'
                         f'<div class="ico" id="rkc{k}">{ico}</div>'
                         f'<div class="lab" id="rkl{k}">{html.escape(it["texto"])}</div></div>')
            js.append(f'tl.fromTo("#rki{k}",{{opacity:0,scale:0.6}},{{opacity:1,scale:1,duration:0.25,ease:"back.out(2)"}},{t_in:.3f});')
            js.append(f'tl.to("#rkl{k}",{{opacity:0,duration:0.15}},{t_fly:.3f});')
            cx_, cy_ = x + D / 2, y0 + (n - 1) * gap + D / 2
            # vuelo con posiciones fijas (el icono siempre está en item_x, item_y): determinista en cualquier worker
            icx, icy = ix + 56, rk.get("item_y", 205) + 56
            js.append(f'tl.to("#rkc{k}",{{x:{cx_ - icx:.0f},y:{cy_ - icy:.0f},scale:{D / 112:.3f},duration:0.45,'
                      f'ease:"power3.in"}},{t_fly:.3f});')
            js.append(f'tl.set("#rkc{k}",{{opacity:0}},{t_fly + 0.45:.3f});')
            slot_icon[n] = ico
            tl_ = t_fly + 0.45
            js.append(f'tl.set("#rks{n}",{{backgroundColor:"{rk.get("color", "#FFC800")}",borderStyle:"solid",borderColor:"#000"}},{tl_:.3f});')
            js.append(f'tl.set("#rks{n} .n",{{color:"#000",webkitTextStrokeWidth:0}},{tl_:.3f});')
            js.append(f'tl.fromTo("#rks{n}",{{scale:1.5}},{{scale:1,duration:0.25,ease:"back.out(3)"}},{t_fly + 0.45:.3f});')
        ev += [(t_in, "pop"), (t_fly, "whoosh"), (t_fly + 0.45, "tic")]
        if rk.get("sello", True):
            parts.append(sello(n, t_num, t_fly + (1.0 if n == 1 else 0.3), n, 10, js, ev))
        zr = rk.get("zoom_ritmo")
        if zr:
            js.append(f'tl.set("#video",{{scale:{zr[k % len(zr)]}}},{t_in:.3f});')

    # columna 1-10: entra escalonada al principio
    slots = []
    for n in range(1, 11):
        if completa:
            slots.append(f'<div class="rk-row" id="rkr{n}" style="top:{(n - 1) * gap}px"><span class="n" id="rkn{n}">{n}.</span>'
                         f'<div class="th" id="rkth{n}">{slot_icon.get(n, "")}</div></div>')
            js.append(f'tl.fromTo("#rkr{n}",{{opacity:0,x:-40}},{{opacity:1,x:0,duration:0.2}},{rk.get("col_t", 1.0) + n * 0.06:.3f});')
        else:
            slots.append(f'<div class="rk-slot" id="rks{n}" style="top:{(n - 1) * gap}px"><span class="n">{n}</span>'
                         f'</div>')
            js.append(f'tl.fromTo("#rks{n}",{{opacity:0,x:-40}},{{opacity:1,x:0,duration:0.2}},{rk.get("col_t", 1.0) + n * 0.06:.3f});')
    parts.insert(0, f'      <div class="clip rk-col" id="rkcol" data-start="0" data-duration="{rk["dur"]:.3f}" '
                    f'data-track-index="7">{"".join(slots)}</div>')

    if rk.get("cta"):
        c = rk["cta"]
        i = _find(seq, c["frase"], 0)
        if i is None:
            raise SystemExit(f"ranking: no encuentro la frase de la caja «{c['frase']}»")
        t_box = seq[i][1]
        k = _find(seq, c["palabra"], t_box)
        # si la palabra no se dice (o se dijo otra), se escribe nada más salir la caja
        t_type = seq[k][1] if k is not None and c.get("escribir") != "al_salir" else t_box + 0.9
        chars = "".join(f'<span class="c" id="rkt{m}">{html.escape(ch)}</span>' for m, ch in enumerate(c["palabra"].upper()))
        parts.append(f'      <div class="clip rk-cta" id="rkcta" data-start="{t_box:.3f}" '
                     f'data-duration="{rk.get("cta_hasta", rk["dur"]) - t_box:.3f}" data-track-index="9">'
                     f'<div class="ph"><span class="hint" id="rkhint">Añade un comentario…</span>{chars}</div>'
                     f'<div class="send" id="rksend"><svg viewBox="0 0 24 24"><path d="M12 19V5M5 12l7-7 7 7"/></svg></div></div>')
        js.append(f'tl.fromTo("#rkcta",{{opacity:0,y:-30}},{{opacity:1,y:0,duration:0.25,ease:"back.out(2)"}},{t_box:.3f});')
        js.append(f'tl.set("#rkhint",{{display:"none"}},{t_type:.3f});')
        for m in range(len(c["palabra"])):
            js.append(f'tl.set("#rkt{m}",{{opacity:1}},{t_type + m * 0.08:.3f});')
            ev.append((t_type + m * 0.08, "tic"))
        t_send = t_type + len(c["palabra"]) * 0.08 + 0.2
        js.append(f'tl.set("#rksend",{{backgroundColor:"#0095f6"}},{t_send:.3f});')
        js.append(f'tl.fromTo("#rksend",{{scale:1.3}},{{scale:1,duration:0.25,ease:"back.out(3)"}},{t_send:.3f});')
        ev += [(t_box, "pop"), (t_send, "pop")]
    return css, "\n".join(parts), js, ev, times
