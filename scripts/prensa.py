"""Prensa: fotos con crédito y titulares con su fuente, apilados arriba (E-64).

Cuando se nombra a alguien o se cuenta algo que salió en prensa, caen arriba, uno encima de otro como papeles
sobre una mesa: una foto con licencia libre (con su pie y su crédito) o un titular real, con el medio y la fecha.
No se hacen capturas de periódicos: el titular se escribe aquí, palabra por palabra, y se cita la fuente.

Receta:
  "prensa": [{"frase": "ella es la alcaldesa", "hasta_frase": "y eso cambia",   (o "dur": 4.0)
              "items": [
                {"tipo": "foto", "frase": "ella es", "imagen": "assets/fotos/x.jpg", "foco": [50, 30],
                 "pie": "Nombre de la persona", "credito": "Foto: Autor · CC BY-SA 4.0 · Wikimedia Commons"},
                {"tipo": "titular", "frase": "lo publicaron", "medio": "EL DIARIO", "fecha": "17-ABR-2026",
                 "titular": "El titular tal cual salió…", "url": "https://…"}]}]
- Una foto solo con licencia que deje reutilizarla (CC0, dominio público, CC BY, CC BY-SA; nunca NC ni ND); su ficha
  (autor, licencia, página) va en assets/fotos/fuentes.json, y el crédito sale siempre en pantalla.
- Un titular tiene que ser el titular real (copiado de la página, sin cambiar palabras; si se recorta, con «…»),
  con su medio, su fecha y su "url" (para el caption y para comprobarlo). Hasta ~110 caracteres.
- Cada pieza entra con rebote al decir su frase; las de debajo se hunden un poco y se oscurecen (profundidad),
  la pila respira despacio mientras está en pantalla y al final todas salen volando hacia arriba, escalonadas.
- Ocupa la franja de arriba (y≈110-650): la tarjeta «Sígueme» baja si coincide.
"""
import html
from pathlib import Path

from efectos import _find, _norm

CSS = """
      .pr-pila { position: absolute; left: 0; top: 0; width: 1080px; height: 760px; z-index: 13; pointer-events: none; }
      .pr-item { position: absolute; left: 100px; top: 110px; width: 880px; opacity: 0; transform-origin: 50% 0%;
                 box-shadow: 0 26px 50px rgba(0,0,0,.55); }
      .pr-foto { background: #fff; padding: 14px 14px 0; border-radius: 10px; }
      .pr-foto .marco { position: relative; width: 852px; height: 430px; overflow: hidden; border-radius: 4px; background: #222; }
      .pr-foto .marco img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; transform-origin: 50% 40%; }
      .pr-foto .pie { display: flex; align-items: baseline; justify-content: space-between; gap: 18px; padding: 12px 6px 14px; }
      .pr-foto .pie b { font: 44px/1 "Anton", sans-serif; text-transform: uppercase; color: #111; white-space: nowrap; }
      .pr-foto .pie i { font: 400 19px/1.15 "Oswald", sans-serif; font-style: normal; color: #666; text-align: right; }
      .pr-tit { background: #f7f4ec; border-radius: 8px; padding: 22px 30px 26px; border-top: 12px solid #111;
                min-height: 340px; box-sizing: border-box; }
      .pr-tit .cab { display: flex; align-items: center; justify-content: space-between; gap: 16px;
                     border-bottom: 3px solid #111; padding-bottom: 12px; margin-bottom: 16px; }
      .pr-tit .cab b { font: 40px/1 "Anton", sans-serif; letter-spacing: .04em; color: #111; text-transform: uppercase; }
      .pr-tit .cab span { font: 600 24px/1 "Oswald", sans-serif; color: #fff; background: #d81e1e; padding: 7px 12px; border-radius: 4px; }
      .pr-tit .txt { font: 700 48px/1.14 Georgia, "Times New Roman", serif; color: #111; }
"""

GIROS = [-2.2, 1.6, -1.2, 2.0, -1.8]


def build_prensa(cfg, words, total, d):
    d = Path(d)
    seq = [(_norm(w["raw"]), w["t0"], w["t1"]) for w in words]

    def at(frase, after=0.0):
        i = _find(seq, frase, after)
        if i is None:
            raise SystemExit(f"prensa: no encuentro la frase «{frase}» (después de {after:.1f}s)")
        return seq[i][1]

    parts, js, ev, win = [], [], [], []
    for n, g in enumerate(cfg["prensa"]):
        t0 = max(0.0, at(g["frase"], g.get("despues_de", 0.0)) - g.get("antes", 0.1))
        t1 = at(g["hasta_frase"], t0) if g.get("hasta_frase") else t0 + g.get("dur", 4.0)
        t1 = min(t1, total)
        items = g["items"]
        if not items:
            raise SystemExit("prensa: un grupo sin «items»")
        caja, tiempos = [], []
        for k, it in enumerate(items):
            tk = t0 + 0.05 if k == 0 or not it.get("frase") else at(it["frase"], t0) - 0.1
            if tk >= t1 - 0.6:
                raise SystemExit(f"prensa: la pieza {k + 1} del grupo {n + 1} entra demasiado tarde ({tk:.2f}s, el grupo acaba en {t1:.2f}s)")
            tiempos.append(tk)
            pid = f"pr{n}_{k}"
            giro = it.get("giro", GIROS[k % len(GIROS)])
            dy = k * 18  # cada papel cae un poco más abajo que el anterior: se ve el canto de los de debajo
            if it.get("tipo") == "foto":
                if not (d / it["imagen"]).exists():
                    raise SystemExit(f"prensa: no encuentro {d / it['imagen']}")
                if not it.get("credito"):
                    raise SystemExit(f"prensa: {it['imagen']} sin «credito» (autor y licencia van en pantalla)")
                fx, fy = it.get("foco", [50, 40])
                cuerpo = (f'<div class="marco"><img id="{pid}i" src="{html.escape(it["imagen"])}" alt="" '
                          f'style="object-position:{fx}% {fy}%"></div><div class="pie"><b>{html.escape(it.get("pie", ""))}</b>'
                          f'<i>{html.escape(it["credito"])}</i></div>')
                cls = "pr-foto"
            elif it.get("tipo") == "titular":
                for c in ("medio", "fecha", "titular", "url"):
                    if not it.get(c):
                        raise SystemExit(f"prensa: titular sin «{c}» (se cita siempre medio, fecha y enlace)")
                if len(it["titular"]) > 120:
                    raise SystemExit(f"prensa: titular de {len(it['titular'])} caracteres; recórtalo con «…» (máx. 120)")
                cuerpo = (f'<div class="cab"><b>{html.escape(it["medio"])}</b><span>{html.escape(it["fecha"])}</span></div>'
                          f'<div class="txt">{html.escape(it["titular"])}</div>')
                cls = "pr-tit"
            else:
                raise SystemExit(f"prensa: tipo «{it.get('tipo')}» desconocido (foto o titular)")
            caja.append(f'<div class="pr-item {cls}" id="{pid}" style="top:{110 + dy}px;z-index:{k + 1}">{cuerpo}</div>')
            # entra con rebote desde arriba, girando, y se queda un poco ladeada
            js.append(f'tl.fromTo("#{pid}",{{opacity:0,y:-520,rotation:{giro * 4:.1f},scale:1.08}},'
                      f'{{opacity:1,y:0,rotation:{giro},scale:1,duration:0.5,ease:"back.out(1.5)"}},{tk:.3f});')
            ev += [(tk, "whoosh"), (tk + 0.38, "pop")]
            # las de debajo se hunden y se oscurecen (profundidad); una foto (más alta que un titular) se desvanece
            # cuando le cae un titular encima, para que no asome por debajo
            for j in range(k):
                hondo = k - j
                tapa = it.get("tipo") == "titular" and items[j].get("tipo") == "foto"
                js.append(f'tl.to("#pr{n}_{j}",{{scale:{1 - 0.04 * hondo:.2f},y:{-14 * hondo},'
                          f'filter:"brightness({max(0.45, 1 - 0.22 * hondo):.2f})",'
                          f'{"opacity:0," if tapa else ""}duration:0.4,ease:"power2.out"}},{tk + 0.12:.3f});')
            if it.get("tipo") == "foto":  # la foto se acerca despacio dentro de su marco (va más rápida que el papel)
                tf = tiempos[k] + max(0.8, t1 - tiempos[k])
                js.append(f'tl.fromTo("#{pid}i",{{scale:1}},{{scale:1.1,duration:{tf - tk:.2f},ease:"none"}},{tk:.3f});')
        parts.append(f'      <div class="clip pr-pila" id="prensa{n}" data-start="{t0:.3f}" data-duration="{t1 - t0:.3f}" '
                     f'data-track-index="{40 + n}">{"".join(caja)}</div>')
        # la pila respira (micromovimiento) y al final sale volando hacia arriba, de la de encima a la de abajo
        js.append(f'tl.fromTo("#prensa{n}",{{y:0}},{{y:-10,duration:{max(0.5, t1 - t0 - 0.5):.2f},ease:"sine.inOut"}},{t0:.3f});')
        if t1 < total - 0.3:  # si el grupo llega al final del vídeo, se queda quieto hasta el último fotograma
            ids = ", ".join(f'"#pr{n}_{k}"' for k in reversed(range(len(items))))
            js.append(f'tl.to([{ids}],{{y:-700,opacity:0,rotation:"+=8",duration:0.4,'
                      f'ease:"power2.in",stagger:0.06}},{t1 - 0.45:.3f});')
            ev.append((t1 - 0.4, "whoosh"))
        win.append((t0, t1))
        print(f"prensa: {len(items)} piezas de {t0:.2f}s a {t1:.2f}s")
    return CSS, "\n".join(parts), js, ev, win
