#!/usr/bin/env python3
"""Texto que acompaña a cada vídeo entregado: mismo nombre que el .mp4, en .txt.

  python3 scripts/textos.py MI_VIDEO --receta proyectos/MI_VIDEO/recetas/golpe.json [--salida x.txt]
  python3 scripts/textos.py MI_VIDEO --receta … --borrador    → crea proyectos/<VIDEO>/caption.md con huecos
  python3 scripts/textos.py MI_VIDEO --receta … --comprobar   → huecos y reglas del caption.md

Lo escribe `entregar.py --usar-muestra` junto al vídeo en la carpeta de entregas. Sin --salida, lo imprime (para revisarlo).

Las palabras de «Comenta» salen de `marca/marca.json` → "palabras". Cada una admite, además de "aviso" y "temas":
  "promesa": lo que promete la primera línea del caption («te mando la guía.»; si no, sale del "aviso"),
  "para":    qué recibe quien la escribe, para las reglas de otra IA (si no, "temas" o "aviso"),
  "verbo":   «Comenta» (por defecto) o «Escribe» (también si su "dicho" dice «Escribe PALABRA»).
Y la marca, "hashtag_fijo" (p. ej. "#tumarca"): el hashtag que va siempre; sin él, los 5 son del tema.
Una receta puede llevar "cuenta_sigueme" ("@otracuenta") para que el primer comentario invite a seguir otra cuenta
(p. ej. la de un podcast en sus shorts); "cuentas_por_outro" en marca.json ({"trozo del outro": "@cuenta"}) lo hace
solo para los shorts que llevan ese outro.

caption.md (fase 2, 25-oct-2026) se escribe en el paso 7 de /editor, antes de la página de revisión, desde
`subtitulos/recetas/plantillas/caption.md`: `--borrador` pone lo fijo (la línea «Comenta…» con su promesa, el
cierre del episodio, las reglas de la portada 9:16) y deja huecos «__ASI__» para lo propio del vídeo, como las
recetas. `revision.py` lo enseña como pieza p00 y no publica la página si quedan huecos.
Lleva, en este orden:
- el contexto (quién habla, de dónde sale), de «## Contexto» en caption.md o de `"contexto"` en la receta;
- el caption y el prompt de portada, si existen en `proyectos/<VIDEO>/caption.md` (secciones «## Caption» y
  «## Portada»; los escribe Claude y los aprueba el creador en la página de revisión);
- el primer comentario, si caption.md lleva «## Primer comentario»: lo publica el creador justo después de
  subir el reel y lo fija; abre la conversación y, en los shorts de un episodio, dice cómo encontrarlo en YouTube
  (en Instagram los enlaces de un comentario no se pueden pulsar; la @ sí, por eso acaba siempre con
  «Sígueme en @tucuenta para…»). Sigue las mismas reglas de palabras que el caption;
- las reglas de la casa para otra IA (palabra activa, «revisa tus mensajes», tu @), para que el caption
  que haga no use una palabra que nadie responde;
- la transcripción limpia (nombre y correcciones de whisper aplicados), con el gancho de frase cortada aparte
  cuando el vídeo sale de un montaje con «impacto» (si no, la frase aparecería dos veces);
- los datos con tarjeta y su fuente.
"""
import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import kit  # noqa: E402
from subtitulos import apply_fixes, fix_name, load_words  # noqa: E402

OUTRO_EPISODIO = f"El episodio completo en mi canal de YouTube, {kit.usuario()}."


def _palabras_activas():
    """Las palabras de «Comenta» de marca.json → {PALABRA: {"para", "promesa", "verbo"}}."""
    out = {}
    for p, v in kit.marca()["palabras"].items():
        v = v if isinstance(v, dict) else {}
        aviso = kit.aviso_palabra(p)
        escribe = re.search(r"\bEscribe\s+" + re.escape(p) + r"\b", v.get("dicho", ""))
        out[p] = {"para": v.get("para") or v.get("temas") or aviso,
                  "promesa": v.get("promesa") or (aviso[:1].lower() + aviso[1:]).rstrip(".") + ".",
                  "verbo": v.get("verbo") or ("Escribe" if escribe else "Comenta")}
    return out


PALABRAS_ACTIVAS = _palabras_activas()
PLANTILLA_CAPTION = ROOT / "subtitulos/recetas/plantillas/caption.md"
# Instagram cuenta como mucho 5 hashtags por post o reel desde el 18-dic-2025 (anuncio de @creators;
# Social Media Today, 18-dic-2025). Si la marca tiene un hashtag fijo, va siempre: quedan 4 para el tema.
HASHTAGS_MAX = 5
HASHTAG_FIJO = kit.marca().get("hashtag_fijo") or ""
HASHTAG_RE = re.compile(r"(?:^|\s)(#\w+)")
HUECO = re.compile(r"__[A-ZÁÉÍÓÚÑ0-9_]+\??__")


def palabras(d):
    if not (d / "palabras.json").exists():  # sin transcripción el vídeo se entrega igual; el texto lo dice
        return []
    words, _ = fix_name(load_words(d / "palabras.json"))
    apply_fixes(words)
    return words


def gancho_de(video):
    """Duración del gancho si el vídeo sale de un montaje que arranca con la frase cortada + «impacto»."""
    m = ROOT / "proyectos/_montajes" / f"{video}.json"
    if not m.exists():
        return 0.0
    tramos = json.loads(m.read_text()).get("tramos", [])
    if len(tramos) > 1 and tramos[1].get("entrada") == "impacto":
        return tramos[0]["a"] - tramos[0]["de"]
    return 0.0


def prosa(words):
    """Palabras → párrafos legibles: uno nuevo tras una pausa larga si el actual ya es largo, o al acabar
    una frase si ya es muy largo (sin silencios recortados apenas quedan pausas)."""
    pars, cur, prev = [], [], None
    for w in words:
        pausa = prev is not None and w["t0"] - prev > 0.9 and len(cur) >= 25
        fin_frase = cur and re.search(r"[.?!]$", cur[-1]) and len(cur) >= 55
        if cur and (pausa or fin_frase):
            pars.append(cur); cur = []
        cur.append(w["raw"]); prev = w["t1"]
    if cur:
        pars.append(cur)
    out = []
    for p in pars:
        t = " ".join(p)
        t = re.sub(r"\s+([,.;:?!])", r"\1", t)
        t = arroba(t)
        t = re.sub(r"(^|[.?!]\s+)([a-záéíóúñ])", lambda m: m.group(1) + m.group(2).upper(), t)
        if not re.search(r"[.?!…]$", t):
            t += "."
        out.append(t)
    return out


def _sin_tildes(s):
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


def arroba(t):
    """«arroba Nombre Apellido» dicho en voz alta → tu @ (si las palabras juntas, sin tildes, son tu usuario)."""
    u = _sin_tildes(kit.usuario(False))
    for n in (3, 2, 1):
        t = re.sub(r"\b[Aa]rroba" + r"\s+(\w+)" * n + r"\b",
                   lambda m: kit.usuario() if _sin_tildes("".join(m.groups())) == u else m.group(0), t)
    return t


def secciones(md):
    """Secciones «## Nombre» de caption.md → {nombre en minúsculas: texto}."""
    out, cur, buf = {}, None, []
    for linea in md.splitlines():
        m = re.match(r"##\s+(.+?)\s*$", linea)
        if m:
            if cur:
                out[cur] = "\n".join(buf).strip()
            cur, buf = m.group(1).lower(), []
        elif cur:
            buf.append(linea)
    if cur:
        out[cur] = "\n".join(buf).strip()
    return out


def palabra_de(cfg):
    """La palabra de «Comenta» que dice el vídeo, o None si no lleva caja (o si su cierre no pide palabra)."""
    if cfg.get("cierre"):
        from cierre import de_receta
        return de_receta(cfg)["palabra"]
    km = cfg.get("comenta")
    rk = ((cfg.get("ranking") or {}).get("cta") or {}).get("palabra")  # el ranking lleva su propia caja
    return (rk or "").upper() or (None if km is False else
                                  ((km or {}).get("palabra") or kit.palabra_por_defecto() or "").upper() or None)


def linea_cta(palabra):
    """Primera línea del caption; nunca con una palabra que nadie responde."""
    if not palabra:
        return ""
    cta = palabra if palabra in PALABRAS_ACTIVAS else kit.palabra_por_defecto()
    if not cta:
        return ""
    v = PALABRAS_ACTIVAS[cta]
    return f"{v['verbo']} {cta} y revisa tus mensajes: {v['promesa']}"


def linea_pregunta(ci):
    from cierre import linea_caption
    return linea_caption(ci)


def cierre_de(cfg):
    from cierre import de_receta
    return de_receta(cfg) if cfg.get("cierre") else None


def cuenta_de(cfg):
    """La cuenta que se etiqueta al final del primer comentario: la tuya, o la que diga la receta
    ("cuenta_sigueme") o marca.json para los shorts con cierto outro ("cuentas_por_outro")."""
    if cfg.get("cuenta_sigueme"):
        return "@" + cfg["cuenta_sigueme"].lstrip("@")
    outro = str(cfg.get("outro", ""))
    for trozo, cuenta in (kit.marca().get("cuentas_por_outro") or {}).items():
        if trozo and trozo in outro:
            return "@" + cuenta.lstrip("@")
    return kit.usuario()


def linea_sigueme(cfg):
    cuenta = cuenta_de(cfg)
    if cuenta != kit.usuario():
        return f"Síguenos en {cuenta} para __POR_QUE_SEGUIRNOS__."
    return f"Sígueme en {cuenta} para __POR_QUE_SEGUIRME__."


def borrador(video, receta, forzar=False):
    """caption.md desde la plantilla: lo fijo puesto, lo propio del vídeo como huecos. Devuelve las pistas."""
    d = ROOT / "proyectos" / video
    cap = d / "caption.md"
    if cap.exists() and not forzar:
        sys.exit(f"{video}: ya hay caption.md; rellena sus huecos o usa --forzar para empezar de cero.")
    cfg = json.loads(Path(receta).read_text())
    palabra = palabra_de(cfg)
    md = PLANTILLA_CAPTION.read_text().replace("{{TEMA}}", cfg.get("tema", video))
    md = md.replace("{{CTA_LINEA}}\n\n", (linea_cta(palabra) + "\n\n") if palabra else "")
    md = md.replace("{{OUTRO_LINEA}}", "\nEl episodio completo, en mi canal de YouTube.\n" if cfg.get("outro") else "")
    md = md.replace("{{SIGUEME_LINEA}}", linea_sigueme(cfg))
    if HASHTAG_FIJO:  # el hashtag de la marca ya puesto; quedan 4 para el tema
        md = md.replace("__CINCO_HASHTAGS_COMO_MUCHO__", f"{HASHTAG_FIJO} __CUATRO_HASHTAGS_COMO_MUCHO__")
    ci = cierre_de(cfg)
    if ci and not ci["palabra"]:  # cierre sin palabra: la pregunta va al final, antes de los hashtags
        md = re.sub(r"\n(?=#\w|__[A-ZÁÉÍÓÚÑ_]*HASHTAGS)", lambda _: "\n" + linea_pregunta(ci) + "\n\n", md, count=1)
    cap.write_text(md)
    words = palabras(d)
    g = gancho_de(video)
    pistas = [f"{video}: borrador en {cap.relative_to(ROOT)} con {len(huecos(md))} huecos."]
    if palabra and palabra not in PALABRAS_ACTIVAS:
        pistas.append(f"⚠ El vídeo dice «Comenta {palabra}», que no está activa: el caption usa "
                      f"{kit.palabra_por_defecto() or 'ninguna (no tienes palabras en marca.json)'}.")
    if g:
        pistas.append("Gancho del vídeo (la frase cortada): «" + " ".join(prosa([w for w in words if w["t0"] < g - 0.05])) + "»")
    if ci and not ci["palabra"]:
        pistas.append(f"- Cierre «{ci['tipo']}»: sin «Comenta». El gancho va en la PRIMERA línea y la pregunta, al final (ya puesta).")
    pistas += ["- El gancho del caption va en la línea 2, tras «Comenta…»; corto, con la idea más fuerte del vídeo." if palabra else
               "- El gancho del caption va en la primera línea; corto, con la idea más fuerte del vídeo.",
               "- Cada cifra tiene que ser la del vídeo. Si nombra a alguien, su @ si lo tiene.",
               (f"- Hashtags: {HASHTAGS_MAX} como máximo, {HASHTAG_FIJO} incluido; los otros 4, del tema concreto."
                if HASHTAG_FIJO else f"- Hashtags: {HASHTAGS_MAX} como máximo, del tema concreto."),
               "- Primer comentario: lo publicas tú al subir el reel y lo fijas. Dos o tres líneas: tu "
               "propia respuesta a la pregunta del vídeo para abrir la conversación (o un dato que no cupo), y en un short de "
               "episodio, el título del episodio para buscarlo en YouTube. Si el vídeo pide palabra, la misma; si no, ninguna. "
               "Acaba siempre con la @ y el porqué de seguirte (ya puesta: rellena el porqué con lo que gana quien te "
               "sigue, p. ej. «tener cada semana el paso a paso de tu tema»).\n"
               "- Portada: la IA de imagen usa tus fotos de referencia, sin captura del vídeo. "
               "Concepto propio del vídeo; el vestuario cuenta la idea (sin disfraz de broma ni ridiculizar a nadie); "
               "tu sello visual siempre.",
               "- «Lo que se guarda»: el dato o la prueba del vídeo como nota de papel pegada con cinta "
               "(tabla con las cifras exactas, lista corta, requisito). Si no hay dato, la prueba más concreta.",
               "- __OTRAS_PERSONAS?__: vacío si sales solo tú; si sale un invitado, una frase con quién es "
               "y que se adjunta su captura.",
               "- Titular de portada: 2 líneas cortas en MAYÚSCULAS, distinto del gancho del vídeo, que se entienda pequeño."]
    return pistas


def huecos(md):
    return HUECO.findall(md)


def comprobar(video, receta):
    """Errores que impiden enseñar o entregar el caption.md, y avisos que solo hay que mirar."""
    d = ROOT / "proyectos" / video
    cap = d / "caption.md"
    if not cap.exists():
        return [f"falta {cap.relative_to(ROOT)} (créalo con --borrador)"], []
    md = cap.read_text()
    errores, avisos = [], []
    if huecos(md):
        errores.append("huecos sin rellenar: " + ", ".join(dict.fromkeys(huecos(md))))
    sec = secciones(md)
    for s in ("contexto", "caption", "portada"):
        if not sec.get(s):
            errores.append(f"falta la sección «## {s.capitalize()}»")
    palabra = palabra_de(json.loads(Path(receta).read_text()))
    caption = sec.get("caption", "")
    primera = caption.split("\n", 1)[0]
    ci = cierre_de(json.loads(Path(receta).read_text()))
    if palabra:
        if not primera.startswith(linea_cta(palabra).split(":")[0]):
            errores.append(f"la primera línea del caption tiene que ser «{linea_cta(palabra)}»")
    elif re.search(r"\bcomenta\b", caption, re.I):
        errores.append("el vídeo no lleva «Comenta» y el caption sí")
    if ci and not ci["palabra"]:
        if ci["pregunta"] not in caption:
            errores.append(f"falta la pregunta del cierre al final del caption: «{linea_pregunta(ci)}»")
        if ci["tipo"] == "info" and "información" not in caption.lower():
            errores.append("el cierre «info» tiene que decir «si quieres información, dímelo ahí» (dispara INFO)")
    for p in re.findall(r"\bComenta\s+([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ0-9]{2,})", caption):
        if p not in PALABRAS_ACTIVAS:
            errores.append(f"«Comenta {p}» no está activa: solo {', '.join(PALABRAS_ACTIVAS)}")
    tags = HASHTAG_RE.findall(caption)
    if len(tags) > HASHTAGS_MAX:
        errores.append(f"{len(tags)} hashtags: Instagram solo cuenta {HASHTAGS_MAX} desde el 18-dic-2025; "
                       + (f"deja {HASHTAG_FIJO} y los 4 más del tema" if HASHTAG_FIJO else f"deja los {HASHTAGS_MAX} más del tema"))
    primer = sec.get("primer comentario", "")
    for p in re.findall(r"\b(?:Comenta|Escribe)\s+([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ0-9]{2,})", primer):
        if _sin_tildes(p) not in [_sin_tildes(x) for x in PALABRAS_ACTIVAS]:
            errores.append(f"el primer comentario usa «{p}», que no está activa: solo {', '.join(PALABRAS_ACTIVAS)}")
        elif palabra and _sin_tildes(p) != _sin_tildes(palabra):
            errores.append(f"el primer comentario pide «{p}» y el vídeo, «{palabra}»: una sola palabra por vídeo")
    cuenta = cuenta_de(cfg_receta := json.loads(Path(receta).read_text()))
    if primer and cuenta not in primer:
        errores.append(f"el primer comentario tiene que acabar con {cuenta} y el porqué de seguirte: "
                       f"«{linea_sigueme(cfg_receta).replace('__POR_QUE_SEGUIRME__', '…').replace('__POR_QUE_SEGUIRNOS__', '…')}»")
    if not palabra and re.search(r"\b(?i:comenta|escribe)\s+[A-ZÁÉÍÓÚÑ]{3,}\b", primer):
        errores.append("el vídeo no pide palabra y el primer comentario sí")
    portada = sec.get("portada", "")
    if portada and "9:16" not in portada:
        errores.append("la portada tiene que ser 9:16 (tapa del reel)")
    # cifras del caption que no aparecen en el vídeo (transcripción o tarjetas): solo aviso
    cfg = json.loads(Path(receta).read_text())
    en_video = " ".join(w["raw"] for w in palabras(d)) + " " + json.dumps(cfg, ensure_ascii=False)
    en_video = re.sub(r"(?<=\d)[.,\s](?=\d{3}\b)", "", en_video)
    for n in re.findall(r"\d[\d.]*", caption):
        limpio = n.rstrip(".").replace(".", "")
        if len(limpio) > 1 and limpio not in en_video:
            avisos.append(f"la cifra {n.rstrip('.')} del caption no aparece en el vídeo")
    return errores, avisos


def texto(video, receta, titulo=None):
    d = ROOT / "proyectos" / video
    cfg = json.loads(Path(receta).read_text())
    words = palabras(d)
    g = gancho_de(video)
    gancho = [w for w in words if w["t0"] < g - 0.05]
    cuerpo = [w for w in words if w["t0"] >= g - 0.05]
    palabra = palabra_de(cfg)
    cap = d / "caption.md"
    sec = secciones(cap.read_text()) if cap.exists() else {}
    if cap.exists() and huecos(cap.read_text()):  # un borrador a medias no sale en el .txt
        print(f"{video}: caption.md tiene huecos; el .txt va sin caption ni portada.", file=sys.stderr)
        sec = {k: v for k, v in sec.items() if k == "contexto" and not huecos(v)}
    cabecera = [titulo or cfg.get("tema", video)]
    if sec.get("contexto") or cfg.get("contexto"):
        cabecera.append(sec.get("contexto") or cfg["contexto"])
    if palabra and palabra not in PALABRAS_ACTIVAS:
        aviso = (f"⚠ El vídeo dice «Comenta {palabra}», que no está activa en tu herramienta de mensajes: nadie responde. "
                 "Avisa antes de publicar.")
        print(f"{video}: {aviso}", file=sys.stderr)
        cabecera.append(aviso)
    bloques = ["\n".join(cabecera)]
    if sec.get("caption"):
        bloques.append("CAPTION (listo para pegar)\n\n" + sec["caption"])
    if sec.get("primer comentario"):
        bloques.append("PRIMER COMENTARIO (publícalo tú nada más subir el reel y fíjalo)\n\n" + sec["primer comentario"])
    if sec.get("portada"):
        bloques.append("PORTADA (prompt para ChatGPT)\n\n" + sec["portada"])

    reglas = ["PARA OTRA IA (si le pides el caption o la portada con esta transcripción)",
              f"- Escribe en español, con el tono de {kit.nombre()} ({kit.usuario()}): cercano, directo, sin promesas falsas."]
    cta = (palabra if palabra in PALABRAS_ACTIVAS else kit.palabra_por_defecto()) if palabra else None  # nunca una palabra muerta
    if cta:
        reglas.append(f"- La PRIMERA línea del caption es la llamada a la acción, siempre así: «Comenta {cta} y revisa tus mensajes» "
                      f"({PALABRAS_ACTIVAS[cta]['para']}); después, el gancho y lo demás (casi todos "
                      f"leen solo la primera línea). No uses otra palabra: solo {', '.join(PALABRAS_ACTIVAS)} tienen respuesta automática.")
    elif cierre_de(cfg):
        ci = cierre_de(cfg)
        reglas.append(f"- Este vídeo cierra con una pregunta, sin «Comenta» (cierre «{ci['tipo']}»): la PRIMERA línea del caption "
                      f"es el gancho y la ÚLTIMA, antes de los hashtags, «{linea_pregunta(ci)}». No añadas «Comenta PALABRA».")
    else:
        reglas.append("- Este vídeo no lleva «Comenta»: no añadas una llamada a comentar.")
    reglas.append("- Cada cifra del caption tiene que ser la del vídeo (abajo, «Datos»). No inventes sueldos, plazos ni requisitos.")
    reglas.append(f"- Como mucho {HASHTAGS_MAX} hashtags (Instagram no cuenta más desde el 18-dic-2025)"
                  + (f", {HASHTAG_FIJO} incluido." if HASHTAG_FIJO else "."))
    if cfg.get("outro"):
        reglas.append("- Es un short de un episodio largo: menciona que el episodio completo está en su canal de YouTube.")
    bloques.append("\n".join(reglas))

    tr = ["TRANSCRIPCIÓN"]
    if gancho:
        tr.append("Gancho (la frase cortada en seco con la que arranca; luego se repite dentro del vídeo):\n"
                  + " ".join(prosa(gancho)))
        tr.append("Vídeo:")
    tr.append("\n\n".join(prosa(cuerpo)) or f"(sin transcripción: falta proyectos/{video}/palabras.json)")
    if cfg.get("outro") and "episodio" in Path(cfg["outro"]).stem:
        tr.append(f"Cierre (outro): {OUTRO_EPISODIO}")
    bloques.append("\n\n".join(tr))

    datos = []
    for x in cfg.get("datos", []):
        if x.get("tipo") == "lista":
            datos.append("- " + " · ".join(i["texto"] for i in x.get("items", [])))
        elif "numero" in x:
            n = f"{x['numero']:,}".replace(",", ".") if isinstance(x["numero"], int) else str(x["numero"])
            datos.append(f"- {x.get('antetitulo', '').strip()}: {n} {x.get('texto', '')}".replace(" :", ":")
                         + (f" — fuente: {x['fuente']}" if x.get("fuente") else ""))
    for x in cfg.get("golpes", []):
        if x.get("cuenta") is not None:
            datos.append(f"- {x['texto']} {x.get('sub', '')}".rstrip()
                         + (f" — fuente: {x['_fuente']}" if x.get("_fuente") else ""))
    if datos:
        bloques.append("DATOS CON TARJETA EN EL VÍDEO\n" + "\n".join(datos))
    return "\n\n────────────────\n\n".join(bloques).rstrip() + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--receta", required=True)
    ap.add_argument("--salida")
    ap.add_argument("--borrador", action="store_true", help="crea caption.md desde la plantilla")
    ap.add_argument("--forzar", action="store_true", help="con --borrador, rehace un caption.md que ya existe")
    ap.add_argument("--comprobar", action="store_true", help="huecos y reglas del caption.md")
    a = ap.parse_args()
    if a.borrador:
        print("\n".join(borrador(a.video, a.receta, a.forzar)))
        return
    if a.comprobar:
        errores, avisos = comprobar(a.video, a.receta)
        for x in avisos:
            print(f"  aviso: {x}")
        if errores:
            sys.exit(f"{a.video}: caption.md no está listo\n" + "\n".join(f"  ✗ {x}" for x in errores))
        print(f"{a.video}: caption.md listo")
        return
    t = texto(a.video, a.receta)
    if a.salida:
        Path(a.salida).write_text(t)
        print(f"{a.video}: texto → {a.salida}")
    else:
        print(t)


if __name__ == "__main__":
    main()
