#!/usr/bin/env python3
"""Carrusel animado de Instagram: portada fija + diapositivas de 7 s en bucle, 1080×1440.

Uso:
  python3 scripts/carrusel.py <nombre>             compone y renderiza → out/carrusel_<nombre>/
  python3 scripts/carrusel.py <nombre> --solo 02   solo esa diapositiva (00 = portada)
  python3 scripts/carrusel.py <nombre> --hoja      además, hoja de fotogramas para revisar
  ENTREGA_APROBADA=1 python3 scripts/carrusel.py <nombre> --entregar
                                                   con el visto bueno del creador: copia lo renderizado a la
                                                   carpeta de entregas («<fecha tema>/<fecha tema> - <letra> carrusel - NN…»)

Entrada: carruseles/<nombre>/carrusel.json. Cada diapositiva tiene antetítulo, título, pastilla, un panel con
bloques que se animan uno detrás de otro (campo, checks, calendario, huella, contador, precio, documento,
tarjeta, estado; y "foto", que llena el panel por detrás con una foto de licencia libre de carruseles/<nombre>/fotos/
y su crédito), dos líneas con **acentos** y pastillas de fuente y aviso. Cada cifra en pantalla tiene que
estar verificada (regla de las tarjetas): la fuente va en su pastilla.

Cierre (la última pieza): «Comenta PALABRA» con "cta" (la palabra por defecto de marca/marca.json si no dice otra),
nada con "cta": false, o «Tu turno» con un cierre sin palabra de `scripts/cierre.py`
("cierre": {"tipo": "info" | "conversacion", "pregunta": "¿…?"}).

Marca: el @ sale de marca/marca.json. La firma del pie del cierre (y el texto alternativo del logo) es "firma" del
carrusel.json, o "firma" de marca/marca.json, o tu nombre. Logo (marca/logos/), foto (marca/fotos/) y avatar
(marca/tarjetas/avatar-youtube.jpg) son opcionales: si no están, la pieza sale sin ellos.

Ritmo: 0,3-5,4 s los bloques entran en orden · hasta 6,5 s estado final · 6,5-7 s fundido y vuelta a empezar.
"""
import argparse
import html
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kit  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
W, H, DUR = 1080, 1440, 7.0
HF = ["npx", "--yes", "hyperframes@0.8.78"]
AMARILLO, NEGRO, CREMA = "#FFC800", "#111111", "#F6EBD0"
FONDOS = {"amarillo": (AMARILLO, NEGRO), "negro": (NEGRO, "#FFFFFF"), "crema": (CREMA, NEGRO)}
# Paletas: "marca" (el acento y el negro de tu marca, con tu logo recoloreado en marca/logos/logo-marca.png) o
# "logo" (paleta alternativa azul marino y dorado, con el logo en sus colores en marca/logos/logo.png). La de "logo"
# se aplica cambiando los colores de marca en la página ya compuesta.
PALETAS = {
    "marca": {"logo": "logo-marca.png", "cambios": {}},
    "logo": {"logo": "logo.png", "cambios": {
        "#111111": "#1B2A3C", "#FFC800": "#C9A86A", "#F6EBD0": "#F3EBDD", "#1a1a1a": "#15233A",
        "#262626": "#22344A", "#3a3a3a": "#2D4058", "#111": "#1B2A3C"}},
}

CHECK = ('<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="11" fill="#FFC800"/><path fill="none" stroke="#111" '
         'stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round" d="M7 12.5l3.2 3.2L17 9"/></svg>')
HUELLA = ('<svg viewBox="0 0 64 64" fill="none" stroke="#FFC800" stroke-width="3" stroke-linecap="round">'
          '<path d="M18 50c-4-6-6-12-6-19a20 20 0 0 1 40 0c0 4-1 8-3 11"/><path d="M24 54c-4-6-6-14-6-23a14 14 0 0 1 28 0'
          'c0 6-1 11-3 15"/><path d="M31 57c-3-8-5-17-5-26a6 6 0 0 1 12 0c0 9-2 17-5 24"/><path d="M32 31c0 9-1 17-4 24"/></svg>')

CSS = """
@font-face { font-family: "Anton"; src: url("assets/Anton-Regular.ttf"); }
@font-face { font-family: "Oswald"; src: url("assets/Oswald-Variable.ttf"); font-weight: 200 700; }
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body { width: 1080px; height: 1440px; overflow: hidden; background: var(--fondo); }
#root { position: relative; width: 1080px; height: 1440px; background: var(--fondo); color: var(--tinta); }
.ante { position: absolute; left: 72px; top: 84px; font: 500 30px "Oswald"; letter-spacing: .14em; opacity: .75; }
.titulo { position: absolute; left: 68px; right: 60px; top: 142px; font-family: "Anton"; line-height: .98;
  text-transform: uppercase; white-space: nowrap; }
.pastilla { position: absolute; left: 72px; top: 300px; padding: 10px 26px; border-radius: 16px; font: 500 34px Menlo, monospace;
  background: var(--pbg); color: var(--ptx); }
.pastilla b { color: var(--pacento); font-weight: 700; margin-right: 12px; }
.panel { position: absolute; left: 72px; top: 392px; width: 936px; height: 690px; border-radius: 44px; background: #1a1a1a;
  border: 3px solid rgba(255,255,255,.08); padding: 34px 40px; display: flex; flex-direction: column; gap: 20px;
  justify-content: center; color: #fff; font-family: "Oswald"; }
.texto { position: absolute; left: 72px; right: 72px; top: 1110px; font: 400 44px/1.5 "Oswald"; }
.texto .ac { display: inline-block; line-height: 1.12; font-weight: 700; padding: 2px 10px; border-radius: 8px;
  background: var(--acbg); color: var(--actx); }
.pie { position: absolute; left: 72px; top: 1300px; display: flex; gap: 16px; z-index: 4; }
.pie span { padding: 10px 22px; border-radius: 14px; font: 600 28px "Oswald"; }
.pie .fuente { background: var(--pbg); color: var(--ptx); }
.pie .aviso { background: var(--avbg); color: var(--tinta); }
.fila { display: flex; gap: 26px; }
.fila > * { flex: 1; }
.b { border-radius: 26px; background: #262626; padding: 24px 30px; }
.campo { display: flex; gap: 18px; align-items: center; font-size: 36px; }
.campo .lab { color: #FFC800; font-weight: 600; }
.campo .val { font-weight: 400; }
.campo .val::after { content: "▍"; color: #FFC800; margin-left: 4px; }
.checks { display: flex; flex-direction: column; gap: 14px; font-size: 36px; }
.checks .it { display: flex; align-items: center; gap: 18px; will-change: transform; }
.checks .it svg, .tic svg { width: 44px; height: 44px; }
.checks .caja { width: 44px; height: 44px; border-radius: 50%; border: 3px solid #555; position: relative; flex: none; }
.checks .caja svg { position: absolute; inset: -3px; }
.contador { text-align: center; padding: 10px 30px; }
.contador .antes { font-size: 28px; letter-spacing: .14em; color: #bbb; }
.contador .num { font-family: "Anton"; font-size: 118px; line-height: 1.05; color: #FFC800; }
.contador .num span { display: inline-block; }
.contador .num small { font-size: 74px; margin-left: 14px; }
.precio { display: flex; align-items: center; justify-content: space-between; background: #fff; color: #111; }
.precio .tit { font-size: 38px; font-weight: 600; max-width: 380px; line-height: 1.1; }
.precio .num { font-family: "Anton"; font-size: 120px; line-height: 1; }
.precio .num small { font-size: 46px; }
.precio .antes { font-size: 30px; font-weight: 600; color: #777; text-align: right; }
.doc { display: flex; align-items: center; gap: 26px; background: #fff; color: #111; position: relative; }
.doc .ico { width: 84px; height: 104px; border-radius: 10px; background: #eee; border: 3px solid #ccc; flex: none;
  background-image: repeating-linear-gradient(#bbb 0 4px, transparent 4px 18px); background-size: 56px 80px;
  background-repeat: no-repeat; background-position: 12px 14px; }
.doc .tit { font-size: 40px; font-weight: 600; line-height: 1.05; }
.doc .sub { font-size: 28px; color: #666; }
.doc .sello { position: absolute; right: 30px; top: 50%; margin-top: -42px; padding: 12px 22px; border: 5px solid #1a8f3c;
  color: #1a8f3c; border-radius: 12px; font: 700 40px "Oswald"; transform: rotate(-8deg); }
.tarjeta { display: flex; align-items: center; gap: 28px; background: linear-gradient(120deg, #2f4f8f, #5a7fc4); }
.tarjeta .foto { width: 92px; height: 112px; border-radius: 12px; background: rgba(255,255,255,.25); flex: none; }
.tarjeta .tit { font-family: "Anton"; font-size: 64px; line-height: 1; }
.tarjeta .sub { font-size: 28px; opacity: .85; }
.cal { display: grid; grid-template-columns: repeat(7, 1fr); gap: 8px; align-content: center; }
.cal i { display: block; height: 24px; border-radius: 6px; background: #3a3a3a; }
.cal i.dia { background: #FFC800; }
.cal .rot, .huella .rot { grid-column: 1 / -1; font-size: 30px; color: #FFC800; font-weight: 600; margin-bottom: 6px; }
.huella { display: flex; flex-direction: column; align-items: center; justify-content: center; position: relative; overflow: hidden; }
.huella svg { width: 100px; height: 100px; }
.huella .scan { position: absolute; left: 0; right: 0; height: 6px; background: #FFC800; box-shadow: 0 0 24px #FFC800; top: 30%; }
.estado { align-self: center; padding: 16px 40px; border-radius: 40px; background: #FFC800; color: #111;
  font: 700 40px "Oswald"; display: flex; gap: 14px; align-items: center; }
.panel.confoto { justify-content: flex-end; overflow: hidden; }
.panel.confoto > :not(.fotofondo) { position: relative; z-index: 1; }
.fotofondo { position: absolute; inset: 0; z-index: 0; overflow: hidden; border-radius: 41px; }
.fotofondo img { width: 100%; height: 100%; object-fit: cover; }
.fotofondo::after { content: ""; position: absolute; inset: 0;
  background: linear-gradient(180deg, rgba(0,0,0,0) 30%, rgba(0,0,0,.55) 55%, rgba(0,0,0,.9) 100%); }
.fotofondo .credito { position: absolute; right: 22px; top: 18px; z-index: 2; padding: 5px 12px; border-radius: 8px;
  background: rgba(0,0,0,.55); color: #fff; font: 400 19px "Oswald"; letter-spacing: .02em; }
.panel.confoto { gap: 12px; padding-bottom: 26px; }
.confoto .contador { background: rgba(17,17,17,.72); padding: 8px 24px; }
.confoto .contador .antes { font-size: 22px; }
.confoto .contador .num { font-size: 84px; }
.confoto .contador .num small { font-size: 52px; margin-left: 10px; }
.confoto .campo { background: rgba(17,17,17,.72); font-size: 30px; padding: 16px 24px; }
.logo { position: absolute; right: 60px; top: 60px; width: 132px; height: 132px; z-index: 5; border-radius: 50%; box-shadow: 0 0 0 3px #FFC800; }
.foto { position: absolute; z-index: 2; }
.portada .titulo { z-index: 3; white-space: normal; top: 230px; font-size: 168px; line-height: 1.08; }
.portada .titulo .ac { display: inline-block; line-height: 1.12; margin-top: 22px; background: #111; color: #FFC800; padding: 26px 22px 0; border-radius: 16px; }
.portada .lista { position: absolute; left: 72px; top: 940px; font: 500 38px/1.5 "Oswald"; }
.portada .lista b { font-family: "Anton"; font-weight: 400; margin-right: 16px; }
.portada .desliza { z-index: 4; position: absolute; right: 72px; bottom: 80px; padding: 18px 34px; border-radius: 40px;
  background: var(--pbg); color: var(--ptx); font: 700 40px "Oswald"; }
.portada .usuario { position: absolute; left: 72px; bottom: 96px; font: 600 34px "Oswald"; }
.portada .logo { width: 170px; height: 170px; }
.cta .titulo { top: 128px; }
.cta .titulo .ac { color: #FFC800; }
.comentario { position: absolute; left: 72px; top: 330px; width: 936px; height: 128px; border-radius: 64px; background: #fff;
  display: flex; align-items: center; gap: 22px; padding: 0 30px; color: #111; font-family: "Oswald"; z-index: 3; }
.comentario .yo { width: 76px; height: 76px; border-radius: 50%; background: #d9d9d9; flex: none; display: flex;
  align-items: center; justify-content: center; font: 600 28px "Oswald"; color: #666; }
.comentario .campo2 { flex: 1; font-size: 44px; color: #999; position: relative; }
.comentario .campo2 b { position: absolute; left: 0; top: 0; color: #111; font-family: "Anton"; font-weight: 400; letter-spacing: .02em; }
.comentario .publicar { font: 700 38px "Oswald"; color: #b5cdf5; }
.respuesta { position: absolute; left: 150px; top: 486px; width: 760px; display: flex; gap: 20px; align-items: flex-start;
  color: #fff; font-family: "Oswald"; z-index: 3; }
.respuesta img { width: 84px; height: 84px; border-radius: 50%; object-fit: cover; flex: none; }
.respuesta .burbuja { background: #262626; border-radius: 28px; padding: 18px 28px; font-size: 36px; line-height: 1.25; }
.respuesta .burbuja b { color: #FFC800; font-weight: 600; display: block; font-size: 30px; }
.revisa { position: absolute; left: 72px; top: 700px; padding: 18px 34px; border-radius: 40px; background: #FFC800; color: #111;
  font: 700 42px "Oswald"; z-index: 3; }
.cta .texto { top: 860px; right: 520px; font-size: 46px; }
.cta .pie { top: 1290px; }
.turno .titulo { top: 196px; right: 72px; white-space: normal; line-height: 1.02; }
.turno .comentario { top: 480px; }
.turno .respuesta { top: 636px; }
.turno .revisa { top: 800px; }
.turno .texto { top: 940px; }
"""

PAGE = """<!doctype html>
<html lang="es"><head><meta charset="utf-8" /><meta name="viewport" content="width={W}, height={H}" />
<title>{titulo}</title><script src="assets/gsap.min.js"></script>
<style>:root {{ {vars} }}{css}</style></head>
<body><div id="root" class="{clase}" data-composition-id="main" data-start="0" data-duration="{dur}" data-width="{W}" data-height="{H}">
{cuerpo}
</div><script>
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{ paused: true }});
{js}
tl.set({{}}, {{}}, {dur});
window.__timelines["main"] = tl;
</script></body></html>
"""


def acentos(txt):
    return re.sub(r"\*\*(.+?)\*\*", r'<span class="ac">\1</span>', html.escape(txt))


def colores(fondo):
    bg, tinta = FONDOS[fondo]
    claro = fondo != "negro"
    return (f"--fondo: {bg}; --tinta: {tinta}; --pbg: {NEGRO if claro else AMARILLO}; --ptx: {'#fff' if claro else NEGRO}; "
            f"--pacento: {AMARILLO if claro else NEGRO}; --acbg: {NEGRO if claro else 'transparent'}; --actx: {AMARILLO}; "
            f"--avbg: {'rgba(0,0,0,.12)' if claro else 'rgba(255,255,255,.14)'};")


def tam_titulo(t):
    """Anton en mayúsculas ocupa ~0,52 em por carácter: el título en una línea dentro de 800 px (a la derecha va el logo), máx. 136 px (con el título más bajo, deja aire a la pastilla)."""
    return min(136, int(800 / (0.52 * max(len(t), 1))))


# FIRMA se cambia por la firma del carrusel al escribir cada página (ver firma()).
FIRMA = "§FIRMA§"
LOGO = f'<img class="logo" src="assets/logo.png" alt="{FIRMA}">'
AVATAR = '<img src="assets/avatar.jpg">'
# sin avatar en marca/tarjetas/, un círculo gris del mismo tamaño en su sitio
SIN_AVATAR = '<span style="width:84px;height:84px;border-radius:50%;background:#555;flex:none"></span>'
FOTO_POR_DEFECTO = "retrato.png"  # en marca/fotos/: tu foto recortada (PNG con transparencia)


def firma(c):
    """Quién firma el pie del cierre y el logo: "firma" del carrusel, la de tu marca o tu nombre."""
    return c.get("firma") or kit.marca().get("firma") or kit.nombre()


def cifra_js(v, b):
    """Número a la española mientras sube: miles con punto (1.018) y `"decimales"` con coma (44,5)."""
    return (f'(x=>{{const p=x.toFixed({int(b.get("decimales", 0))}).split(".");'
            f'return p[0].replace(/\\B(?=(\\d{{3}})+(?!\\d))/g,".")+(p[1]?","+p[1]:"")}})({v})')


def bloque(b, n, t0):
    """HTML de un bloque del panel y su animación, que empieza en t0. Devuelve (html, js, fin)."""
    i, tipo, js = f"b{n}", b["tipo"], []
    entra = f'tl.fromTo("#{i}",{{opacity:0,y:30}},{{opacity:1,y:0,duration:0.35,ease:"back.out(1.8)"}},{t0:.2f});'
    if tipo == "campo":
        v = b["valor"]
        h = (f'<div class="b campo" id="{i}"><span class="lab">{html.escape(b["etiqueta"])}:</span>'
             f'<span class="val" id="{i}v"></span></div>')
        d = min(1.2, 0.05 * len(v))
        js += [entra, f'const o{i}={{n:0}};tl.to(o{i},{{n:{len(v)},duration:{d:.2f},ease:"none",onUpdate:()=>'
               f'{{document.getElementById("{i}v").textContent={json.dumps(v)}.slice(0,Math.round(o{i}.n))}}}},{t0 + 0.3:.2f});']
        return h, js, t0 + 0.3 + d
    if tipo == "checks":
        its = "".join(f'<div class="it" id="{i}i{k}"><span class="caja"><span id="{i}c{k}">{CHECK}</span></span>{html.escape(x)}</div>'
                      for k, x in enumerate(b["items"]))
        js.append(entra)
        for k in range(len(b["items"])):  # escalonado: la línea entra con rebote y después se marca
            t = t0 + 0.25 + 0.42 * k
            js.append(f'tl.fromTo("#{i}i{k}",{{opacity:0,x:-70}},{{opacity:1,x:0,duration:0.4,ease:"back.out(2)"}},{t:.2f});')
            js.append(f'tl.fromTo("#{i}c{k}",{{scale:0}},{{scale:1,duration:0.25,ease:"back.out(3)"}},{t + 0.25:.2f});')
        return f'<div class="b checks" id="{i}">{its}</div>', js, t0 + 0.5 + 0.42 * len(b["items"])
    if tipo == "contador":
        h = (f'<div class="b contador" id="{i}"><div class="antes">{html.escape(b.get("antes", ""))}</div>'
             f'<div class="num"><span id="{i}n">0</span><small>{html.escape(b.get("unidad", ""))}</small></div></div>')
        js += [entra, f'const o{i}={{v:0}};tl.to(o{i},{{v:{b["valor"]},duration:0.7,ease:"power2.out",onUpdate:()=>'
               f'{{document.getElementById("{i}n").textContent={cifra_js(f"o{i}.v", b)}}}}},{t0 + 0.2:.2f});',
               f'tl.fromTo("#{i}n",{{scale:1}},{{scale:1.14,duration:0.16,yoyo:true,repeat:1,ease:"power2.out"}},{t0 + 0.9:.2f});']
        return h, js, t0 + 1.2
    if tipo == "precio":
        h = (f'<div class="b precio" id="{i}"><div class="tit">{html.escape(b["titulo"])}</div><div>'
             f'<div class="antes">{html.escape(b.get("antes", ""))}</div><div class="num"><span id="{i}n">0</span>'
             f'<small>{html.escape(b.get("unidad", ""))}</small></div></div></div>')
        js += [entra, f'const o{i}={{v:0}};tl.to(o{i},{{v:{b["valor"]},duration:0.8,ease:"power2.out",onUpdate:()=>'
               f'{{document.getElementById("{i}n").textContent={cifra_js(f"o{i}.v", b)}}}}},{t0 + 0.2:.2f});']
        return h, js, t0 + 1.0
    if tipo == "documento":
        sello = f'<div class="sello" id="{i}s">{html.escape(b["sello"])}</div>' if b.get("sello") else ""
        h = (f'<div class="b doc" id="{i}"><div class="ico"></div><div><div class="tit">{html.escape(b["titulo"])}</div>'
             f'<div class="sub">{html.escape(b.get("sub", ""))}</div></div>{sello}</div>')
        js.append(f'tl.fromTo("#{i}",{{opacity:0,x:120}},{{opacity:1,x:0,duration:0.4,ease:"power3.out"}},{t0:.2f});')
        if sello:
            js.append(f'tl.fromTo("#{i}s",{{opacity:0,scale:2.2}},{{opacity:1,scale:1,duration:0.3,ease:"power4.in"}},{t0 + 0.6:.2f});')
        return h, js, t0 + 1.0
    if tipo == "tarjeta":
        h = (f'<div class="b tarjeta" id="{i}"><div class="foto"></div><div><div class="tit">{html.escape(b["titulo"])}</div>'
             f'<div class="sub">{html.escape(b.get("sub", ""))}</div></div></div>')
        js.append(f'tl.fromTo("#{i}",{{opacity:0,rotationY:-70,x:-60}},{{opacity:1,rotationY:0,x:0,duration:0.55,'
                  f'ease:"power3.out"}},{t0:.2f});')
        return h, js, t0 + 0.7
    if tipo == "calendario":
        dias = "".join(f'<i{" class=dia id=" + i + "d" if k == b.get("dia", 17) else ""}></i>' for k in range(28))
        h = f'<div class="b cal" id="{i}"><div class="rot">{html.escape(b.get("rotulo", "Cita"))}</div>{dias}</div>'
        js += [entra, f'tl.fromTo("#{i}d",{{scale:0.2,background:"#3a3a3a"}},{{scale:1,background:"#FFC800",duration:0.3,'
               f'ease:"back.out(3)"}},{t0 + 0.6:.2f});']
        return h, js, t0 + 1.0
    if tipo == "huella":
        h = (f'<div class="b huella" id="{i}"><div class="rot">{html.escape(b.get("rotulo", "Huellas"))}</div>{HUELLA}'
             f'<div class="scan" id="{i}s"></div></div>')
        js += [entra, f'tl.fromTo("#{i}s",{{y:0,opacity:1}},{{y:110,duration:0.7,ease:"sine.inOut",yoyo:true,repeat:1}},'
               f'{t0 + 0.3:.2f});', f'tl.to("#{i}s",{{opacity:0,duration:0.2}},{t0 + 1.7:.2f});']
        return h, js, t0 + 1.0
    if tipo == "estado":
        tic = CHECK.replace('fill="#FFC800"', 'fill="#111"').replace('stroke="#111"', 'stroke="#FFC800"')
        h = f'<div class="estado" id="{i}"><span class="tic">{tic}</span>{html.escape(b["texto"])}</div>'
        js.append(f'tl.fromTo("#{i}",{{opacity:0,scale:0.6}},{{opacity:1,scale:1,duration:0.35,ease:"back.out(2.5)"}},{t0:.2f});')
        return h, js, t0 + 0.5
    if tipo == "foto":
        # Foto de apoyo: llena el panel por detrás de los demás bloques, se
        # acerca despacio (micromovimiento) y lleva siempre su crédito. Solo fotos con licencia libre
        # (Wikimedia Commons: CC0, dominio público, CC BY, CC BY-SA), con autor y licencia en «credito».
        # "foco" [x, y] en % elige qué parte de la foto se ve; "zoom" (>1) la amplía para subir o bajar lo
        # importante por encima de las cifras, que tapan el tercio de abajo.
        fx, fy = b.get("foco", [50, 40])
        z = float(b.get("zoom", 1)) * 100
        estilo = (f"object-position:{fx}% {fy}%" if z == 100 else
                  f"position:absolute;width:{z:.0f}%;height:{z:.0f}%;left:{-(z - 100) * fx / 100:.1f}%;"
                  f"top:{-(z - 100) * fy / 100:.1f}%;object-position:{fx}% {fy}%")
        h = (f'<div class="fotofondo" id="{i}"><img id="{i}img" src="assets/fotos/{html.escape(b["imagen"])}" '
             f'style="{estilo}"><span class="credito">{html.escape(b["credito"])}</span></div>')
        js += [f'tl.fromTo("#{i}",{{opacity:0}},{{opacity:1,duration:0.5,ease:"power2.out"}},0.1);',
               f'tl.fromTo("#{i}img",{{scale:1.12}},{{scale:1.0,duration:{DUR - 0.6:.2f},ease:"sine.out"}},0.1);']
        return h, js, 0.6
    raise SystemExit(f"bloque desconocido: {tipo}")


def diapositiva(s, n, total):
    """Composición de una diapositiva: cabecera y pie quietos; el panel se anima y se funde para el bucle."""
    filas = s["panel"]
    planos = [b for f in filas for b in (f if isinstance(f, list) else [f])]
    confoto = any(b["tipo"] == "foto" for b in planos)
    paso = min(1.3, 3.4 / max(len([b for b in planos if b["tipo"] != "foto"]), 1))
    k, html_panel, fin = 0, [], 0.0
    # Movimiento: la pastilla y el panel entran con rebote; el panel respira (zoom lento) y el logo y el
    # título flotan a ritmos distintos (parallax). Todo vuelve a su sitio a los 7 s para que el bucle no salte.
    js = ['tl.fromTo(".pastilla",{opacity:0,x:-80},{opacity:1,x:0,duration:0.45,ease:"back.out(2)"},0.05);',
          'tl.fromTo("#panel",{opacity:0,y:50,scale:0.92},{opacity:1,y:0,scale:1,duration:0.55,ease:"back.out(1.6)"},0.1);',
          f'tl.to("#panel",{{scale:1.025,duration:{DUR - 1.2:.2f},ease:"sine.inOut"}},0.65);',
          f'tl.fromTo(".logo",{{y:0}},{{y:-12,duration:{DUR / 2:.2f},ease:"sine.inOut",yoyo:true,repeat:1}},0);',
          f'tl.fromTo(".titulo",{{x:0}},{{x:6,duration:{DUR / 2:.2f},ease:"sine.inOut",yoyo:true,repeat:1}},0);']
    turno = 0  # los bloques entran escalonados; la foto, de fondo, no cuenta en el escalonado
    for f in filas:
        grupo = f if isinstance(f, list) else [f]
        partes = []
        for b in grupo:
            h, j, f_ = bloque(b, k, 0.55 + paso * turno)
            fin = max(fin, f_)
            partes.append(h)
            js += j
            k += 1
            turno += b["tipo"] != "foto"
        html_panel.append(f'<div class="fila">{"".join(partes)}</div>' if isinstance(f, list) else partes[0])
    tt = min(fin + 0.15, 4.6)  # el texto de abajo entra cuando el panel ya contó lo suyo; luego laten sus acentos
    js += [f'tl.fromTo(".texto",{{opacity:0,y:36}},{{opacity:1,y:0,duration:0.45,ease:"back.out(1.8)"}},{tt:.2f});',
           f'tl.fromTo(".texto .ac",{{scale:0.7}},{{scale:1,duration:0.3,ease:"back.out(3)",stagger:0.18}},{tt + 0.25:.2f});',
           f'tl.to(["#panel",".texto",".pastilla"],{{opacity:0,duration:0.4}},{DUR - 0.5:.2f});']
    t = s["titulo"]
    cuerpo = (LOGO + f'<div class="ante">{n:02d} / {total:02d} — {html.escape(s["antetitulo"].upper())}</div>'
              f'<div class="titulo" style="font-size:{tam_titulo(t)}px">{html.escape(t)}</div>'
              f'<div class="pastilla"><b>›</b>{html.escape(s["pastilla"])}</div>'
              f'<div class="panel{" confoto" if confoto else ""}" id="panel">{"".join(html_panel)}</div>'
              f'<div class="texto">{acentos(s["texto"])}</div>'
              f'<div class="pie"><span class="fuente">{html.escape(s["fuente"])}</span>'
              + (f'<span class="aviso">{html.escape(s["aviso"])}</span>' if s.get("aviso") else "") + '</div>')
    return PAGE.format(W=W, H=H, titulo=html.escape(t), vars=colores(s.get("fondo", "amarillo")), css=CSS, clase="",
                       dur=DUR, cuerpo=cuerpo, js="\n".join(js))


def portada(c):
    p = c["portada"]
    n = len(c["diapositivas"])
    lista = "".join(f'<div><b>{k:02d}</b>{html.escape(s["titulo"])}</div>' for k, s in enumerate(c["diapositivas"], 1))
    # Con más de 6 piezas el índice pisaba el usuario: se apoya encima de él y encoge la letra.
    estilo = "" if n <= 6 else f' style="top:auto;bottom:170px;font-size:{34 if n <= 8 else 31}px;line-height:1.4"'
    cuerpo = (LOGO + '<img class="foto" src="assets/foto.png" style="right:-120px;bottom:0;height:640px">'
              f'<div class="ante">{html.escape(p.get("antetitulo", "").upper())}</div>'
              f'<div class="titulo">{acentos(p["titulo"])}</div><div class="lista"{estilo}>{lista}</div>'
              f'<div class="usuario">{html.escape(kit.usuario())}</div><div class="desliza">Desliza →</div>')
    # Un título largo con muchas piezas se montaba encima del índice: se encoge hasta dejar 30 px de aire.
    # Si ya cabe, no se toca: las portadas aprobadas salen igual. Se mide con Anton ya cargada: con la letra de reserva,
    # más ancha, encogía títulos que sí cabían.
    encaja = ('document.fonts.ready.then(()=>{const t=document.querySelector(".portada .titulo"),'
              'l=document.querySelector(".portada .lista");let f=parseFloat(getComputedStyle(t).fontSize);'
              'while(f>90&&t.getBoundingClientRect().bottom>l.getBoundingClientRect().top-30){f-=4;t.style.fontSize=f+"px";}});')
    return PAGE.format(W=W, H=H, titulo="Portada", vars=colores(p.get("fondo", "amarillo")), css=CSS, clase="portada",
                       dur=1.0, cuerpo=cuerpo, js=encaja)


def llamada(c):
    """Cierre de todos los carruseles: se escribe la palabra en un comentario, responde tu usuario
    y «Revisa tus mensajes». Solo palabras montadas (las de marca/marca.json → "palabras")."""
    cta = c.get("cta") or {}
    pal = cta.get("palabra") or kit.palabra_por_defecto()
    activas = kit.palabras()
    if not pal:
        raise SystemExit('cta: no tienes palabras de «Comenta» en marca/marca.json; usa "cta": false o un cierre sin '
                         'palabra ("cierre": {"tipo": "info" | "conversacion", …})')
    if pal.upper() not in activas:
        raise SystemExit(f"cta: «{pal}» no está montada en tus mensajes automáticos "
                         f"(solo {', '.join(sorted(activas)) or 'ninguna'}; ver marca/marca.json)")
    v = kit.marca()["palabras"].get(pal.upper())
    texto = (v.get("texto") if isinstance(v, dict) else None) or f"Comenta **{pal}** y te escribo por mensaje."
    k = {"palabra": pal, "titulo": f"Comenta **{pal}**", "texto": texto,
         "respuesta": "¡Te escribo por mensaje! 📩", **cta}
    # etiqueta del pie según la palabra (corta: a la derecha está la foto)
    k.setdefault("aviso", kit.aviso_palabra(pal))
    cuerpo = (LOGO + '<img class="foto" src="assets/foto.png" style="right:-140px;bottom:0;height:560px">'
              '<div class="ante">ÚLTIMO PASO</div>'
              f'<div class="titulo" style="font-size:{tam_titulo(k["titulo"].replace("*", ""))}px">{acentos(k["titulo"])}</div>'
              '<div class="comentario" id="km"><div class="yo">Tú</div><div class="campo2">'
              f'<span id="kmph">Añade un comentario…</span><b id="kmtx"></b></div><div class="publicar" id="kmpub">Publicar</div></div>'
              f'<div class="respuesta" id="kmr">{AVATAR}<div class="burbuja"><b>{html.escape(kit.usuario())}</b>'
              f'{html.escape(k["respuesta"])}</div></div>'
              '<div class="revisa" id="kmrev">📩 Revisa tus mensajes</div>'
              f'<div class="texto">{acentos(k["texto"])}</div>'
              f'<div class="pie"><span class="fuente">{FIRMA}</span><span class="aviso">{html.escape(k["aviso"])}</span></div>')
    js = [f'tl.fromTo("#km",{{opacity:0,y:40}},{{opacity:1,y:0,duration:0.35,ease:"back.out(2)"}},0.3);',
          'tl.set("#kmph",{opacity:0},0.9);',
          f'const okm={{n:0}};tl.to(okm,{{n:{len(pal)},duration:0.8,ease:"none",onUpdate:()=>'
          f'{{document.getElementById("kmtx").textContent={json.dumps(pal)}.slice(0,Math.round(okm.n))}}}},0.9);',
          'tl.to("#kmpub",{color:"#0095f6",duration:0.15},1.8);',
          'tl.fromTo("#kmpub",{scale:1},{scale:1.15,duration:0.12,yoyo:true,repeat:1},2.1);',
          'tl.fromTo("#kmr",{opacity:0,y:30},{opacity:1,y:0,duration:0.4,ease:"back.out(1.8)"},2.6);',
          'tl.fromTo("#kmrev",{opacity:0,scale:0.6},{opacity:1,scale:1,duration:0.35,ease:"back.out(2.5)"},3.4);',
          'tl.fromTo("#kmrev",{scale:1},{scale:1.06,duration:0.4,yoyo:true,repeat:3,ease:"sine.inOut"},4.0);',
          f'tl.to(["#km","#kmr","#kmrev"],{{opacity:0,duration:0.4}},{DUR - 0.5:.2f});']
    return PAGE.format(W=W, H=H, titulo="Llamada", vars=colores(k.get("fondo", "negro")), css=CSS, clase="cta",
                       dur=DUR, cuerpo=cuerpo, js="\n".join(js))


def cierre_pregunta(c):
    """El cierre sin palabra del carrusel ("cierre": {"tipo": "info" | "conversacion", "pregunta": …}), o None.
    Los cierres con palabra siguen en "cta" (la pieza «Comenta»)."""
    from cierre import de_receta
    k = de_receta({"cierre": c["cierre"]}) if c.get("cierre") else None
    if k and k["palabra"]:
        raise SystemExit('cierre: en el carrusel, los cierres con palabra van en "cta" (la pieza «Comenta»)')
    return k


def pregunta(k):
    """Cierre sin palabra (cierres que rotan; `scripts/cierre.py`): «Tu turno», la pregunta y la pastilla
    de cierre.py. Con "info", alguien pide información en un comentario y responde tu usuario."""
    info = k["tipo"] == "info"
    p = k["pregunta"]
    cuerpo = (LOGO + '<img class="foto" src="assets/foto.png" style="right:-140px;bottom:0;height:560px">'
              '<div class="ante">TU TURNO</div>'
              f'<div class="titulo" style="font-size:{84 if len(p) <= 50 else 66}px">{acentos(p)}</div>')
    js = []
    if info:
        com = k.get("comentario", "Quiero información")
        cuerpo += ('<div class="comentario" id="km"><div class="yo">Tú</div><div class="campo2">'
                   f'<span id="kmph">Añade un comentario…</span><b id="kmtx"></b></div><div class="publicar" id="kmpub">Publicar</div></div>'
                   f'<div class="respuesta" id="kmr">{AVATAR}<div class="burbuja"><b>{html.escape(kit.usuario())}</b>'
                   '¡Te escribo por mensaje! 📩</div></div>')
        js += [f'tl.fromTo("#km",{{opacity:0,y:40}},{{opacity:1,y:0,duration:0.35,ease:"back.out(2)"}},0.3);',
               'tl.set("#kmph",{opacity:0},0.9);',
               f'const okm={{n:0}};tl.to(okm,{{n:{len(com)},duration:0.9,ease:"none",onUpdate:()=>'
               f'{{document.getElementById("kmtx").textContent={json.dumps(com)}.slice(0,Math.round(okm.n))}}}},0.9);',
               'tl.to("#kmpub",{color:"#0095f6",duration:0.15},1.9);',
               'tl.fromTo("#kmpub",{scale:1},{scale:1.15,duration:0.12,yoyo:true,repeat:1},2.2);',
               'tl.fromTo("#kmr",{opacity:0,y:30},{opacity:1,y:0,duration:0.4,ease:"back.out(1.8)"},2.7);']
    t_pie = 3.5 if info else 0.6
    estilo = "" if info else ' style="top:500px"'
    texto = acentos("Te leo en los **comentarios**. Si quieres **información**, dímelo ahí.") if info else ""
    cuerpo += (f'<div class="revisa" id="kmrev"{estilo}>{html.escape(k["pie"])}</div>'
               + (f'<div class="texto">{texto}</div>' if texto else "")
               + f'<div class="pie"><span class="fuente">{FIRMA}</span>'
               f'<span class="aviso">{"Te escribo por mensaje" if info else "Te leo"}</span></div>')
    salen = json.dumps(["#kmrev", "#km", "#kmr"] if info else ["#kmrev"])
    js += [f'tl.fromTo("#kmrev",{{opacity:0,scale:0.6}},{{opacity:1,scale:1,duration:0.35,ease:"back.out(2.5)"}},{t_pie});',
           f'tl.fromTo("#kmrev",{{scale:1}},{{scale:1.06,duration:0.4,yoyo:true,repeat:3,ease:"sine.inOut"}},{t_pie + 0.6});',
           f'tl.to({salen},{{opacity:0,duration:0.4}},{DUR - 0.5:.2f});']
    return PAGE.format(W=W, H=H, titulo="Tu turno", vars=colores(k.get("fondo", "negro")), css=CSS, clase="cta turno",
                       dur=DUR, cuerpo=cuerpo, js="\n".join(js))


HISTORIA_H, HISTORIA_MARGEN = 1920, 240


def a_historias(page):
    """La misma pieza para historias de Instagram: lienzo 9:16 de 1080×1920 con el diseño de
    1080×1440 en el centro. Los 240 px de arriba y abajo quedan libres para la barra del perfil y la caja de
    «Enviar mensaje», y se rellenan con el color de la pieza. En historias no hay comentarios: el cierre pasa a
    «Respóndeme» y «Desliza» a «Toca»."""
    page = page.replace("html, body { width: 1080px; height: 1440px;", f"html, body {{ width: 1080px; height: {HISTORIA_H}px;")
    page = page.replace("#root { position: relative; width: 1080px; height: 1440px;",
                        f"#root {{ position: relative; width: 1080px; height: {HISTORIA_H}px;")
    page = page.replace(f'content="width={W}, height={H}"', f'content="width={W}, height={HISTORIA_H}"')
    page = page.replace(f'data-height="{H}"', f'data-height="{HISTORIA_H}"')
    page = re.sub(r'(<div id="root"[^>]*>)', rf'\1<div id="lienzo" style="position:absolute;left:0;top:{HISTORIA_MARGEN}px;'
                  rf'width:{W}px;height:{H}px">', page, count=1)
    page = page.replace("\n</div><script>", "\n</div></div><script>", 1)
    # tu foto de la portada y del cierre llega hasta el borde de abajo de la pantalla (si no, se corta en el aire)
    page = re.sub(r'<img class="foto" src="assets/foto.png" style="right:(-?\d+)px;bottom:0;height:(\d+)px">',
                  lambda m: (f'<img class="foto" src="assets/foto.png" style="right:{int(m[1]) - 60}px;'
                             f'bottom:-{HISTORIA_MARGEN}px;height:{int(m[2]) + HISTORIA_MARGEN}px">'), page)
    page = page.replace(">Desliza →<", ">Toca →<")
    # cierre «Tu turno»: la respuesta llega por mensaje, no en un comentario
    page = page.replace("Añade un comentario…", f"Responder a {html.escape(kit.usuario(False))}…").replace(">Publicar<", ">Enviar<")
    page = re.sub(r"Te leo en los .*?dímelo ahí\.", 'Respóndeme a esta <span class="ac">historia</span> y te escribo '
                  'por <span class="ac">mensaje</span>.', page)
    page = page.replace("DÍMELO AHÍ", "RESPÓNDEME").replace("TE LEO EN LOS COMENTARIOS 👇", "RESPÓNDEME POR AQUÍ 📩")
    return page


def opcionales(paleta, foto):
    """Logo, foto y avatar de marca/: la ruta de cada uno si existe, o None (no vienen con el kit)."""
    rutas = {"logo": ROOT / "marca/logos" / PALETAS[paleta]["logo"],
             "foto": ROOT / "marca/fotos" / foto if foto else None,
             "avatar": ROOT / "marca/tarjetas/avatar-youtube.jpg"}
    return {k: (p if p and p.exists() else None) for k, p in rutas.items()}


def preparar_dir(d, extras):
    (d / "assets").mkdir(parents=True, exist_ok=True)
    plantilla = ROOT / "subtitulos"  # la composición base del kit: config de HyperFrames y GSAP
    for f in ["hyperframes.json", "package.json"]:
        shutil.copy2(plantilla / f, d / f)
    (d / "meta.json").write_text(json.dumps({"id": d.name, "name": d.name}, indent=2))
    shutil.copy2(plantilla / "assets/gsap.min.js", d / "assets/gsap.min.js")
    shutil.copy2(ROOT / "marca/fuentes/Anton-Regular.ttf", d / "assets/Anton-Regular.ttf")
    shutil.copy2(ROOT / "marca/fuentes/Oswald-Variable.ttf", d / "assets/Oswald-Variable.ttf")
    for k, dst in (("logo", "logo.png"), ("foto", "foto.png"), ("avatar", "avatar.jpg")):
        if extras[k]:
            shutil.copy2(extras[k], d / "assets" / dst)


def hf(args, cwd):
    env = {**__import__("os").environ, "HYPERFRAMES_SKIP_SKILLS": "1"}
    env.pop("GEMINI_API_KEY", None)
    r = subprocess.run(HF + args, cwd=cwd, env=env, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"hyperframes {args[0]} falló en {cwd.name}:\n{r.stdout[-1500:]}{r.stderr[-1500:]}")
    return r.stdout


def entregar(c, base, out, historias=False):
    """Lo renderizado en out/ a la carpeta de entregas, con el tema y la letra de variante; una fila en el registro.
    Las historias van como otra variante («B historias») en la misma carpeta del tema."""
    import datetime
    import os
    from terminados import destino, registrar
    if os.environ.get("ENTREGA_APROBADA") != "1":
        sys.exit("entregar: solo con el visto bueno del creador (ENTREGA_APROBADA=1 delante)")
    piezas = sorted(out.glob("[0-9][0-9]*.mp4")) + [out / "pie.txt"]
    piezas = [out / "00_portada.png"] + [p for p in piezas if not p.name.endswith("_hoja.png")]
    falta = [p.name for p in piezas if not p.exists()]
    if falta:
        sys.exit(f"entregar: falta renderizar {falta}")
    clave = "letra_historias" if historias else "letra"
    cfg = {"tema": c["tema"], "variante": "historias" if historias else "carrusel", "letra": c.get(clave)}
    dst = destino(cfg, base / "carrusel.json")  # …/<fecha tema>/<fecha tema> - A carrusel.mp4
    if historias:  # en su propia carpeta, «<fecha tema> - historias», con la letra siguiente
        propia = dst.parent.with_name(f"{dst.parent.name} - historias")
        propia.mkdir(exist_ok=True)
        if not any(dst.parent.iterdir()):
            dst.parent.rmdir()
        dst = propia / dst.name
    raiz = dst.with_suffix("").name
    for p in piezas:
        nombre = {"00_portada.png": "00 portada.png", "pie.txt": "pie.txt"}.get(p.name, p.name)
        shutil.copy2(p, dst.parent / f"{raiz} - {nombre}")
    registrar(dst.with_name(f"{raiz} ({len(piezas) - 1} piezas + pie)"), f"carrusel {base.name}", base / "carrusel.json")
    if not c.get(clave):
        letra = raiz.split(" - ")[1][0]
        c2 = ({"tema": c["tema"], "letra": letra, **{k: v for k, v in c.items() if k != "tema"}} if not historias
              else {**c, "letra_historias": letra})
        (base / "carrusel.json").write_text(json.dumps(c2, ensure_ascii=False, indent=2) + "\n")
    print(f"entregado: {dst.parent.name}/{raiz} - 00…{len(piezas) - 2:02d} + pie ({datetime.date.today()})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("nombre")
    ap.add_argument("--solo", help="número de diapositiva (00 = portada)")
    ap.add_argument("--hoja", action="store_true", help="hoja de fotogramas de cada diapositiva para revisar")
    ap.add_argument("--paleta", choices=sorted(PALETAS), help="probar otra paleta (sale en out/carrusel_<nombre>_<paleta>/)")
    ap.add_argument("--entregar", action="store_true", help="entrega lo ya renderizado (necesita ENTREGA_APROBADA=1)")
    ap.add_argument("--historias", action="store_true",
                    help="las mismas piezas en 9:16 (1080×1920) para historias → out/carrusel_<nombre>_historias/")
    a = ap.parse_args()
    base = ROOT / "carruseles" / a.nombre
    c = json.loads((base / "carrusel.json").read_text())
    paleta = a.paleta or c.get("paleta", "marca")
    sufijo = (f"_{a.paleta}" if a.paleta else "") + ("_historias" if a.historias else "")
    out = ROOT / "out" / f"carrusel_{a.nombre}{sufijo}"
    if a.historias and c.get("cta") is not False and not c.get("cierre"):
        sys.exit("historias: en las historias no hay comentarios, así que «Comenta PALABRA» no funciona. "
                 'Usa un cierre sin palabra ("cierre": {"tipo": "info" | "conversacion", …}) o "cta": false.')
    total = len(c["diapositivas"])
    turno = cierre_pregunta(c)
    diapos = 1 + total + (turno is not None or c.get("cta") is not False)
    if diapos > 10:
        sys.exit(f"{a.nombre}: {diapos} diapositivas con portada y cierre; 10 como mucho (Instagram admite 20, "
                 "pero pasadas 10 casi nadie llega al final)")
    out.mkdir(parents=True, exist_ok=True)
    if a.entregar:
        return entregar(c, base, out, a.historias)
    trabajos = [("00", portada(c))] + [(f"{n:02d}", diapositiva(s, n, total)) for n, s in enumerate(c["diapositivas"], 1)]
    if turno:
        trabajos.append((f"{total + 1:02d}", pregunta(turno)))
    elif c.get("cta") is not False:
        trabajos.append((f"{total + 1:02d}", llamada(c)))
    foto = c.get("foto") or FOTO_POR_DEFECTO
    extras = opcionales(paleta, foto)
    if not extras["logo"] and c.get("logo") is not False:
        print(f"aviso: no está marca/logos/{PALETAS[paleta]['logo']}: las piezas salen sin logo")
    if not extras["foto"] and c.get("foto") is not False:
        print(f"aviso: no está marca/fotos/{foto}: las piezas salen sin tu foto")
    for num, page in trabajos:
        if a.solo and num != a.solo:
            continue
        d = base / "build" / (f"h{num}" if a.historias else num)
        preparar_dir(d, extras)
        if (base / "fotos").is_dir():  # fotos de apoyo del bloque "foto" (fuera de git; créditos en fotos/fuentes.json)
            shutil.copytree(base / "fotos", d / "assets/fotos", dirs_exist_ok=True)
        for viejo, nuevo in PALETAS[paleta]["cambios"].items():
            page = page.replace(viejo, nuevo)
        # Noticias delicadas: "logo": false quita el logo y "foto": false la foto, para que el carrusel no parezca
        # publicidad. Sin el archivo en marca/, también se quitan.
        if c.get("logo") is False or not extras["logo"]:
            page = page.replace(LOGO, "")
        if c.get("foto") is False or not extras["foto"]:
            page = re.sub(r'<img class="foto"[^>]*>', "", page)
        if not extras["avatar"]:
            page = page.replace(AVATAR, SIN_AVATAR)
        page = page.replace(FIRMA, html.escape(firma(c)))
        if a.historias:
            page = a_historias(page)
        (d / "index.html").write_text(kit.pinta(page))
        lint = hf(["lint"], d)
        if re.search(r"[1-9]\d* error\(s\)", lint):
            sys.exit(f"{num}: lint con errores\n{lint[-1500:]}")
        if num == "00":
            hf(["snapshot", "--at", "0.5", "--no-end"], d)
            shutil.copy2(next((d / "snapshots").glob("frame-*.png")), out / "00_portada.png")
            print(f"00: portada → {out / '00_portada.png'}")
            continue
        dest = out / f"{num}.mp4"
        hf(["render", "-o", str(dest), "--quiet"], d)
        print(f"{num}: {c['diapositivas'][int(num) - 1]['titulo'] if int(num) <= total else 'Cierre'} → {dest}")
        if a.hoja:
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(dest), "-vf",
                            "fps=1,scale=360:-1,tile=7x1", "-frames:v", "1", str(out / f"{num}_hoja.png")])
    if a.historias:  # las historias no llevan caption: el pie dice cómo subirlas
        ult = f"{len(trabajos) - 1:02d}"
        resumen = f"{total:02d}" if total >= 2 else ult
        (out / "pie.txt").write_text(
            f"Historias de «{c['tema']}» (9:16). No llevan caption.\n\n"
            f"- Todas, de la 00 a la {ult}, en orden: valen también para una destacada fija.\n"
            f"- Para el día, una tanda corta: 00 (portada), {resumen} y {ult} (el cierre).\n"
            "- Etiqueta con su @ a las marcas que salgan (el logo ya está en cada pieza).\n"
            "- La 00 es una imagen: en Instagram, déjala 5-7 s.\n"
            "- En el cierre, si quieres, añade un sticker de pregunta o de encuesta en la franja de abajo.\n\n"
            "Fuentes y créditos de las fotos: los mismos que el carrusel (pie del carrusel).\n")
    else:
        (out / "pie.txt").write_text(c["pie"].strip() + "\n")
    print(f"pie → {out / 'pie.txt'}")


if __name__ == "__main__":
    main()
