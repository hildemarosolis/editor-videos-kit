"""Piezas que se pegan encima de un episodio largo (1920×1080): rótulo de nombre y tarjeta de suscribirse.
Cada programa de podcast pone sus colores y fuentes con `estilo` (marca/kits/<id>.json → "programa" → "estilo");
lo que no lleve sale con el estilo por defecto de ESTILO.

Cada pieza es una composición pequeña de HyperFrames con fondo transparente que se renderiza a MOV
(ProRes 4444 con alfa) y FFmpeg la pega en su sitio y su segundo. Así el episodio entero no pasa por Chrome.
Movimiento según la regla de la casa: entran con rebote (back.out) y escalonadas.
"""
import html
from pathlib import Path

GSAP = '<script src="assets/gsap.min.js"></script>'
FONTS = """
@font-face { font-family: "Chillax"; src: url("assets/Chillax-Regular.ttf"); font-weight: 400; }
@font-face { font-family: "Chillax"; src: url("assets/Chillax-Medium.ttf"); font-weight: 500; }
@font-face { font-family: "Chillax"; src: url("assets/Chillax-Semibold.ttf"); font-weight: 600; }
"""

# ---------------------------------------------------------------- rótulo
ROTULO_W, ROTULO_H = 1000, 250   # 250 de alto: cabe la línea de Instagram
ROTULO_DUR = 5.5
ROTULO_MARGEN = 80          # px desde el borde izquierdo o derecho del cuadro
ROTULO_Y = 810              # parte de arriba del lienzo; el panel queda entre ~830 y ~960
ROTULO_SONIDOS = [(0.15, "whoosh")]


ROTULO_SUBE_IG = 46         # con la línea de Instagram el rótulo sube para no acercarse al borde de abajo


def ig_svg(color="#8C96FF"):
    return (f'<svg viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.2" stroke-linecap="round" '
            'stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/>'
            f'<circle cx="17.5" cy="6.5" r="0.6" fill="{color}"/></svg>')


IG_SVG = ig_svg()
# Estilo por defecto (fuente Chillax, azul y lila). Un programa cambia solo lo que lleve en su "estilo".
ESTILO = {"fuentes_css": FONTS, "familia": '"Chillax", sans-serif', "familia_nombre": None, "nombre_peso": 600,
          "nombre_px": 54, "mayusculas": False, "barra": "#475CDC", "barra_rgb": "71,92,220",
          "panel": "rgba(26,28,25,.88)", "nombre": "#E6E6E6", "cargo": "#8C96FF", "cargo_peso": 500, "ig": "#E6E6E6",
          "ig_icono": "#8C96FF"}


def rotulo_xy(lado, usuario=None):
    return ((ROTULO_MARGEN if lado == "izq" else 1920 - ROTULO_MARGEN - ROTULO_W),
            ROTULO_Y - (ROTULO_SUBE_IG if usuario else 0))


def rotulo_html(nombre, cargo, lado="izq", usuario=None, estilo=None):
    """Nombre, cargo y, si hay `usuario`, una línea con el icono de Instagram y su @."""
    e = ESTILO | (estilo or {})
    fam_nombre = f' font-family: {e["familia_nombre"]};' if e["familia_nombre"] else ""
    mayus = " text-transform: uppercase; letter-spacing: .02em;" if e["mayusculas"] else ""
    der = lado == "der"
    sx = 1 if not der else -1
    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8" /><meta name="viewport" content="width={ROTULO_W}, height={ROTULO_H}" />
<title>Rótulo {html.escape(nombre)}</title>{GSAP}
<style>{e["fuentes_css"]}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{ width: {ROTULO_W}px; height: {ROTULO_H}px; background: transparent; overflow: hidden; }}
#root {{ position: relative; width: {ROTULO_W}px; height: {ROTULO_H}px; overflow: hidden; font-family: {e["familia"]}; }}
#pieza {{ position: absolute; inset: 0; }}
#caja {{ position: absolute; top: 24px; {'right' if der else 'left'}: 10px; display: flex; flex-direction: {'row-reverse' if der else 'row'};
         align-items: stretch; }}
#barra {{ width: 10px; border-radius: 5px; background: {e["barra"]}; box-shadow: 0 0 18px rgba({e["barra_rgb"]},.85); }}
#panel {{ position: absolute; top: 0; bottom: 0; {'right' if der else 'left'}: 0; width: 100%; border-radius: 14px;
          background: {e["panel"]}; box-shadow: 0 10px 30px rgba(0,0,0,.35);
          transform-origin: {'100%' if der else '0%'} 50%; }}
#textos {{ position: relative; padding: 20px 38px 22px 30px; text-align: {'right' if der else 'left'}; }}
#nombre {{ font-weight: {e["nombre_peso"]}; font-size: {e["nombre_px"]}px; line-height: 1.08; color: {e["nombre"]}; white-space: nowrap;{fam_nombre}{mayus} }}
#cargo {{ font-weight: {e["cargo_peso"]}; font-size: 25px; letter-spacing: .16em; text-transform: uppercase; color: {e["cargo"]};
          margin-top: 8px; white-space: nowrap; }}
#ig {{ display: flex; align-items: center; gap: 10px; margin-top: 10px; font-weight: 500; font-size: 30px; color: {e["ig"]};
       white-space: nowrap; justify-content: {'flex-end' if der else 'flex-start'}; }}
#ig svg {{ width: 30px; height: 30px; flex: none; }}
</style></head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{ROTULO_DUR}" data-width="{ROTULO_W}" data-height="{ROTULO_H}" data-fps="25">
  <div id="pieza" class="clip" data-start="0" data-duration="{ROTULO_DUR}" data-track-index="0">
    <div id="caja"><div id="panel"></div><div id="barra"></div>
      <div id="textos"><div id="nombre">{html.escape(nombre)}</div><div id="cargo">{html.escape(cargo)}</div>{f'<div id="ig">{ig_svg(e["ig_icono"])}<span>{html.escape(usuario)}</span></div>' if usuario else ''}</div></div>
  </div>
</div>
<script>
  window.__timelines = window.__timelines || {{}};
  const tl = gsap.timeline({{ paused: true }});
  tl.fromTo("#barra", {{ scaleY: 0 }}, {{ scaleY: 1, duration: 0.35, ease: "back.out(2.2)" }}, 0.0);
  tl.fromTo("#panel", {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.5, ease: "power3.out" }}, 0.12);
  tl.fromTo("#nombre", {{ opacity: 0, x: {-34 * sx} }}, {{ opacity: 1, x: 0, duration: 0.45, ease: "back.out(1.8)" }}, 0.28);
  tl.fromTo("#cargo", {{ opacity: 0, x: {-24 * sx} }}, {{ opacity: 1, x: 0, duration: 0.4, ease: "back.out(1.8)" }}, 0.42);
  {'tl.fromTo("#ig", {{ opacity: 0, x: ' + str(-24 * sx) + ' }}, {{ opacity: 1, x: 0, duration: 0.4, ease: "back.out(1.8)" }}, 0.56);' if usuario else ''}
  tl.to("#barra", {{ boxShadow: "0 0 28px rgba({e["barra_rgb"]},1)", duration: 1.6, ease: "sine.inOut", yoyo: true, repeat: 1 }}, 1.2);
  tl.to(["#nombre", "#cargo"{', "#ig"' if usuario else ''}], {{ opacity: 0, x: {-20 * sx}, duration: 0.25, ease: "power2.in", stagger: 0.05 }}, {ROTULO_DUR - 0.6});
  tl.to("#panel", {{ scaleX: 0, duration: 0.35, ease: "power2.in" }}, {ROTULO_DUR - 0.45});
  tl.to("#barra", {{ scaleY: 0, duration: 0.2, ease: "power2.in" }}, {ROTULO_DUR - 0.22});
  window.__timelines["main"] = tl;
</script>
</body></html>
"""


# ---------------------------------------------------------------- tarjeta de suscribirse (al canal del programa)
TARJETA_W, TARJETA_H = 780, 170
TARJETA_DUR = 6.0
TARJETA_XY = ((1920 - TARJETA_W) // 2, 830)  # abajo, centrada, a la altura de los rótulos: ahí no hay caras en ningún plano
TARJETA_SONIDOS = [(0.25, "pop"), (2.0, "tic")]
BELL = ('<svg viewBox="0 0 24 24"><path fill="#fff" d="M12 22a2.5 2.5 0 0 0 2.45-2h-4.9A2.5 2.5 0 0 0 12 22zm7-6V11'
        'c0-3.07-1.64-5.64-4.5-6.32V4a1.5 1.5 0 0 0-3 0v.68C8.63 5.36 7 7.92 7 11v5l-2 2v1h14v-1l-2-2z"/></svg>')


def tarjeta_html(canal, titulo="Suscríbete"):
    """canal: {"nombre", "usuario", "avatar", "suscriptores"?} (el "canal" del programa).
    Sin "suscriptores" sale sin cifra (con pocos, resta) y sin insignia de verificado. Con ellos («39,7 mil»),
    la cifra va debajo del nombre, como en YouTube."""
    # como YouTube: debajo del nombre, los suscriptores si los hay; si no, el @ (el @ y la cifra juntos no caben)
    sub = f"{canal['suscriptores']} suscriptores" if canal.get("suscriptores") else canal["usuario"]
    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8" /><meta name="viewport" content="width={TARJETA_W}, height={TARJETA_H}" />
<title>{html.escape(titulo)}</title>{GSAP}
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{ width: {TARJETA_W}px; height: {TARJETA_H}px; background: transparent; overflow: hidden; }}
#root {{ position: relative; width: {TARJETA_W}px; height: {TARJETA_H}px; overflow: hidden;
         font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; }}
#pieza {{ position: absolute; inset: 0; }}
#yt {{ position: absolute; left: 10px; top: 14px; width: {TARJETA_W - 20}px; height: 140px; }}
#fondo {{ position: absolute; inset: 0; background: #fff; border-radius: 28px; transform-origin: 70px 70px;
          box-shadow: 0 10px 30px rgba(0,0,0,.30); }}
#foto {{ position: absolute; left: 20px; top: 20px; width: 100px; height: 100px; border-radius: 50%; object-fit: cover; }}
#datos {{ position: absolute; left: 140px; top: 30px; }}
#usuario {{ font-size: 34px; font-weight: 500; color: #0f0f0f; letter-spacing: -0.4px; }}
#sub {{ font-size: 23px; color: #606060; margin-top: 6px; }}
.boton {{ position: absolute; right: 24px; top: 38px; height: 64px; border-radius: 32px; padding: 0 28px;
          display: flex; align-items: center; font-weight: 500; font-size: 26px; }}
#b1 {{ background: #0f0f0f; color: #fff; }}
#b2 {{ background: #f0f0f0; color: #0f0f0f; right: 100px; opacity: 0; }}
#campana {{ position: absolute; right: 24px; top: 38px; width: 64px; height: 64px; border-radius: 50%; background: #0f0f0f;
            display: flex; align-items: center; justify-content: center; opacity: 0; }}
#campana svg {{ width: 36px; height: 36px; }}
</style></head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{TARJETA_DUR}" data-width="{TARJETA_W}" data-height="{TARJETA_H}" data-fps="25">
  <div id="pieza" class="clip" data-start="0" data-duration="{TARJETA_DUR}" data-track-index="0">
    <div id="yt"><div id="fondo"></div><img id="foto" src="assets/{Path(canal['avatar']).name}" />
      <div id="datos"><div id="usuario">{html.escape(canal['nombre'])}</div><div id="sub">{html.escape(sub)}</div></div>
      <div class="boton" id="b1">Suscribirse</div><div class="boton" id="b2">¡Suscrito!</div><div id="campana">{BELL}</div></div>
  </div>
</div>
<script>
  window.__timelines = window.__timelines || {{}};
  const tl = gsap.timeline({{ paused: true }});
  tl.fromTo("#foto", {{ scale: 0 }}, {{ scale: 1, duration: 0.35, ease: "back.out(2.2)" }}, 0.0);
  tl.fromTo("#fondo", {{ scaleX: 0.15, scaleY: 0.15, opacity: 0 }}, {{ scaleX: 1, scaleY: 1, opacity: 1, duration: 0.4, ease: "power3.out" }}, 0.25);
  tl.fromTo(["#datos", "#b1"], {{ opacity: 0, x: -20 }}, {{ opacity: 1, x: 0, duration: 0.3, ease: "back.out(1.8)", stagger: 0.08 }}, 0.5);
  tl.to("#b1", {{ scale: 0.92, duration: 0.08, ease: "power2.out" }}, 1.9);
  tl.to("#b1", {{ opacity: 0, duration: 0.12 }}, 2.0);
  tl.to("#b2", {{ opacity: 1, duration: 0.15 }}, 2.0);
  tl.fromTo("#campana", {{ opacity: 0, scale: 0.5 }}, {{ opacity: 1, scale: 1, duration: 0.25, ease: "back.out(3)" }}, 2.2);
  tl.fromTo("#campana svg", {{ rotation: -18 }}, {{ rotation: 0, duration: 0.6, ease: "elastic.out(1.2,0.3)" }}, 2.3);
  tl.fromTo("#yt", {{ y: 0 }}, {{ y: -4, duration: 3.0, ease: "sine.inOut" }}, 2.5);
  tl.to("#yt", {{ opacity: 0, y: 16, duration: 0.3, ease: "power2.in" }}, {TARJETA_DUR - 0.35});
  window.__timelines["main"] = tl;
</script>
</body></html>
"""
