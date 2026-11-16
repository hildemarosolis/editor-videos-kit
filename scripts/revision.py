#!/usr/bin/env python3
"""Página de revisión de una muestra: cada pieza del vídeo con Aprobado / Cambios / Pendiente.

Uso:
  python3 scripts/revision.py <VIDEO> --receta <receta> [--version v2 --cambiadas p05 p07]
      → out/revision_<VIDEO>_<receta>/ con index.html (la página), muestra.mp4 (copia de revisión < 14 MB)
        y piezas.json. Claude la publica como página privada de claude.ai (Artifact con `db`) y lee
        las marcas del creador con ArtifactData (colección «marcas», documentos «<version>-pNN»).
        Bajo el vídeo, «Nota en este segundo» guarda notas libres con su segundo exacto (colección «notas»,
        documentos «<version>-<id>» con t, pieza, texto); `ajustes.py notas` las lista.
        En una v2, `--cambiadas` señala las piezas rehechas; las aprobadas en la versión anterior se copian
        como «aprobado» a los documentos de la nueva con ArtifactData, para que solo quede pendiente lo rehecho.

La pieza p00 es el texto para publicar: caption y portada 9:16 de `proyectos/<VIDEO>/caption.md` (paso 7 de
/editor, `textos.py --borrador`). Sin caption.md, o con huecos, la página no se hace (salvo `--sin-caption`).

Las piezas salen de la composición (`proyectos/<VIDEO>/index.html`: cada `.clip` con su data-start y
data-duration, sin subtítulos) y de la receta (textos, frases, cifras y fuentes). «Lo que dice» es lo que
suena alrededor del momento en `palabras.json`. «Necesita» marca lo que el creador tiene que confirmar:
una cifra de tarjeta que no coincide con la dicha, un dato sin fuente o los suscriptores de marca/canal.json viejos (sin canal.json, la tarjeta de YouTube no se revisa).
"""
import argparse
import html
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kit  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PLANTILLA = ROOT / "scripts" / "revision_pagina.html"
MAX_MB = 14
# Clases de .clip que son piezas; el resto (subtítulos, sombras, partes de una escena) no se revisa aparte.
PIEZAS = {"gancho", "prueba", "cuentas", "impacto", "golpe", "chips", "seguir", "comenta", "logo", "opciones",
          "sello", "dt-tit", "pg-stk", "dt-cmp", "nv-tabla", "bw-lin", "pz-esc", "rk-item", "rk-cta", "tp-tit", "tp-mid", "partida",
          "rv-cab", "titulares", "mv-marco", "camara", "flotantes", "comentarios", "conv", "pr-pila"}
TIPOS = {"gancho": "Gancho", "prueba": "Dato", "cuentas": "Dato", "impacto": "Zoom", "golpe": "Golpe",
         "chips": "Lista", "seguir": "Sígueme", "comenta": "Comenta", "logo": "Logo", "yt": "YouTube",
         "opciones": "Opciones", "sello": "Sello", "dt-tit": "Titular detrás", "pg-stk": "Pegatina congelada", "dt-cmp": "Antes y después", "nv-tabla": "Ranking por niveles", "bw-lin": "Barrido de color", "pz-esc": "Pizarra",
         "rk-item": "Ranking", "rk-cta": "Comenta", "tp-tit": "Titular", "tp-mid": "Puesto",
         "partida": "Pantalla partida", "rv-cab": "Portada de revista", "titulares": "Lluvia de titulares",
         "mv-marco": "Dentro del móvil", "camara": "Zoom de cámara",
         "flotantes": "Tarjetas flotantes", "comentarios": "Comentario", "conv": "Conversación",
         "pr-pila": "Fotos y titulares"}


def palabras(d):
    out = []
    for w in json.loads((d / "palabras.json").read_text())["transcription"]:
        t = w["text"].strip()
        if t:
            out.append((w["offsets"]["from"] / 1000, t))
    return out


def dice(ws, t0, dur):
    """Lo que suena desde un poco antes de la pieza hasta su final (como mucho 4 s)."""
    sel = [t for s, t in ws if t0 - 1.8 <= s <= t0 + min(dur, 4.0)]
    txt = " ".join(sel)
    txt = re.sub(r"\s+([,.;:?!])", r"\1", txt)
    return txt.strip()


def numeros(txt):
    return [int(n.replace(".", "")) for n in re.findall(r"\d[\d.]*\d|\d", txt)]


def clips(d):
    h = (d / "index.html").read_text()
    for m in re.finditer(r'<\w+[^>]*class="clip ([^"]+)"[^>]*>', h):
        tag = m.group(0)
        clases = m.group(1).split()
        ident = re.search(r'id="([^"]+)"', tag)
        ini = re.search(r'data-start="([\d.]+)"', tag)
        dur = re.search(r'data-duration="([\d.]+)"', tag)
        if not (ident and ini and dur):
            continue
        base = "yt" if re.fullmatch(r"yt\d+", clases[0]) else clases[0]
        if base in PIEZAS or base == "yt":
            yield base, ident.group(1), float(ini.group(1)), float(dur.group(1))


def num(ident):
    m = re.search(r"(\d+)$", ident)
    return int(m.group(1)) if m else 0


def describir(base, ident, receta, canal):
    """(título, qué hace, necesita[]) de una pieza a partir de su receta."""
    n = num(ident)
    necesita = []
    if base == "dt-tit":
        dt = (receta.get("detras") or [{}])[n] if n < len(receta.get("detras") or []) else {}
        texto = dt.get("texto", "").replace("|", " ")
        return (texto or "Titular detrás", f"Titular gigante «{texto}» detrás de tu cabeza (tu silueta va delante).", necesita)
    if base == "dt-cmp":
        e = (receta.get("detras") or [{}])[n] if n < len(receta.get("detras") or []) else {}
        if not e.get("fuente"):
            necesita.append("Esta comparación no tiene fuente anotada en la receta.")
        return (f"{e.get('valor_antes', '')} → {e.get('valor_despues', '')}",
                f"Tarjeta de cristal a tu espalda: «{e.get('valor_antes', '')}» ({e.get('txt_antes', '')}) se tacha y sale "
                f"«{e.get('valor_despues', '')}» ({e.get('txt_despues', '')}) en amarillo.", necesita)
    if base == "nv-tabla":
        nv = receta.get("niveles") or {}
        lista = ", ".join(f"{it.get('nombre')} → {it.get('fila')}" for it in nv.get("items", []))
        return (nv.get("tema", "Ranking por niveles"), f"Tabla por niveles ({', '.join(nv.get('filas', []))}) arriba y tú en la "
                f"franja de abajo; cada elemento cae en su fila al nombrarlo: {lista}.", necesita)
    if base == "bw-lin":
        return ("Barrido de color", "Una raya amarilla cruza la pantalla y el vídeo pasa a color de cine"
                + (" hasta el final." if not (receta.get("barrido") or {}).get("seg") else "."), necesita)
    if base == "pg-stk":
        pg = (receta.get("pegatina") or [{}])[n] if n < len(receta.get("pegatina") or []) else {}
        rol = f" y debajo «{pg['rol']}»" if pg.get("rol") else ""
        return (pg.get("nombre", "Pegatina"), f"El plano se congela con un destello y sales recortado como pegatina, "
                f"con la etiqueta «{pg.get('nombre', '')}»{rol}; luego el vídeo sigue.", necesita)
    if base == "gancho":
        g = receta.get("gancho", {})
        return (f"{g.get('antetitulo', '')} {g.get('titular', '')}".strip(),
                f"Titular que se escribe: «{g.get('antetitulo', '')}» y «{g.get('titular', '')}» en grande.", necesita)
    if base in ("prueba", "cuentas"):
        dato = (receta.get("datos") or [{}])[n] if n < len(receta.get("datos") or []) else {}
        numero = dato.get("numero")
        cifra = f"{numero:,}".replace(",", ".") if isinstance(numero, (int, float)) else str(numero or "")
        if not dato.get("fuente"):
            necesita.append("Este dato no tiene fuente anotada en la receta.")
        if dato.get("necesita"):  # lo que el creador tiene que confirmar de esta cifra (p. ej. no cuadra con el convenio)
            necesita.append(dato["necesita"])
        return (f"{dato.get('antetitulo', '')} · {cifra}".strip(" ·"),
                f"Tarjeta oscura: «{dato.get('antetitulo', '')}», el número sube hasta {cifra} y debajo "
                f"«{dato.get('texto', '')}».", necesita, dato)
    if base == "impacto":
        imp = (receta.get("impactos") or [{}])[n] if n < len(receta.get("impactos") or []) else {}
        return ("Zoom de golpe", f"El plano se acerca de golpe (×{imp.get('zoom', 1.2)}) durante "
                f"{imp.get('dur', 1.0)} s para subrayar la frase.", necesita)
    if base == "golpe":
        g = (receta.get("golpes") or [{}])[n] if n < len(receta.get("golpes") or []) else {}
        if g.get("necesita"):
            necesita.append(g["necesita"])
        if g.get("estilo") == "alarma":
            hace = (f"Rótulo grande «{g.get('texto', '')}» con un aro rojo que lo rodea, temblor, destello rojo en los "
                    f"bordes y sonido de {g.get('sonido', 'error')}"
                    + (", y se tacha" if g.get("tachado") else "")
                    + (f"; debajo «{g['sub']}»" if g.get("sub") else "") + ".")
            if g.get("cuenta") is not None:
                return (g.get("texto", ""), hace, necesita, {"numero": g["cuenta"], "fuente": g.get("_fuente", "")})
            return (g.get("texto", "Golpe"), hace, necesita)
        return (g.get("texto", "Golpe"), f"Rótulo grande «{g.get('texto', '')}»"
                + (" que se tacha en rojo." if g.get("tachado") else "."), necesita)
    if base == "partida":
        pt = (receta.get("partidas") or [{}])[n] if n < len(receta.get("partidas") or []) else {}
        return (f"{pt.get('a', '')} / {pt.get('b', '')}",
                f"La pantalla se parte en dos: «{pt.get('a', '')}» ({pt.get('a_sub', '')}) a un lado y "
                f"«{pt.get('b', '')}» ({pt.get('b_sub', '')}) al otro, cada mitad con su dibujo.", necesita)
    if base == "rv-cab":
        e = (receta.get("detras") or [{}])[n] if n < len(receta.get("detras") or []) else {}
        partes = [f"cabecera «{e.get('cabecera', '')}» detrás de tu cabeza"]
        if e.get("numero"):
            partes.append(f"número «{e['numero']}» ({e.get('numero_txt', '').replace('|', ' ')})")
        if e.get("titular"):
            partes.append(f"titular «{e['titular'].replace('|', ' ')}»")
        return (f"Revista · {e.get('cabecera', '')}", "Portada de revista: fondo aclarado como papel, "
                + ", ".join(partes) + ", fecha y código de barras.", necesita)
    if base == "titulares":
        tz = (receta.get("titulares") or [{}])[n] if n < len(receta.get("titulares") or []) else {}
        items = [i["texto"] if isinstance(i, dict) else i for i in tz.get("items", [])]
        return (f"{len(items)} titulares", "Lluvia de titulares de prensa que caen a tu alrededor: "
                + ", ".join(f"«{i}»" for i in items) + ".", necesita)
    if base == "pr-pila":  # E-64: fotos con crédito y titulares reales con medio, fecha y enlace
        g = (receta.get("prensa") or [{}])[n] if n < len(receta.get("prensa") or []) else {}
        partes, fuentes = [], []
        for it in g.get("items", []):
            if it.get("tipo") == "foto":
                partes.append(f"foto «{it.get('pie', '')}» ({it.get('credito', '')})")
            else:
                partes.append(f"titular de {it.get('medio', '')} ({it.get('fecha', '')}): «{it.get('titular', '')}»")
                fuentes.append(f"{it.get('medio', '')} {it.get('fecha', '')} · {it.get('url', '')}")
        primero = (g.get("items") or [{}])[0]
        titulo = primero.get("pie") or primero.get("medio") or "Fotos y titulares"
        return (f"{titulo} (+{len(g.get('items', [])) - 1})" if len(g.get("items", [])) > 1 else titulo,
                "Caen arriba, una encima de otra como papeles: " + "; ".join(partes) + ".", necesita,
                {"fuente": " | ".join(fuentes)})
    if base == "mv-marco":
        mv = (receta.get("movil") or [{}])[n] if n < len(receta.get("movil") or []) else {}
        return (mv.get("titulo") or "Dentro del móvil", "Tu vídeo entra dentro de un móvil con la interfaz de Reels"
                + (f", con «{mv['titulo']}» encima" if mv.get("titulo") else "")
                + (f" y el pie «{mv['pie']}»" if mv.get("pie") else "") + "; los subtítulos bajan debajo del móvil.", necesita)
    if base == "flotantes":
        fl = (receta.get("flotantes") or [{}])[n] if n < len(receta.get("flotantes") or []) else {}
        items = [i.get("texto", "") for i in fl.get("items", [])]
        return (" · ".join(items), "Tarjetas con icono que entran girando en 3D al decirlas, flotan y se balancean "
                f"({'arriba' if fl.get('zona') == 'arriba' else 'abajo' if fl.get('zona', 'abajo') == 'abajo' else 'sobre el primer plano'}): "
                + ", ".join(f"«{i.get('texto', '')}»" + (f" ({i['sub']})" if i.get("sub") else "") for i in fl.get("items", [])) + ".", necesita)
    if base == "comentarios":
        cm = (receta.get("comentarios") or [{}])[n] if n < len(receta.get("comentarios") or []) else {}
        caps = cm.get("capturas") or [cm.get("captura", "")]
        return (f"{len(caps)} comentario(s) de seguidores",
                "La captura real de cada comentario público entra con un pop, una tras otra: foto de perfil difuminada "
                "y nombre visible. Mira que la foto quede bien tapada.", necesita)
    if base == "conv":
        cv = (receta.get("conversacion") or [{}])[n] if n < len(receta.get("conversacion") or []) else {}
        lineas = cv.get("lineas", [])
        return (f"Conversación · {len(lineas)} burbujas",
                "La charla con la voz de fuera de cámara sale como un chat, una burbuja al decir cada frase "
                "(gris a la izquierda la otra persona, amarilla a la derecha tú): "
                + " / ".join(f"«{l.get('texto', '')}»" for l in lineas) + ". Los subtítulos se ocultan mientras.", necesita)
    if base == "camara":
        cm = (receta.get("camara") or [{}])[n] if n < len(receta.get("camara") or []) else {}
        return ("Zoom de cámara", f"Visor de cámara (REC que parpadea, esquinas, contador) y zoom lento hacia tu cara "
                f"(×{cm.get('zoom', 1.25)}).", necesita)
    if base == "pz-esc":
        esc = (receta.get("pizarra", {}).get("escenas") or [{}])
        e = esc[n] if n < len(esc) else {}
        tipo = e.get("tipo", "")
        if tipo == "mapa" and e.get("lugares"):
            hace = ("Pizarra: el mapa de España se dibuja y aparece "
                    + ", ".join(f"{l['nombre']}" for l in e["lugares"]) + " en su sitio real, con un aro que late.")
        elif tipo == "mapa":
            hace = (f"Pizarra: el mapa de España se dibuja y aparecen {e.get('puntos', 60)} puntos, uno por pueblo, con el "
                    f"contador «{e.get('ante', 'MÁS DE')} {e.get('puntos', 60)} {e.get('texto', '')}».")
        elif tipo == "balanza":
            pl = e.get("platillos", ["COSTE", "BENEFICIO"])
            hace = (f"Pizarra: balanza {pl[0]} / {pl[1]} que se equilibra y se inclina; entra "
                    f"«{e.get('tercero', 'OPORTUNIDAD')}» y, al decir que cae, todo se viene abajo.")
        elif tipo == "foto":
            fotos = e.get("fotos", [])
            hace = ("Pizarra: " + ("foto de apoyo" if len(fotos) == 1 else f"{len(fotos)} fotos de apoyo seguidas")
                    + " en un marco que se acerca despacio, con autor y licencia abajo ("
                    + "; ".join(f.get("credito", "") for f in fotos) + ")"
                    + (f", y la pastilla «{e['dato']['texto']}»." if e.get("dato") else "."))
            necesita = list(necesita or []) + ["Que la foto encaje con lo que dices (son de Wikimedia Commons, con licencia libre)."]
        else:
            hace = f"Pizarra: escena «{tipo}»" + (f" ({e['seccion']})." if e.get("seccion") else ".")
        titulo = e.get("seccion") or e.get("titulo") or e.get("ante") or tipo
        return (f"Pizarra · {titulo}", hace, necesita, {"fuente": e.get("_fuente", "")}) if e.get("_fuente") else \
            (f"Pizarra · {titulo}", hace, necesita)
    if base == "chips":
        c = (receta.get("chips") or [{}])[n] if n < len(receta.get("chips") or []) else {}
        items = [i.get("texto", "") for i in c.get("items", [])]
        return (" · ".join(items), "Pastillas que aparecen arriba según dices cada palabra: "
                + ", ".join(f"«{i}»" for i in items) + ".", necesita)
    if base == "yt":
        yt = canal.get("youtube", {})
        subs = yt.get("suscriptores", 0)
        texto = f"{subs / 1000:.1f}".replace(".", ",") + " mil" if subs >= 10000 else str(subs)
        act = yt.get("actualizado", "")
        try:
            if (date.today() - date.fromisoformat(act)).days > 14:
                necesita.append(f"Los suscriptores ({texto}) son del {act}: ¿los actualizo?")
        except ValueError:
            necesita.append("canal.json no dice cuándo se apuntaron los suscriptores.")
        return ("Tarjeta de YouTube", f"Tarjeta con tu foto, {yt.get('usuario', kit.usuario())}, {texto} "
                "suscriptores y el botón «Suscribirse» que pasa a «¡Suscrito!» con la campana.", necesita)
    if base == "seguir":
        return ("Sígueme", f"«SÍGUEME EN {kit.usuario()}» con los iconos de Instagram, TikTok, YouTube y "
                "Facebook hasta el final.", necesita)
    if base == "comenta" and receta.get("cierre"):
        from cierre import de_receta
        ci = de_receta(receta)
        if not ci["palabra"]:
            return (f"Cierre: {ci['pregunta']}", f"Cierre «{ci['tipo']}»: la pregunta «{ci['pregunta']}» escrita en una caja "
                    f"blanca en el sitio de los subtítulos y debajo «{ci['pie']}».", necesita)
        return (f"Cierre {ci['palabra']}", f"Cierre «{ci['tipo']}»: caja «{ci['palabra']}»"
                + (" como notificación de iPhone arriba." if ci.get("estilo") == "notificacion" else " abajo."), necesita)
    if base in ("comenta", "rk-cta"):
        c = (receta.get("ranking") or {}).get("cta") if base == "rk-cta" else receta.get("comenta")
        palabra = ((c.get("palabra") if isinstance(c, dict) else None) or kit.palabra_por_defecto() or "").upper()
        if palabra not in kit.palabras():
            activas = ", ".join(kit.marca()["palabras"]) or "ninguna"
            necesita.append(f"«{palabra}» no es una palabra activa en tu herramienta de mensajes ({activas}).")
        if isinstance(c, dict) and c.get("estilo") == "notificacion":
            return (f"Comenta {palabra}", f"Notificación de iPhone arriba con tu foto: «{kit.usuario(False)} · ahora · "
                    f"Comenta {palabra} y revisa tus mensajes».", necesita)
        return (f"Comenta {palabra}", f"Caja abajo: «COMENTA {palabra} · Revisa tus mensajes».", necesita)
    if base == "logo":
        lg = (receta.get("logos") or [{}])[n] if n < len(receta.get("logos") or []) else {}
        nombre = Path(lg.get("archivo", "logo")).stem.replace("-", " ")
        return (f"Logo {nombre}", f"El logo de {nombre} arriba, solo, mientras lo nombras.", necesita)
    return (TIPOS.get(base, base), f"{TIPOS.get(base, base)} en pantalla.", necesita)


def piezas_de(video, receta_nombre):
    from ajustes import descriptores  # los campos que la página deja editar en cada pieza (fase 4 del editor)
    d = ROOT / "proyectos" / video
    receta = json.loads((d / "recetas" / f"{receta_nombre}.json").read_text())
    canal_json = ROOT / "marca" / "canal.json"  # suscriptores para la tarjeta de YouTube; si no existe, se sigue sin ella
    canal = json.loads(canal_json.read_text()) if canal_json.exists() else {}
    ws = palabras(d)
    lista = []
    for base, ident, t0, dur in sorted(clips(d), key=lambda c: c[2]):
        r = describir(base, ident, receta, canal)
        titulo, hace, necesita = r[:3]
        lo_dice = dice(ws, t0, dur)
        if base == "logo":  # logo0 es el primero que sale, no el primero de la receta: se busca el que se nombra
            for lg in receta.get("logos") or []:
                if any(f in lo_dice.lower() for f in [lg.get("frase", "")] + lg.get("alias", []) if f):
                    nombre = Path(lg.get("archivo", "logo")).stem.replace("-", " ")
                    titulo, hace = f"Logo {nombre}", f"El logo de {nombre} arriba, solo, mientras lo nombras."
                    break
        fuente = ""
        if len(r) > 3:  # dato: la cifra de la tarjeta frente a la dicha
            dato = r[3]
            fuente = dato.get("fuente", "")
            dichos = numeros(lo_dice)
            if dato.get("numero") is not None and dichos and dato["numero"] not in dichos:
                dicho = f"{dichos[0]:,}".replace(",", ".")
                puesto = f"{dato['numero']:,}".replace(",", ".")
                if kit.nombre() in fuente:  # ya la eligió el creador: se recuerda, no se vuelve a preguntar
                    fuente = f"Dices {dicho}; la tarjeta pone {puesto}. {fuente}"
                else:
                    necesita.append(f"Dices {dicho}; la tarjeta pone {puesto}. ¿Vale así?")
        lista.append({"id": f"p{len(lista) + 1:02d}", "clip": ident, "tipo": TIPOS.get(base, base),
                      "t": round(t0, 2), "dur": round(dur, 2), "titulo": titulo, "dice": lo_dice,
                      "hace": hace, "fuente": fuente, "necesita": necesita,
                      "ajustes": descriptores(receta, ident)})
    return receta, lista


def pieza_texto(video, receta_ruta):
    """p00: el caption y la portada de caption.md (fase 2 del texto, 25-oct-2026). None si no hay caption.md."""
    from textos import comprobar, secciones
    cap = ROOT / "proyectos" / video / "caption.md"
    if not cap.exists():
        return None
    errores, avisos = comprobar(video, receta_ruta)
    if errores:
        sys.exit(f"{video}: caption.md no está listo\n" + "\n".join(f"  ✗ {x}" for x in errores))
    sec = secciones(cap.read_text())
    portada = sec["portada"]
    m = re.search(r"TEXTO renderizado[^\n]*\n\s*\n(.+?)\n\s*\n", portada, re.S)
    titular = m.group(1).strip() if m else ""
    seg = re.search(r"en el segundo (\d+(?:[.,]\d+)?)", portada)
    return {"id": "p00", "clip": "caption", "tipo": "Texto", "texto": True, "t": 0, "dur": 0,
            "titulo": "Caption y portada",
            "dice": "", "hace": "", "fuente": "", "necesita": avisos,
            "caption": sec["caption"], "titular": titular,
            "captura": f"Captura en el segundo {seg.group(1)} de la muestra." if seg else "",
            "prompt": portada}


def copia_revision(src, dst, dur):
    """540 px y el bitrate justo para quedar por debajo de MAX_MB."""
    kbps = int(MAX_MB * 8000 * 0.92 / dur) - 96
    kbps = max(400, min(kbps, 2500))
    subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y", "-i", str(src),
                    "-vf", "scale=540:-2", *kit.h264(f"{kbps}k", f"{int(kbps * 1.2)}k"), "-c:a", "aac", "-b:a", "96k",
                    "-movflags", "+faststart", str(dst)], check=True)
    mb = dst.stat().st_size / 1e6
    if mb > MAX_MB:
        sys.exit(f"La copia de revisión ocupa {mb:.1f} MB (máximo {MAX_MB}).")
    return mb


def duracion(f):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--receta", required=True)
    ap.add_argument("--version", default="v1")
    ap.add_argument("--cambiadas", nargs="*", default=[], help="piezas rehechas en esta versión (p05 …)")
    ap.add_argument("--sin-caption", action="store_true", help="publicar sin la pieza p00 (sin caption.md)")
    a = ap.parse_args()

    muestra = ROOT / "out" / f"{a.video}_{a.receta}_muestra.mp4"
    if not muestra.exists():
        sys.exit(f"No hay muestra: {muestra.name}. Primero entregar.py … --muestra.")
    receta, lista = piezas_de(a.video, a.receta)
    texto = None if a.sin_caption else pieza_texto(a.video, ROOT / "proyectos" / a.video / "recetas" / f"{a.receta}.json")
    if texto is None and not a.sin_caption:
        sys.exit(f"{a.video}: falta caption.md (paso 7 de /editor): python3 scripts/textos.py {a.video} "
                 f"--receta proyectos/{a.video}/recetas/{a.receta}.json --borrador, y rellena sus huecos. "
                 "Sin él: --sin-caption.")
    if texto:
        lista.insert(0, texto)
    for p in lista:
        p["cambiada"] = p["id"] in a.cambiadas
    out = ROOT / "out" / f"revision_{a.video}_{a.receta}"
    out.mkdir(parents=True, exist_ok=True)
    dur = duracion(muestra)
    mb = copia_revision(muestra, out / "muestra.mp4", dur)

    datos = {"video": a.video, "receta": a.receta, "version": a.version,
             "tema": receta.get("tema", a.video), "letra": receta.get("letra", ""),
             "variante": receta.get("variante", a.receta), "duracion": round(dur, 2), "piezas": lista}
    (out / "piezas.json").write_text(json.dumps(datos, ensure_ascii=False, indent=2))
    pagina = kit.pinta(PLANTILLA.read_text()).replace("__TITULO__", html.escape(f"Revisión {datos['tema']}"))
    pagina = pagina.replace("__DATOS__", json.dumps(datos, ensure_ascii=False).replace("</", "<\\/"))
    (out / "index.html").write_text(pagina)

    print(f"{a.video}: {len(lista)} piezas · copia de revisión {mb:.1f} MB · {out.relative_to(ROOT)}/")
    for p in lista:
        aviso = f"  ⚠ {' / '.join(p['necesita'])}" if p["necesita"] else ""
        cuando = "texto " if p.get("texto") else f"{p['t']:5.1f}s"
        print(f"  {p['id']} {cuando:>6} {p['tipo']:<10} {p['titulo']}{aviso}")


if __name__ == "__main__":
    main()
