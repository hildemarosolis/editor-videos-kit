#!/usr/bin/env python3
"""«Ruta en un mapa»: de un JSON de paradas a un vídeo 1080×1920 sin cara.

Arriba, la foto de cada parada con su etiqueta y sus chips; abajo, un mapa oscuro donde la ruta
se dibuja justo cuando la voz nombra cada parada. Dos mapas: «mundo» (Natural Earth, Mercator)
y «madrid» (teselas de OpenStreetMap montadas en assets/madrid.png, ver madrid_vista.json).

  python3 scripts/ruta.py proyectos/_rutas/RUTA_BOG_MAD.json            compone proyectos/_rutas/<NOMBRE>/
  python3 scripts/ruta.py proyectos/_rutas/RUTA_BOG_MAD.json --render   y además renderiza raw/<NOMBRE>.mp4

Después, el camino de siempre: preparar.py <NOMBRE> --sin-silencios → receta (subtítulos, tarjetas
de datos, logo, «Comenta», «Sígueme») → entregar.py --muestra. Las paradas se anclan a frases.
Las fotos solo con licencia libre (Wikimedia Commons), con autor y licencia en creditos.json: salen en pantalla.
El mapa «mundo» está encuadrado para un viaje de América a España (destino "MAD"); otros destinos piden
ajustar S, LON0 y MAD_Y."""
import argparse
import html
import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kit  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
W, H, PH = 1080, 1920, 800          # PH: alto de la foto; el mapa ocupa de y=800 al final
MH = H - PH
AMA, TINTA, MAR, TIERRA, BORDE, RESALTE = "#FFC800", "#0B1118", "#0E1620", "#1E2A37", "#2D3C4D", "#33506B"
COLA = 2.0                          # segundos tras la voz: la caja «Comenta» y «Sígueme» tienen sitio
# Mercator del mapa «mundo»: px por radián y dónde cae Madrid (en coordenadas de la página)
S, LON0, MAD_Y = 595.0, -90.5, 1130.0


def norm(s):
    return re.sub(r"[^\wáéíóúüñ]", "", s.lower())


def cargar_palabras(path):
    d = json.loads(Path(path).read_text())["transcription"]
    out = []
    for s in d:
        t = s["text"].strip()
        if t:
            out.append({"w": t, "n": norm(t), "t0": s["offsets"]["from"] / 1000, "t1": s["offsets"]["to"] / 1000})
    return out


def anclador(words):
    seq = [w["n"] for w in words]

    def at(frase, after=0.0):
        f = [norm(x) for x in frase.split() if norm(x)]
        for i in range(len(seq) - len(f) + 1):
            if words[i]["t0"] >= after - 0.01 and seq[i:i + len(f)] == f:
                return words[i]["t0"]
        sys.exit(f"ruta: no encuentro «{frase}» después de {after:.2f}s en la transcripción")
    return at


# ---------- mapa «mundo» ----------
def merc(lat):
    return math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


def mundo_xy(lat, lon):
    """Coordenadas dentro del panel del mapa (0..1080 × 0..1120)."""
    x = (math.radians(lon) - math.radians(LON0)) * S
    y = MAD_Y - (merc(lat) - merc(40.4719)) * S - PH
    return x, y


def paises_svg(topo_path, resaltar=("170", "724")):
    topo = json.loads(Path(topo_path).read_text())
    sc, tr = topo["transform"]["scale"], topo["transform"]["translate"]
    arcs = []
    for a in topo["arcs"]:
        x = y = 0
        pts = []
        for dx, dy in a:
            x += dx
            y += dy
            pts.append((x * sc[0] + tr[0], y * sc[1] + tr[1]))
        arcs.append(pts)

    def anillo(idx):
        pts = []
        for i in idx:
            a = arcs[i] if i >= 0 else arcs[~i][::-1]
            pts += a if not pts else a[1:]
        return pts

    normales, resaltados = [], []
    for g in topo["objects"]["countries"]["geometries"]:
        polys = g["arcs"] if g["type"] == "MultiPolygon" else [g["arcs"]] if g["type"] == "Polygon" else []
        d = []
        for poly in polys:
            for r in poly:
                pts = anillo(r)
                if not any(-110 < lon < 40 and -45 < lat < 72 for lon, lat in pts):
                    continue
                seg, last = [], None
                for lon, lat in pts:
                    lat = max(-80, min(80, lat))
                    x, y = mundo_xy(lat, lon)
                    if last and abs(x - last[0]) + abs(y - last[1]) < 1.6:
                        continue
                    seg.append(f"{x:.1f},{y:.1f}")
                    last = (x, y)
                if len(seg) > 2:
                    d.append("M" + "L".join(seg) + "Z")
        if d:
            (resaltados if g.get("id") in resaltar else normales).append("".join(d))
    return normales, resaltados


def gran_circulo(a, b, n=48):
    def v(lat, lon):
        la, lo = math.radians(lat), math.radians(lon)
        return (math.cos(la) * math.cos(lo), math.cos(la) * math.sin(lo), math.sin(la))
    p, q = v(*a), v(*b)
    om = math.acos(sum(x * y for x, y in zip(p, q)))
    pts = []
    for i in range(n + 1):
        t = i / n
        k1, k2 = math.sin((1 - t) * om) / math.sin(om), math.sin(t * om) / math.sin(om)
        x, y, z = (k1 * p[j] + k2 * q[j] for j in range(3))
        pts.append((math.degrees(math.atan2(z, math.hypot(x, y))), math.degrees(math.atan2(y, x))))
    return pts


def largo(pts):
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


# ---------- mapa «madrid» (OSM) ----------
def madrid_xy(lat, lon, vista):
    n = 2 ** vista["z"] * 256
    x = (lon + 180) / 360 * n
    y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
    return (x - vista["x0"]) * vista["escala"], (y - vista["y0"]) * vista["escala"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ruta")
    ap.add_argument("--render", action="store_true")
    a = ap.parse_args()
    cfg = json.loads(Path(a.ruta).read_text())
    nombre = cfg["nombre"]
    D = Path(a.ruta).with_suffix("")
    words = cargar_palabras(ROOT / cfg["palabras"])
    at = anclador(words)
    voz = ROOT / cfg["voz"]
    dur_voz = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                    "default=nw=1:nk=1", str(voz)], capture_output=True, text=True).stdout)
    TOTAL = round(dur_voz + COLA, 2)
    cred = json.loads((D / "creditos.json").read_text())
    vista = json.loads((D / "madrid_vista.json").read_text())
    P = cfg["puntos"]
    nombres = cfg.get("nombres", {})

    # tiempos de cada parada
    paradas = cfg["paradas"]
    t_par, prev = [], 0.0
    for p in paradas:
        prev = at(p["frase"], prev)
        t_par.append(prev)
    fin = t_par[1:] + [TOTAL]

    h, js, sfx = [], [], []

    # ---- mapas ----
    normales, resaltados = paises_svg(D / "assets/countries-50m.json")
    mundo = [f'<path d="{d}" class="pais"/>' for d in normales] + [f'<path d="{d}" class="pais res"/>' for d in resaltados]
    mx, my = mundo_xy(*P["MAD"])
    marcas_m, marcas_md, trazos_m, trazos_md = [], [], [], []

    def marca(id_, x, y, texto, lado="der"):
        dx = 26 if lado == "der" else -26
        anchor = "start" if lado == "der" else "end"
        return (f'<g id="{id_}" opacity="0"><circle cx="{x:.1f}" cy="{y:.1f}" r="34" class="pulso" id="{id_}p"/>'
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="13" class="punto"/>'
                f'<text x="{x + dx:.1f}" y="{y + 12:.1f}" text-anchor="{anchor}" class="nom">{html.escape(texto)}</text></g>')

    for k, p in enumerate(paradas):
        t0 = t_par[k]
        if p.get("marca"):
            pid = p["marca"]
            mid = f"mk{k}"
            if p["mapa"] == "mundo":
                x, y = mundo_xy(*P[pid])
                marcas_m.append(marca(mid, x, y, nombres.get(pid, pid)))
            else:
                x, y = madrid_xy(*P[pid], vista)
                marcas_md.append(marca(mid, x, y, nombres.get(pid, pid), "izq" if x > 700 else "der"))
            js.append(f'tl.fromTo("#{mid}",{{opacity:0,scale:.3,transformOrigin:"{x:.0f}px {y:.0f}px"}},'
                      f'{{opacity:1,scale:1,duration:.5,ease:"back.out(2.5)"}},{t0 + .25:.3f});')
            js.append(f'tl.fromTo("#{mid}p",{{attr:{{r:14}},opacity:.9}},{{attr:{{r:60}},opacity:0,duration:1.1,'
                      f'repeat:{max(0, int((fin[k] - t0) / 1.1) - 1)},ease:"power1.out"}},{t0 + .3:.3f});')
        if p.get("vuelo"):
            v = p["vuelo"]
            pts = [mundo_xy(*q) for q in gran_circulo(P[v["de"]], P[v["a"]])]
            L = largo(pts)
            d = "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
            trazos_m.append(f'<path id="arco" d="{d}" class="arco" style="stroke-dasharray:{L:.0f};stroke-dashoffset:{L:.0f}"/>'
                            f'<circle id="avion" r="16" cx="{pts[0][0]:.1f}" cy="{pts[0][1]:.1f}" class="avion" opacity="0"/>')
            tv = at(v["desde_frase"], t0) if v.get("desde_frase") else t0 + .3
            js.append(f'tl.set("#arco",{{opacity:1}},{tv:.3f});')  # el extremo redondo se vería antes de dibujarse
            js.append(f'tl.to("#arco",{{strokeDashoffset:0,duration:{v["dur"]},ease:"power1.inOut"}},{tv:.3f});')
            js.append(f'tl.set("#avion",{{opacity:1}},{tv:.3f});')
            pasos = 24
            for i in range(1, pasos + 1):
                # el punto recorre el arco con la misma curva que el trazo (aprox. por tramos)
                f = (1 - math.cos(math.pi * i / pasos)) / 2
                x, y = pts[min(len(pts) - 1, round(f * (len(pts) - 1)))]
                js.append(f'tl.to("#avion",{{attr:{{cx:{x:.1f},cy:{y:.1f}}},duration:{v["dur"] / pasos:.3f},ease:"none"}},'
                          f'{tv + v["dur"] * (i - 1) / pasos:.3f});')
            js.append(f'tl.to("#avion",{{opacity:0,duration:.3}},{tv + v["dur"] + .1:.3f});')
            mid = "mkdest"
            marcas_m.append(marca(mid, mx, my, nombres.get(v["a"], v["a"]), "izq"))
            js.append(f'tl.fromTo("#{mid}",{{opacity:0,scale:.3,transformOrigin:"{mx:.0f}px {my:.0f}px"}},'
                      f'{{opacity:1,scale:1,duration:.5,ease:"back.out(2.5)"}},{tv + v["dur"] - .1:.3f});')
            sfx.append((tv, "whoosh"))
        if p.get("linea"):
            li = p["linea"]
            tl0 = t0 + .4
            for tramo, cls, dur, color in [(li["puntos"], "lin", li["dur"], li["color"]),
                                           (li.get("sigue", {}).get("puntos"), "sig", li.get("sigue", {}).get("dur", 1), "#FFFFFF")]:
                if not tramo:
                    continue
                pts = [madrid_xy(*P[q], vista) for q in tramo]
                L = largo(pts)
                d = "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
                lid = f"{cls}{k}"
                trazos_md.append(f'<path id="{lid}" d="{d}" class="{cls}" style="stroke:{color};stroke-dasharray:{L:.0f};'
                                 f'stroke-dashoffset:{L:.0f}"/>')
                for j, (x, y) in enumerate(pts):
                    if 0 < j < len(pts) - 1 or cls == "lin":
                        trazos_md.append(f'<circle id="{lid}e{j}" cx="{x:.1f}" cy="{y:.1f}" r="7" class="est" opacity="0"/>')
                        js.append(f'tl.to("#{lid}e{j}",{{opacity:1,duration:.15}},{tl0 + dur * j / max(1, len(pts) - 1):.3f});')
                js.append(f'tl.set("#{lid}",{{opacity:1}},{tl0:.3f});')
                js.append(f'tl.to("#{lid}",{{strokeDashoffset:0,duration:{dur},ease:"power1.inOut"}},{tl0:.3f});')
                if cls == "lin":
                    x, y = pts[len(pts) // 2]
                    trazos_md.append(f'<g id="{lid}t" opacity="0"><rect x="{x + 18:.0f}" y="{y - 64:.0f}" width="96" height="56" rx="14" '
                                     f'style="fill:{color}"/><text x="{x + 66:.0f}" y="{y - 22:.0f}" class="ltxt">{li["nombre"]}</text></g>')
                    js.append(f'tl.fromTo("#{lid}t",{{opacity:0,y:10}},{{opacity:1,y:0,duration:.35,ease:"back.out(2)"}},{tl0 + .3:.3f});')
                tl0 += dur

    h.append(f'''<div id="mapas">
  <svg id="mundo" viewBox="0 0 {W} {MH}" width="{W}" height="{MH}">
    <rect width="{W}" height="{MH}" fill="{MAR}"/>
    <g id="mundog">{"".join(mundo)}{"".join(trazos_m)}{"".join(marcas_m)}</g>
  </svg>
  <div id="madrid"><img src="assets/madrid.png"/>
    <svg viewBox="0 0 {W} {MH}" width="{W}" height="{MH}">{"".join(trazos_md)}{"".join(marcas_md)}</svg></div>
  <div class="atrib" id="atm">Mapa: Natural Earth</div>
  <div class="atrib" id="atd" style="opacity:0">© OpenStreetMap</div>
  <div id="sombra"></div>
</div>''')

    # qué mapa se ve en cada parada (y el cambio con zoom hacia el punto)
    mapa_actual = "mundo"
    js.append(f'tl.to("#mundog",{{scale:1.035,transformOrigin:"{mx:.0f}px {my:.0f}px",duration:{TOTAL},ease:"none"}},0);')
    for k, p in enumerate(paradas):
        t0 = t_par[k]
        if p["mapa"] != mapa_actual:
            bx, by = madrid_xy(*P[paradas[k].get("marca") or "T4"], vista) if p["mapa"] == "madrid" else (mx, my)
            if p["mapa"] == "madrid":
                js.append(f'tl.to("#mundo",{{scale:6,opacity:0,transformOrigin:"{mx:.0f}px {my:.0f}px",duration:.8,ease:"power2.in"}},{t0:.3f});')
                js.append(f'tl.fromTo("#madrid",{{opacity:0,scale:1.6,transformOrigin:"{bx:.0f}px {by:.0f}px"}},'
                          f'{{opacity:1,scale:1,duration:.9,ease:"power3.out"}},{t0 + .45:.3f});')
                js.append(f'tl.to("#madrid img",{{scale:1.05,transformOrigin:"50% 40%",duration:{fin[k] - t0 + 30},ease:"none"}},{t0 + .5:.3f});')
                js.append(f'tl.to("#atm",{{opacity:0,duration:.3}},{t0:.3f});tl.to("#atd",{{opacity:1,duration:.3}},{t0 + .6:.3f});')
            else:
                js.append(f'tl.to("#madrid",{{opacity:0,scale:.7,duration:.6,ease:"power2.in"}},{t0:.3f});')
                # immediateRender:false: si no, GSAP deja el mundo invisible desde el segundo 0
                js.append(f'tl.fromTo("#mundo",{{scale:6,opacity:0}},{{scale:1,opacity:1,transformOrigin:"{mx:.0f}px {my:.0f}px",'
                          f'duration:1.0,ease:"power3.out",immediateRender:false}},{t0 + .3:.3f});')
                js.append(f'tl.to("#atd",{{opacity:0,duration:.3}},{t0:.3f});tl.to("#atm",{{opacity:1,duration:.3}},{t0 + .6:.3f});')
            mapa_actual = p["mapa"]

    # ---- fotos de arriba, etiquetas y chips ----
    def foto_div(fid, foto, t0, t1, z=1):
        c = cred[foto]
        lic = f'Foto: {html.escape(c["autor"])} · {html.escape(c["licencia"])} · Wikimedia Commons'
        h.append(f'<div class="clip foto" id="{fid}" data-start="{t0:.3f}" data-duration="{t1 - t0:.3f}" data-track-index="{2 + z}">'
                 f'<div class="img" style="background-image:url(assets/fotos/{foto}.jpg)"></div>'
                 f'<div class="cred">{lic}</div></div>')
        js.append(f'tl.fromTo("#{fid}",{{opacity:0,x:90}},{{opacity:1,x:0,duration:.45,ease:"power3.out"}},{t0:.3f});')
        js.append(f'tl.fromTo("#{fid} .img",{{scale:1.0}},{{scale:1.09,duration:{t1 - t0:.3f},ease:"none"}},{t0:.3f});')

    for k, p in enumerate(paradas):
        t0, t1 = t_par[k], fin[k]
        if p.get("foto2"):
            t2 = at(p["foto2"]["frase"], t0)
            foto_div(f"f{k}", p["foto"], t0, t2 + .5)
            foto_div(f"f{k}b", p["foto2"]["foto"], t2, t1 + .5, z=2)
        else:
            foto_div(f"f{k}", p["foto"], t0, t1 + .5, z=1 + k % 2)
        if p.get("etiqueta"):  # sin etiqueta en el cierre: arriba salen el logo y «Sígueme»
            h.append(f'<div class="clip etq" id="e{k}" data-start="{t0:.3f}" data-duration="{t1 - t0:.3f}" data-track-index="8">'
                     f'<span>{html.escape(p["etiqueta"])}</span></div>')
            js.append(f'tl.fromTo("#e{k}",{{opacity:0,x:-60}},{{opacity:1,x:0,duration:.4,ease:"back.out(2)"}},{t0 + .15:.3f});')
        sfx.append((t0, "whoosh"))
        for j, c in enumerate(p.get("chips", [])):
            tc = at(c["frase"], t0)
            cid = f"c{k}_{j}"
            cls = "chip aviso" if c.get("aviso") else "chip"
            top = 560 + j * 98 if len(p["chips"]) > 1 else 658
            h.append(f'<div class="clip {cls}" id="{cid}" data-start="{tc:.3f}" data-duration="{t1 - tc:.3f}" data-track-index="9" '
                     f'style="top:{top}px"><span>{html.escape(c["texto"])}</span></div>')
            js.append(f'tl.fromTo("#{cid}",{{opacity:0,scale:.6,x:-40}},{{opacity:1,scale:1,x:0,duration:.38,ease:"back.out(2.2)"}},{tc:.3f});')
            sfx.append((tc, "tic" if c["texto"].startswith("✓") else "pop"))

    # ---- portada ----
    po = cfg["portada"]
    t_fin_portada = t_par[0]
    lineas = "".join(f'<div class="tl{i}">{" ".join(f"<span class=pw>{html.escape(w)}</span>" for w in linea.split())}</div>'
                     for i, linea in enumerate(po["titular"]))
    tchip = at(po["chip"]["frase"])
    h.append(f'''<div class="clip" id="portada" data-start="0" data-duration="{t_fin_portada + .6:.3f}" data-track-index="10">
  <div class="img" style="background-image:url(assets/fotos/{po["foto"]}.jpg)"></div><div class="velo"></div>
  <svg class="pruta" viewBox="0 0 {W} {H}"><path id="pruta" d="M-40,1700 C260,1460 520,1500 700,1180 S960,820 1120,700"
    style="stroke-dasharray:1500;stroke-dashoffset:1500"/></svg>
  <div class="ptit">{lineas}</div>
  <div class="pchip" id="pchip"><span>{html.escape(po["chip"]["texto"])}</span></div>
  <div class="cred">Foto: {html.escape(cred[po["foto"]]["autor"])} · {html.escape(cred[po["foto"]]["licencia"])} · Wikimedia Commons</div>
</div>''')
    js.append('tl.fromTo("#portada .img",{scale:1.12},{scale:1,duration:%.2f,ease:"power1.out"},0);' % (t_fin_portada + .6))
    js.append('tl.fromTo(".pw",{opacity:0,y:70,scale:.8},{opacity:1,y:0,scale:1,duration:.45,stagger:.12,ease:"back.out(2.2)"},.05);')
    js.append('tl.to("#pruta",{strokeDashoffset:0,duration:1.6,ease:"power2.inOut"},.3);')
    js.append(f'tl.fromTo("#pchip",{{opacity:0,scale:.5}},{{opacity:1,scale:1,duration:.4,ease:"back.out(2.5)"}},{tchip:.3f});')
    js.append(f'tl.to("#portada",{{opacity:0,scale:1.06,duration:.55,ease:"power2.in"}},{t_fin_portada:.3f});')
    sfx.append((tchip, "pop"))

    css = f'''
@font-face {{ font-family:"Anton"; src:url("assets/Anton-Regular.ttf"); }}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{W}px;height:{H}px;overflow:hidden;background:{TINTA}}}
#root{{position:relative;width:{W}px;height:{H}px;overflow:hidden;background:{TINTA};font-family:"Anton";color:#fff}}
#mapas{{position:absolute;left:0;top:{PH}px;width:{W}px;height:{MH}px;overflow:hidden;background:{MAR}}}
#mundo,#madrid{{position:absolute;inset:0;width:{W}px;height:{MH}px}}
#madrid{{opacity:0}}
#madrid img{{position:absolute;inset:0;width:{W}px;height:{MH}px;
  filter:invert(1) hue-rotate(185deg) brightness(.7) contrast(1.05) saturate(.25)}}
#madrid svg{{position:absolute;inset:0}}
#sombra{{position:absolute;left:0;top:0;width:{W}px;height:140px;background:linear-gradient({TINTA},rgba(11,17,24,0))}}
.pais{{fill:{TIERRA};stroke:{BORDE};stroke-width:1.2}}
.pais.res{{fill:{RESALTE};stroke:#4B6B88;stroke-width:1.6}}
.arco{{opacity:0;fill:none;stroke:{AMA};stroke-width:9;stroke-linecap:round}}
.avion{{fill:#fff;stroke:{AMA};stroke-width:6}}
.punto{{fill:{AMA};stroke:{TINTA};stroke-width:4}}
.pulso{{fill:none;stroke:{AMA};stroke-width:5}}
.nom{{font:44px Anton;fill:#fff;paint-order:stroke;stroke:{TINTA};stroke-width:10px;letter-spacing:.02em}}
.lin{{opacity:0;fill:none;stroke-width:13;stroke-linecap:round;stroke-linejoin:round}}
.sig{{fill:none;stroke-width:7;stroke-linecap:round;stroke-linejoin:round;opacity:0}}
.est{{fill:#fff;stroke:{TINTA};stroke-width:3}}
.ltxt{{font:38px Anton;fill:{TINTA};text-anchor:middle}}
.atrib{{position:absolute;right:16px;top:12px;font:20px/1 Helvetica,Arial,sans-serif;color:rgba(255,255,255,.7);z-index:3}}
.foto{{position:absolute;left:0;top:0;width:{W}px;height:{PH}px;overflow:hidden}}
.foto .img,#portada .img{{position:absolute;inset:0;background-size:cover;background-position:center}}
.foto::after{{content:"";position:absolute;left:0;right:0;bottom:0;height:260px;background:linear-gradient(rgba(11,17,24,0),{TINTA})}}
.cred{{position:absolute;right:18px;bottom:12px;font:19px/1.2 Helvetica,Arial,sans-serif;color:rgba(255,255,255,.75);z-index:2;
  text-shadow:0 1px 3px #000;max-width:900px;text-align:right}}
.etq{{position:absolute;left:60px;top:150px;z-index:20}}
.etq span{{display:inline-block;background:{AMA};color:{TINTA};font-size:50px;line-height:1;padding:18px 28px 16px;border-radius:16px;
  letter-spacing:.02em;box-shadow:0 8px 0 rgba(0,0,0,.25)}}
.chip{{position:absolute;left:60px;z-index:21}}
.chip span{{display:inline-block;background:rgba(11,17,24,.9);color:#fff;font-size:48px;line-height:1;padding:18px 26px 16px;
  border-left:12px solid {AMA};border-radius:12px;letter-spacing:.02em}}
.chip.aviso span{{background:#fff;color:{TINTA};border-left-color:#E5484D}}
#portada{{position:absolute;inset:0;z-index:30;overflow:hidden}}
.velo{{position:absolute;inset:0;background:linear-gradient(rgba(11,17,24,.25) 30%,rgba(11,17,24,.85) 75%)}}
.pruta{{position:absolute;inset:0;width:{W}px;height:{H}px}}
.pruta path{{fill:none;stroke:{AMA};stroke-width:12;stroke-linecap:round;opacity:.9}}
.ptit{{position:absolute;left:70px;right:120px;top:300px;font-size:178px;line-height:.98;text-transform:uppercase}}
.ptit .pw{{display:inline-block;margin-right:.18em;-webkit-text-stroke:10px #000;paint-order:stroke fill}}
.ptit .tl1{{color:{AMA}}}
.pchip{{position:absolute;left:70px;top:680px}}
.pchip span{{display:inline-block;background:{AMA};color:{TINTA};font-size:56px;padding:18px 30px 16px;border-radius:16px}}
'''
    page = f'''<!doctype html>
<html lang="es"><head><meta charset="utf-8"/><meta name="viewport" content="width={W}, height={H}"/>
<title>{nombre}</title>
<script src="assets/gsap.min.js"></script>
<style>{css}</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="{W}" data-height="{H}">
<audio id="voz" src="assets/audio.m4a" data-start="0" data-duration="{TOTAL}" data-track-index="1"></audio>
{chr(10).join(h)}
</div>
<script>
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(js)}
tl.set({{}},{{}},{TOTAL});
window.__timelines["main"] = tl;
</script></body></html>'''
    (D / "index.html").write_text(kit.pinta(page))

    # audio: voz + cola en silencio + sonidos de cada aparición, a −14 LUFS
    larga = D / "assets/voz_cola.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(voz), "-af", f"apad=pad_dur={COLA}", "-ar", "48000", str(larga)], check=True)
    sys.path.insert(0, str(ROOT / "scripts"))
    from sfx import mix
    if cfg.get("sonidos", True):
        mix(larga, sorted(sfx), D / "assets/sfx", D / "assets/audio.m4a")
    else:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(larga), "-c:a", "aac", "-b:a", "192k", str(D / "assets/audio.m4a")], check=True)
    (D / "package.json").write_text(json.dumps({"name": nombre.lower().replace("_", "-"), "private": True, "type": "module"}, indent=2))
    print(f"{D / 'index.html'} · {len(paradas)} paradas · {TOTAL}s")
    for k, p in enumerate(paradas):
        print(f"  {t_par[k]:6.2f}  {p['etiqueta']}")

    if a.render:
        env = dict(os.environ, HYPERFRAMES_SKIP_SKILLS="1")
        hf = ["npx", "--yes", "hyperframes@0.8.78"]
        subprocess.run(hf + ["lint"], cwd=D, env=env, check=True)
        out = ROOT / "raw" / f"{nombre}.mp4"
        subprocess.run(hf + ["render", "-o", str(out), "--quiet"], cwd=D, env=env, check=True)
        print(f"→ {out}")


if __name__ == "__main__":
    main()
