#!/usr/bin/env python3
"""Cierres que rotan: cada vídeo lleva en su receta un `"cierre"` y no se cierra siempre igual.

  "cierre": {"tipo": "conversacion", "pregunta": "¿Con qué perfil estás llegando tú?", "frase": "con qué perfil"}
  "cierre": {"tipo": "info", "pregunta": "¿Ya sabes qué vía es la tuya?"}
  "cierre": {"tipo": "<palabra en minúsculas>", "estilo": "caja" | "notificacion"}   (p. ej. "guia")
  ("cierre": "guia" también vale)

| tipo         | qué dices al final                                             | embudo |
| conversacion | pregunta concreta + «te leo en los comentarios»                | no     |
| info         | pregunta + «y si quieres información, dímelo ahí y te escribo» | no     |
| <palabra>    | «Comenta PALABRA y revisa tus mensajes»                        | sí     |

Las palabras son las de `marca/marca.json` → "palabras": solo las que tengas montadas en tu herramienta de
mensajes automáticos (ManyChat u otra). Si una palabra no está montada, nadie responde: no la uses.

Reglas: nunca el mismo cierre dos vídeos seguidos y como mucho 2 de embudo cada 7.
- En el vídeo: los cierres sin palabra sacan la caja «pregunta» (la pregunta escrita y «te leo en los comentarios»)
  en el sitio de los subtítulos mientras la dice. Los de embudo, la caja «Comenta» (o la notificación).
- En el caption: con embudo, la primera línea es la llamada; sin embudo, la primera línea es el gancho y la pregunta
  va al final.
- `"frase"`: dónde lo dice en el vídeo. Sin ella, sale justo antes de «Sígueme» (o del final).
Las recetas sin `"cierre"` sacan la caja «Comenta» con su palabra (o la de por defecto), o nada con `"comenta": false`.

  python3 scripts/cierre.py sugerir      → los últimos cierres entregados y cuál toca ahora
  python3 scripts/cierre.py guia         → cómo decir cada cierre al grabar
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kit  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def tipo_de(palabra):
    """ASESORÍA → asesoria: el tipo de cierre de una palabra."""
    return "".join(c for c in unicodedata.normalize("NFD", palabra.lower()) if unicodedata.category(c) != "Mn")


def _cierres():
    out = {
        "conversacion": {"palabra": None, "embudo": False, "pie": "TE LEO EN LOS COMENTARIOS 👇",
                         "caption": "{pregunta} Te leo en los comentarios 👇",
                         "dicho": "«¿…pregunta concreta…? Te leo en los comentarios.»",
                         "temas": "opinión, historias, mitos"},
        "info": {"palabra": None, "embudo": False, "campana": "INFO", "pie": "¿QUIERES INFO? DÍMELO AHÍ 📩",
                 "caption": "{pregunta} Te leo en los comentarios, y si quieres información, dímelo ahí y te escribo 📩",
                 "dicho": "«¿…pregunta…? Te leo en los comentarios. Y si quieres información, dímelo ahí y te escribo.»",
                 "temas": "temas generales"},
    }
    for palabra, v in kit.marca()["palabras"].items():
        v = v if isinstance(v, dict) else {}
        out[tipo_de(palabra)] = {"palabra": palabra, "embudo": v.get("embudo", True),
                                 "dicho": v.get("dicho", f"«Comenta {palabra} y revisa tus mensajes.»"),
                                 "temas": v.get("temas", ""), "rotacion": v.get("rotacion", True),
                                 **({"campana": v["campana"]} if v.get("campana") else {})}
    return out


CIERRES = _cierres()
EMBUDO_MAX, VENTANA = 2, 7


def de_receta(cfg):
    """El cierre de una receta como dict (tipo, palabra, embudo, pregunta, estilo, pie, frase), o None si no lleva."""
    c = cfg.get("cierre")
    if c is None:  # recetas antiguas: la caja «Comenta» de siempre
        km = cfg.get("comenta")
        rk = ((cfg.get("ranking") or {}).get("cta") or {}).get("palabra")
        if rk:
            return {"tipo": tipo_de(rk), "palabra": rk.upper(), "embudo": True, "antiguo": True}
        if km is False:
            return None
        km = km or {}
        palabra = (km.get("palabra") or kit.palabra_por_defecto() or "").upper()
        if not palabra:
            return None
        tipo = tipo_de(palabra)
        return {"tipo": tipo, "palabra": palabra, "embudo": True, "estilo": km.get("estilo", "caja"), "antiguo": True}
    if isinstance(c, str):
        c = {"tipo": c}
    tipo = c.get("tipo")
    if tipo not in CIERRES:
        raise SystemExit(f"cierre: «{tipo}» no existe ({', '.join(CIERRES)})")
    base = CIERRES[tipo]
    out = {**base, **c, "tipo": tipo, "palabra": base["palabra"], "embudo": base["embudo"]}
    if base["palabra"]:
        out.setdefault("estilo", "caja")
    else:
        out["estilo"] = "pregunta"
        p = (c.get("pregunta") or "").strip()
        if not p:
            raise SystemExit(f"cierre «{tipo}»: falta «pregunta» (una pregunta concreta, la que dices al final)")
        if len(p) > 70:
            raise SystemExit(f"cierre «{tipo}»: la pregunta pasa de 70 caracteres ({len(p)})")
        out["pregunta"] = p
    return out


def linea_caption(c):
    """La línea del caption que lleva el cierre sin palabra (va al final, antes de los hashtags)."""
    return CIERRES[c["tipo"]]["caption"].format(pregunta=c["pregunta"]) if c and not c["palabra"] else ""


def _entregas():
    """(proyecto, receta) de cada entrega en orden, la última al final."""
    filas = []
    f = ROOT / "proyectos/_entregas.md"
    for l in (f.read_text().splitlines() if f.exists() else []):
        cols = [x.strip() for x in l.strip().strip("|").split("|")]
        if len(cols) >= 5 and re.fullmatch(r"\d{4}-\d{2}-\d{2}", cols[0]):
            filas.append((cols[0], cols[3], cols[4], cols[5] if len(cols) > 5 else ""))
    return filas


def historial(n=VENTANA):
    out = []
    for fecha, proyecto, receta, publicado in _entregas()[-n:]:
        r = ROOT / "proyectos" / proyecto / "recetas" / receta
        try:
            if proyecto.startswith("carrusel "):  # los carruseles también cuentan: «cierre», o «cta» como la caja «Comenta»
                cfg = json.loads((ROOT / "carruseles" / proyecto.split(" ", 1)[1] / "carrusel.json").read_text())
                if "cierre" not in cfg:
                    cfg = {"comenta": False if cfg.get("cta") is False else cfg.get("cta") or {}}
                c = de_receta(cfg)
            else:
                c = de_receta(json.loads(r.read_text()))
        except (OSError, json.JSONDecodeError, SystemExit):
            c = None
        out.append((fecha, proyecto, c["tipo"] if c else "sin cierre", bool(c and c["embudo"]), publicado))
    return out


def libres(h=None):
    """(cierres que pueden ir ahora, el último, cuántos de embudo en la ventana). Lo usa también pedido.py."""
    h = historial() if h is None else h
    ultimos = [x[2] for x in h][-1:]  # regla: no repetir el último
    embudos = sum(x[3] for x in h)
    out = [t for t in CIERRES if t not in ultimos and CIERRES[t].get("rotacion", True)]
    if embudos >= EMBUDO_MAX:
        out = [t for t in out if not CIERRES[t]["embudo"]]
    return out, ultimos, embudos


def sugerir():
    h = historial()
    print(f"Últimas {len(h)} entregas (la de abajo, la más reciente):")
    for fecha, proyecto, tipo, embudo, publicado in h:
        print(f"  {fecha}  {proyecto:<22} {tipo:<12} {'embudo' if embudo else '      '}  {publicado}")
    libres_, ultimos, embudos = libres(h)
    if embudos >= EMBUDO_MAX:
        print(f"\nYa hay {embudos} de embudo en las últimas {len(h)}: toca un cierre sin palabra.")
    print(f"\nPuede ir ahora: {', '.join(libres_)} (no repite {', '.join(ultimos) or '—'}).")
    for t in libres_:
        print(f"  {t:<12} {CIERRES[t]['temas']}")


def guia():
    print("Cómo cerrar al grabar (dilo tal cual, al final, mirando a cámara):\n")
    for t, c in CIERRES.items():
        print(f"- {t:<12} {c['dicho']}   ({c['temas']})")
    print("\nLa pregunta, concreta y de tu tema: «¿Con qué perfil estás llegando tú?», «¿Tú qué harías en mi lugar?». No vale «¿qué opinas?».")


if __name__ == "__main__":
    {"sugerir": sugerir, "guia": guia}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: sys.exit(__doc__))()
