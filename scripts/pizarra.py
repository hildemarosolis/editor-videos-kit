"""Modelo M11 «Pizarra arriba».

La cara baja al tercio inferior y los dos tercios de arriba son una pizarra oscura donde se
dibuja lo que se dice: una escena por idea, ancladas a frases de la transcripción. Sirve sobre
todo para re-editar vídeos ya grabados y que parezcan otros.

Receta:
  "subtitulos": {"top": 880},
  "pizarra": {
    "cara": "franja" | "circulo",   # franja: cara abajo · circulo: cara arriba a la derecha
                                    # cada escena puede cambiarlo con su propio "cara": la cara viaja de un sitio a otro
    "cara_y": 1360,                 # franja: dónde queda el centro de la cara (usa "centro_cara")
    "corte_y": 1100,                # franja: dónde empieza la franja de vídeo
    "circulo": {"x": 865, "y": 345, "r": 150, "zoom": 0.8},   # circulo: centro, radio y escala de la cara
    "final_completo": true,         # al salir «comenta» vuelve a pantalla completa y se queda (útil en círculo)
    "entrada": {"frase": "...", "dur": 0.6},       # empieza con el plano completo y pasa a la pizarra ahí
                                                   # ("despues_de": segundos, si la frase ya sale en el gancho)
    "respiros": [{"frase": "...", "dur": 2.5}],   # vuelve a pantalla completa un momento (o "hasta_frase")
    "escenas": [{"tipo": "titulo"|"iconos"|"lista"|"movil"|"campo"|"numero"|"curva"|"diagrama"|"evolucion"|"mapa"|"balanza"|"captura"|"bicicleta"|"escanos"|"foto",
                 "frase": "...", "seccion": "EL PROCESO", ...}],  # «seccion»: etiqueta arriba a la izquierda
    "completo_desde": {"frase": "..."}   # ahí vuelve a pantalla completa y se queda (cierre hablado a cámara)
  }
Una escena sin voz (la persona piensa, no habla) se ancla con "t" en segundos en vez de "frase", y
"zona": [arriba, abajo] le da más alto que el normal. La escena "evolucion": barras de seguidores por
red que suben paso a paso, un móvil con tus vídeos de cada época y comentarios anónimos que se acumulan.
"mapa" (España dibujándose y un punto por pueblo hasta "puntos", con su contador; con "lugares":
[{"nombre", "lat", "lon"}] los puntos van en su sitio real con su nombre y sin contador) y "balanza" (dos
platillos que se equilibran; al llegar "cae_frase" todo se viene abajo). Esa toma se prepara con `preparar.py --sin-silencios`.
Escena "captura": la web oficial de verdad dentro de una ventana de navegador; baja
hasta la línea que importa, la resalta en amarillo y deja encima una pastilla con el dato. La imagen
sale de `scripts/captura.py` (con su .json de marcas) o de una captura hecha a mano.
Escena "escanos": hemiciclo de 350 escaños que se llena partido a partido con sus
contadores, la raya de la mayoría y una pastilla con la suma; cada cifra, con su "fuente" debajo.
Cada escena dura hasta la siguiente (o "hasta_frase"). La pizarra se aparta sola cuando salen
un logo, la caja «comenta» o la tarjeta «sígueme».
"""
import html
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kit  # noqa: E402
from efectos import _find, _norm  # noqa: E402

W = 1080
TOP, BOT = 250, 870           # zona útil de la pizarra (debajo van los subtítulos)
L, CW = 110, 800              # márgenes de la zona segura de Reels

ICONOS = {
    "movil": '<rect x="6.5" y="2" width="11" height="20" rx="2.5"/><path d="M10.5 18.5h3"/>',
    "reloj": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3.5 2"/>',
    "euro": '<path d="M17.5 6.5A7 7 0 1 0 17.5 17.5"/><path d="M4 10.5h9M4 13.5h9"/>',
    "maleta": '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M9 7V4.5h6V7M3 12.5h18"/>',
    "huella": '<path d="M12 4a7 7 0 0 0-7 7v3M12 4a7 7 0 0 1 7 7v2.5M8.5 20a10 10 0 0 0 1-5v-4a2.5 2.5 0 0 1 5 0v2M12 11v4.5a10 10 0 0 1-1.5 5.5M15.5 16a14 14 0 0 1-1 4"/>',
    "sms": '<path d="M4 5h16v11H9l-5 4z"/><path d="M8 9.5h8M8 12.5h5"/>',
    "carpeta": '<path d="M3 6.5V19h18V8.5h-9l-2-2z"/>',
    "persona": '<circle cx="12" cy="8" r="4"/><path d="M4.5 21a7.5 7.5 0 0 1 15 0"/>',
    "calendario": '<rect x="3.5" y="5" width="17" height="15" rx="2"/><path d="M3.5 10h17M8 3v4M16 3v4"/>',
    "llave": '<circle cx="8" cy="15" r="4"/><path d="M11 12l9-9M17 6l2.5 2.5M14.5 8.5l2 2"/>',
    "alerta": '<path d="M12 3l10 18H2z"/><path d="M12 10v5M12 18v.01"/>',
    "check": '<path d="M4 12.5l5 5L20 6.5"/>',
    "x": '<path d="M6 6l12 12M18 6L6 18"/>',
    "casa": '<path d="M3 11l9-7 9 7v9H3z"/><path d="M9.5 20v-6h5v6"/>',
    "estrella": '<path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z"/>',
    "tijeras": '<circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M20 4L8.1 15.9M14.5 14.5L20 20M8.1 8.1L12 12"/>',
    "esmalte": '<rect x="6.5" y="10" width="11" height="11" rx="2.5"/><path d="M9.5 10V6.5h5V10M10.5 6.5V3h3v3.5"/>',
    "subida": '<path d="M3 17l6-6 4 4 8-8"/><path d="M15 7h6v6"/>',
}
try:  # los del ranking (oficios, documentos) también sirven
    from ranking import ICONS as _RK
    ICONOS = {**_RK, **ICONOS}
except Exception:
    pass


def icono(nombre):
    if nombre not in ICONOS:
        raise SystemExit(f"pizarra: icono «{nombre}» no existe ({', '.join(sorted(ICONOS))})")
    return f'<svg viewBox="0 0 24 24">{ICONOS[nombre]}</svg>'


CSS = """
      @font-face {{ font-family: "Oswald"; src: url("assets/fuentes/Oswald-Variable.ttf"); font-weight: 200 700; }}
      #root {{ background: radial-gradient(120% 60% at 50% 28%, #1d1d1d 0%, #0b0b0b 60%, #070707 100%); }}
      #video {{ z-index: 1; }}
      .pz-aro {{ position: absolute; left: {AX}px; top: {AY}px; width: {AD}px; height: {AD}px; z-index: 4;
                 border-radius: 50%; border: 6px solid var(--amarillo); box-shadow: 0 0 40px rgba(255,200,0,.25);
                 pointer-events: none; }}
      .cap {{ top: var(--capy, {CAPY}px) !important; }}
      .pz-sec {{ position: absolute; left: 0; top: {SECY}px; display: flex; align-items: center; gap: 14px;
                 font: 34px/1 "Anton", sans-serif; letter-spacing: .22em; color: #fff; text-transform: uppercase; }}
      .pz-sec i {{ display: block; width: 10px; height: 40px; background: var(--amarillo); border-radius: 3px; }}
      .pz-diag {{ position: relative; width: {CW}px; }}
      .pz-diag svg.lin {{ position: absolute; left: 0; top: 0; overflow: visible; }}
      .pz-diag svg.lin path {{ fill: none; stroke: #3a3a3a; stroke-width: 5; stroke-linejoin: round; }}
      .pz-nodo {{ position: absolute; display: flex; align-items: center; justify-content: center; gap: 14px;
                  padding: 0 18px; border-radius: 26px; background: #161616; border: 4px solid #2a2a2a; }}
      .pz-nodo svg {{ flex: none; width: 54px; height: 54px; fill: none; stroke: var(--amarillo); stroke-width: 1.8;
                      stroke-linecap: round; stroke-linejoin: round; }}
      .pz-nodo img {{ flex: none; height: 84px; width: 84px; border-radius: 50%; background: #fff; padding: 3px; }}
      .pz-nodo.col {{ flex-direction: column; gap: 8px; padding: 10px 12px; }}
      .pz-nodo.col .tx {{ align-items: center; }}
      .pz-nodo.col svg {{ width: 48px; height: 48px; }}
      .pz-nodo .tx {{ display: flex; flex-direction: column; gap: 4px; }}
      .pz-nodo b {{ font: 40px/1 "Anton", sans-serif; color: #fff; text-transform: uppercase; white-space: nowrap; }}
      .pz-nodo em {{ font: 400 28px/1 "Oswald", sans-serif; font-style: normal; color: #bdbdbd; white-space: nowrap; }}
      .pz-nodo .pz-raya {{ height: 10px; }}
      .pz-borde {{ position: absolute; left: 0; width: 1080px; top: {BY}px; height: 140px; z-index: 2;
                   background: linear-gradient(#0b0b0b, rgba(11,11,11,0)); pointer-events: none; }}
      .pz-rejilla {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; z-index: 0;
                     background-image: radial-gradient(rgba(255,255,255,.07) 1.6px, transparent 1.6px);
                     background-size: 40px 40px; }}
      #root {{ --pz: 1; }}
      .pz-esc {{ filter: opacity(var(--pz)); z-index: 3; position: absolute; left: {L}px; width: {CW}px; top: {TOP}px; height: {ALTO}px;
                 display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 26px; }}
      .pz-ante {{ font: 40px/1 "Anton", sans-serif; letter-spacing: .28em; color: var(--amarillo); }}
      .pz-tit {{ font: 124px/1.0 "Anton", sans-serif; text-transform: uppercase; color: #fff; text-align: center; }}
      .pz-tit span {{ display: inline-block; margin: 0 .08em; }}
      .pz-tit .acc {{ color: var(--amarillo); }}
      .pz-sub {{ font: 300 46px/1.2 "Oswald", sans-serif; color: #bdbdbd; text-align: center; }}
      .pz-ico {{ width: 200px; height: 200px; border-radius: 50%; background: #171717; border: 3px solid #2c2c2c;
                 display: flex; align-items: center; justify-content: center; }}
      .pz-ico svg, .pz-card svg, .pz-li svg, .pz-chip svg {{ fill: none; stroke: var(--amarillo); stroke-width: 1.7;
                 stroke-linecap: round; stroke-linejoin: round; }}
      .pz-ico svg {{ width: 110px; height: 110px; }}
      .pz-fila {{ display: flex; gap: 28px; justify-content: center; }}
      .pz-card {{ position: relative; width: 240px; padding: 34px 10px 28px; border-radius: 30px; background: #161616;
                  border: 3px solid #2a2a2a; display: flex; flex-direction: column; align-items: center; gap: 20px; }}
      .pz-card svg {{ width: 120px; height: 120px; }}
      .pz-card b {{ font: 44px/1.05 "Anton", sans-serif; color: #fff; text-transform: uppercase; text-align: center; }}
      .pz-raya {{ position: absolute; left: 8%; right: 8%; top: 46%; height: 14px; background: #ff3b3b;
                  border-radius: 7px; transform-origin: 0 50%; }}
      .pz-ul {{ list-style: none; display: flex; flex-direction: column; gap: 22px; width: 100%; }}
      .pz-li {{ display: flex; align-items: center; gap: 26px; padding: 20px 28px; border-radius: 24px;
                background: #161616; border: 3px solid #2a2a2a; }}
      .pz-li svg {{ flex: none; width: 76px; height: 76px; stroke-width: 2.6; }}
      .pz-li.x svg {{ stroke: #ff3b3b; }}
      .pz-li.yo {{ border-color: var(--amarillo); }}
      .pz-li span {{ font: 64px/1.05 "Anton", sans-serif; color: #fff; text-transform: uppercase; }}
      .pz-mov {{ display: flex; align-items: center; gap: 30px; }}
      .pz-tel {{ position: relative; width: 370px; height: 640px; border-radius: 56px; background: #101010;
                 border: 9px solid #2e2e2e; box-shadow: 0 0 0 2px #3b3b3b, 0 30px 60px rgba(0,0,0,.6);
                 padding: 64px 18px 18px; display: flex; flex-direction: column; gap: 14px; overflow: hidden; }}
      .pz-tel::before {{ content: ""; position: absolute; left: 50%; top: 16px; width: 100px; height: 28px;
                         margin-left: -50px; border-radius: 14px; background: #000; }}
      .pz-noti {{ border-radius: 22px; background: rgba(60,60,60,.92); padding: 14px 16px; color: #fff;
                  font: 400 30px/1.25 -apple-system, "Helvetica Neue", Arial, sans-serif; }}
      .pz-noti i {{ display: block; font-style: normal; font-size: 22px; color: #bbb; margin-bottom: 4px; }}
      .pz-noti strong {{ color: var(--amarillo); }}
      .pz-msg {{ max-width: 86%; border-radius: 22px; padding: 12px 16px; color: #fff; background: #2a2a2a;
                 font: 400 28px/1.25 -apple-system, "Helvetica Neue", Arial, sans-serif; align-self: flex-start; }}
      .pz-msg.yo {{ align-self: flex-end; background: var(--amarillo); color: #000; }}
      .pz-lado {{ display: flex; flex-direction: column; gap: 22px; }}
      .pz-chip {{ position: relative; display: flex; align-items: center; gap: 18px; padding: 16px 26px; border-radius: 40px;
                  background: #161616; border: 3px solid #2a2a2a; font: 50px/1 "Anton", sans-serif; color: #fff; }}
      .pz-chip svg {{ width: 50px; height: 50px; }}
      .pz-chip .pz-raya {{ height: 10px; top: 44%; }}
      .pz-sello {{ font: 74px/1 "Anton", sans-serif; color: #ff3b3b; border: 7px solid #ff3b3b; border-radius: 18px;
                   padding: 10px 24px; transform: rotate(-8deg); text-transform: uppercase; }}
      .pz-form {{ width: 800px; border-radius: 30px; background: #f4f4f4; padding: 34px 38px; display: flex;
                  flex-direction: column; gap: 18px; box-shadow: 0 30px 60px rgba(0,0,0,.6); }}
      .pz-form .h {{ font: 600 30px/1 "Oswald", sans-serif; letter-spacing: .12em; color: #777; text-transform: uppercase; }}
      .pz-form .t {{ font: 68px/1.05 "Anton", sans-serif; color: #111; text-transform: uppercase; }}
      .pz-form .lab {{ font: 500 30px/1 "Oswald", sans-serif; color: #444; margin-top: 10px; }}
      .pz-form .campo {{ height: 92px; border-radius: 18px; border: 4px solid #111; background: #fff; display: flex;
                         align-items: center; padding: 0 24px; font: 70px/1 "Anton", sans-serif; color: #111; }}
      .pz-form .campo .c {{ display: none; }}
      .pz-form .campo .cur {{ width: 5px; height: 58px; background: #111; margin-left: 4px; }}
      .pz-form .ok {{ align-self: flex-end; font: 44px/1 "Anton", sans-serif; color: #111; background: var(--amarillo);
                      border-radius: 40px; padding: 12px 26px; }}
      .pz-num {{ font: 300px/0.9 "Anton", sans-serif; color: var(--amarillo); }}
      .pz-num-txt {{ font: 64px/1.05 "Anton", sans-serif; color: #fff; text-transform: uppercase; text-align: center; }}
      .pz-curva svg {{ width: 780px; height: 420px; overflow: visible; }}
      .pz-curva .eje {{ stroke: #3a3a3a; stroke-width: 4; fill: none; }}
      .pz-curva .linea {{ stroke: var(--amarillo); stroke-width: 12; fill: none; stroke-linecap: round; }}
      .pz-curva .punto {{ fill: #fff; }}
      .pz-curva .area {{ fill: url(#pzgrad); }}
      .pz-evo {{ position: relative; width: {CW}px; height: 100%; align-self: stretch; }}
      .pz-evo .ante {{ position: absolute; left: 0; right: 0; top: 0; text-align: center; font: 600 28px/1 "Oswald", sans-serif;
                       letter-spacing: .12em; color: var(--amarillo); }}
      .pz-evo .seg {{ position: absolute; left: 0; top: 70px; font: 60px/1 "Anton", sans-serif; color: #fff; letter-spacing: .02em; }}
      .pz-evo .filas {{ position: absolute; left: 0; top: 170px; width: 450px; display: flex; flex-direction: column; gap: 34px; }}
      .pz-evo .fila {{ display: flex; align-items: center; gap: 22px; }}
      .pz-evo .red {{ width: 80px; height: 80px; border-radius: 50%; border: 3px solid var(--amarillo); background: #111;
                      display: flex; align-items: center; justify-content: center; flex: none; }}
      .pz-evo .red svg {{ width: 40px; height: 40px; fill: #fff; }}
      .pz-evo .barra {{ flex: 1; height: 34px; border-radius: 17px; background: #2e2e2e; overflow: hidden; }}
      .pz-evo .barra i {{ display: block; height: 100%; width: 100%; border-radius: 17px; transform-origin: 0 50%;
                          background: linear-gradient(90deg, #d9a800, var(--amarillo)); }}
      .pz-evo .tel {{ position: absolute; left: 490px; top: 70px; width: 300px; height: 534px; border-radius: 44px;
                      border: 10px solid #000; box-shadow: 0 0 0 3px #3a3a3a, 0 20px 50px rgba(0,0,0,.6); background: #000; }}
      .pz-evo .anio {{ position: absolute; left: 490px; top: 622px; width: 300px; text-align: center;
                       font: 600 28px/1 "Oswald", sans-serif; color: #bbb; letter-spacing: .1em; }}
      .pz-evo .com {{ position: absolute; left: 0; top: 820px; display: flex; gap: 18px; align-items: center; background: #fff;
                      border-radius: 30px; padding: 14px 26px; max-width: 800px; transform-origin: 0 50%; }}
      .pz-evo .com .av {{ width: 56px; height: 56px; border-radius: 50%; background: #bdbdbd; flex: none; }}
      .pz-evo .com b {{ display: block; font: 600 24px/1.1 "Oswald", sans-serif; color: #777; }}
      .pz-evo .com span {{ font: 500 38px/1.15 "Oswald", sans-serif; color: #111; }}
      .pz-cap {{ position: relative; width: {CW}px; height: 100%; align-self: center; }}
      .pz-cap .win {{ position: absolute; left: 0; right: 0; top: 0; border-radius: 22px; overflow: hidden; background: #fff;
                      border: 3px solid #2e2e2e; box-shadow: 0 30px 60px rgba(0,0,0,.6); transform-origin: 50% 40%; }}
      .pz-cap .bar {{ height: 58px; background: #1c1c1c; display: flex; align-items: center; gap: 12px; padding: 0 18px; }}
      .pz-cap .bar i {{ width: 14px; height: 14px; border-radius: 50%; background: #444; flex: none; }}
      .pz-cap .url {{ flex: 1; margin-left: 8px; height: 38px; border-radius: 19px; background: #2b2b2b; display: flex;
                      align-items: center; gap: 10px; padding: 0 16px; font: 500 24px/1 "Oswald", sans-serif; color: #ddd;
                      white-space: nowrap; overflow: hidden; }}
      .pz-cap .url svg {{ width: 20px; height: 20px; fill: none; stroke: #8fd18f; stroke-width: 2.4; flex: none; }}
      .pz-cap .fecha {{ font: 400 20px/1 "Oswald", sans-serif; color: #888; white-space: nowrap; }}
      .pz-cap .vista {{ position: relative; overflow: hidden; background: #fff; }}
      .pz-cap .hoja {{ position: absolute; left: 0; top: 0; width: 100%; }}
      .pz-cap .hoja img {{ display: block; width: 100%; }}
      .pz-cap .marca {{ position: absolute; border-radius: 4px; background: rgba(255,200,0,.45); border: 2px solid var(--amarillo);
                        transform-origin: 0 50%; mix-blend-mode: multiply; }}
      .pz-cap .dato {{ position: absolute; left: 0; right: 0; display: flex; justify-content: center; }}
      .pz-cap .dato b {{ font: 58px/1 "Anton", sans-serif; color: #000; background: var(--amarillo); border: 5px solid #000;
                         border-radius: 44px; padding: 14px 34px; text-transform: uppercase; white-space: nowrap;
                         box-shadow: 0 12px 0 rgba(0,0,0,.45); }}
      .pz-foto {{ position: relative; width: {CW}px; height: 100%; align-self: center; }}
      .pz-foto .ante {{ position: absolute; left: 0; right: 0; top: 0; text-align: center; }}
      .pz-foto .marco {{ position: absolute; left: 0; right: 0; border-radius: 26px; overflow: hidden; background: #111;
                         border: 4px solid #fff; box-shadow: 0 30px 60px rgba(0,0,0,.6); }}
      .pz-foto .marco img {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; opacity: 0;
                             transform-origin: 50% 50%; }}
      .pz-foto .cred {{ position: absolute; left: 0; right: 0; bottom: 0; padding: 26px 18px 10px; text-align: right;
                        font: 400 19px/1.1 "Oswald", sans-serif; color: rgba(255,255,255,.82); white-space: nowrap;
                        background: linear-gradient(rgba(0,0,0,0), rgba(0,0,0,.65)); opacity: 0; }}
      .pz-foto .dato {{ position: absolute; left: 0; right: 0; display: flex; justify-content: center; }}
      .pz-foto .dato b {{ font: 58px/1 "Anton", sans-serif; color: #000; background: var(--amarillo); border: 5px solid #000;
                          border-radius: 44px; padding: 14px 34px; text-transform: uppercase; white-space: nowrap;
                          box-shadow: 0 12px 0 rgba(0,0,0,.45); }}
      .pz-evo-vid {{ position: absolute; object-fit: cover; border-radius: 34px; z-index: 4; filter: opacity(var(--pz)); }}
"""


def build_pizarra(cfg, words, total, ocupado):
    """Devuelve css, html, js, eventos y las ventanas que cubre (para el aviso de datos sin tarjeta).

    `ocupado`: ventanas (de, a) en las que otra pieza usa la parte de arriba; la pizarra se aparta.
    """
    pz = cfg["pizarra"]
    seq = [(_norm(w["raw"]), w["t0"], w["t1"]) for w in words]

    def at(frase, after=0.0):
        i = _find(seq, frase, after)
        if i is None:
            raise SystemExit(f"pizarra: no encuentro la frase «{frase}» (después de {after:.1f}s)")
        return seq[i][1]

    cx, cy = cfg.get("centro_cara", [540, 620])
    base = pz.get("cara", "franja")
    # cómo se ve la cara en cada modo. Todos recortan con inset(… round …) para que GSAP pueda pasar
    # de uno a otro con una transición suave (de circle() a inset() no sabe interpolar).
    c = {"x": 865, "y": 345, "r": 150, "zoom": 0.8, **pz.get("circulo", {})}
    z, rl = c["zoom"], c["r"] / c["zoom"]
    cara_y, by = pz.get("cara_y", 1360), pz.get("corte_y", 1100)
    vy = cara_y - cy                       # franja: cuánto baja el vídeo
    sub = cfg.get("subtitulos", {}).get("top")
    modos = {
        "circulo": dict(video=f'x:{c["x"] - cx * z:.1f},y:{c["y"] - cy * z:.1f},scale:{z},'
                              f'clipPath:"inset({cy - rl:.1f}px {W - cx - rl:.1f}px {1920 - cy - rl:.1f}px {cx - rl:.1f}px round {rl:.1f}px)"',
                        top=520, capy=sub if base == "circulo" and sub else 1220, secy=230, aro=1, borde=0, rej=1, pz=1),
        "franja": dict(video=f'x:0,y:{vy},scale:1,clipPath:"inset({by - vy}px 0px 0px 0px round 0px)"',
                       top=TOP, capy=sub if base == "franja" and sub else 880, secy=200, aro=0, borde=1, rej=1, pz=1),
        "completo": dict(video='x:0,y:0,scale:1,clipPath:"inset(0px 0px 0px 0px round 0px)"',
                         top=TOP, capy=960, secy=200, aro=0, borde=0, rej=0, pz=0),
    }
    for m in ("circulo", "franja"):
        modos[m]["bot"] = modos[m]["capy"] - 30 if m == "circulo" else BOT
    mb = modos[base]
    css = CSS.format(BY=by, L=L, CW=CW, TOP=mb["top"], ALTO=mb["bot"] - mb["top"], CAPY=mb["capy"],
                     SECY=mb["secy"] - mb["top"], AX=c["x"] - c["r"] - 6, AY=c["y"] - c["r"] - 6,
                     AD=2 * c["r"] + 12)
    parts = ['      <div class="pz-rejilla" id="pzrej"></div>', '      <div class="pz-borde" id="pzbor"></div>',
             '      <div class="pz-aro" id="pzaro"></div>']
    js, ev, win = [], [], []

    def estado(m, t=None, dur=0.45):
        """Pone (t=None) o lleva (t) la cara, la decoración y los subtítulos al modo m."""
        d = modos[m]
        props = [("#video", d["video"]), ("#pzaro", f'opacity:{d["aro"]}'), ("#pzbor", f'opacity:{d["borde"]}'),
                 ("#pzrej", f'opacity:{d["rej"]}'), ("#root", f'"--capy":"{d["capy"]}px"')]
        if t is None:  # punto de partida: también en t=0 para que al rebobinar GSAP vuelva aquí
            for sel, pr in props + [("#root", f'"--pz":{d["pz"]}')]:
                js.append(f'gsap.set("{sel}",{{{pr}}});tl.set("{sel}",{{{pr}}},0);')
            return
        for sel, pr in props:
            ease = ',ease:"power3.inOut"' if sel == "#video" else ""
            if sel == "#pzaro":  # el aro sale cuando la cara ya casi ha llegado y se va en cuanto empieza a moverse
                ta, da = (t + dur * 0.7, dur * 0.3) if d["aro"] else (t, 0.1)
                js.append(f'tl.to("#pzaro",{{{pr},duration:{da:.2f}}},{ta:.3f});')
                continue
            js.append(f'tl.to("{sel}",{{{pr},duration:{dur}{ease}}},{t:.3f});')
        js.append(f'tl.to("#root",{{"--pz":{d["pz"]},duration:0.3}},{t + (dur * 0.5 if d["pz"] else 0):.3f});')

    js.append('gsap.set("#video",{transformOrigin:"0px 0px"});')
    escenas = pz["escenas"]
    m0 = escenas[0].get("cara", base)

    # entrada: arranca con el plano completo y pasa a la pizarra con una transición
    t_ent = 0.0
    if pz.get("entrada"):
        en = pz["entrada"]
        t_ent = at(en["frase"], en.get("despues_de", 0.0)) - 0.1 if en.get("frase") else en.get("t", 2.0)
        de = en.get("dur", 0.6)
        estado("completo")
        estado(m0, t_ent, de)
        ev += [(t_ent, "subida"), (t_ent + de * 0.6, "whoosh")]
        print(f"pizarra: entrada con plano completo hasta {t_ent:.2f}s")
    else:
        estado(m0)

    t_esc = []
    after = t_ent
    for k, e in enumerate(escenas):
        if "t" in e:  # escena sin voz: se ancla en segundos
            t = e["t"]
        elif k == 0 and not e.get("frase"):
            t = t_ent + pz.get("entrada", {}).get("dur", 0.6) * 0.4
        else:
            t = at(e["frase"], after) - e.get("antes", 0.15)
        t_esc.append(max(0.0, t))
        after = t
    fin_pz = min([a for a, _ in ocupado if a > t_esc[-1]] + [total])
    t_comp = None
    if pz.get("completo_desde"):
        cd = pz["completo_desde"]
        t_comp = (at(cd["frase"], t_esc[-1]) if cd.get("frase") else cd["t"]) - 0.2
        fin_pz = min(fin_pz, t_comp)
    tramos = []  # (desde, modo) para saber a qué modo volver tras un respiro
    for k, e in enumerate(escenas):
        t0 = t_esc[k]
        t1 = at(e["hasta_frase"], t0) if e.get("hasta_frase") else (t_esc[k + 1] if k + 1 < len(escenas) else fin_pz)
        dur = t1 - t0
        win.append((t0, t1))
        m = e.get("cara", base)
        if m not in modos or m == "completo":
            raise SystemExit(f"pizarra: escena {k}: «cara» debe ser circulo o franja (no «{m}»)")
        if k and m != escenas[k - 1].get("cara", base):
            estado(m, t0 - 0.1)  # cambia de cuadro: la cara viaja a su nuevo sitio
            ev.append((t0 - 0.1, "subida"))
        tramos.append((t0, m))
        sid = f"pz{k}"
        extra = []  # piezas que van fuera de la escena (vídeos del móvil de "evolucion")
        md = modos[m]
        alto = e["zona"][1] - e["zona"][0] if e.get("zona") else md["bot"] - md["top"]
        inner = ESCENAS[e["tipo"]](dict(e, _dir=cfg.get("_dir", "."), _extra=extra, _alto=alto), sid, t0, t1, at, js, ev)
        if e.get("seccion"):
            inner = (f'<div class="pz-sec" id="{sid}sec" style="top:{md["secy"] - md["top"]}px"><i></i>'
                     f'{html.escape(e["seccion"])}</div>' + inner)
            _entra(js, f"#{sid}sec", t0 + 0.02, "{opacity:0,x:-30}", '{opacity:1,x:0,duration:0.25,ease:"power2.out"}')
        pos = f' style="top:{md["top"]}px;height:{md["bot"] - md["top"]}px"' if m != base else ""
        if e.get("zona"):
            pos = f' style="top:{e["zona"][0]}px;height:{e["zona"][1] - e["zona"][0]}px"'
        parts.append(f'      <div class="clip pz-esc" id="{sid}" data-start="{t0:.3f}" data-duration="{dur:.3f}" '
                     f'data-track-index="3"{pos}>{inner}</div>')
        js.append(f'tl.to("#{sid}",{{opacity:0,duration:0.15}},{t1 - 0.15:.3f});')
        parts.extend(extra)
        if k:
            ev.append((t0, "whoosh"))
        print(f"pizarra: {e['tipo']:<8} {m:<7} {t0:6.2f}–{t1:6.2f}s")

    def modo_en(t):
        return next((m for a, m in reversed(tramos) if a <= t), tramos[0][1])

    # final: al salir la caja «comenta» (o lo primero que ocupe arriba tras la última escena) vuelve a pantalla completa
    final = t_comp if t_comp is not None else (fin_pz if pz.get("final_completo") and fin_pz < total else None)
    if final is not None:
        estado("completo", final - 0.2)
        ev.append((final - 0.2, "whoosh"))
        print(f"pizarra: final a pantalla completa desde {final - 0.2:.2f}s")

    # la pizarra se aparta cuando arriba sale otra pieza (logo, «comenta», «sígueme»)
    juntas = []
    for a, b in sorted(ocupado):
        if final is not None and a >= final - 0.01:
            continue  # ya está a pantalla completa
        if juntas and a <= juntas[-1][1] + 0.3:
            juntas[-1] = (juntas[-1][0], max(juntas[-1][1], b))
        else:
            juntas.append((a, b))
    for a, b in juntas:
        if b >= total - 0.3:
            js.append(f'tl.to("#root",{{"--pz":0,duration:0.2}},{max(0, a - 0.2):.3f});')
            continue
        js.append(f'tl.to("#root",{{"--pz":0,duration:0.2}},{max(0, a - 0.2):.3f});'
                  f'tl.to("#root",{{"--pz":1,duration:0.2}},{b:.3f});')

    # respiros: el vídeo vuelve un momento a pantalla completa
    for r in pz.get("respiros", []):
        a = at(r["frase"], r.get("despues_de", 0.0)) - 0.1
        b = at(r["hasta_frase"], a) - 0.3 if r.get("hasta_frase") else a + r.get("dur", 2.5)
        estado("completo", a, 0.35)
        estado(modo_en(b), b, 0.35)
        ev.append((a, "whoosh"))
        print(f"pizarra: respiro {a:6.2f}–{b:6.2f}s")
    return css, "\n".join(parts), js, ev, win


def _entra(js, sel, t, desde="{opacity:0,y:30}", hasta="{opacity:1,y:0,duration:0.3,ease:\"back.out(1.8)\"}"):
    js.append(f'tl.fromTo("{sel}",{desde},{hasta},{t:.3f});')


def _titulo(e, sid, t0, t1, at, js, ev):
    out = []
    if e.get("ante"):
        out.append(f'<div class="pz-ante" id="{sid}a">{html.escape(e["ante"])}</div>')
        _entra(js, f"#{sid}a", t0 + 0.05)
    if e.get("icono"):
        out.append(f'<div class="pz-ico" id="{sid}i">{icono(e["icono"])}</div>')
        _entra(js, f"#{sid}i", t0 + 0.1, "{opacity:0,scale:0.4}", '{opacity:1,scale:1,duration:0.35,ease:"back.out(2.2)"}')
    palabras = []
    for n, p in enumerate(e["titulo"].split(" ")):
        cls = ' class="acc"' if p in e.get("acento", []) else ""
        palabras.append(f'<span{cls} id="{sid}w{n}">{html.escape(p)}</span>')
        _entra(js, f"#{sid}w{n}", t0 + 0.15 + 0.09 * n, "{opacity:0,y:50}")
    px = f' style="font-size:{e["px"]}px"' if e.get("px") else ""
    out.append(f'<h1 class="pz-tit"{px}>{" ".join(palabras)}</h1>')
    if e.get("sub"):
        ts = at(e["sub_frase"], t0 - 0.5) if e.get("sub_frase") else t0 + 0.5
        out.append(f'<div class="pz-sub" id="{sid}s">{html.escape(e["sub"])}</div>')
        _entra(js, f"#{sid}s", ts)
    return "".join(out)


def _tachar(e, it, sid_it, t0, at, js, ev, giro=-14):
    js.append(f'gsap.set("#{sid_it} .pz-raya",{{rotation:{giro},scaleX:0}});')
    if it.get("tachar_frase"):
        tx = at(it["tachar_frase"], t0)
        js.append(f'tl.fromTo("#{sid_it} .pz-raya",{{rotation:{giro},scaleX:0}},{{rotation:{giro},scaleX:1,duration:0.18,ease:"power2.out"}},{tx:.3f});'
                  f'tl.to("#{sid_it}",{{opacity:0.45,duration:0.2}},{tx + 0.1:.3f});')
        ev.append((tx, "tic"))


def _iconos(e, sid, t0, t1, at, js, ev):
    out = []
    if e.get("titulo"):
        out.append(f'<div class="pz-ante" id="{sid}a">{html.escape(e["titulo"])}</div>')
        _entra(js, f"#{sid}a", t0 + 0.05)
    cards = []
    for n, it in enumerate(e["items"]):
        ti = at(it["frase"], t0 - 0.5) - 0.05 if it.get("frase") else t0 + 0.15 * n
        cards.append(f'<div class="pz-card" id="{sid}c{n}">{icono(it["icono"])}<b>{html.escape(it["texto"])}</b>'
                     f'<div class="pz-raya"></div></div>')
        _entra(js, f"#{sid}c{n}", ti, "{opacity:0,scale:0.5}", '{opacity:1,scale:1,duration:0.3,ease:"back.out(2.2)"}')
        ev.append((ti, "pop"))
        _tachar(e, it, f"{sid}c{n}", t0, at, js, ev)
    out.append(f'<div class="pz-fila">{"".join(cards)}</div>')
    return "".join(out)


def _lista(e, sid, t0, t1, at, js, ev):
    out = []
    if e.get("titulo"):
        out.append(f'<div class="pz-ante" id="{sid}a">{html.escape(e["titulo"])}</div>')
        _entra(js, f"#{sid}a", t0 + 0.05)
    lis = []
    for n, it in enumerate(e["items"]):
        ti = at(it["frase"], t0 - 0.5) - 0.05 if it.get("frase") else t0 + 0.2 * n
        cls = " ".join(c for c in ["pz-li", "x" if it.get("icono") == "x" else "", "yo" if it.get("resalta") else ""] if c)
        lis.append(f'<li class="{cls}" id="{sid}l{n}">{icono(it.get("icono", "check"))}<span>{html.escape(it["texto"])}</span></li>')
        _entra(js, f"#{sid}l{n}", ti, "{opacity:0,x:-50}", '{opacity:1,x:0,duration:0.25,ease:"back.out(1.8)"}')
        ev.append((ti, "tic"))
    out.append(f'<ul class="pz-ul">{"".join(lis)}</ul>')
    return "".join(out)


def _movil(e, sid, t0, t1, at, js, ev):
    msgs = []
    for n, m in enumerate(e.get("mensajes", [])):
        ti = at(m["frase"], t0 - 0.5) - 0.05 if m.get("frase") else t0 + 0.3
        if m.get("tipo") == "noti":
            txt = html.escape(m["texto"])
            for clave in m.get("resalta", []):
                txt = txt.replace(html.escape(clave), f"<strong>{html.escape(clave)}</strong>")
            msgs.append(f'<div class="pz-noti" id="{sid}m{n}"><i>{html.escape(m.get("app", "Mensajes · ahora"))}</i>{txt}</div>')
            _entra(js, f"#{sid}m{n}", ti, "{opacity:0,y:-40}", '{opacity:1,y:0,duration:0.3,ease:"back.out(1.6)"}')
        else:
            cls = "pz-msg yo" if m.get("de") == "yo" else "pz-msg"
            msgs.append(f'<div class="{cls}" id="{sid}m{n}">{html.escape(m["texto"])}</div>')
            _entra(js, f"#{sid}m{n}", ti, "{opacity:0,scale:0.7}", '{opacity:1,scale:1,duration:0.25,ease:"back.out(2)"}')
        ev.append((ti, "pop"))
    tel = f'<div class="pz-tel" id="{sid}t">{"".join(msgs)}</div>'
    _entra(js, f"#{sid}t", t0 + 0.05, "{opacity:0,y:80}", '{opacity:1,y:0,duration:0.4,ease:"power3.out"}')
    lado = []
    for n, it in enumerate(e.get("lado", [])):
        ti = at(it["frase"], t0 - 0.5) - 0.05
        ico = icono(it["icono"]) if it.get("icono") else ""
        lado.append(f'<div class="pz-chip" id="{sid}d{n}">{ico}{html.escape(it["texto"])}<div class="pz-raya"></div></div>')
        _entra(js, f"#{sid}d{n}", ti, "{opacity:0,x:60}", '{opacity:1,x:0,duration:0.25,ease:"back.out(2)"}')
        ev.append((ti, "pop"))
        _tachar(e, it, f"{sid}d{n}", t0, at, js, ev, giro=-8)
    if e.get("sello"):
        s = e["sello"]
        ts = at(s["frase"], t0)
        lado.append(f'<div class="pz-sello" id="{sid}x">{html.escape(s["texto"])}</div>')
        _entra(js, f"#{sid}x", ts, "{opacity:0,scale:2.2}", '{opacity:1,scale:1,duration:0.18,ease:"power3.in"}')
        ev.append((ts, "impacto"))
    return f'<div class="pz-mov">{tel}<div class="pz-lado">{"".join(lado)}</div></div>'


def _campo(e, sid, t0, t1, at, js, ev):
    valor = e["valor"]
    # los espacios como &nbsp;: dentro del campo (flex) un espacio suelto no ocupa nada
    chars = "".join(f'<span class="c" id="{sid}v{n}">{"&nbsp;" if ch == " " else html.escape(ch)}</span>'
                    for n, ch in enumerate(valor))
    tv = at(e["valor_frase"], t0 - 0.5) if e.get("valor_frase") else t0 + 0.8
    for n in range(len(valor)):
        js.append(f'tl.set("#{sid}v{n}",{{display:"inline"}},{tv + n * 0.07:.3f});')
        if valor[n] != " " and n % 2 == 0:
            ev.append((tv + n * 0.07, "tic"))
    ok = ""
    if e.get("ok"):
        tk = at(e["ok_frase"], tv) if e.get("ok_frase") else tv + len(valor) * 0.07 + 0.4
        ok = f'<div class="ok" id="{sid}k">{html.escape(e["ok"])}</div>'
        _entra(js, f"#{sid}k", tk, "{opacity:0,scale:0.5}", '{opacity:1,scale:1,duration:0.25,ease:"back.out(2.4)"}')
        ev.append((tk, "pop"))
    _entra(js, f"#{sid}f", t0 + 0.05, "{opacity:0,y:60}", '{opacity:1,y:0,duration:0.35,ease:"power3.out"}')
    return (f'<div class="pz-form" id="{sid}f"><div class="h">{html.escape(e.get("cabecera", ""))}</div>'
            f'<div class="t">{html.escape(e.get("titulo", ""))}</div><div class="lab">{html.escape(e["etiqueta"])}</div>'
            f'<div class="campo">{chars}<span class="cur"></span></div>{ok}</div>')


def _numero(e, sid, t0, t1, at, js, ev):
    tn = at(e["numero_frase"], t0 - 0.5) - 0.05 if e.get("numero_frase") else t0 + 0.1
    out = []
    if e.get("ante"):
        out.append(f'<div class="pz-ante" id="{sid}a">{html.escape(e["ante"])}</div>')
        _entra(js, f"#{sid}a", t0 + 0.05)
    out.append(f'<div class="pz-num" id="{sid}n">{html.escape(e["numero"])}</div>')
    _entra(js, f"#{sid}n", tn, "{opacity:0,scale:1.8}", '{opacity:1,scale:1,duration:0.22,ease:"power3.out"}')
    ev.append((tn, "impacto"))
    if e.get("texto"):
        out.append(f'<div class="pz-num-txt" id="{sid}x">{html.escape(e["texto"])}</div>')
        _entra(js, f"#{sid}x", tn + 0.3)
    return "".join(out)


def _curva(e, sid, t0, t1, at, js, ev):
    pts = [(40, 360), (220, 320), (380, 250), (540, 170), (740, 40)]
    d = "M" + " L".join(f"{x},{y}" for x, y in pts)
    area = d + " L740,380 L40,380 Z"
    dots = "".join(f'<circle class="punto" id="{sid}p{n}" cx="{x}" cy="{y}" r="14"/>' for n, (x, y) in enumerate(pts))
    tc = at(e["frase_sube"], t0 - 0.5) if e.get("frase_sube") else t0 + 0.3
    js.append(f'gsap.set("#{sid}l",{{strokeDasharray:1200,strokeDashoffset:1200}});')
    js.append(f'tl.to("#{sid}l",{{strokeDashoffset:0,duration:1.4,ease:"power2.inOut"}},{tc:.3f});')
    js.append(f'tl.fromTo("#{sid}r",{{opacity:0}},{{opacity:1,duration:0.8}},{tc + 0.6:.3f});')
    for n in range(len(pts)):
        js.append(f'tl.fromTo("#{sid}p{n}",{{scale:0,transformOrigin:"50% 50%"}},{{scale:1,duration:0.2,ease:"back.out(3)"}},'
                  f'{tc + 0.28 * n:.3f});')
    ev.append((tc, "subida"))
    out = []
    if e.get("titulo"):
        out.append(f'<div class="pz-ante" id="{sid}a">{html.escape(e["titulo"])}</div>')
        _entra(js, f"#{sid}a", t0 + 0.05)
    out.append(f'<div class="pz-curva"><svg viewBox="0 0 780 420"><defs><linearGradient id="pzgrad" x1="0" y1="0" x2="0" y2="1">'
               f'<stop offset="0" stop-color="#FFC800" stop-opacity=".35"/><stop offset="1" stop-color="#FFC800" stop-opacity="0"/>'
               f'</linearGradient></defs><path class="eje" d="M40,20 L40,380 L760,380"/>'
               f'<path class="area" id="{sid}r" d="{area}"/><path class="linea" id="{sid}l" d="{d}"/>{dots}</svg></div>')
    if e.get("texto"):
        out.append(f'<div class="pz-num-txt" id="{sid}x">{html.escape(e["texto"])}</div>')
        _entra(js, f"#{sid}x", tc + 1.2)
    return "".join(out)


def _diagrama(e, sid, t0, t1, at, js, ev):
    """Esquema que se arma nodo a nodo. Cada nodo: id, texto, sub, icono o imagen,
    padre, frase (cuándo aparece), resalta (se ilumina al aparecer), tachar_frase.
    "activo": [{"nodo": id, "frase": ...}] ilumina un nodo (y apaga el anterior) cuando se dice."""
    nodos = {n["id"]: n for n in e["nodos"]}
    nivel = {}

    def prof(i):
        if i not in nivel:
            nivel[i] = 0 if not nodos[i].get("padre") else prof(nodos[i]["padre"]) + 1
        return nivel[i]
    filas = {}
    for n in e["nodos"]:
        filas.setdefault(prof(n["id"]), []).append(n["id"])
    alto = e.get("alto", 560)
    nf = max(filas) + 1
    # una fila con varios nodos estrechos los apila (icono arriba, texto abajo) y es más alta
    ancho_f = {f: min(e.get("ancho", 560), CW / len(ids) - 20) for f, ids in filas.items()}
    alto_f = {f: 150 if ancho_f[f] < 330 else 116 for f in filas}
    h = max(alto_f.values())
    paso = (alto - h) / max(nf - 1, 1)
    pos = {}
    for f, ids in filas.items():
        for k, i in enumerate(ids):
            pos[i] = ((k + 0.5) * CW / len(ids), f * paso if nf > 1 else (alto - h) / 2)
    out, lineas = [], []
    if e.get("titulo"):
        out.append(f'<div class="pz-ante" id="{sid}a">{html.escape(e["titulo"])}</div>')
        _entra(js, f"#{sid}a", t0 + 0.05)
    t_de = {}
    for n in e["nodos"]:
        i = n["id"]
        t_de[i] = at(n["frase"], t0 - 0.5) - 0.05 if n.get("frase") else t0 + 0.15
    for n in e["nodos"]:
        i, (x, y) = n["id"], pos[n["id"]]
        ti = t_de[i]
        ancho, hn = ancho_f[nivel[i]], alto_f[nivel[i]]
        col = ancho < 330
        if n.get("imagen"):
            cara = f'<img src="assets/{n["imagen"]}" alt="{html.escape(n["texto"])}">'
        else:
            cara = icono(n["icono"]) if n.get("icono") else ""
        sub = f'<em>{html.escape(n["sub"])}</em>' if n.get("sub") else ""
        # letra según el hueco: Anton mide ~0,47 em por carácter
        fs = min(46, int((ancho - (0 if col else 68 if cara else 0) - 44) / (max(len(n["texto"]), 1) * 0.47)))
        tx = (f'<div class="tx"><b style="font-size:{fs}px">{html.escape(n["texto"])}</b>{sub}</div>'
              if not n.get("imagen") or n.get("con_texto") else "")
        out.append(f'<div class="pz-nodo{" col" if col else ""}" id="{sid}n_{i}" style="left:{x - ancho / 2:.0f}px;'
                   f'top:{y:.0f}px;width:{ancho:.0f}px;height:{hn}px">{cara}{tx}<div class="pz-raya"></div></div>')
        _entra(js, f"#{sid}n_{i}", ti, "{opacity:0,scale:0.5}", '{opacity:1,scale:1,duration:0.3,ease:"back.out(2.2)"}')
        ev.append((ti, "pop"))
        if n.get("padre"):
            px, py = pos[n["padre"]]
            y0, y1 = py + alto_f[nivel[n["padre"]]], y
            m = (y0 + y1) / 2
            d = f"M{px:.0f},{y0:.0f} V{m:.0f} H{x:.0f} V{y1:.0f}"
            largo = abs(m - y0) + abs(x - px) + abs(y1 - m) + 2
            lineas.append(f'<path id="{sid}l_{i}" d="{d}"/>')
            js.append(f'tl.fromTo("#{sid}l_{i}",{{strokeDasharray:{largo:.0f},strokeDashoffset:{largo:.0f}}},'
                      f'{{strokeDasharray:{largo:.0f},strokeDashoffset:0,duration:0.3,ease:"power2.out"}},{ti - 0.2:.3f});')
        _tachar(e, n, f"{sid}n_{i}", t0, at, js, ev, giro=-6)
    activos = [(t_de[n["id"]] + 0.25, n["id"]) for n in e["nodos"] if n.get("resalta")]
    activos += [(at(a["frase"], t0 - 0.5), a["nodo"]) for a in e.get("activo", [])]
    previo = None
    for ta, i in sorted(activos):
        if previo:
            js.append(f'tl.to("#{sid}n_{previo}",{{borderColor:"#2a2a2a",boxShadow:"0 0 0 rgba(255,200,0,0)",scale:1,'
                      f'duration:0.2}},{ta:.3f});')
        js.append(f'tl.fromTo("#{sid}n_{i}",{{borderColor:"#2a2a2a",boxShadow:"0 0 0 rgba(255,200,0,0)",scale:1}},'
                  f'{{borderColor:"#FFC800",boxShadow:"0 0 46px rgba(255,200,0,0.45)",scale:1.06,duration:0.25,'
                  f'ease:"back.out(2)",immediateRender:false}},{ta:.3f});')
        if nodos[i].get("padre"):
            js.append(f'tl.to("#{sid}l_{i}",{{stroke:"#FFC800",duration:0.2}},{ta:.3f});')
        ev.append((ta, "tic"))
        previo = i
    out.append(f'<div class="pz-diag" style="height:{alto}px"><svg class="lin" width="{CW}" height="{alto}">'
               f'{"".join(lineas)}</svg>{"".join(out[1:] if e.get("titulo") else out)}</div>')
    return (out[0] if e.get("titulo") else "") + out[-1]



REDES = ["instagram", "tiktok", "youtube", "facebook"]


def _icono_red(nombre):
    import re
    from pathlib import Path
    svg = (Path(__file__).resolve().parent.parent / "marca/redes" / f"{nombre}.svg").read_text()
    return re.sub(r"<title>.*?</title>", "", svg)


def _clip_movil(src, desde, dur, dst):
    """Tramo de un vídeo antiguo para el móvil: 540×960, SDR, sin sonido. Gira y pasa a SDR los del iPhone (HLG)."""
    import subprocess
    from pathlib import Path
    from prueba_corte import probe_video
    src, dst = Path(src), Path(dst)
    if not src.exists():
        raise SystemExit(f"evolucion: no encuentro el clip {src}")
    if dst.exists() and dst.stat().st_mtime > src.stat().st_mtime:
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    trc, rot, _, _ = probe_video(src)
    fuente = src
    if trc in ("arib-std-b67", "smpte2084"):
        fuente = dst.with_suffix(".sdr.mp4")
        giro = {-90: "clock", 270: "clock", 90: "cclock", -270: "cclock"}.get(rot, "")
        ent, vf = kit.vf_a_sdr(giro)  # en Mac, por el chip; en Windows y Linux, con zscale
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *ent,
                        "-ss", f"{desde}", "-t", f"{dur}", "-i", str(src), "-an",
                        "-vf", vf, *kit.h264("12M"), str(fuente)], check=True)
        desde = 0
    # sin -noautorotate: así el SDR sale derecho y sin marca de rotación (como en prueba_corte.py)
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{desde}", "-t", f"{dur}", "-i", str(fuente),
                    "-an", "-vf", "scale=540:960:force_original_aspect_ratio=increase,crop=540:960,fps=30",
                    "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(dst)], check=True)
    if fuente != src:
        fuente.unlink()


def _evolucion(e, sid, t0, t1, at, js, ev):
    """Barras de seguidores por red que suben paso a paso, un móvil con los vídeos de cada época y
    comentarios anónimos que se acumulan (el nuevo abajo, el anterior se apaga encima).

    "pasos": [{"t": 3.0, "nivel": 0-100, "critica": "...", "clip": "ruta", "desde": 12, "anio": "2019"}, ...]
    o varios vídeos por paso: "clips": [{"clip": "ruta", "desde": 4, "anio": "2024"}, ...] (se reparten el paso).
    Sin cifras: solo barras (no se afirma ningún número). Cada red sube a un ritmo algo distinto."""
    from pathlib import Path
    pasos = e["pasos"]
    zona_top = e.get("zona", [120, 1090])[0]
    ritmo = e.get("ritmo", [1.0, 0.86, 0.74, 0.62])
    filas = "".join(f'<div class="fila"><div class="red">{_icono_red(r)}</div><div class="barra"><i id="{sid}b{n}"></i></div></div>'
                    for n, r in enumerate(REDES))
    out = [f'<div class="pz-evo">',
           f'<div class="ante" id="{sid}an">{html.escape(e.get("ante", ""))}</div>' if e.get("ante") else "",
           f'<div class="seg" id="{sid}sg">{html.escape(e.get("titulo", "SEGUIDORES"))}</div>',
           f'<div class="filas" id="{sid}fl">{filas}</div><div class="tel" id="{sid}tel"></div>']
    for n in range(len(REDES)):
        js.append(f'gsap.set("#{sid}b{n}",{{scaleX:0.001}});tl.set("#{sid}b{n}",{{scaleX:0.001}},0);')
    _entra(js, f"#{sid}sg", t0 + 0.05)
    _entra(js, f"#{sid}fl", t0 + 0.15)
    _entra(js, f"#{sid}tel", t0 + 0.1, "{opacity:0,y:60}", '{opacity:1,y:0,duration:0.4,ease:"power3.out"}')
    # el móvil: su pantalla son vídeos sueltos encima (data-start propio), en la misma posición
    vx, vy = L + 490 + 10, zona_top + 70 + 10
    d = Path(e["_dir"])
    for k, pa in enumerate(pasos):
        ta = pa["t"]
        tb = pasos[k + 1]["t"] if k + 1 < len(pasos) else t1
        # barras
        nivel = pa.get("nivel", 0)
        for n in range(len(REDES)):
            v = max(0.001, min(1.0, nivel / 100 * ritmo[n]))
            js.append(f'tl.to("#{sid}b{n}",{{scaleX:{v:.3f},duration:{1.0 + 0.15 * n:.2f},ease:"power2.out"}},{ta + 0.25:.3f});')
        if k and nivel:
            ev.append((ta + 0.2, "subida"))
        # comentario: entra abajo; el anterior sube y se apaga; el de antes desaparece
        if pa.get("critica"):
            out.append(f'<div class="com" id="{sid}c{k}"><div class="av"></div><div><b>alguien</b>'
                       f'<span>{html.escape(pa["critica"])}</span></div></div>')
            js.append(f'tl.fromTo("#{sid}c{k}",{{opacity:0,y:40}},{{opacity:1,y:0,duration:0.3,ease:"back.out(1.8)"}},{ta + 0.9:.3f});')
            ev.append((ta + 0.9, "pop"))
            js.append(f'gsap.set("#{sid}c{k}",{{opacity:0}});')
            if k >= 1 and pasos[k - 1].get("critica"):
                js.append(f'tl.to("#{sid}c{k - 1}",{{y:-118,scale:0.86,opacity:0.35,duration:0.3}},{ta + 0.9:.3f});')
            if k >= 2 and pasos[k - 2].get("critica"):
                js.append(f'tl.to("#{sid}c{k - 2}",{{opacity:0,duration:0.25}},{ta + 0.9:.3f});')
        # vídeos de esa época: uno ("clip") o varios ("clips") que se reparten el tiempo del paso
        clips = pa.get("clips") or ([{"clip": pa["clip"], "desde": pa.get("desde", 0), "anio": pa.get("anio")}]
                                    if pa.get("clip") else [])
        if not clips and pa.get("anio"):
            clips = [{"anio": pa["anio"]}]
        tramo = (tb - ta) / max(len(clips), 1)
        for j, cl in enumerate(clips):
            ca, cb = ta + tramo * j, ta + tramo * (j + 1)
            anio = cl.get("anio", pa.get("anio"))
            if anio:  # el año debajo del móvil
                out.append(f'<div class="anio" id="{sid}y{k}_{j}">TUS VÍDEOS · {html.escape(str(anio))}</div>')
                js.append(f'gsap.set("#{sid}y{k}_{j}",{{opacity:0}});tl.set("#{sid}y{k}_{j}",{{opacity:1}},{ca:.3f});'
                          f'tl.set("#{sid}y{k}_{j}",{{opacity:0}},{cb:.3f});')
            if cl.get("clip"):
                rel = f"assets/evolucion/paso{k + 1}_{j + 1}.mp4"
                _clip_movil(cl["clip"], cl.get("desde", 0), cb - ca + 0.3, d / rel)
                e["_extra"].append(f'      <video id="{sid}v{k}_{j}" class="clip pz-evo-vid" src="{rel}" data-start="{ca:.3f}" '
                                   f'data-duration="{cb - ca:.3f}" data-track-index="{30 + k * 6 + j}" data-has-audio="false" '
                                   f'muted playsinline style="left:{vx}px;top:{vy}px;width:280px;height:514px"></video>')
    out.append("</div>")
    return "".join(out)

# España peninsular simplificada (lon, lat), en el sentido de las agujas del reloj desde Finisterre.
ESPANA = [(-9.3, 42.9), (-9.0, 43.2), (-8.4, 43.38), (-7.68, 43.78), (-6.0, 43.57), (-5.0, 43.47), (-3.8, 43.47),
          (-3.0, 43.38), (-1.79, 43.38), (-1.4, 43.05), (-0.5, 42.8), (0.7, 42.85), (1.45, 42.6), (2.0, 42.4),
          (3.17, 42.43), (3.2, 41.9), (2.2, 41.4), (1.0, 41.05), (0.7, 40.7), (0.0, 39.9), (-0.33, 39.47),
          (0.2, 38.75), (-0.48, 38.35), (-0.7, 37.7), (-1.6, 37.3), (-2.1, 36.73), (-3.0, 36.75), (-4.4, 36.72),
          (-5.35, 36.15), (-5.6, 36.0), (-6.3, 36.5), (-6.95, 37.2), (-7.4, 37.18), (-7.5, 37.6), (-7.3, 38.2),
          (-7.0, 38.6), (-7.3, 39.4), (-7.0, 39.7), (-6.9, 40.2), (-6.8, 41.0), (-6.2, 41.6), (-6.6, 41.95),
          (-7.2, 41.9), (-8.1, 41.85), (-8.9, 41.9), (-8.85, 42.1), (-9.0, 42.5)]


def _mapa(e, sid, t0, t1, at, js, ev):
    import random
    k, w, h = 60.0, 800, 520
    xy = [((lon + 9.5) * k, (44.0 - lat) * k * 1.3) for lon, lat in ESPANA]
    esc = min(w / max(x for x, _ in xy), h / max(y for _, y in xy))
    ox = (w - max(x for x, _ in xy) * esc) / 2  # centrado en la pizarra
    pts = [(ox + x * esc, y * esc) for x, y in xy]
    ruta = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + " Z"

    def dentro(px, py):
        c = False
        for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
            if (y1 > py) != (y2 > py) and px < (x2 - x1) * (py - y1) / (y2 - y1) + x1:
                c = not c
        return c
    rnd, puntos = random.Random(e.get("semilla", 8305)), []
    # «lugares»: sitios reales [{"nombre", "lat", "lon"}] en vez de puntos al azar;
    # cada uno con su nombre al lado y un aro que late. Sin contador: arriba solo «ante» y «texto».
    lugares = e.get("lugares") or []
    if lugares:
        puntos = [(ox + (l["lon"] + 9.5) * k * esc, (44.0 - l["lat"]) * k * 1.3 * esc) for l in lugares]
    n = len(puntos) if lugares else e.get("puntos", 60)
    while len(puntos) < n:  # repartidos por todo el mapa, sin amontonarse
        px, py = rnd.uniform(0, w), rnd.uniform(0, h)
        if dentro(px, py) and all((px - a) ** 2 + (py - b) ** 2 > 34 ** 2 for a, b in puntos):
            puntos.append((px, py))
    if not lugares:
        puntos.sort(key=lambda q: q[0] + q[1] * 0.4)
    circ = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{18 if lugares else 11}"/>' for x, y in puntos)
    nombres = "".join(f'<circle class="{sid}aro" cx="{x:.1f}" cy="{y:.1f}" r="18" fill="none" stroke="var(--amarillo)" stroke-width="5"/>'
                      f'<text x="{x + 34:.1f}" y="{y + 16:.1f}" font-family="Anton" font-size="52" fill="#fff" stroke="#000" '
                      f'stroke-width="8" paint-order="stroke">{html.escape(l["nombre"].upper())}</text>'
                      for (x, y), l in zip(puntos, lugares))
    t_ent = t0 + 0.05
    t_pts = t_ent + 0.7
    dur_pts = e.get("dur_puntos", 0.4 if lugares else 2.6)
    if lugares:  # el aro late desde que cae el punto y el nombre entra con él
        js.append(f'tl.fromTo("#{sid}l text",{{opacity:0,x:-20}},{{opacity:1,x:0,duration:0.3,ease:"back.out(2)"}},{t_pts + 0.15:.3f});'
                  f'tl.fromTo(".{sid}aro",{{scale:1,opacity:0.9,transformOrigin:"50% 50%"}},{{scale:3,opacity:0,duration:0.9,'
                  f'repeat:{max(1, int((t1 - t_pts) / 0.9) - 1)},ease:"power1.out"}},{t_pts + 0.2:.3f});')
    js.append(f'tl.fromTo("#{sid}r",{{strokeDashoffset:1}},{{strokeDashoffset:0,duration:0.8,ease:"power2.inOut"}},{t_ent:.3f});'
              f'tl.fromTo("#{sid}r",{{fillOpacity:0}},{{fillOpacity:1,duration:0.4}},{t_ent + 0.6:.3f});'
              f'tl.fromTo("#{sid}p circle",{{scale:0,opacity:0,transformOrigin:"50% 50%"}},{{scale:1,opacity:1,duration:0.18,'
              f'ease:"back.out(3)",stagger:{dur_pts / n:.4f}}},{t_pts:.3f});'
              f'const mc{sid}={{v:0}};tl.fromTo(mc{sid},{{v:0}},{{v:{n},duration:{dur_pts},ease:"none",'
              f'onUpdate:()=>{{document.getElementById("{sid}n").textContent=Math.round(mc{sid}.v)}}}},{t_pts:.3f});')
    _entra(js, f"#{sid}c", t_ent)
    ev.append((t_ent, "whoosh"))
    ev += [(t_pts + dur_pts * f, "tic") for f in ((0,) if lugares else (0, 0.2, 0.4, 0.6, 0.8, 1.0))]
    return (f'<div style="position:relative;width:{w}px;height:{h + 150}px">'
            f'<div id="{sid}c" style="display:flex;align-items:baseline;gap:18px;height:130px">'
            f'<span style="font:44px/1 Anton,sans-serif;color:#fff;letter-spacing:.08em">{html.escape(e.get("ante", "MÁS DE"))}</span>'
            + (f'<span id="{sid}n" style="display:none">0</span>' if lugares else
               f'<span id="{sid}n" style="font:130px/1 Anton,sans-serif;color:var(--amarillo);font-variant-numeric:tabular-nums">0</span>')
            + f'<span style="font:44px/1.1 Anton,sans-serif;color:#fff;letter-spacing:.06em;text-transform:uppercase">'
            f'{html.escape(e.get("texto", "pueblos recorridos"))}</span></div>'
            f'<svg viewBox="0 0 {w} {h}" style="width:{w}px;height:{h}px;overflow:visible">'
            f'<path id="{sid}r" d="{ruta}" pathLength="1" stroke-dasharray="1" fill="rgba(255,200,0,.07)" '
            f'stroke="var(--amarillo)" stroke-width="5" stroke-linejoin="round"/>'
            f'<g id="{sid}p" fill="var(--amarillo)" stroke="#000" stroke-width="3">{circ}</g><g id="{sid}l">{nombres}</g></svg></div>')


def _balanza(e, sid, t0, t1, at, js, ev):
    """Coste y beneficio en una balanza; entra la oportunidad y, al decir que cae, todo se viene abajo."""
    a, b = (html.escape(x) for x in e.get("platillos", ["COSTE", "BENEFICIO"]))
    tercero = html.escape(e.get("tercero", "OPORTUNIDAD"))
    t_eq = at(e["equilibra_frase"], t0 - 0.5) if e.get("equilibra_frase") else t0 + 1.2
    t_baja = at(e["baja_frase"], t0 - 0.5) if e.get("baja_frase") else None
    t_ter = at(e["tercero_frase"], t0 - 0.5) if e.get("tercero_frase") else None
    t_cae = at(e["cae_frase"], t0 - 0.5) if e.get("cae_frase") else None
    plato = lambda x, lbl, i: (f'<g id="{sid}p{i}"><path d="M{x - 90} 300 L{x} 230 L{x + 90} 300" fill="none" stroke="#fff" stroke-width="4"/>'
                               f'<path d="M{x - 110} 300 h220 a110 34 0 0 1 -220 0z" fill="#2a2a2a" stroke="var(--amarillo)" stroke-width="6"/>'
                               f'<rect x="{x - 125}" y="160" width="250" height="64" rx="12" fill="var(--amarillo)" stroke="#000" stroke-width="5"/>'
                               f'<text x="{x}" y="207" text-anchor="middle" font-family="Anton" font-size="46" fill="#000">{lbl}</text></g>')
    svg = (f'<svg viewBox="0 0 800 560" style="width:800px;height:560px;overflow:visible" id="{sid}s">'
           f'<g id="{sid}f"><path d="M400 250 L330 520 H470 Z" fill="#1d1d1d" stroke="#fff" stroke-width="5" stroke-linejoin="round"/>'
           f'<rect x="300" y="515" width="200" height="20" rx="6" fill="#fff"/></g>'
           f'<g id="{sid}v"><rect x="130" y="222" width="540" height="18" rx="9" fill="#fff"/>'
           f'<circle cx="400" cy="231" r="16" fill="var(--amarillo)" stroke="#000" stroke-width="4"/>'
           f'{plato(170, a, 0)}{plato(630, b, 1)}</g></svg>')
    caja = (f'<div id="{sid}t" style="position:absolute;left:0;right:0;top:0;display:flex;justify-content:center;opacity:0">'
            f'<div style="font:84px/1 Anton,sans-serif;color:#fff;background:#d4261a;border:6px solid #000;border-radius:16px;'
            f'padding:14px 30px;box-shadow:0 10px 0 rgba(0,0,0,.4)">{tercero}</div></div>')
    flecha = (f'<div id="{sid}x" style="position:absolute;left:0;right:0;top:220px;display:flex;justify-content:center;opacity:0">'
              f'<svg viewBox="0 0 24 24" style="width:300px;height:300px" fill="none" stroke="#ff3b3b" stroke-width="3" '
              f'stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v16M5 12l7 7 7-7"/></svg></div>')
    js.append(f'tl.fromTo("#{sid}f",{{opacity:0,y:60}},{{opacity:1,y:0,duration:0.3,ease:"back.out(1.8)"}},{t0 + 0.05:.3f});'
              f'tl.fromTo("#{sid}v",{{opacity:0,y:-80}},{{opacity:1,y:0,duration:0.35,ease:"bounce.out"}},{t0 + 0.25:.3f});'
              f'gsap.set("#{sid}v",{{svgOrigin:"400 231"}});')
    ev += [(t0 + 0.05, "whoosh"), (t0 + 0.35, "pop")]
    # se equilibra: un vaivén que se calma
    js.append(f'tl.to("#{sid}v",{{keyframes:[{{rotation:-9,duration:0.3}},{{rotation:7,duration:0.3}},{{rotation:-3,duration:0.25}},'
              f'{{rotation:0,duration:0.25}}],ease:"sine.inOut"}},{t_eq:.3f});')
    if t_baja is not None:  # el coste baja de peso: su platillo sube
        js.append(f'tl.to("#{sid}v",{{rotation:12,duration:0.45,ease:"back.out(2)"}},{t_baja:.3f});')
        ev.append((t_baja, "whoosh"))
    if t_ter is not None:
        js.append(f'tl.fromTo("#{sid}t",{{opacity:0,y:-120,scale:0.6}},{{opacity:1,y:0,scale:1,duration:0.35,'
                  f'ease:"back.out(2.2)"}},{t_ter:.3f});')
        ev.append((t_ter, "pop"))
    if t_cae is not None:  # todo se viene abajo
        js.append(f'tl.to("#{sid}v",{{y:900,rotation:38,duration:0.75,ease:"power2.in"}},{t_cae:.3f});'
                  f'tl.to("#{sid}f",{{y:900,rotation:-14,duration:0.75,ease:"power2.in"}},{t_cae + 0.08:.3f});'
                  f'tl.to("#{sid}t",{{y:1000,rotation:-22,duration:0.8,ease:"power2.in"}},{t_cae + 0.15:.3f});'
                  f'tl.fromTo("#{sid}x",{{opacity:0,y:-60}},{{opacity:1,y:0,duration:0.3,ease:"back.out(2)"}},{t_cae + 0.7:.3f});')
        ev += [(t_cae + 0.05, "error"), (t_cae + 0.7, "boom")]
    return f'<div style="position:relative;width:800px;height:660px">{caja}<div style="position:absolute;top:100px">{svg}</div>{flecha}</div>'


def _bicicleta(e, sid, t0, t1, at, js, ev):
    """Migrar es una bicicleta con dos ruedas. Se dibuja, las ruedas giran solas;
    al decir que una falla, la de atrás se pone roja y se suelta, la bici se inclina y sale el aviso;
    luego vuelve a su sitio y cada rueda recibe su nombre al decirlo ("ruedas" + "rueda_frases").
    Claves (todas opcionales salvo la frase de la escena): ruedas, dos_frase, falla_frase, peligro_frase,
    peligro_texto, arregla_frase, rueda_frases, ok_frase."""
    r1, r2 = (html.escape(x) for x in e.get("ruedas", ["PAPELES", "TRABAJO"]))
    T = lambda k: at(e[k], t0 - 0.5) if e.get(k) else None
    t_dos, t_falla, t_pel, t_arr, t_ok = (T(k) for k in ("dos_frase", "falla_frase", "peligro_frase",
                                                         "arregla_frase", "ok_frase"))
    t_lab = [at(f, t0 - 0.5) if f else None for f in (e.get("rueda_frases") or [None, None])]
    aviso = html.escape(e.get("peligro_texto", "PROCESO EN PELIGRO"))
    R, CY, XA, XB = 118, 262, 190, 610   # radio, altura de los ejes, rueda de atrás y de delante

    def rueda(i, x):
        radios = "".join(f'<line x1="{x}" y1="{CY}" x2="{x + R * 0.86 * c:.1f}" y2="{CY + R * 0.86 * s:.1f}"/>'
                         for c, s in ((1, 0), (.5, .866), (-.5, .866), (-1, 0), (-.5, -.866), (.5, -.866)))
        return (f'<g id="{sid}w{i}"><circle id="{sid}n{i}" cx="{x}" cy="{CY}" r="{R}" fill="#151515" stroke="#fff" stroke-width="12"/>'
                f'<g id="{sid}r{i}" stroke="#6a6a6a" stroke-width="4">{radios}</g>'
                f'<circle cx="{x}" cy="{CY}" r="14" fill="var(--amarillo)" stroke="#000" stroke-width="4"/></g>')

    cuadro = [  # (de, a) del cuadro: vainas, sillín, barra, tubo diagonal, horquilla y manillar
        "M190 262 L385 272", "M385 272 L330 118", "M330 118 L190 262", "M330 118 L560 108",
        "M560 108 L385 272", "M560 108 L610 262", "M560 108 L548 70 L606 64", "M298 104 L362 104"]
    lineas = "".join(f'<path id="{sid}c{k}" d="{d}" pathLength="1"/>' for k, d in enumerate(cuadro))

    def etiqueta(i, x, txt):
        return (f'<g id="{sid}e{i}" opacity="0"><rect x="{x - 175}" y="404" width="350" height="78" rx="16" '
                f'fill="var(--amarillo)" stroke="#000" stroke-width="5"/>'
                f'<text x="{x - 22}" y="462" text-anchor="middle" font-family="Anton" font-size="54" fill="#000">{txt}</text>'
                f'<g id="{sid}k{i}" opacity="0"><circle cx="{x + 128}" cy="443" r="26" fill="#000"/>'
                f'<path d="M{x + 115} 444 l9 9 l17 -19" fill="none" stroke="var(--amarillo)" stroke-width="7" '
                f'stroke-linecap="round" stroke-linejoin="round"/></g></g>')

    svg = (f'<svg viewBox="0 0 800 490" style="width:800px;height:490px;overflow:visible">'
           f'<g id="{sid}b">{rueda(0, XA)}{rueda(1, XB)}'
           f'<g fill="none" stroke="#fff" stroke-width="12" stroke-linecap="round" stroke-linejoin="round">{lineas}</g>'
           f'<circle cx="385" cy="272" r="22" fill="#151515" stroke="var(--amarillo)" stroke-width="6"/></g>'
           f'<g id="{sid}x" opacity="0" stroke="#ff3b3b" stroke-width="16" stroke-linecap="round">'
           f'<path d="M{XA - 70} {CY - 70} l140 140M{XA + 70} {CY - 70} l-140 140"/></g>'
           f'{etiqueta(0, XA, r1)}{etiqueta(1, XB, r2)}</svg>')
    caja = (f'<div id="{sid}a" style="height:96px;display:flex;justify-content:center;align-items:center;opacity:0">'
            f'<div style="display:flex;align-items:center;gap:16px;font:66px/1 Anton,sans-serif;color:#fff;background:#d4261a;'
            f'border:6px solid #000;border-radius:16px;padding:10px 26px;box-shadow:0 8px 0 rgba(0,0,0,.4)">'
            f'<svg viewBox="0 0 24 24" style="width:58px;height:58px" fill="none" stroke="#fff" stroke-width="2.4" '
            f'stroke-linecap="round" stroke-linejoin="round">{ICONOS["alerta"]}</svg>{aviso}</div></div>')

    # dibujo: las ruedas entran con rebote (escalonadas) y el cuadro se traza encima
    js.append(f'gsap.set("#{sid}w0",{{svgOrigin:"{XA} {CY}"}});gsap.set("#{sid}w1",{{svgOrigin:"{XB} {CY}"}});'
              f'gsap.set("#{sid}r0",{{svgOrigin:"{XA} {CY}"}});gsap.set("#{sid}r1",{{svgOrigin:"{XB} {CY}"}});'
              f'gsap.set("#{sid}b",{{svgOrigin:"{XB} {CY + R}"}});'
              f'gsap.set("#{sid}e0",{{svgOrigin:"{XA} 443"}});gsap.set("#{sid}e1",{{svgOrigin:"{XB} 443"}});')
    for i in (0, 1):
        js.append(f'tl.fromTo("#{sid}w{i}",{{scale:0,opacity:0}},{{scale:1,opacity:1,duration:0.4,'
                  f'ease:"back.out(1.8)"}},{t0 + 0.05 + 0.15 * i:.3f});')
    js.append(f'tl.fromTo("#{sid}c0,#{sid}c1,#{sid}c2,#{sid}c3,#{sid}c4,#{sid}c5,#{sid}c6,#{sid}c7",'
              f'{{strokeDasharray:1,strokeDashoffset:1}},{{strokeDashoffset:0,duration:0.35,ease:"power2.out",'
              f'stagger:0.06}},{t0 + 0.3:.3f});')
    ev += [(t0 + 0.05, "whoosh"), (t0 + 0.2, "pop")]
    # micromovimiento: las ruedas giran todo el rato y la bici se mece un poco
    dur = max(0.5, t1 - t0)
    js.append(f'tl.to("#{sid}r0,#{sid}r1",{{rotation:{int(dur * 140)},duration:{dur:.2f},ease:"none"}},{t0:.3f});')
    vaiven = max(1, int(dur / 0.6))
    js.append(f'tl.to("#{sid}b",{{y:-6,duration:0.6,ease:"sine.inOut",yoyo:true,repeat:{vaiven}}},{t0 + 0.6:.3f});')
    if t_dos is not None:  # «dos ruedas»: las dos se encienden, una detrás de otra
        for i in (0, 1):
            js.append(f'tl.to("#{sid}n{i}",{{stroke:"#FFC800",duration:0.2}},{t_dos + 0.18 * i:.3f});'
                      f'tl.fromTo("#{sid}w{i}",{{scale:1}},{{keyframes:[{{scale:1.12,duration:0.14}},{{scale:1,duration:0.22}}],'
                      f'ease:"back.out(2)"}},{t_dos + 0.18 * i:.3f});')
            ev.append((t_dos + 0.18 * i, "tic"))
    if t_falla is not None:  # «falla»: la de atrás se pone roja y se suelta; la bici se inclina
        js.append(f'tl.to("#{sid}n0",{{stroke:"#ff3b3b",duration:0.15}},{t_falla:.3f});'
                  f'tl.to("#{sid}w0",{{x:-46,y:30,rotation:-24,duration:0.45,ease:"power2.in"}},{t_falla + 0.1:.3f});'
                  f'tl.to("#{sid}b",{{rotation:-7,duration:0.45,ease:"back.out(2)"}},{t_falla + 0.1:.3f});'
                  f'tl.fromTo("#{sid}x",{{opacity:0,scale:0.4}},{{opacity:1,scale:1,svgOrigin:"{XA} {CY}",duration:0.3,'
                  f'ease:"back.out(2.2)"}},{t_falla + 0.35:.3f});')
        ev += [(t_falla + 0.05, "error")]
    if t_pel is not None:
        js.append(f'tl.fromTo("#{sid}a",{{opacity:0,y:-60,scale:0.7}},{{opacity:1,y:0,scale:1,duration:0.35,'
                  f'ease:"back.out(2.2)"}},{t_pel:.3f});')
        ev.append((t_pel, "impacto"))
    if t_arr is not None:  # vuelve a su sitio: el aviso se va y la rueda se arregla
        js.append(f'tl.to("#{sid}a",{{opacity:0,y:-40,duration:0.25}},{t_arr:.3f});'
                  f'tl.to("#{sid}x",{{opacity:0,duration:0.2}},{t_arr:.3f});'
                  f'tl.to("#{sid}w0",{{x:0,y:0,rotation:0,duration:0.45,ease:"back.out(1.8)"}},{t_arr + 0.1:.3f});'
                  f'tl.to("#{sid}b",{{rotation:0,duration:0.45,ease:"back.out(1.8)"}},{t_arr + 0.1:.3f});'
                  f'tl.to("#{sid}n0",{{stroke:"#FFC800",duration:0.2}},{t_arr + 0.3:.3f});')
        ev.append((t_arr + 0.1, "whoosh"))
    for i, t in enumerate(t_lab):  # cada rueda recibe su nombre al decirlo
        if t is None:
            continue
        js.append(f'tl.fromTo("#{sid}e{i}",{{opacity:0,y:30,scale:0.6}},{{opacity:1,y:0,scale:1,duration:0.35,'
                  f'ease:"back.out(2)"}},{t - 0.05:.3f});')
        ev.append((t - 0.05, "pop"))
    if t_ok is not None:  # «innegociables»: las dos ruedas con su visto
        for i in (0, 1):
            js.append(f'tl.fromTo("#{sid}k{i}",{{opacity:0}},{{opacity:1,duration:0.2}},{t_ok + 0.15 * i:.3f});'
                      f'tl.fromTo("#{sid}e{i}",{{scale:1}},{{keyframes:[{{scale:1.1,duration:0.12}},{{scale:1,duration:0.2}}],'
                      f'ease:"back.out(2)"}},{t_ok + 0.15 * i:.3f});')
            ev.append((t_ok + 0.15 * i, "tic"))
    return f'<div style="position:relative;width:800px">{caja}{svg}</div>'


def _captura(e, sid, t0, t1, at, js, ev):
    """La web oficial dentro de una ventana: baja hasta la línea, la resalta y saca el dato.

    "imagen": "assets/capturas/boe.png"   (relativa al proyecto; de scripts/captura.py o hecha a mano)
    "resalta": "texto buscado con captura.py"  o, en una captura a mano, {"y": …, "h": …, "x"?: …, "w"?: …}
               en píxeles de la imagen (y "dpr": 2 si es de pantalla Retina)
    "baja_frase", "resalta_frase": cuándo baja y cuándo se marca (si no, poco después de entrar)
    "dato": {"texto": "PLAZO: 3 MESES", "frase": "…"}   pastilla con el dato, con rebote
    "dominio", "fecha": para la barra (si no, salen del .json de captura.py)
    Solo páginas oficiales y públicas, sin datos personales en pantalla."""
    import json
    import subprocess
    from pathlib import Path
    d = Path(e["_dir"])
    img = d / e["imagen"]
    if not img.exists():
        raise SystemExit(f"captura: no encuentro {img}")
    meta = img.with_suffix(".json")
    if meta.exists():
        info = json.loads(meta.read_text())
    else:  # captura a mano: el tamaño sale de la imagen
        wh = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=width,height", "-of", "csv=p=0", str(img)],
                            capture_output=True, text=True).stdout.strip().split(",")
        dpr = e.get("dpr", 1)
        info = {"ancho": int(wh[0]) / dpr, "alto": int(wh[1]) / dpr, "marcas": {}}
    alto = e.get("_alto", BOT - TOP)
    win_h = alto - (90 if e.get("dato") else 10)
    bar, borde = 58, 3
    vw = CW - 2 * borde
    vh = win_h - bar - 2 * borde
    k = vw / info["ancho"]
    hoja_h = info["alto"] * k
    r = e.get("resalta")
    if isinstance(r, str):
        if r not in info["marcas"]:
            raise SystemExit(f"captura: «{r}» no está en {meta.name} (hay: {', '.join(info['marcas']) or 'ninguna'}). "
                             f"Repite captura.py con --busca \"{r}\"")
        r = info["marcas"][r]
    domin = e.get("dominio", info.get("dominio", ""))
    fecha = e.get("fecha", info.get("fecha", ""))
    if fecha and len(fecha) == 10:  # 2026-11-04 → 4-nov-2026
        a, mm, dd = fecha.split("-")
        fecha = f"{int(dd)}-{'ene feb mar abr may jun jul ago sep oct nov dic'.split()[int(mm) - 1]}-{a}"
    marca = ""
    ty = 0.0
    tb = at(e["baja_frase"], t0 - 0.5) if e.get("baja_frase") else t0 + 0.7
    lineas = []
    if r:
        lineas = r.get("lineas") or [{"x": r.get("x", 0), "y": r["y"], "w": r.get("w", info["ancho"]), "h": r.get("h", 30)}]
        y_top = min(l["y"] for l in lineas)
        y_bot = max(l["y"] + l["h"] for l in lineas)
        cy = (y_top + y_bot) / 2 * k
        ty = max(0.0, min(cy - vh * 0.45, hoja_h - vh))
        px, py = 6, 2
        marca = "".join(f'<div class="marca" id="{sid}m{n}" style="left:{max(0, l["x"] * k - px):.1f}px;top:{l["y"] * k - py:.1f}px;'
                        f'width:{min(vw, l["w"] * k + 2 * px):.1f}px;height:{l["h"] * k + 2 * py:.1f}px"></div>'
                        for n, l in enumerate(lineas))
    dur_baja = min(1.6, max(0.7, ty / 700))
    tr = at(e["resalta_frase"], t0 - 0.5) if e.get("resalta_frase") else tb + dur_baja + 0.1
    # entra con rebote, micromovimiento lento (zoom suave) mientras está en pantalla
    js.append(f'tl.fromTo("#{sid}w",{{opacity:0,y:70,scale:0.94}},{{opacity:1,y:0,scale:1,duration:0.4,ease:"back.out(1.6)"}},{t0 + 0.03:.3f});'
              f'tl.to("#{sid}w",{{scale:1.025,duration:{max(0.5, t1 - t0 - 0.5):.2f},ease:"none"}},{t0 + 0.45:.3f});')
    if ty > 1:
        js.append(f'tl.fromTo("#{sid}h",{{y:0}},{{y:{-ty:.0f},duration:{dur_baja:.2f},ease:"power2.inOut"}},{tb:.3f});')
        ev.append((tb, "whoosh"))
    if marca:
        for n in range(len(lineas)):
            js.append(f'tl.fromTo("#{sid}m{n}",{{scaleX:0,opacity:0}},{{scaleX:1,opacity:1,duration:0.3,ease:"power2.out"}},'
                      f'{tr + 0.22 * n:.3f});')
        ev.append((tr, "tic"))
        # zoom a la línea para que se lea en el móvil (la página de ordenador es letra pequeña)
        x0 = min(l["x"] for l in lineas) * k
        x1 = max(l["x"] + l["w"] for l in lineas) * k
        z = max(1.0, min(e.get("zoom", 1.9), 0.92 * vw / max(1, x1 - x0 + 12)))
        if z > 1.05:
            cx = (x0 + x1) / 2
            dx = min(max(vw / 2 - cx, (vw - cx) * (1 - z)), cx * (z - 1))
            tz = tr + 0.22 * len(lineas) + 0.25
            js.append(f'gsap.set("#{sid}h",{{transformOrigin:"{cx:.0f}px {cy:.0f}px"}});'
                      f'tl.to("#{sid}h",{{scale:{z:.2f},x:{dx:.0f},duration:0.7,ease:"power3.inOut"}},{tz:.3f});')
            ev.append((tz, "subida"))
    dato = ""
    if e.get("dato"):
        dt = e["dato"]
        td = at(dt["frase"], t0 - 0.5) - 0.05 if dt.get("frase") else tr + 0.35
        dato = f'<div class="dato" id="{sid}d" style="top:{win_h - 38}px"><b>{html.escape(dt["texto"])}</b></div>'
        js.append(f'tl.fromTo("#{sid}d",{{opacity:0,y:40,scale:0.6}},{{opacity:1,y:0,scale:1,duration:0.35,ease:"back.out(2.2)"}},{td:.3f});')
        ev.append((td, "pop"))
    candado = '<svg viewBox="0 0 24 24"><rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/></svg>'
    return (f'<div class="pz-cap"><div class="win" id="{sid}w" style="height:{win_h}px">'
            f'<div class="bar"><i></i><i></i><i></i><div class="url">{candado}{html.escape(domin)}</div>'
            f'<div class="fecha">{"captura " + html.escape(fecha) if fecha else ""}</div></div>'
            f'<div class="vista" style="height:{vh}px"><div class="hoja" id="{sid}h">'
            f'<img src="{html.escape(e["imagen"])}" alt="">{marca}</div></div></div>{dato}</div>')


def _escanos(e, sid, t0, t1, at, js, ev):
    """Hemiciclo del Congreso: 350 escaños que se llenan partido a partido, de
    izquierda a derecha, con su contador; luego la raya de la mayoría y una pastilla con la suma.
    "partidos": [{"nombre", "escanos", "color"}] en orden de izquierda a derecha; los que falten hasta
    "total" (350) salen en gris como «Otros» en el sitio de "otros_pos" (índice, por defecto 1).
    Opcionales: "mayoria" (176), "suma": {"texto", "frase"}, "fuente" (línea pequeña debajo)."""
    import math
    total, mayoria = e.get("total", 350), e.get("mayoria", 176)
    partidos = [dict(p) for p in e["partidos"]]
    resto = total - sum(p["escanos"] for p in partidos)
    if resto < 0:
        raise SystemExit(f"pizarra escanos: los partidos suman más de {total}")
    if resto:
        partidos.insert(e.get("otros_pos", 1), {"nombre": "Otros", "escanos": resto, "color": "#7a7a7a"})
    # filas del hemiciclo: escaños por fila proporcionales al radio
    CX, CY, R0, R1, FILAS = 400, 440, 150, 385, 9
    radios = [R0 + (R1 - R0) * i / (FILAS - 1) for i in range(FILAS)]
    por_fila = [r / sum(radios) * total for r in radios]
    enteros = [int(x) for x in por_fila]
    for i in sorted(range(FILAS), key=lambda i: por_fila[i] - enteros[i], reverse=True)[:total - sum(enteros)]:
        enteros[i] += 1
    asientos = []
    for r, n in zip(radios, enteros):
        for k in range(n):
            a = math.pi * (1 - k / (n - 1)) if n > 1 else math.pi / 2
            asientos.append((a, r))
    asientos.sort(key=lambda s: (-s[0], s[1]))   # de izquierda a derecha
    puntos, i0 = [], 0
    for j, p in enumerate(partidos):
        for a, r in asientos[i0:i0 + p["escanos"]]:
            puntos.append(f'<circle class="{sid}p{j}" cx="{CX + r * math.cos(a):.1f}" cy="{CY - r * math.sin(a):.1f}" '
                          f'r="0" fill="{p["color"]}"/>')
        i0 += p["escanos"]
    raya = (f'<g id="{sid}m" opacity="0"><line x1="{CX}" y1="{CY - R1 - 34}" x2="{CX}" y2="{CY - R0 + 30}" stroke="#fff" '
            f'stroke-width="5" stroke-dasharray="14 10"/>'
            f'<text x="{CX}" y="{CY - R1 - 46}" text-anchor="middle" font-family="Anton" font-size="34" fill="#fff" '
            f'letter-spacing="2">MAYORÍA: {mayoria}</text></g>')
    svg = (f'<svg viewBox="0 0 800 470" style="width:800px;height:470px;overflow:visible">{"".join(puntos)}{raya}</svg>')
    nombres = [p for p in partidos if p["nombre"] != "Otros"]
    cont = "".join(f'<div id="{sid}c{j}" style="opacity:0;text-align:center"><div style="font:76px/1 Anton,sans-serif;'
                   f'color:{p["color"]};-webkit-text-stroke:3px #000;paint-order:stroke fill"><span id="{sid}n{j}">0</span></div>'
                   f'<div style="font:34px/1.1 Anton,sans-serif;color:#fff;letter-spacing:2px">{html.escape(p["nombre"].upper())}</div></div>'
                   for j, p in enumerate(partidos) if p["nombre"] != "Otros")
    filas = f'<div style="display:flex;justify-content:center;gap:70px;margin-top:6px">{cont}</div>'
    # cada partido entra en orden; el tiempo que tarda depende de sus escaños
    t, dur_total = t0 + 0.3, 2.4
    for j, p in enumerate(partidos):
        d = max(0.25, dur_total * p["escanos"] / total)
        js.append(f'tl.fromTo(".{sid}p{j}",{{attr:{{r:0}}}},{{attr:{{r:9.5}},duration:0.22,ease:"back.out(3)",'
                  f'stagger:{d / max(1, p["escanos"]):.4f}}},{t:.3f});')
        if p["nombre"] != "Otros":
            js.append(f'tl.fromTo("#{sid}c{j}",{{opacity:0,y:20}},{{opacity:1,y:0,duration:0.25,ease:"back.out(2)"}},{t:.3f});'
                      f'const {sid}k{j}={{v:0}};tl.fromTo({sid}k{j},{{v:0}},{{v:{p["escanos"]},duration:{d:.2f},ease:"power1.out",'
                      f'onUpdate:()=>{{document.getElementById("{sid}n{j}").textContent=Math.round({sid}k{j}.v)}}}},{t:.3f});')
            ev.append((t, "tic"))
        t += d + 0.1
    js.append(f'tl.fromTo("#{sid}m",{{opacity:0}},{{opacity:1,duration:0.3}},{t:.3f});')
    ev.append((t, "whoosh"))
    out = [f'<div style="position:relative;width:800px;height:620px"><div style="position:absolute;top:30px">{svg}</div>'
           f'<div style="position:absolute;top:470px;left:0;right:0">{filas}</div>']
    if e.get("suma"):
        ts = at(e["suma"]["frase"], t0 - 0.5) if e["suma"].get("frase") else t + 0.6
        ts = max(ts, t + 0.3)
        out.append(f'<div id="{sid}s" style="position:absolute;left:0;right:0;top:250px;display:flex;justify-content:center;opacity:0">'
                   f'<div style="font:78px/1 Anton,sans-serif;color:#000;background:var(--amarillo);border:6px solid #000;'
                   f'border-radius:18px;padding:12px 30px;box-shadow:0 10px 0 rgba(0,0,0,.45)">{html.escape(e["suma"]["texto"])}</div></div>')
        js.append(f'tl.fromTo("#{sid}s",{{opacity:0,scale:0.5,y:40}},{{opacity:1,scale:1,y:0,duration:0.35,ease:"back.out(2.2)"}},{ts:.3f});'
                  f'tl.to("#{sid}s",{{scale:1.04,duration:0.6,yoyo:true,repeat:{max(1, int((t1 - ts) / 0.6) - 1)},ease:"sine.inOut"}},{ts + 0.35:.3f});')
        ev.append((ts, "pop"))
    if e.get("fuente"):
        out.append(f'<div style="position:absolute;left:0;right:0;top:600px;text-align:center;font:400 26px/1.2 Oswald,sans-serif;'
                   f'color:#bdbdbd">{html.escape(e["fuente"])}</div>')
    return "".join(out) + "</div>"


def _foto(e, sid, t0, t1, at, js, ev):
    """Foto de apoyo de internet: una o varias fotos con licencia
    libre dentro de un marco; cada una entra en su frase y se acerca despacio (micromovimiento), con el
    crédito siempre visible abajo.

    "fotos": [{"imagen": "assets/fotos/x.jpg", "frase": "…", "credito": "Foto: Autor · CC BY-SA 4.0 · Wikimedia Commons",
               "foco": [50, 40]}]   foco: qué punto de la foto queda en el centro (en %), opcional
    "ante": "ANTETÍTULO"   (opcional, en amarillo encima)
    "dato": {"texto": "…", "frase": "…"}   pastilla amarilla con rebote debajo (opcional)
    Solo fotos con licencia que permita reutilizarlas (CC0, dominio público, CC BY, CC BY-SA; nunca NC ni ND);
    la ficha de cada una (autor, licencia, página) se guarda en assets/fotos/fuentes.json."""
    from pathlib import Path
    d = Path(e["_dir"])
    alto = e.get("_alto", BOT - TOP)
    arriba = 70 if e.get("ante") else 0
    abajo = 90 if e.get("dato") else 0
    fotos = e["fotos"]
    for f in fotos:
        if not (d / f["imagen"]).exists():
            raise SystemExit(f"foto: no encuentro {d / f['imagen']}")
        if not f.get("credito"):
            raise SystemExit(f"foto: {f['imagen']} sin «credito» (autor y licencia van en pantalla)")
    out = []
    if e.get("ante"):
        out.append(f'<div class="ante pz-ante" id="{sid}a">{html.escape(e["ante"])}</div>')
        _entra(js, f"#{sid}a", t0 + 0.05)
    imgs, creds = [], []
    tiempos = []
    for n, f in enumerate(fotos):
        ti = t0 + 0.05 if n == 0 or not f.get("frase") else at(f["frase"], t0) - 0.1
        tiempos.append(ti)
    for n, f in enumerate(fotos):
        ti = tiempos[n]
        tf = tiempos[n + 1] if n + 1 < len(fotos) else t1
        fx, fy = f.get("foco", [50, 50])
        imgs.append(f'<img id="{sid}f{n}" src="{html.escape(f["imagen"])}" alt="" style="object-position:{fx}% {fy}%">')
        creds.append(f'<div class="cred" id="{sid}c{n}">{html.escape(f["credito"])}</div>')
        if n == 0:
            js.append(f'tl.set("#{sid}f{n}",{{opacity:1}},{ti:.3f});tl.set("#{sid}c{n}",{{opacity:1}},{ti:.3f});')
        else:  # la siguiente entra encima con un pequeño empujón y la anterior se va
            js.append(f'tl.fromTo("#{sid}f{n}",{{opacity:0,scale:1.18,x:60}},{{opacity:1,scale:1.06,x:0,duration:0.45,ease:"back.out(1.4)"}},{ti:.3f});'
                      f'tl.to("#{sid}c{n - 1}",{{opacity:0,duration:0.15}},{ti:.3f});'
                      f'tl.to("#{sid}c{n}",{{opacity:1,duration:0.2}},{ti + 0.2:.3f});')
            ev.append((ti, "whoosh"))
        # micromovimiento: la foto se acerca despacio dentro del marco (el marco va más lento: parallax)
        z0 = 1.0 if n == 0 else 1.06
        js.append(f'tl.fromTo("#{sid}f{n}",{{scale:{z0}}},{{scale:{z0 + 0.09:.2f},duration:{max(0.6, tf - ti):.2f},ease:"none"}},'
                  f'{ti + (0 if n == 0 else 0.45):.3f});')
    # el marco entra con rebote y luego deriva un poco (más lento que la foto)
    js.append(f'tl.fromTo("#{sid}m",{{opacity:0,y:80,scale:0.9,rotation:-2}},{{opacity:1,y:0,scale:1,rotation:0,duration:0.45,ease:"back.out(1.6)"}},{t0 + 0.03:.3f});'
              f'tl.to("#{sid}m",{{scale:1.02,y:-8,duration:{max(0.5, t1 - t0 - 0.5):.2f},ease:"none"}},{t0 + 0.48:.3f});')
    out.append(f'<div class="marco" id="{sid}m" style="top:{arriba}px;height:{alto - arriba - abajo}px">'
               f'{"".join(imgs)}{"".join(creds)}</div>')
    if e.get("dato"):
        dt = e["dato"]
        td = at(dt["frase"], t0 - 0.5) - 0.05 if dt.get("frase") else t0 + 0.6
        out.append(f'<div class="dato" id="{sid}d" style="top:{alto - abajo - 38}px"><b>{html.escape(dt["texto"])}</b></div>')
        js.append(f'tl.fromTo("#{sid}d",{{opacity:0,y:40,scale:0.6}},{{opacity:1,y:0,scale:1,duration:0.35,ease:"back.out(2.2)"}},{td:.3f});')
        ev.append((td, "pop"))
    return f'<div class="pz-foto">{"".join(out)}</div>'


ESCENAS = {"foto": _foto, "escanos": _escanos, "diagrama": _diagrama, "titulo": _titulo, "iconos": _iconos, "lista": _lista, "movil": _movil,
           "campo": _campo, "numero": _numero, "curva": _curva, "evolucion": _evolucion,
           "mapa": _mapa, "balanza": _balanza, "captura": _captura, "bicicleta": _bicicleta}
