"""Elementos gráficos dinámicos reutilizables en cualquier receta.

- golpes: una palabra dicha se convierte en una palabra gigante en la zona de
  subtítulos (que se ocultan mientras dura); opcional blanco y negro del vídeo
  (énfasis) o tachado rojo. `"estilo": "alarma"` (25-oct-2026): aro rojo que se dibuja alrededor,
  temblor, destello rojo en los bordes y zumbido de error; admite "sub" (pastilla debajo), "cuenta"
  (el número sube hasta su valor) y "sonido" (error por defecto). `"estilo": "magia"` (31-oct-2026): destellos que
  estallan alrededor, brillo del vídeo y campanitas; con "tachado", la raya llega después.
- titulares: lluvia de titulares de prensa que caen alrededor de la persona: mitos, noticias, frases
  hechas. Cada uno con su etiqueta roja («ÚLTIMA HORA»); se quedan en los bordes, sin tapar la cara.
- movil: el vídeo entra dentro de un móvil con la interfaz de Reels; los subtítulos bajan debajo.
- camara: visor de cámara (REC que parpadea, esquinas, código de tiempo) y zoom lento hacia la cara.
- partidas: la pantalla se parte en dos un momento (p. ej. CIUDAD / PUEBLO), cada mitad con su dibujo arriba;
  mientras, el vídeo baja y se encoge un poco para que las tarjetas no tapen la cara ("baja": [y, escala]).
- chips: una pastilla por palabra (p. ej. países) que aparece al decirla, arriba.
- flotantes: tarjetas con icono (cursos, oficios, etapas) que entran girando en 3D al decirlas, flotan y se
  balancean mientras se habla de ellas y salen volando. "zona": "arriba" / "abajo"
  (cada mitad de la pantalla partida del reencuadre) o "cerrado" (primer plano); se colocan a los lados de la cara.
- conversacion: cuando alguien habla fuera de cámara, la charla sale como un chat:
  la voz de fuera en burbuja gris a la izquierda, la tuya en amarillo a la derecha; cada burbuja entra
  al decirse y los subtítulos se ocultan mientras tanto.
- sellos: nota grande tipo «5/10» en la zona de subtítulos (la usa el ranking).
- cierre (`scripts/cierre.py`): el cierre que rota. Con palabra (las de marca/marca.json → "palabras"), la caja
  «Comenta» de abajo; sin palabra (conversacion, info), la caja «pregunta» en el sitio de los subtítulos.
- comenta: caja de comentario que escribe la palabra activa (la "palabra_por_defecto" de marca/marca.json si la
  receta no dice otra; sin ninguna, no sale) + «revisa tus mensajes»; sale en todos los vídeos salvo
  `"comenta": false`. `"estilo": "notificacion"`: en vez de la caja, una notificación de iPhone arriba con tu foto,
  «tucuenta · ahora» y «Comenta PALABRA y revisa tus mensajes 📩»; mismo momento; espera a que acaben los logos y tarjetas de datos de arriba
  y, si no queda hueco, sale la caja.
Todo se ancla a la transcripción por frase; nada de tiempos a mano.
"""
import html
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kit  # noqa: E402

CSS = """
      .golpe {{ position: absolute; left: 0; width: 1080px; top: {GY}px; height: 300px; z-index: 12;
                display: flex; align-items: center; justify-content: center; pointer-events: none; }}
      .golpe span {{ position: relative; font: 190px/1 "Anton", sans-serif; text-transform: uppercase;
                     color: var(--amarillo); -webkit-text-stroke: 22px #000; paint-order: stroke fill;
                     text-shadow: 0 12px 0 rgba(0,0,0,.45); white-space: nowrap; }}
      .golpe.rojo span {{ color: #ff3b3b; }}
      .golpe .raya {{ position: absolute; left: -4%; right: -4%; top: 48%; height: 26px; background: #ff3b3b;
                      border: 6px solid #000; transform: rotate(-6deg); transform-origin: 0 50%; }}
      .golpe.alarma {{ height: 420px; top: {AY}px; }}
      .golpe.alarma .al-caja {{ position: relative; display: flex; flex-direction: column; align-items: center; gap: 14px; }}
      .golpe.alarma span {{ color: #fff; }}
      .golpe.alarma.rojo span {{ color: #ff3b3b; }}
      .golpe .al-aro {{ position: absolute; left: -16%; top: -75%; width: 132%; height: 250%; overflow: visible; }}
      .golpe .al-aro ellipse {{ fill: none; stroke: #ff2d2d; stroke-width: 15; stroke-linecap: round; }}
      .golpe .al-sub {{ font: 46px/1 "Anton", sans-serif; letter-spacing: .1em; color: #000; background: var(--amarillo);
                       border: 5px solid #000; padding: 10px 22px; border-radius: 12px; text-transform: uppercase; opacity: 0; }}
      .al-flash {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; z-index: 11; opacity: 0;
                  pointer-events: none; background: radial-gradient(closest-side, rgba(255,0,0,0) 60%, rgba(255,20,20,.6) 100%); }}
      .partida {{ position: absolute; left: 0; top: 0; width: 1080px; height: 640px; z-index: 10; pointer-events: none; overflow: hidden; }}
      .pt-lado {{ position: absolute; top: 0; width: 540px; height: 640px; display: flex; flex-direction: column;
                 align-items: center; padding-top: 150px; box-sizing: border-box; gap: 10px; }}
      .pt-a {{ left: 0; background: linear-gradient(180deg, rgba(20,34,66,.94) 0%, rgba(20,34,66,.7) 60%, rgba(20,34,66,0) 100%); }}
      .pt-b {{ left: 540px; background: linear-gradient(180deg, rgba(196,120,34,.94) 0%, rgba(196,120,34,.7) 60%, rgba(196,120,34,0) 100%); }}
      .pt-lado svg {{ width: 360px; height: 225px; }}
      .pt-lado b {{ font: 104px/1 "Anton", sans-serif; color: #fff; -webkit-text-stroke: 12px #000; paint-order: stroke fill; }}
      .pt-lado i {{ font: 56px/1 "Anton", sans-serif; font-style: normal; color: var(--amarillo); text-transform: uppercase;
                   -webkit-text-stroke: 8px #000; paint-order: stroke fill; }}
      .pt-raya {{ position: absolute; left: 526px; top: 0; width: 28px; height: 600px; background: #fff;
                 border-left: 6px solid #000; border-right: 6px solid #000; box-sizing: border-box; }}
      .cap {{ margin-top: var(--capdy, 0px); }}  /* GSAP pisa «translate» en los subtítulos */
      .flotantes {{ position: absolute; inset: 0; width: 1080px; height: 1920px; z-index: 13; pointer-events: none; perspective: 1100px; opacity: 0; }}
      .fl {{ position: absolute; width: 400px; box-sizing: border-box; padding: 18px 20px 16px; display: flex; gap: 16px; align-items: center;
             background: rgba(14,14,22,.86); border: 4px solid var(--amarillo); border-radius: 22px; opacity: 0;
             box-shadow: 0 18px 40px rgba(0,0,0,.55); transform-style: preserve-3d; }}
      .fl svg {{ flex: 0 0 76px; width: 76px; height: 76px; padding: 12px; box-sizing: border-box; border-radius: 16px; background: var(--amarillo);
                fill: none; stroke: #000; stroke-width: 2.4; stroke-linecap: round; stroke-linejoin: round; }}
      .fl b {{ display: block; font: 52px/1.02 "Anton", sans-serif; font-weight: 400; color: #fff; text-transform: uppercase; }}
      .fl i {{ display: block; margin-top: 6px; font: 29px/1.15 "Anton", sans-serif; font-style: normal; letter-spacing: .04em;
              color: var(--amarillo); text-transform: uppercase; }}
      .titulares {{ position: absolute; inset: 0; width: 1080px; height: 1920px; z-index: 9; pointer-events: none; overflow: hidden; }}
      .tz {{ position: absolute; max-width: 560px; padding: 16px 22px 14px; background: #f6f2e9; box-shadow: 0 10px 0 rgba(0,0,0,.35);
             border: 3px solid #111; font: 50px/1 "Anton", sans-serif; color: #111; text-transform: uppercase; white-space: nowrap; opacity: 0; }}
      .tz i {{ position: absolute; left: -3px; top: -30px; font: 24px/1 "Anton", sans-serif; font-style: normal; letter-spacing: .1em;
               color: #fff; background: #e2261b; padding: 6px 10px 5px; border: 3px solid #111; }}
      .tz.der {{ text-align: right; }}
      .tz.der i {{ left: auto; right: -3px; }}
      .mv-marco {{ position: absolute; inset: 0; width: 1080px; height: 1920px; z-index: 8; pointer-events: none; opacity: 0; }}
      .mv-hueco {{ position: absolute; border-radius: 46px; box-shadow: 0 0 0 1600px #0c1733, 0 0 0 14px #050505 inset; }}
      .mv-bisel {{ position: absolute; border-radius: 64px; border: 16px solid #0b0b0b; box-shadow: 0 0 0 3px #3a3a3a, 0 40px 80px rgba(0,0,0,.6); }}
      .mv-isla {{ position: absolute; width: 150px; height: 42px; border-radius: 21px; background: #000; }}
      .mv-ui {{ position: absolute; color: #fff; font-family: -apple-system, "Helvetica Neue", Arial, sans-serif; }}
      .mv-ui svg {{ width: 50px; height: 50px; fill: none; stroke: #fff; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;
                    filter: drop-shadow(0 2px 3px rgba(0,0,0,.5)); }}
      .mv-reels {{ font-size: 34px; font-weight: 700; text-shadow: 0 2px 6px rgba(0,0,0,.5); }}
      .mv-lado {{ display: flex; flex-direction: column; gap: 30px; align-items: center; font-size: 22px; font-weight: 600; }}
      .mv-user {{ display: flex; align-items: center; gap: 14px; font-size: 28px; font-weight: 700; text-shadow: 0 2px 6px rgba(0,0,0,.6); }}
      .mv-user img {{ width: 56px; height: 56px; border-radius: 50%; border: 2px solid #fff; object-fit: cover; }}
      .mv-user span.s {{ font-size: 22px; font-weight: 600; border: 2px solid #fff; border-radius: 10px; padding: 5px 12px; }}
      .mv-pie {{ font-size: 26px; text-shadow: 0 2px 6px rgba(0,0,0,.6); }}
      .mv-barra {{ position: absolute; height: 5px; background: rgba(255,255,255,.35); border-radius: 3px; overflow: hidden; }}
      .mv-barra b {{ display: block; height: 100%; width: 100%; background: #fff; transform-origin: 0 50%; }}
      .mv-titulo {{ position: absolute; left: 0; width: 1080px; text-align: center; font: 64px/1 "Anton", sans-serif; color: #fff;
                    text-transform: uppercase; }}
      .mv-titulo b {{ color: var(--amarillo); font-weight: 400; }}
      .camara {{ position: absolute; inset: 0; width: 1080px; height: 1920px; z-index: 9; pointer-events: none; opacity: 0;
                 font: 34px/1 "JetBrains Mono", Menlo, monospace; color: #fff; text-shadow: 0 2px 4px rgba(0,0,0,.6); }}
      .cm-esq {{ position: absolute; width: 90px; height: 90px; border: 0 solid #fff; filter: drop-shadow(0 2px 3px rgba(0,0,0,.5)); }}
      .cm-rec {{ position: absolute; left: 200px; top: 168px; display: flex; align-items: center; gap: 14px; font-weight: 700; }}
      .cm-rec i {{ width: 26px; height: 26px; border-radius: 50%; background: #ff2a2a; display: block; box-shadow: 0 0 12px #ff2a2a; }}
      .cm-tc {{ position: absolute; right: 200px; top: 168px; font-variant-numeric: tabular-nums; }}
      .cm-info {{ position: absolute; left: 200px; bottom: 330px; font-size: 26px; opacity: .9; }}
      .cm-bat {{ position: absolute; right: 200px; bottom: 328px; width: 64px; height: 30px; border: 3px solid #fff; border-radius: 6px; }}
      .cm-bat::after {{ content: ""; position: absolute; right: -10px; top: 7px; width: 6px; height: 10px; background: #fff; border-radius: 2px; }}
      .cm-bat b {{ position: absolute; left: 3px; top: 3px; bottom: 3px; width: 70%; background: #fff; border-radius: 2px; }}
      .cm-foco {{ position: absolute; border: 3px solid #fff; filter: drop-shadow(0 2px 3px rgba(0,0,0,.5)); }}
      .cm-cruz {{ position: absolute; left: 520px; top: 940px; width: 40px; height: 40px; }}
      .cm-cruz::before, .cm-cruz::after {{ content: ""; position: absolute; background: rgba(255,255,255,.8); }}
      .cm-cruz::before {{ left: 18px; top: 0; width: 4px; height: 40px; }}
      .cm-cruz::after {{ top: 18px; left: 0; height: 4px; width: 40px; }}
      .chips {{ position: absolute; left: {CL}px; width: {CW}px; top: {CY}px; z-index: 4;
                display: flex; flex-wrap: wrap; justify-content: center; gap: 16px; }}
      .chip {{ font: 52px/1 "Anton", sans-serif; text-transform: uppercase; color: #000; opacity: 0;
               background: var(--amarillo); border: 5px solid #000; border-radius: 40px; padding: 14px 28px;
               box-shadow: 0 8px 0 rgba(0,0,0,.35); }}
      .conv {{ position: absolute; left: 80px; width: 920px; z-index: 13; display: flex; flex-direction: column; gap: 22px; }}
      .cv {{ max-width: 720px; padding: 22px 32px 24px; border-radius: 40px; opacity: 0;
             font: 700 50px/1.12 -apple-system, "Helvetica Neue", Arial, sans-serif; box-shadow: 0 16px 40px rgba(0,0,0,.5); }}
      .cv i {{ display: block; margin-bottom: 8px; font: 700 24px/1 -apple-system, "Helvetica Neue", Arial, sans-serif;
               font-style: normal; letter-spacing: .12em; text-transform: uppercase; opacity: .7; }}
      .cv.fuera {{ align-self: flex-start; background: #2c2c2e; color: #fff; border-bottom-left-radius: 10px; }}
      .cv.yo {{ align-self: flex-end; background: var(--amarillo); color: #000; border-bottom-right-radius: 10px; }}
      .opciones {{ position: absolute; left: {CL}px; width: {CW}px; top: {OY}px; z-index: 4;
                   display: flex; align-items: center; justify-content: center; gap: 22px; }}
      .opc {{ position: relative; min-width: 250px; padding: 22px 30px; border-radius: 28px; text-align: center;
              border: 6px dashed var(--amarillo); background: rgba(0,0,0,.6);
              font: 74px/1 "Anton", sans-serif; color: #fff; text-transform: uppercase; opacity: 0; }}
      .opc .x {{ position: absolute; left: 6%; right: 6%; top: 46%; height: 14px; background: #ff3b3b;
                 border: 4px solid #000; transform: rotate(-8deg); transform-origin: 0 50%; opacity: 0; }}
      .opc-o {{ font: 64px/1 "Anton", sans-serif; color: var(--amarillo); -webkit-text-stroke: 8px #000;
                paint-order: stroke fill; opacity: 0; }}
      .seguir {{ position: absolute; left: {CL}px; width: {CW}px; top: {SY}px; z-index: 9;
                 display: flex; flex-direction: column; align-items: center; gap: 14px; }}
      .sg-ante {{ font: 38px/1 "Anton", sans-serif; letter-spacing: .3em; color: var(--amarillo);
                  -webkit-text-stroke: 7px #000; paint-order: stroke fill; opacity: 0; }}
      .sg-user {{ font: 96px/1 "Anton", sans-serif; color: #fff; -webkit-text-stroke: 14px #000;
                  paint-order: stroke fill; text-shadow: 0 8px 0 rgba(0,0,0,.45); white-space: nowrap; }}
      .sg-user .c {{ opacity: 0; }}
      .sg-user .at {{ color: var(--amarillo); }}
      .sg-redes {{ display: flex; gap: 22px; }}
      .sg-red {{ width: 104px; height: 104px; border-radius: 50%; background: #111; border: 5px solid var(--amarillo);
                 display: flex; align-items: center; justify-content: center; opacity: 0;
                 box-shadow: 0 8px 0 rgba(0,0,0,.4); }}
      .sg-red svg {{ width: 54px; height: 54px; fill: #fff; }}
      .seguir.abajo {{ top: 1226px; gap: 10px; }}
      .seguir.abajo .sg-ante {{ font-size: 30px; }}
      .seguir.abajo .sg-user {{ font-size: 74px; }}
      .seguir.abajo .sg-red {{ width: 84px; height: 84px; }}
      .seguir.abajo .sg-red svg {{ width: 44px; height: 44px; }}
      .comenta {{ position: absolute; left: {CL}px; width: {CW}px; top: {KY}px; z-index: 9;
                  display: flex; flex-direction: column; align-items: center; gap: 12px; }}
      .km-ante {{ font: 46px/1 "Anton", sans-serif; letter-spacing: .3em; color: var(--amarillo);
                  -webkit-text-stroke: 8px #000; paint-order: stroke fill; }}
      .km-caja {{ width: 100%; display: flex; align-items: center; gap: 18px; padding: 22px 26px; border-radius: 60px;
                  background: #fff; box-shadow: 0 10px 0 rgba(0,0,0,.35), 0 0 0 5px var(--amarillo); }}
      .km-caja .ph {{ flex: 1; font: 54px/1 "Anton", sans-serif; color: #111; letter-spacing: .04em; white-space: nowrap; }}
      .km-caja .ph .c {{ opacity: 0; }}
      .km-caja .ph .hint {{ color: #9a9a9a; }}
      .km-send {{ width: 80px; height: 80px; border-radius: 50%; background: #d9d9d9; flex: none;
                  display: flex; align-items: center; justify-content: center; }}
      .km-send svg {{ width: 46px; height: 46px; fill: none; stroke: #fff; stroke-width: 3;
                      stroke-linecap: round; stroke-linejoin: round; }}
      .km-dm {{ font: 50px/1 "Anton", sans-serif; text-transform: uppercase; color: #000; opacity: 0;
                background: var(--amarillo); border: 5px solid #000; border-radius: 40px; padding: 14px 28px;
                box-shadow: 0 8px 0 rgba(0,0,0,.35); }}
      .comenta.pq {{ top: {PY}px; }}
      .pq-caja {{ width: 100%; padding: 26px 34px 22px; border-radius: 44px; background: #fff; text-align: center;
                  box-shadow: 0 10px 0 rgba(0,0,0,.35), 0 0 0 5px var(--amarillo);
                  font-family: "Anton", sans-serif; line-height: 1.08; color: #111; }}
      .pq-caja .pw {{ display: inline-block; margin: 0 .12em; opacity: 0; }}
      .comenta.pq.abajo {{ top: {KY}px; gap: 10px; }}
      .comenta.pq .km-dm {{ font-size: 44px; white-space: nowrap; }}
      .sello {{ position: absolute; left: 0; width: 1080px; top: {GY}px; height: 300px; z-index: 12;
                display: flex; align-items: center; justify-content: center; }}
      .sello b {{ font: 230px/1 "Anton", sans-serif; color: var(--amarillo); -webkit-text-stroke: 24px #000;
                  paint-order: stroke fill; text-shadow: 0 14px 0 rgba(0,0,0,.45); }}
      .sello i {{ font: 110px/1 "Anton", sans-serif; font-style: normal; color: #fff; -webkit-text-stroke: 14px #000;
                  paint-order: stroke fill; margin: 70px 0 0 10px; }}
"""


# la notificación de «comenta»: solo se añade si la receta la pide
NOTI_CSS = """
      .noti {{ position: absolute; left: 44px; width: 992px; top: {y}px; z-index: 15; }}
      .nt-card {{ display: flex; align-items: center; gap: 22px; padding: 18px 28px; border-radius: 40px;
                  background: rgba(28,28,30,.86); backdrop-filter: blur(30px) saturate(1.6);
                  box-shadow: 0 18px 50px rgba(0,0,0,.45), inset 0 0 0 1.5px rgba(255,255,255,.12);
                  font-family: -apple-system, "SF Pro Text", "Helvetica Neue", Arial, sans-serif; color: #fff; }}
      .nt-ic {{ width: 92px; height: 92px; border-radius: 50%; flex: none; object-fit: cover;
                box-shadow: 0 0 0 4px var(--amarillo); }}
      .nt-txt {{ flex: 1; min-width: 0; }}
      .nt-top {{ display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 4px; }}
      .nt-top b {{ font-size: 36px; font-weight: 700; }}
      .nt-top span {{ font-size: 30px; color: rgba(255,255,255,.55); }}
      .nt-body {{ font-size: 38px; line-height: 1.25; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
      .nt-body em {{ display: inline-block; font-style: normal; font-weight: 800; color: #000; background: var(--amarillo);
                     border-radius: 12px; padding: 0 12px; }}
"""


CIUDAD_SVG = ('<svg viewBox="0 0 400 250"><g fill="#0a0f1c" stroke="#000" stroke-width="3">'
              '<rect x="10" y="110" width="60" height="140"/><rect x="75" y="40" width="70" height="210"/>'
              '<rect x="150" y="90" width="55" height="160"/><rect x="210" y="10" width="80" height="240"/>'
              '<rect x="295" y="70" width="50" height="180"/><rect x="350" y="130" width="45" height="120"/></g>'
              '<g fill="#ffc800">' + "".join(f'<rect x="{x}" y="{y}" width="10" height="14"/>'
                                            for x in (88, 118, 225, 255, 305) for y in (70, 110, 150, 190)) + '</g></svg>')
PUEBLO_SVG = ('<svg viewBox="0 0 400 250"><g fill="#5a2e0c" stroke="#000" stroke-width="3" stroke-linejoin="round">'
              '<path d="M20 250V170l45-35 45 35v80z"/><path d="M120 250V150l55-45 55 45v100z"/>'
              '<path d="M245 250V60l30-40 30 40v190z"/><path d="M315 250V180l40-30 40 30v70z"/></g>'
              '<path d="M275 0v18M266 9h18" stroke="#000" stroke-width="5"/>'
              '<g fill="#ffc800"><rect x="160" y="170" width="28" height="40" rx="14"/><rect x="265" y="90" width="20" height="34" rx="10"/></g></svg>')


MV_ICONOS = {
    "corazon": '<path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z"/>',
    "comenta": '<path d="M20 12a8 8 0 1 1-3.2-6.4A8 8 0 0 1 20 12z"/><path d="M20 12l1 5-5-1.5"/>',
    "envia": '<path d="M21 3L3 10.5l7 2.5 2.5 7z"/><path d="M10 13l11-10"/>',
    "mas": '<circle cx="5" cy="12" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/>',
    "camara": '<rect x="3" y="6" width="18" height="14" rx="3"/><circle cx="12" cy="13" r="4"/><path d="M9 6l1.5-2h3L15 6"/>',
}
# huecos de la lluvia de titulares: (x, y, giro, lado) alrededor de la cara, fuera de la zona de subtítulos
TZ_SITIOS = [(24, 330, -6, "izq"), (24, 250, 5, "der"), (30, 620, 4, "izq"), (30, 560, -5, "der"),
             (24, 1330, -4, "izq"), (24, 1430, 5, "der"), (40, 1580, 3, "izq"), (40, 820, -3, "der")]


def _norm(s):
    return re.sub(r"[^\wáéíóúüñ]", "", s.lower())


def _find(seq, frase, after=0.0):
    f = [_norm(x) for x in frase.split()]
    for i in range(len(seq) - len(f) + 1):
        if seq[i][1] >= after and [s for s, _, _ in seq[i:i + len(f)]] == f:
            return i
    return None


def hide_subs(js, t0, t1):
    js.append(f'tl.set("#root",{{"--subs":0}},{t0:.3f});tl.set("#root",{{"--subs":1}},{t1:.3f});')


def sello(n, t0, t1, valor, sobre, js, ev):
    """Nota grande «valor/sobre» que cae con golpe; devuelve el HTML."""
    hide_subs(js, t0, t1)
    js.append(f'tl.fromTo("#sello{n}",{{scale:2.4,opacity:0,rotation:-14}},{{scale:1,opacity:1,rotation:-6,'
              f'duration:0.16,ease:"power4.in"}},{t0:.3f});')
    for k, dx in enumerate([10, -8, 5, 0]):
        js.append(f'tl.set("#sello{n}",{{x:{dx}}},{t0 + 0.16 + 0.03 * k:.3f});')
    ev.append((t0 + 0.12, "impacto"))
    return (f'      <div class="clip sello" id="sello{n}" data-start="{t0:.3f}" data-duration="{t1 - t0:.3f}" '
            f'data-track-index="10"><b>{valor}</b><i>/{sobre}</i></div>')


def _alarma(n, g, t0, dur, cls, raya, px, parts, js, ev):
    """Golpe «alarma»: el texto entra de golpe, un aro rojo lo rodea, tiembla y los bordes destellan en rojo."""
    sub = f'<div class="al-sub" id="alsub{n}">{html.escape(g["sub"])}</div>' if g.get("sub") else ""
    texto = "0" if g.get("cuenta") is not None else html.escape(g["texto"])
    parts.append(f'      <div class="clip al-flash" id="alf{n}" data-start="{t0:.3f}" data-duration="{dur:.3f}" '
                 f'data-track-index="22"></div>')
    parts.append(f'      <div class="clip {cls} alarma" id="golpe{n}" data-start="{t0:.3f}" data-duration="{dur:.3f}" '
                 f'data-track-index="11"><div class="al-caja" id="alc{n}">'
                 f'<span style="font-size:{px}px"><b id="altx{n}" style="font-weight:400">{texto}</b>{raya}'
                 f'<svg class="al-aro" viewBox="0 0 100 100" preserveAspectRatio="none">'
                 f'<ellipse id="alaro{n}" cx="50" cy="50" rx="47" ry="44" pathLength="1" '
                 f'vector-effect="non-scaling-stroke" stroke-dasharray="1" stroke-dashoffset="1"/></svg></span>{sub}</div></div>')
    js.append(f'tl.fromTo("#golpe{n} span",{{scale:0.25,opacity:0}},{{scale:1,opacity:1,duration:0.2,'
              f'ease:"back.out(2.8)"}},{t0:.3f});')
    js.append(f'tl.fromTo("#alaro{n}",{{strokeDashoffset:1}},{{strokeDashoffset:0,duration:0.32,ease:"power2.out"}},{t0 + 0.12:.3f});')
    js.append(f'tl.fromTo("#alc{n}",{{x:-16,rotation:-1.5}},{{x:16,rotation:1.5,duration:0.05,repeat:7,yoyo:true,'
              f'ease:"none"}},{t0 + 0.14:.3f});tl.set("#alc{n}",{{x:0,rotation:0}},{t0 + 0.55:.3f});')
    js.append(f'tl.fromTo("#alf{n}",{{opacity:0}},{{opacity:1,duration:0.07,repeat:3,yoyo:true}},{t0 + 0.12:.3f});')
    if g.get("cuenta") is not None:
        v = g["cuenta"]
        js.append(f'const alv{n}={{v:0}};tl.fromTo(alv{n},{{v:0}},{{v:{v},duration:{g.get("cuenta_s", 0.6)},ease:"power2.out",'
                  f'onUpdate:()=>{{document.getElementById("altx{n}").textContent='
                  f'String(Math.round(alv{n}.v)).replace(/\\B(?=(\\d{{3}})+(?!\\d))/g,".")}}}},{t0:.3f});')
    if sub:
        js.append(f'tl.fromTo("#alsub{n}",{{opacity:0,y:20}},{{opacity:1,y:0,duration:0.22,ease:"back.out(2)"}},{t0 + 0.35:.3f});')
    if raya:
        js.append(f'tl.fromTo("#raya{n}",{{scaleX:0}},{{scaleX:1,duration:0.16,ease:"power3.out"}},{t0 + 0.5:.3f});')
        ev.append((t0 + 0.5, "whoosh"))
    js.append(f'tl.to("#golpe{n} span",{{scale:1.06,duration:{max(0.2, dur - 0.8):.2f},ease:"none"}},{t0 + 0.6:.3f});')
    ev += [(t0, "impacto"), (t0 + 0.12, g.get("sonido", "error"))]


def _momento(seq, x, nombre):
    """(t0, dur) de una pieza anclada a "frase" (o "t") con "dur" o "hasta_frase"."""
    if x.get("frase"):
        i = _find(seq, x["frase"], x.get("despues_de", 0.0))
        if i is None:
            raise SystemExit(f"{nombre}: no encuentro «{x['frase']}»")
        t0 = seq[i][1] - x.get("antes", 0.1)
    else:
        t0 = x.get("t", 0.0)
    if x.get("hasta_frase"):
        j = _find(seq, x["hasta_frase"], t0)
        if j is None:
            raise SystemExit(f"{nombre}: no encuentro «{x['hasta_frase']}»")
        return max(0.0, t0), seq[j][1] - max(0.0, t0)
    return max(0.0, t0), x.get("dur", 3.0)


def _titulares(n, tz, seq, parts, js, ev, cara=(540, 620)):
    """Lluvia de titulares: caen uno tras otro alrededor de la persona, cada uno a un hueco que no tape la cara."""
    t0, dur = _momento(seq, tz, "titulares")
    cx, cy = cara
    libres = list(TZ_SITIOS)
    items, sitios = [], []
    for it in tz["items"]:
        texto = it["texto"] if isinstance(it, dict) else it
        ancho = len(texto) * 50 * 0.47 + 50  # Anton 50 px ≈ 0,47 em por carácter, más el relleno
        for sitio in libres:
            x, y, _, lado = sitio
            izq, der = (x, x + ancho) if lado == "izq" else (1080 - x - ancho, 1080 - x)
            if not (y + 80 > cy - 180 and y < cy + 80 and der > cx - 160 and izq < cx + 160):
                items.append(it)
                sitios.append(sitio)
                libres.remove(sitio)
                break
    if len(items) < len(tz["items"]):
        print(f"titulares: {len(tz['items']) - len(items)} no caben sin tapar la cara; se quedan fuera")
    paso = min(0.35, max(0.12, (dur * 0.45) / max(len(items), 1)))
    caja = []
    for k, it in enumerate(items):
        x, y, giro, lado = sitios[k]
        texto = it["texto"] if isinstance(it, dict) else it
        etq = (it.get("etiqueta") if isinstance(it, dict) else None) or tz.get("etiqueta", "ÚLTIMA HORA")
        pos = f"left:{x}px" if lado == "izq" else f"right:{x}px"  # x: distancia al borde de su lado
        caja.append(f'<div class="tz {lado}" id="tz{n}_{k}" style="{pos};top:{y}px;transform:rotate({giro}deg)">'
                    f'<i>{html.escape(etq)}</i>{html.escape(texto)}</div>')
        tk = t0 + 0.05 + k * paso
        js.append(f'tl.fromTo("#tz{n}_{k}",{{opacity:0,y:-260,rotation:{giro * 3},scale:1.15}},{{opacity:1,y:0,'
                  f'rotation:{giro},scale:1,duration:0.32,ease:"back.out(1.7)"}},{tk:.3f});')
        ev.append((tk + 0.2, "pop"))
    parts.append(f'      <div class="clip titulares" id="titulares{n}" data-start="{t0:.3f}" data-duration="{dur:.3f}" '
                 f'data-track-index="27">{"".join(caja)}</div>')
    js.append(f'tl.to("#titulares{n} .tz",{{y:420,opacity:0,rotation:"+=12",duration:0.35,ease:"power2.in",stagger:0.04}},'
              f'{t0 + dur - 0.45:.3f});')
    ev.append((t0, "whoosh"))
    print(f"titulares: {len(items)} de {t0:.2f}s a {t0 + dur:.2f}s")


# Iconos de línea para las tarjetas flotantes (viewBox 24×24, trazo).
FL_ICONOS = {
    "codigo": "M8 6l-6 6 6 6M16 6l6 6-6 6",
    "grado": "M2 9l10-5 10 5-10 5zM6 11v5c3 2 9 2 12 0v-5",
    "reloj": "M12 3a9 9 0 1 0 .01 0M12 7v5l3 2",
    "lupa": "M10 4a6 6 0 1 0 .01 0M15 15l6 6",
    "salud": "M12 4v16M4 12h16",
    "herramienta": "M14.5 3.5a4 4 0 0 0 5 5l-10 10-3-3 10-10a4 4 0 0 0-2-2z",
    "tecnologia": "M3 5h18v11H3zM8 20h8M12 16v4",
    "barco": "M3 15l2 5h14l2-5zM6 15V9h12v6M12 4v5",
    "bici": "M5 14a3 3 0 1 0 .01 0M19 14a3 3 0 1 0 .01 0M5 17l4-8h6l4 8M9 9l3 8",
    "pausa": "M8 5v14M16 5v14",
    "dinero": "M3 7h18v10H3zM12 9a3 3 0 1 0 .01 0",
    "escudo": "M12 3l8 3v6c0 5-4 8-8 9-4-1-8-4-8-9V6z",
    "datos": "M4 20V10M10 20V4M16 20v-7M22 20H2",
    "instagram": "M7 3h10a4 4 0 0 1 4 4v10a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4V7a4 4 0 0 1 4-4zM12 8a4 4 0 1 0 .01 0M17.5 6.5h.01",
}
# Huecos (lado, distancia al borde, top) por zona, alternando lados para no tapar la cara.
FL_SITIOS = {
    "arriba": [("izq", 26, 150), ("der", 26, 330), ("izq", 26, 520), ("der", 26, 700)],
    "abajo": [("izq", 22, 1240), ("der", 22, 1430), ("izq", 22, 1620), ("der", 22, 1240)],
    "cerrado": [("izq", 26, 230), ("der", 26, 420), ("izq", 26, 610), ("der", 26, 230)],
}


def _flotantes(n, fl, seq, parts, js, ev):
    """Tarjetas flotantes: cada una entra girando al decirla, flota y se balancea en 3D; al final salen volando."""
    t0, dur = _momento(seq, fl, "flotantes")
    sitios = FL_SITIOS[fl.get("zona", "abajo")]
    caja, tk_prev = [], t0
    for k, it in enumerate(fl["items"]):
        i = _find(seq, it["frase"], max(t0 - 0.2, tk_prev - 0.2)) if it.get("frase") else None
        if it.get("frase") and i is None:
            raise SystemExit(f"flotantes: no encuentro «{it['frase']}»")
        tk = max(t0, seq[i][1] - 0.1) if i is not None else t0 + 0.15 * k
        tk_prev = tk
        lado, x, y = it.get("sitio") or sitios[k % len(sitios)]
        pos = f"left:{x}px" if lado == "izq" else f"right:{x}px"
        sub = f'<i>{html.escape(it["sub"])}</i>' if it.get("sub") else ""
        icono = FL_ICONOS.get(it.get("icono", "codigo"), FL_ICONOS["codigo"])
        ancho = f";width:{it['ancho']}px" if it.get("ancho") else ""  # p. ej. un nombre con su @
        caja.append(f'<div class="fl" id="fl{n}_{k}" style="{pos};top:{y}px{ancho}"><svg viewBox="0 0 24 24"><path d="{icono}"/></svg>'
                    f'<div><b>{html.escape(it["texto"])}</b>{sub}</div></div>')
        gira = -70 if lado == "izq" else 70
        js.append(f'tl.fromTo("#fl{n}_{k}",{{opacity:0,scale:0.35,rotationY:{gira},rotationX:20,y:40}},{{opacity:1,scale:1,'
                  f'rotationY:{-gira / 7:.0f},rotationX:0,y:0,duration:0.45,ease:"back.out(1.8)"}},{tk:.3f});')
        # flotar: subir y bajar y balancearse en 3D hasta que salen (repeticiones finitas: la línea de tiempo se puede rebobinar)
        resto = t0 + dur - 0.45 - (tk + 0.45)
        if resto > 0.5:
            per = 1.3 + 0.17 * k
            rep = max(0, int(resto / per) - 1)
            js.append(f'tl.to("#fl{n}_{k}",{{y:-16,rotationY:{gira / 6:.0f},rotationX:-7,duration:{per:.2f},ease:"sine.inOut",'
                      f'repeat:{rep},yoyo:true}},{tk + 0.45:.3f});')
        ev.append((tk, "whoosh"))
    parts.append(f'      <div class="clip flotantes" id="flotantes{n}" data-start="{t0:.3f}" data-duration="{dur:.3f}" '
                 f'data-track-index="28">{"".join(caja)}</div>')
    js.append(f'tl.set("#flotantes{n}",{{opacity:1}},{t0:.3f});')
    js.append(f'tl.to("#flotantes{n} .fl",{{opacity:0,scale:0.5,rotationY:90,y:-80,duration:0.35,ease:"power2.in",stagger:0.06,'
              f'overwrite:"auto"}},{t0 + dur - 0.45:.3f});')
    print(f"flotantes: {len(fl['items'])} de {t0:.2f}s a {t0 + dur:.2f}s ({fl.get('zona', 'abajo')})")


def _movil(n, mv, seq, cfg, parts, js, ev):
    """El vídeo se mete en un móvil con la interfaz de Reels; los subtítulos bajan por debajo del móvil."""
    t0, dur = _momento(seq, mv, "movil")
    s = mv.get("escala", 0.62)
    w, h = 1080 * s, 1920 * s
    x0, y0 = (1080 - w) / 2, mv.get("y", 250)
    r = 46  # radio de la pantalla, ya escalada
    ic = lambda k: f'<svg viewBox="0 0 24 24">{MV_ICONOS[k]}</svg>'
    avatar = mv.get("avatar", "assets/tarjetas/avatar-youtube.jpg")
    if cfg.get("_dir") and not (Path(cfg["_dir"]) / avatar).exists():  # la foto de perfil, desde marca/
        import shutil
        foto = Path(__file__).resolve().parent.parent / "marca/tarjetas/avatar-youtube.jpg"
        if not foto.exists():
            raise SystemExit("movil: falta tu foto de perfil en marca/tarjetas/avatar-youtube.jpg "
                             "(o pon \"avatar\": \"assets/…\" en la receta)")
        (Path(cfg["_dir"]) / avatar).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(foto, Path(cfg["_dir"]) / avatar)
    usuario = html.escape(mv.get("usuario", kit.usuario()).lstrip("@"))
    tit = ""
    if mv.get("titulo"):
        tit = (f'<div class="mv-titulo" id="mvt{n}" style="top:{y0 - 120:.0f}px">'
               + " ".join(f"<b>{html.escape(p)}</b>" if p in mv.get("acento", []) else html.escape(p)
                          for p in mv["titulo"].split(" ")) + "</div>")
    ui = (f'<div class="mv-hueco" style="left:{x0:.0f}px;top:{y0:.0f}px;width:{w:.0f}px;height:{h:.0f}px"></div>'
          f'<div class="mv-bisel" style="left:{x0 - 16:.0f}px;top:{y0 - 16:.0f}px;width:{w + 32:.0f}px;height:{h + 32:.0f}px"></div>'
          f'<div class="mv-isla" style="left:{540 - 75}px;top:{y0 + 22:.0f}px"></div>'
          f'<div class="mv-ui mv-reels" style="left:{x0 + 34:.0f}px;top:{y0 + 86:.0f}px">Reels</div>'
          f'<div class="mv-ui" style="left:{x0 + w - 84:.0f}px;top:{y0 + 78:.0f}px">{ic("camara")}</div>'
          f'<div class="mv-ui mv-lado" style="left:{x0 + w - 86:.0f}px;top:{y0 + h * 0.52:.0f}px">'
          f'<div>{ic("corazon")}</div><div>{ic("comenta")}</div><div>{ic("envia")}</div><div>{ic("mas")}</div></div>'
          f'<div class="mv-ui mv-user" style="left:{x0 + 30:.0f}px;top:{y0 + h - 190:.0f}px">'
          f'<img src="{avatar}" alt="">{usuario}<span class="s">Seguir</span></div>'
          f'<div class="mv-ui mv-pie" style="left:{x0 + 30:.0f}px;top:{y0 + h - 110:.0f}px;width:{w - 150:.0f}px">'
          f'{html.escape(mv.get("pie", ""))}</div>'
          f'<div class="mv-barra" style="left:{x0 + 24:.0f}px;top:{y0 + h - 30:.0f}px;width:{w - 48:.0f}px"><b id="mvb{n}"></b></div>')
    parts.append(f'      <div class="clip mv-marco" id="movil{n}" data-start="{t0:.3f}" data-duration="{dur:.3f}" '
                 f'data-track-index="28">{tit}{ui}</div>')
    clip = f'inset(0px 0px 0px 0px round {r / s:.1f}px)'
    capdy = y0 + h + 30 - cfg.get("_sub_top", 960)
    js.append(f'gsap.set("#video",{{transformOrigin:"0px 0px"}});tl.set("#root",{{"--capdy":"0px"}},0);')
    js.append(f'tl.fromTo("#movil{n}",{{opacity:0}},{{opacity:1,duration:0.2}},{t0 + 0.22:.3f});')  # cuando el vídeo ya casi está dentro
    js.append(f'tl.to("#video",{{x:{x0:.1f},y:{y0:.1f},scale:{s},clipPath:"{clip}",duration:0.4,ease:"power3.inOut"}},{t0:.3f});')
    # los subtítulos bajan un poco antes que el vídeo, para que nunca queden dentro de la pantalla del móvil
    js.append(f'tl.to("#root",{{"--capdy":"{capdy:.0f}px",duration:0.3,ease:"power2.inOut"}},{max(0.0, t0 - 0.25):.3f});')
    js.append(f'tl.fromTo("#mvb{n}",{{scaleX:0}},{{scaleX:1,duration:{dur:.3f},ease:"none"}},{t0:.3f});')
    if tit:
        js.append(f'tl.fromTo("#mvt{n}",{{opacity:0,y:-30}},{{opacity:1,y:0,duration:0.3,ease:"back.out(2)"}},{t0 + 0.3:.3f});')
    js.append(f'tl.to("#movil{n}",{{opacity:0,duration:0.25}},{t0 + dur - 0.3:.3f});')
    js.append(f'tl.to("#video",{{x:0,y:0,scale:1,clipPath:"inset(0px 0px 0px 0px round 0px)",duration:0.4,'
              f'ease:"power3.inOut"}},{t0 + dur - 0.35:.3f});')
    js.append(f'tl.to("#root",{{"--capdy":"0px",duration:0.4,ease:"power3.inOut"}},{t0 + dur - 0.35:.3f});')
    ev += [(t0, "whoosh"), (t0 + dur - 0.35, "whoosh")]
    print(f"movil: {t0:.2f}–{t0 + dur:.2f}s")


def _camara(n, cm, seq, cfg, parts, js, ev):
    """Visor de cámara: esquinas, REC que parpadea, código de tiempo que corre y zoom lento hacia la cara."""
    t0, dur = _momento(seq, cm, "camara")
    z = cm.get("zoom", 1.25)
    cx, cy = cfg.get("centro_cara", [540, 620])
    m, L, g = 80, 90, 7
    esq = "".join(f'<div class="cm-esq" style="{a}:{m}px;{b}:{m + (220 if b == "bottom" else 60)}px;'
                  f'border-{a}-width:{g}px;border-{b}-width:{g}px"></div>'
                  for a in ("left", "right") for b in ("top", "bottom"))
    fw, fh = 300, 340
    parts.append(f'      <div class="clip camara" id="camara{n}" data-start="{t0:.3f}" data-duration="{dur:.3f}" '
                 f'data-track-index="29">{esq}<div class="cm-rec"><i id="cmr{n}"></i>REC</div>'
                 f'<div class="cm-tc" id="cmtc{n}">00:00:00:00</div>'
                 f'<div class="cm-info">{html.escape(cm.get("info", "4K · 30 FPS · ISO 400"))}</div>'
                 f'<div class="cm-bat"><b></b></div><div class="cm-cruz"></div>'
                 f'<div class="cm-foco" id="cmf{n}" style="left:{cx - fw / 2:.0f}px;top:{cy - fh / 2:.0f}px;'
                 f'width:{fw}px;height:{fh}px"></div></div>')
    inicio = cm.get("tc_inicio", 12.0)  # segundos que marca el contador al empezar
    js.append(f'tl.fromTo("#camara{n}",{{opacity:0,scale:1.06}},{{opacity:1,scale:1,duration:0.25,ease:"power2.out"}},{t0:.3f});')
    js.append(f'tl.fromTo("#cmr{n}",{{opacity:1}},{{opacity:0.15,duration:0.45,repeat:{max(1, int(dur / 0.45))},'
              f'yoyo:true,ease:"steps(1)"}},{t0:.3f});')
    js.append(f'const cmt{n}={{v:{inicio}}};tl.fromTo(cmt{n},{{v:{inicio}}},{{v:{inicio + dur},duration:{dur:.3f},ease:"none",'
              f'onUpdate:()=>{{const v=cmt{n}.v,f=Math.floor((v%1)*30),s=Math.floor(v)%60,mi=Math.floor(v/60)%60,'
              f'p=x=>String(x).padStart(2,"0");document.getElementById("cmtc{n}").textContent="00:"+p(mi)+":"+p(s)+":"+p(f)}}}},{t0:.3f});')
    # el cuadro de enfoque busca la cara: se cierra y parpadea una vez
    js.append(f'tl.fromTo("#cmf{n}",{{scale:1.6,opacity:0}},{{scale:1,opacity:1,duration:0.35,ease:"power3.out"}},{t0 + 0.15:.3f});'
              f'tl.to("#cmf{n}",{{opacity:0.3,duration:0.08,repeat:3,yoyo:true}},{t0 + 0.5:.3f});'
              f'tl.to("#cmf{n}",{{borderColor:"#ffc800",duration:0.1}},{t0 + 0.8:.3f});')
    js.append(f'gsap.set("#video",{{transformOrigin:"0px 0px"}});')
    js.append(f'tl.to("#video",{{x:{cx * (1 - z):.1f},y:{cy * (1 - z):.1f},scale:{z},duration:{max(0.5, dur - 0.4):.3f},'
              f'ease:"power1.inOut"}},{t0:.3f});')
    js.append(f'tl.to("#camara{n}",{{opacity:0,duration:0.2}},{t0 + dur - 0.25:.3f});')
    js.append(f'tl.to("#video",{{x:0,y:0,scale:1,duration:0.3,ease:"power2.inOut"}},{t0 + dur - 0.3:.3f});')
    ev += [(t0, "tic"), (t0 + 0.8, "tic")]
    print(f"camara: {t0:.2f}–{t0 + dur:.2f}s (zoom ×{z})")


def _comentarios(n, cm, seq, cfg, parts, js, ev):
    """Comentarios públicos de seguidores: la captura real, con la foto difuminada y el nombre
    visible, entran una tras otra con un pop al decir la frase. Los ajustes de cada captura (recorte, foto,
    pública o DM) están en guiones/<guion>/comentarios.json; un DM nunca sale en tarjeta."""
    import json
    import subprocess
    root = Path(__file__).resolve().parent.parent
    g = root / "guiones" / cm["guion"]
    ajustes = {c["captura"]: c for c in json.loads((g / "comentarios.json").read_text())}
    capturas = cm.get("capturas") or [cm["captura"]]
    t0, dur = _momento(seq, cm, "comentarios")
    dst = Path(cfg.get("_dir", ".")) / "assets/comentarios"
    dst.mkdir(parents=True, exist_ok=True)
    ancho, y, hueco = cm.get("ancho", 940), cm.get("y", 230), 22
    imgs, alto = [], 0
    for k, cap in enumerate(capturas):
        aj = ajustes.get(cap)
        if not aj:
            raise SystemExit(f"comentarios: {cap} no está en {g.name}/comentarios.json")
        if aj.get("tipo") != "publico":
            raise SystemExit(f"comentarios: {cap} es un mensaje privado; un DM nunca sale en tarjeta")
        png = dst / f"c{n}_{k}.png"
        cmd = [kit.python_opencv(), str(root / "scripts/comentario.py"), str(g / cap), str(png)]
        for clave, nargs in (("recorte", 4), ("avatar", 3)):
            if aj.get(clave):
                cmd += [f"--{clave}", *map(str, aj[clave])]
        for t in aj.get("tapar", []):
            cmd += ["--tapar", *map(str, t)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode:
            raise SystemExit(f"comentarios: {r.stderr.strip() or r.stdout.strip()}")
        wh = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=width,height", "-of", "csv=p=0",
                             str(png)], capture_output=True, text=True).stdout
        w, h = (int(x) for x in wh.strip().split(",")[:2])
        imgs.append((png.name, h * ancho / w))
        alto += h * ancho / w + (hueco if k else 0)
    escala = min(1.0, cm.get("alto_max", 600) / alto)  # que nunca bajen hasta los subtítulos
    w_ = ancho * escala
    html_imgs = "".join(
        f'<img id="com{n}_{k}" src="assets/comentarios/{nombre}" style="display:block;width:{w_:.0f}px;'
        f'margin:{0 if k == 0 else hueco * escala:.0f}px auto 0;border-radius:26px;'
        f'border:2px solid rgba(255,255,255,.18);box-shadow:0 18px 50px rgba(0,0,0,.55);opacity:0">'
        for k, (nombre, _) in enumerate(imgs))
    parts.append(f'      <div class="clip comentarios" id="com{n}" data-start="{t0:.3f}" data-duration="{dur:.3f}" '
                 f'data-track-index="27" style="position:absolute;left:0;top:{y}px;width:1080px;opacity:0">{html_imgs}</div>')
    js.append(f'tl.set("#com{n}",{{opacity:1}},{t0:.3f});')
    for k in range(len(imgs)):
        tk = t0 + k * cm.get("cada", 0.45)
        js.append(f'tl.fromTo("#com{n}_{k}",{{opacity:0,scale:0.72,rotation:{-3 if k % 2 == 0 else 3},y:30}},'
                  f'{{opacity:1,scale:1,rotation:0,y:0,duration:0.35,ease:"back.out(1.8)"}},{tk:.3f});')
        ev.append((tk, "pop"))
    js.append(f'tl.to("#com{n}",{{opacity:0,y:-24,duration:0.3}},{t0 + dur - 0.3:.3f});')
    print(f"comentarios: {len(imgs)} captura(s) de {cm['guion']} {t0:.2f}–{t0 + dur:.2f}s")


def _conversacion(n, cv, seq, parts, js, ev):
    """Charla con alguien fuera de cámara como un chat: cada línea es una burbuja que entra al decirla
    ("quien": "fuera" a la izquierda, gris; "yo" a la derecha, amarilla). Los subtítulos se ocultan mientras."""
    burbujas, tiempos, t_prev = [], [], cv.get("despues_de", 0.0)
    for k, ln in enumerate(cv["lineas"]):
        i = _find(seq, ln["frase"], t_prev)
        if i is None:
            raise SystemExit(f"conversacion: no encuentro «{ln['frase']}»")
        tk = max(0.0, seq[i][1] - 0.1)
        t_prev = seq[i][1]
        quien = ln.get("quien", "fuera")
        etiqueta = ln.get("etiqueta", cv.get("etiqueta_fuera", "Fuera de cámara") if quien == "fuera" else "")
        etq = f"<i>{html.escape(etiqueta)}</i>" if etiqueta else ""
        burbujas.append(f'<div class="cv {quien}" id="cv{n}_{k}">{etq}{html.escape(ln["texto"])}</div>')
        tiempos.append((tk, quien))
    j = _find(seq, cv["lineas"][-1]["frase"], tiempos[-1][0])
    t_fin = seq[j + len(cv["lineas"][-1]["frase"].split()) - 1][2] + cv.get("queda", 1.0)
    t0 = tiempos[0][0]
    parts.append(f'      <div class="clip conv" id="conv{n}" data-start="{t0:.3f}" data-duration="{t_fin - t0:.3f}" '
                 f'data-track-index="26" style="top:{cv.get("y", 760)}px">{"".join(burbujas)}</div>')
    hide_subs(js, t0, t_fin)
    for k, (tk, quien) in enumerate(tiempos):
        dx = -60 if quien == "fuera" else 60
        js.append(f'tl.fromTo("#cv{n}_{k}",{{opacity:0,scale:0.6,x:{dx},y:24}},{{opacity:1,scale:1,x:0,y:0,duration:0.32,'
                  f'ease:"back.out(2)"}},{tk:.3f});')
        ev.append((tk, "pop"))
    # micromovimiento: la charla flota despacio mientras está en pantalla
    rep = max(0, int((t_fin - t0 - 0.6) / 1.6) - 1)
    js.append(f'tl.to("#conv{n}",{{y:-10,duration:1.6,ease:"sine.inOut",repeat:{rep},yoyo:true}},{t0:.3f});')
    js.append(f'tl.to("#conv{n} .cv",{{opacity:0,y:-30,duration:0.3,stagger:0.05,overwrite:"auto"}},{t_fin - 0.35:.3f});')
    print(f"conversacion: {len(tiempos)} burbujas de {t0:.2f}s a {t_fin:.2f}s")


def build_efectos(cfg, words, safe_l, cap_w, sub_top):
    seq = [(_norm(w["raw"]), w["t0"], w["t1"]) for w in words]
    cfg["_sub_top"] = sub_top
    css = CSS.format(GY=sub_top - 20, AY=sub_top - 80, CL=safe_l, CW=cap_w, CY=cfg.get("chips_y", 200), OY=cfg.get("opciones_y", 220),
                     SY=(cfg.get("seguir") or {}).get("y", 190),
                     KY=(cfg.get("comenta") or {}).get("y", 1232), PY=sub_top - 30)
    parts, js, ev = [], [], []
    bn_on = False
    base_f = cfg.get("video_filtro", "none")
    for n, g in enumerate(cfg.get("golpes", [])):
        i = _find(seq, g["frase"], g.get("despues_de", 0.0))  # «despues_de»: si la frase se dice dos veces
        if i is None:
            raise SystemExit(f"golpe: no encuentro «{g['frase']}»")
        t0, dur = seq[i][1], g.get("dur", 0.9)
        cls = "golpe rojo" if g.get("tachado") or g.get("rojo") else "golpe"
        raya = '<div class="raya" id="raya%d"></div>' % n if g.get("tachado") else ""
        # tamaño según el largo: Anton mide ~0,47 em por carácter en mayúsculas; caben ~960 px
        px = min(190, int(g.get("ancho", 960) / (max(len(g["texto"]), 1) * 0.47)))
        # «ancho» y «x»: el golpe se queda en una zona (p. ej. a la izquierda de la lista del ranking)
        caja = f' style="left:{g.get("x", (1080 - g["ancho"]) // 2)}px;width:{g["ancho"]}px"' if g.get("ancho") else ""
        if g.get("estilo") == "alarma":
            _alarma(n, g, t0, dur, cls, raya, min(px, 170), parts, js, ev)
            hide_subs(js, t0, t0 + dur)
            print(f"golpe alarma: {g['texto']} a {t0:.2f}s")
            continue
        parts.append(f'      <div class="clip {cls}" id="golpe{n}" data-start="{t0:.3f}" data-duration="{dur:.3f}"{caja} '
                     f'data-track-index="11"><span style="font-size:{px}px">{html.escape(g["texto"])}{raya}</span></div>')
        hide_subs(js, t0, t0 + dur)
        js.append(f'tl.fromTo("#golpe{n} span",{{scale:0.3,opacity:0}},{{scale:1,opacity:1,duration:0.18,'
                  f'ease:"back.out(2.6)"}},{t0:.3f});')
        if g.get("estilo") == "magia":
            # «magia»: destellos que estallan alrededor de la palabra, brillo del vídeo
            # y arpegio de campanitas; si va tachada, la raya llega después y rompe el hechizo
            import math
            chispas = "".join(
                f'<svg class="chispa" id="ch{n}_{k}" viewBox="0 0 24 24" style="position:absolute;left:50%;top:50%;'
                f'width:{56 + 22 * (k % 3)}px;height:{56 + 22 * (k % 3)}px;margin:-40px 0 0 -40px;opacity:0">'
                f'<path d="M12 1l2.6 8.4L23 12l-8.4 2.6L12 23l-2.6-8.4L1 12l8.4-2.6z" fill="{cfg.get("acento", "#FFC800") if k % 2 else "#fff"}"/></svg>'
                for k in range(12))
            parts[-1] = parts[-1].replace("</span></div>", f"</span>{chispas}</div>")
            for k in range(12):
                ang = 2 * math.pi * k / 12 + 0.3
                dx, dy = math.cos(ang) * (300 + 60 * (k % 3)), math.sin(ang) * (130 + 40 * (k % 2))
                js.append(f'tl.fromTo("#ch{n}_{k}",{{x:0,y:0,scale:0,rotation:0,opacity:0}},{{x:{dx:.0f},y:{dy:.0f},scale:1,opacity:1,'
                          f'rotation:{180 if k % 2 else -180},duration:0.5,ease:"power3.out"}},{t0 + 0.02 * k:.3f});')
                js.append(f'tl.to("#ch{n}_{k}",{{opacity:0,scale:0.2,duration:0.25}},{t0 + 0.52 + 0.02 * k:.3f});')
            js.append(f'tl.set("#video",{{filter:"brightness(1.3) saturate(1.25) contrast(1.05)"}},{t0:.3f});'
                      f'tl.set("#video",{{filter:"{base_f}"}},{t0 + 0.35:.3f});')
            ev.append((t0, "magia"))
        if raya:
            js.append(f'tl.fromTo("#raya{n}",{{scaleX:0}},{{scaleX:1,duration:0.18,ease:"power2.out"}},{t0 + (0.6 if g.get("estilo") == "magia" else 0.25):.3f});')
            ev.append((t0 + (0.6 if g.get("estilo") == "magia" else 0.25), "whoosh"))
        if g.get("bn"):
            bn_on = True
            js.append(f'tl.set("#video",{{filter:"grayscale(1) contrast(1.25)"}},{t0:.3f});'
                      f'tl.set("#video",{{filter:"{base_f}"}},{t0 + dur:.3f});')
        if g.get("estilo") != "magia":
            ev.append((t0, "impacto" if g.get("bn") else "pop"))
        print(f"golpe: {g['texto']} a {t0:.2f}s")
    if bn_on:
        js.insert(0, f'tl.set("#video",{{filter:"{base_f}"}},0);')

    for n, pt in enumerate(cfg.get("partidas", [])):
        i = _find(seq, pt["frase"], pt.get("despues_de", 0.0))
        if i is None:
            raise SystemExit(f"partida: no encuentro «{pt['frase']}»")
        t0, dur = seq[i][1] - 0.1, pt.get("dur", 1.6)
        lado = lambda k, dib: (f'<div class="pt-lado pt-{k}" id="pt{n}{k}">{dib}<b>{html.escape(pt[k])}</b>'
                               f'<i>{html.escape(pt.get(k + "_sub", ""))}</i></div>')
        parts.append(f'      <div class="clip partida" id="partida{n}" data-start="{t0:.3f}" data-duration="{dur:.3f}" '
                     f'data-track-index="23">{lado("a", CIUDAD_SVG)}{lado("b", PUEBLO_SVG)}'
                     f'<div class="pt-raya" id="pt{n}r"></div></div>')
        js.append(f'tl.fromTo("#pt{n}a",{{x:-540}},{{x:0,duration:0.24,ease:"power3.out"}},{t0:.3f});'
                  f'tl.fromTo("#pt{n}b",{{x:540}},{{x:0,duration:0.24,ease:"power3.out"}},{t0:.3f});'
                  f'tl.fromTo("#pt{n}r",{{scaleY:0}},{{scaleY:1,duration:0.2,ease:"power2.out"}},{t0 + 0.18:.3f});'
                  f'tl.fromTo("#pt{n}a b, #pt{n}b b",{{scale:0.3,opacity:0}},{{scale:1,opacity:1,duration:0.2,'
                  f'ease:"back.out(2.6)"}},{t0 + 0.2:.3f});'
                  f'tl.to("#pt{n}a",{{x:-540,duration:0.22,ease:"power2.in"}},{t0 + dur - 0.22:.3f});'
                  f'tl.to("#pt{n}b",{{x:540,duration:0.22,ease:"power2.in"}},{t0 + dur - 0.22:.3f});'
                  f'tl.to("#pt{n}r",{{opacity:0,duration:0.15}},{t0 + dur - 0.2:.3f});')
        by, bs = pt.get("baja", [300, 1.0])  # la cara baja por debajo de las tarjetas
        bx = 1080 * (1 - bs) / 2  # el vídeo escala desde su esquina (transformOrigin 0 0)
        js.append(f'gsap.set("#video",{{transformOrigin:"0px 0px"}});'
                  f'tl.to("#video",{{x:{bx:.1f},y:{by},scale:{bs},duration:0.28,ease:"power3.out"}},{t0:.3f});'
                  f'tl.to("#video",{{x:0,y:0,scale:1,duration:0.28,ease:"power3.inOut"}},{t0 + dur - 0.25:.3f});')
        ev += [(t0, "whoosh"), (t0 + 0.2, "impacto")]
        print(f"partida: {pt['a']} / {pt['b']} a {t0:.2f}s")

    for n, tz in enumerate(cfg.get("titulares", [])):
        _titulares(n, tz, seq, parts, js, ev, cfg.get("centro_cara", [540, 620]))
    for n, mv in enumerate(cfg.get("movil", [])):
        _movil(n, mv, seq, cfg, parts, js, ev)
    for n, cm in enumerate(cfg.get("camara", [])):
        _camara(n, cm, seq, cfg, parts, js, ev)
    for n, fl in enumerate(cfg.get("flotantes", [])):
        _flotantes(n, fl, seq, parts, js, ev)
    for n, cm in enumerate(cfg.get("comentarios", [])):
        _comentarios(n, cm, seq, cfg, parts, js, ev)
    for n, cv in enumerate(cfg.get("conversacion", [])):
        _conversacion(n, cv, seq, parts, js, ev)

    for n, c in enumerate(cfg.get("chips", [])):
        ids, t_first, t_end = [], None, None
        for k, item in enumerate(c["items"]):
            i = _find(seq, item["frase"], t_first or c.get("despues_de", 0.0))
            t0 = seq[i][1]
            t_first = t_first if t_first is not None else t0
            ids.append(f'<div class="chip" id="chip{n}_{k}">{html.escape(item["texto"])}</div>')
            js.append(f'tl.fromTo("#chip{n}_{k}",{{opacity:0,scale:0.4,y:-20}},{{opacity:1,scale:1,y:0,duration:0.22,'
                      f'ease:"back.out(2.4)"}},{t0:.3f});')
            ev.append((t0, "pop"))
            t_end = seq[i + len(item["frase"].split()) - 1][2]
        hasta = t_end + c.get("queda", 1.0)
        st = f' style="top:{c["y"]}px"' if c.get("y") else ""  # "y" propio del grupo
        parts.append(f'      <div class="clip chips" id="chips{n}"{st} data-start="{t_first:.3f}" '
                     f'data-duration="{hasta - t_first:.3f}" data-track-index="12">{"".join(ids)}</div>')
        cfg.setdefault("_arriba", []).append((t_first, hasta))  # la tarjeta «sígueme» no se pone encima
        print(f"chips: {len(c['items'])} de {t_first:.2f}s a {hasta:.2f}s")
    for n, o in enumerate(cfg.get("opciones", [])):
        i = _find(seq, o["pregunta_frase"])
        j = _find(seq, o["elige_frase"], seq[i][1]) if i is not None else None
        if i is None or j is None:
            raise SystemExit(f"opciones: no encuentro «{o['pregunta_frase']}» / «{o['elige_frase']}»")
        t0, te = seq[i][1], seq[j][1]
        hasta = te + o.get("queda", 2.0)
        gana, pierde = ("b", "a") if o["elige"] == "b" else ("a", "b")
        fs = 74 if len(o["a"]) + len(o["b"]) <= 14 else 54
        parts.append(f'      <div class="clip opciones" id="opc{n}" data-start="{t0:.3f}" data-duration="{hasta - t0:.3f}" '
                     f'data-track-index="13"><div class="opc" id="opc{n}a" style="font-size:{fs}px">{html.escape(o["a"])}<div class="x"></div></div>'
                     f'<div class="opc-o" id="opc{n}o">O</div>'
                     f'<div class="opc" id="opc{n}b" style="font-size:{fs}px">{html.escape(o["b"])}<div class="x"></div></div></div>')
        js.append(f'tl.fromTo("#opc{n}a",{{opacity:0,x:-60}},{{opacity:1,x:0,duration:0.25,ease:"back.out(2)"}},{t0:.3f});')
        js.append(f'tl.fromTo("#opc{n}o",{{opacity:0,scale:0.3}},{{opacity:1,scale:1,duration:0.2}},{t0 + 0.15:.3f});')
        js.append(f'tl.fromTo("#opc{n}b",{{opacity:0,x:60}},{{opacity:1,x:0,duration:0.25,ease:"back.out(2)"}},{t0 + 0.25:.3f});')
        js.append(f'tl.to("#opc{n}{pierde}",{{opacity:0.45,scale:0.85,duration:0.2}},{te:.3f});')
        # la raya solo en la que pierde (27-oct-2026: antes la de la ganadora se veía desde el principio)
        js.append(f'tl.fromTo("#opc{n}{pierde} .x",{{scaleX:0,opacity:1}},{{scaleX:1,opacity:1,duration:0.18}},{te:.3f});')
        js.append(f'tl.to("#opc{n}{gana}",{{scale:1.18,backgroundColor:"{cfg.get("acento", "#FFC800")}",color:"#000",borderStyle:"solid",'
                  f'borderColor:"#000",duration:0.22,ease:"back.out(3)"}},{te:.3f});')
        ev += [(t0, "pop"), (t0 + 0.25, "pop"), (te, "impacto")]
        print(f"opciones: {o['a']} / {o['b']} de {t0:.2f}s, elige {o[gana]} a {te:.2f}s")
    # tarjeta «sígueme»: automática en todos los vídeos salvo "seguir": false en la receta
    sg = cfg.get("seguir", {})
    if sg is not False:
        sg = {"frase": "sígueme", "usuario": kit.usuario(), "redes": list(kit.marca()["redes"]),
              "antetitulo": "SÍGUEME EN", **(sg or {})}
        i = _find(seq, sg["frase"], cfg.get("gancho", {}).get("hasta", 0) if cfg.get("gancho") else 0)
        total = cfg.get("_duracion") or (seq[-1][2] if seq else 0)
        # Sale en TODOS los vídeos: al decir «sígueme» o, si no lo dice, en los últimos segundos.
        t0 = seq[i][1] if i is not None else max(0.0, total - sg.get("final", 3.5))
        if total > 5:
            dur = total - t0 if total - t0 < 12 else sg.get("dur", 5.0)
            cfg["_seguir"] = (t0, t0 + dur)
            redes_dir = Path(__file__).resolve().parent.parent / "marca/redes"
            iconos = ""
            for k, r in enumerate(sg["redes"]):
                path = re.search(r'<path d="([^"]+)"', (redes_dir / f"{r}.svg").read_text()).group(1)
                iconos += f'<div class="sg-red" id="sgr{k}"><svg viewBox="0 0 24 24"><path d="{path}"/></svg></div>'
                js.append(f'tl.fromTo("#sgr{k}",{{opacity:0,scale:0.3,y:20}},{{opacity:1,scale:1,y:0,duration:0.22,'
                          f'ease:"back.out(2.6)"}},{t0 + 0.7 + k * 0.13:.3f});')
                ev.append((t0 + 0.7 + k * 0.13, "tic"))
            user = "".join(f'<span class="c{" at" if ch == "@" else ""}" id="sgc{m}">{html.escape(ch)}</span>'
                           for m, ch in enumerate(sg["usuario"]))
            for m in range(len(sg["usuario"])):
                js.append(f'tl.set("#sgc{m}",{{opacity:1}},{t0 + 0.1 + m * 0.03:.3f});')
            parts.append(f'      <div class="clip seguir" id="seguir" data-start="{t0:.3f}" data-duration="{dur:.3f}" '
                         f'data-track-index="14"><div class="sg-ante" id="sgante">{html.escape(sg["antetitulo"])}</div>'
                         f'<div class="sg-user">{user}</div><div class="sg-redes">{iconos}</div></div>')
            js.append(f'tl.fromTo("#sgante",{{opacity:0,y:10}},{{opacity:1,y:0,duration:0.2}},{t0:.3f});')
            js.append(f'tl.fromTo("#seguir",{{scale:0.85}},{{scale:1,duration:0.3,ease:"back.out(2)"}},{t0:.3f});')
            ev.append((t0, "pop"))
            print(f"seguir: {sg['usuario']} a {t0:.2f}s ({dur:.1f}s)")
    # caja «comenta PALABRA» (la llamada por defecto es la "palabra_por_defecto" de marca/marca.json).
    # Al decir «comenta»; si no lo dice, justo antes de la tarjeta «sígueme» (o del final si va con outro).
    km = cfg.get("comenta", {})
    rk_cta = (cfg.get("ranking") or {}).get("cta")
    total = cfg.get("_duracion") or (seq[-1][2] if seq else 0)
    if cfg.get("cierre") and not rk_cta and total > 12:  # cierres que rotan (scripts/cierre.py)
        from cierre import de_receta
        ci = de_receta(cfg)
        if not ci["palabra"]:
            _pregunta(ci, seq, total, cfg, parts, js, ev)
            return css, "\n".join(parts), js, ev
        km = {"palabra": ci["palabra"], "frase": ci.get("frase", "comenta"),
              **({"estilo": "notificacion"} if ci.get("estilo") == "notificacion" else {}),
              **{k: ci[k] for k in ("dur", "y", "ante", "aviso") if k in ci}}
        # una palabra puede traer su propia caja en marca/marca.json → "palabras": {"CONSULTA": {"caja":
        # {"ante": "ESCRIBE", "aviso": "📩 Te escribo"}}} (para las que se «escriben» en vez de «comentar»)
        pv = kit.marca()["palabras"].get(ci["palabra"].upper())
        for k, v in ((pv.get("caja") or {}) if isinstance(pv, dict) else {}).items():
            km.setdefault(k, v)
    if km is not False and not rk_cta and total > 12:
        km = {"palabra": kit.palabra_por_defecto(), "frase": "comenta", "dur": 5.5, "aviso": "📩 Revisa tus mensajes", **(km or {})}
        if not km["palabra"]:
            print("comenta: sin palabra (marca/marca.json no tiene ninguna y la receta no dice cuál) → sin caja")
            km = False
    if km is not False and not rk_cta and total > 12:
        i = _find(seq, km["frase"], cfg.get("gancho", {}).get("hasta", 0) if cfg.get("gancho") else 0)
        # si lo dice, sale entera aunque coincida con «sígueme» (una va abajo y la otra arriba);
        # si no lo dice, va justo antes de «sígueme» (o del final)
        fin = cfg["_seguir"][0] if cfg.get("_seguir") else total
        t0 = seq[i][1] if i is not None else max(0.0, fin - km["dur"])
        dur = min(km["dur"], total - t0) if i is not None else min(km["dur"], fin - t0)
        palabra = km["palabra"].upper()
        if km.get("estilo") == "notificacion":
            extra = _notificacion(km, palabra, t0, dur, total, cfg, parts, js, ev)
            if extra is not None:
                return css + extra, "\n".join(parts), js, ev
            # sin hueco arriba: la caja de siempre, para que la llamada no se pierda
        chars = "".join(f'<span class="c" id="kmc{m}">{html.escape(ch)}</span>' for m, ch in enumerate(palabra))
        parts.append(f'      <div class="clip comenta" id="comenta" data-start="{t0:.3f}" data-duration="{dur:.3f}" '
                     f'data-track-index="15"><div class="km-ante">{html.escape(km.get("ante", "COMENTA"))}</div><div class="km-caja"><div class="ph"><span class="hint" id="kmhint">'
                     f'Añade un comentario…</span>{chars}</div><div class="km-send" id="kmsend"><svg viewBox="0 0 24 24">'
                     f'<path d="M12 19V5M5 12l7-7 7 7"/></svg></div></div>'
                     f'<div class="km-dm" id="kmdm">{html.escape(km["aviso"])}</div></div>')
        js.append(f'tl.fromTo("#comenta",{{opacity:0,y:40}},{{opacity:1,y:0,duration:0.35,ease:"back.out(2)"}},{t0:.3f});')
        tt = t0 + 0.9  # deja leer «Añade un comentario…» antes de escribir
        js.append(f'tl.set("#kmhint",{{display:"none"}},{tt:.3f});')
        for m in range(len(palabra)):
            js.append(f'tl.set("#kmc{m}",{{opacity:1}},{tt + m * 0.12:.3f});')
            ev.append((tt + m * 0.12, "tic"))
        ts = tt + len(palabra) * 0.12 + 0.35
        js.append(f'tl.set("#kmsend",{{backgroundColor:"#0095f6"}},{ts:.3f});')
        js.append(f'tl.fromTo("#kmsend",{{scale:1.3}},{{scale:1,duration:0.25,ease:"back.out(3)"}},{ts:.3f});')
        js.append(f'tl.fromTo("#kmdm",{{opacity:0,scale:0.5}},{{opacity:1,scale:1,duration:0.25,ease:"back.out(2.4)"}},{ts + 0.25:.3f});')
        ev += [(t0, "pop"), (ts, "pop"), (ts + 0.25, "whoosh")]
        cfg["_comenta"] = (t0, t0 + dur)
        print(f"comenta: {palabra} a {t0:.2f}s ({dur:.1f}s)")
    return css, "\n".join(parts), js, ev


def _pregunta(ci, seq, total, cfg, parts, js, ev):
    """Cierre sin palabra: la pregunta escrita en una caja blanca, en el sitio de los subtítulos mientras la dices,
    y debajo «te leo en los comentarios» (o «¿quieres información? dímelo ahí»)."""
    i = _find(seq, ci["frase"], 0) if ci.get("frase") else None
    if ci.get("frase") and i is None:
        raise SystemExit(f"cierre: no encuentro la frase «{ci['frase']}»")
    fin = cfg["_seguir"][0] if cfg.get("_seguir") else total
    dur = ci.get("dur", 6.0)
    t0 = seq[i][1] - 0.1 if i is not None else max(0.0, fin - dur)
    dur = min(dur, total - t0)
    p = ci["pregunta"]
    # si la dices, va en el sitio de los subtítulos (que se ocultan); si no, abajo, más pequeña y sin tocarlos
    dicha = i is not None
    px = (64 if len(p) <= 28 else 56 if len(p) <= 48 else 48) if dicha else (52 if len(p) <= 28 else 46 if len(p) <= 48 else 40)
    palabras_ = p.split()
    pw = "".join(f'<span class="pw" id="pqw{k}">{html.escape(w)}</span>' for k, w in enumerate(palabras_))
    ante = f'<div class="km-ante">{html.escape(ci.get("ante", "TU TURNO"))}</div>' if dicha else ""
    parts.append(f'      <div class="clip comenta pq{"" if dicha else " abajo"}" id="comenta" data-start="{t0:.3f}" '
                 f'data-duration="{dur:.3f}" data-track-index="15">{ante}'
                 f'<div class="pq-caja" style="font-size:{px}px">{pw}</div>'
                 f'<div class="km-dm" id="kmdm">{html.escape(ci.get("pie") or "")}</div></div>')
    js.append(f'tl.fromTo("#comenta",{{opacity:0,y:40,scale:0.9}},{{opacity:1,y:0,scale:1,duration:0.4,ease:"back.out(2)"}},{t0:.3f});')
    for k in range(len(palabras_)):  # las palabras entran escalonadas, al ritmo de lectura
        js.append(f'tl.fromTo("#pqw{k}",{{opacity:0,y:18}},{{opacity:1,y:0,duration:0.22,ease:"back.out(2)"}},{t0 + 0.25 + 0.09 * k:.3f});')
    tp = t0 + 0.25 + 0.09 * len(palabras_) + 0.2
    js.append(f'tl.fromTo("#kmdm",{{opacity:0,scale:0.5}},{{opacity:1,scale:1,duration:0.28,ease:"back.out(2.4)"}},{tp:.3f});')
    js.append(f'tl.to("#comenta",{{y:-8,duration:{max(0.5, dur - 1.2):.3f},ease:"sine.inOut"}},{t0 + 0.6:.3f});')
    # la pregunta va en el sitio de los subtítulos: se ocultan mientras está en pantalla
    if dicha:
        js.append(f'tl.to("#root",{{"--subs":0,duration:0.15}},{t0:.3f});tl.to("#root",{{"--subs":1,duration:0.15}},{t0 + dur:.3f});')
    ev += [(t0, "pop"), (tp, "whoosh")]
    cfg["_comenta"] = (t0, t0 + dur)
    print(f"cierre: {ci['tipo']} «{p}» a {t0:.2f}s ({dur:.1f}s)")


def _notificacion(km, palabra, t0, dur, total, cfg, parts, js, ev):
    """La llamada «Comenta» como notificación de iPhone arriba.

    Tu foto de perfil como icono (marca/canal.json y marca/tarjetas/), sin logos de WhatsApp ni de Instagram: son marcas.
    Arriba ya salen los logos y las tarjetas de datos: si coincide con uno, espera a que termine.
    Si coincide con «sígueme», la tarjeta baja (se apunta en "_arriba")."""
    import json
    import shutil
    raiz = Path(__file__).resolve().parent.parent
    ocupado = sorted(cfg.get("_ocupado_arriba", []))
    for a, b in ocupado:
        if a < t0 + dur and t0 < b:
            t0 = b + 0.15
    dur = min(dur, total - t0)
    if dur < 2.5:
        print(f"comenta (notificación): sin hueco libre arriba a {t0:.2f}s → caja de siempre")
        return None
    canal = raiz / "marca/canal.json"
    avatar = json.loads(canal.read_text())["youtube"]["avatar"] if canal.exists() else None
    if not avatar or not (raiz / "marca/tarjetas" / avatar).exists():
        print("comenta (notificación): falta tu foto (marca/canal.json → youtube.avatar, en marca/tarjetas/) → caja de siempre")
        return None
    dst = Path(cfg.get("_dir", ".")) / "assets"
    dst.mkdir(parents=True, exist_ok=True)
    shutil.copy2(raiz / "marca/tarjetas" / avatar, dst / f"noti-{avatar}")
    usuario = km.get("usuario", kit.usuario(False)).lstrip("@")
    antes, _, despues = km.get("texto", "Comenta {palabra} y revisa tus mensajes 📩").partition("{palabra}")
    cuerpo = f'{html.escape(antes)}<em id="ntw">{html.escape(palabra)}</em>{html.escape(despues)}'
    parts.append(f'      <div class="clip comenta noti" id="comenta" data-start="{t0:.3f}" data-duration="{dur:.3f}" '
                 f'data-track-index="15"><div class="nt-card" id="ntc"><img class="nt-ic" src="assets/noti-{avatar}">'
                 f'<div class="nt-txt"><div class="nt-top"><b>{html.escape(usuario)}</b><span>ahora</span></div>'
                 f'<div class="nt-body">{cuerpo}</div></div></div></div>')
    # baja desde fuera de la pantalla con rebote, la palabra late, flota un poco y vuelve a subir
    js.append(f'tl.fromTo("#ntc",{{y:-320,opacity:1}},{{y:0,duration:0.5,ease:"back.out(1.5)"}},{t0:.3f});')
    tp = t0 + 0.9
    js.append(f'tl.fromTo("#ntw",{{scale:1}},{{scale:1.18,duration:0.16,yoyo:true,repeat:1,ease:"power2.out"}},{tp:.3f});')
    js.append(f'tl.fromTo("#ntc",{{rotation:0}},{{rotation:0.6,duration:0.9,yoyo:true,repeat:{max(0, int((dur - 2.0) / 0.9))},'
              f'ease:"sine.inOut"}},{t0 + 0.6:.3f});')
    js.append(f'tl.to("#ntc",{{y:-320,duration:0.35,ease:"power2.in"}},{t0 + dur - 0.35:.3f});')
    ev += [(t0, "pop"), (tp, "tic")]
    cfg["_comenta"] = (t0, t0 + dur)
    sg = cfg.get("_seguir")
    if sg and sg[0] < t0 + dur and t0 < sg[1]:
        cfg["_seguir_abajo"] = True  # «sígueme» baja aunque haya pizarra: arriba está la notificación
    print(f"comenta (notificación): {palabra} a {t0:.2f}s ({dur:.1f}s)")
    return NOTI_CSS.format(y=km.get("y", 150))
