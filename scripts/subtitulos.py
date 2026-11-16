#!/usr/bin/env python3
"""Genera subtitulos/index.html (composición HyperFrames) desde subtitulos/palabras.json.

Marca: amarillo #FFC800 en la palabra que se dice, blanco con contorno negro grueso
en el resto, Anton (condensada pesada), MAYÚSCULAS. Vídeo y audio van como capas
originales: los subtítulos son lo único que se añade.

Uso: python3 scripts/subtitulos.py [--dir subtitulos] [--receta subtitulos/recetas/ref1.json]

El color de marca (#FFC800) se cambia por el acento de marca/marca.json al escribir index.html (kit.pinta).

Dos opciones de la receta:
- "marca_agua": true | "texto" | {"texto", "opacidad", "px", "y"}: tu @ en gris translúcido justo encima de
  los subtítulos, todo el vídeo (por defecto tu usuario de marca/marca.json, 38 %, Anton 54 px, 70 px por encima de la caja).
  Se apaga con los subtítulos (--subs) y no sale con la pizarra, el ranking por niveles ni el ranking.
- "subtitulos": {"resaltar": ["frase clave", …]}: esas palabras van en negro sobre una caja amarilla (o del
  color de "acento") y la palabra activa deja de ponerse amarilla, para que no haya dos amarillos a la vez.
  Las frases se buscan en la transcripción sin mayúsculas, tildes aparte, palabra a palabra.
"""
import argparse
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kit  # noqa: E402

W, H = 1080, 1920
YELLOW = "#FFC800"
SAFE_L, SAFE_R = 110, 170      # px: botones de TikTok/Reels a la derecha; margen cómodo a la izquierda
CAP_TOP, CAP_H = 960, 260     # caja del subtítulo; termina en y=1220, libre de descripción/usuario (~y>1450)
FONT_PX, STROKE_PX = 88, 15
MAX_WORDS = 3
MAX_CHARS = 17
LINK = {"a", "al", "de", "del", "en", "con", "por", "para", "y", "o", "que", "la", "el", "los", "las",
        "un", "una", "unos", "se", "si", "lo", "te", "me", "tu", "no", "es", "le", "como", "mi"}
# Correcciones sobre lo que whisper oyó (secuencia de palabras en minúscula -> reemplazo).
# Son deducciones por el contexto, no oídas: se imprimen para que se revisen.
# Las tuyas (nombres de invitados, tu apellido…) van en marca/marca.json → "correcciones": [[["oído"], ["bien"]], …].
FIXES = [
    (["id", "y", "vuelta"], ["ida", "y", "vuelta"]),
    (["paga", "confirmada"], ["pago", "confirmado"]),
    (["dificil", "de", "atención"], ["déficit", "de", "atención"]),
    (["resolvencia"], ["solvencia"]),
    (["esta", "gramo"], ["este", "gramo"]),
    (["sabater"], ["Savater"]),
    (["saliona"], ["Sayona"]),
    (["cepe"], ["SEPE"]),
    (["de", "globo"], ["de", "Glovo"]),
    (["panes", "de", "globero"], ["panas", "gloveros"]),
    (["lere"], ["ERTE"]),
    (["al", "ere"], ["al", "ERTE"]),
    (["cuar"], ["QA"]),
    (["osd"], ["OCDE"]),                     # «la OCDE toma una referencia»
    (["1000", "eurista"], ["mileurista"]),   # dos palabras en una: se juntan
    (["feijó"], ["Feijóo"]),
] + [(list(a), list(b)) for a, b in kit.marca().get("correcciones", [])]


def load_words(path):
    out = []
    for seg in json.load(open(path))["transcription"]:
        t = seg["text"].strip()
        if not t or re.fullmatch(r"\[.*\]", t):
            continue
        out.append({"raw": t, "t0": seg["offsets"]["from"] / 1000, "t1": seg["offsets"]["to"] / 1000})
    return out


def norm(w):
    return re.sub(r"[^\wáéíóúüñ%]", "", w.lower())


NOMBRE = kit.nombre()
# Cómo suele oír whisper tu nombre, en marca/marca.json → "nombre_whisper" (en minúsculas, sin puntuación):
#   {"una": "<regex de una palabra mal oída>", "dos": [["y", "el"], "<regex de la 2.ª palabra>"]}
# «dos» cubre los nombres que whisper parte en dos («Y Demaro»). Sin la clave no se corrige nada.
_NW = kit.marca().get("nombre_whisper") or {}
NOMBRE_1 = re.compile(_NW["una"]) if _NW.get("una") else None
NOMBRE_2 = (set(_NW["dos"][0]), re.compile(_NW["dos"][1])) if _NW.get("dos") else None


def fix_name(words):
    """Corrige tu nombre a como se escribe (kit.nombre()) donde whisper lo oyó mal."""
    log, out, i = [], [], 0
    if not NOMBRE_1 and not NOMBRE_2:
        return words, log
    while i < len(words):
        w = words[i]
        n = norm(w["raw"])
        tail = re.search(r"[.,;:?!]+$", w["raw"])
        if NOMBRE_1 and NOMBRE_1.match(n) and n != norm(NOMBRE):
            log.append(f"{w['raw']} -> {NOMBRE}  @ {w['t0']:.2f}s")
            w = dict(w, raw=NOMBRE + (tail.group(0) if tail else ""))
        elif NOMBRE_2 and i + 1 < len(words) and n in NOMBRE_2[0] and NOMBRE_2[1].match(norm(words[i + 1]["raw"])):
            nxt = words[i + 1]
            tail = re.search(r"[.,;:?!]+$", nxt["raw"])
            log.append(f"{w['raw']} {nxt['raw']} -> {NOMBRE}  @ {w['t0']:.2f}s")
            w = {"raw": NOMBRE + (tail.group(0) if tail else ""), "t0": w["t0"], "t1": nxt["t1"]}
            i += 1
        out.append(w)
        i += 1
    return out, log


def apply_fixes(words):
    log = []
    i = 0
    while i < len(words):
        for pat, rep in FIXES:
            n = len(pat)
            if [norm(w["raw"]) for w in words[i:i + n]] == pat:
                if len(rep) == 1 < n:  # varias palabras en una: la primera se queda con todo el tramo
                    tail = re.search(r"[.,;:?!]+$", words[i + n - 1]["raw"])
                    log.append(f"{' '.join(w['raw'] for w in words[i:i + n])} -> {rep[0]}  @ {words[i]['t0']:.2f}s")
                    words[i:i + n] = [dict(words[i], raw=rep[0] + (tail.group(0) if tail else ""), t1=words[i + n - 1]["t1"])]
                    continue
                for w, new in zip(words[i:i + n], rep):
                    if norm(w["raw"]) != new:
                        tail = re.search(r"[.,;:?!]+$", w["raw"])
                        log.append(f"{w['raw']} -> {new}  @ {w['t0']:.2f}s")
                        w["raw"] = new + (tail.group(0) if tail else "")
        i += 1
    return log


def clean(raw):
    """Quita ¿ ¡ y puntuación de pausa; conserva ? ! % para el énfasis."""
    return re.sub(r"[¿¡;:]|[.,](?!\d)", "", raw).upper()  # «1.400» y «2,5» conservan su punto y su coma


def chunk(words):
    chunks, cur = [], []
    for w in words:
        cur.append(w)
        text = " ".join(clean(x["raw"]) for x in cur)
        end_punct = bool(re.search(r"[.?!;,]$", w["raw"]))
        if end_punct or len(cur) >= MAX_WORDS or len(text) >= MAX_CHARS:
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    # un subtítulo no debe terminar en palabra de enlace: pasa al siguiente bloque
    for i in range(len(chunks) - 1):
        c, nxt = chunks[i], chunks[i + 1]
        if len(c) > 1 and norm(c[-1]["raw"]) in LINK and not re.search(r"[.?!;,]$", c[-1]["raw"]) \
                and len(nxt) < MAX_WORDS and len(" ".join(clean(x["raw"]) for x in [c[-1]] + nxt)) <= MAX_CHARS + 4:
            nxt.insert(0, c.pop())
    # une colas de una sola palabra corta con el bloque anterior si cabe
    merged = []
    for c in chunks:
        if merged and len(c) == 1 and len(clean(c[0]["raw"])) <= 4 \
                and len(merged[-1]) < MAX_WORDS + 1 \
                and not re.search(r"[.?!]$", merged[-1][-1]["raw"]):
            merged[-1].extend(c)
        else:
            merged.append(c)
    return merged


def escalonar(words):
    """Whisper a veces da el mismo inicio a varias palabras seguidas (pasa en audios montados):
    se reparten en el tiempo hasta la siguiente palabra para que los bloques no se pisen."""
    out = [dict(w) for w in words]
    i = 0
    while i < len(out):
        j = i
        while j + 1 < len(out) and out[j + 1]["t0"] <= out[i]["t0"] + 0.05:
            j += 1
        if j > i:
            fin = out[j + 1]["t0"] if j + 1 < len(out) else max(out[j]["t1"], out[i]["t0"] + 0.3 * (j - i + 1))
            paso = (fin - out[i]["t0"]) / (j - i + 1)
            for k in range(i, j + 1):
                out[k]["t0"] = out[i]["t0"] + paso * (k - i)
                out[k]["t1"] = out[k]["t0"] + paso
        i = j + 1
    return out


def marcar_clave(words, frases):
    """Índices de las palabras que forman alguna de las frases (comparadas con norm, palabra a palabra)."""
    ns = [norm(w["raw"]) for w in words]
    clave = set()
    for f in frases:
        pat = [norm(x) for x in f.split() if norm(x)]
        if not pat:
            continue
        hits = [i for i in range(len(ns) - len(pat) + 1) if ns[i:i + len(pat)] == pat]
        if not hits:
            print(f"aviso: «{f}» no está en la transcripción (resaltar)")
        for i in hits:
            clave.update(range(i, i + len(pat)))
    return clave


def build(words, total, resaltar=()):
    words = escalonar(words)
    clave = marcar_clave(words, resaltar) if resaltar else set()
    for i, w in enumerate(words):
        w["_clave"] = i in clave
    chunks = chunk(words)
    parts, js = [], []
    for ci, c in enumerate(chunks):
        t0 = max(0.0, c[0]["t0"] - 0.03)
        nxt = chunks[ci + 1][0]["t0"] - 0.03 if ci + 1 < len(chunks) else total
        t1 = min(c[-1]["t1"] + 0.12, nxt, total)
        spans = []
        for wi, w in enumerate(c):
            span = f'<span class="w" id="c{ci}w{wi}">{html.escape(clean(w["raw"]))}</span>'
            # las palabras clave seguidas comparten una sola caja amarilla
            if w["_clave"] and (wi == 0 or not c[wi - 1]["_clave"]):
                span = '<span class="caja">' + span
            if w["_clave"] and (wi + 1 == len(c) or not c[wi + 1]["_clave"]):
                span += '</span>'
            spans.append(span)
            ws = w["t0"]
            we = c[wi + 1]["t0"] if wi + 1 < len(c) else t1
            if not resaltar:  # con caja amarilla, la palabra activa solo da su golpe de escala
                js.append(f'tl.set("#c{ci}w{wi}",{{color:"{YELLOW}"}},{ws:.3f});')
            js.append(f'tl.fromTo("#c{ci}w{wi}",{{scale:1}},{{scale:1.07,duration:0.09,ease:"power2.out",'
                      f'yoyo:true,repeat:1}},{ws:.3f});')
            if not resaltar:
                js.append(f'tl.set("#c{ci}w{wi}",{{color:"#FFFFFF"}},{we:.3f});')
        parts.append(f'      <div class="clip cap" id="c{ci}" data-start="{t0:.3f}" '
                     f'data-duration="{t1 - t0:.3f}" data-track-index="2"><p>{" ".join(spans).replace(" </span>", "</span> ")}</p></div>')
        js.append(f'tl.fromTo("#c{ci}",{{scale:0.86,opacity:0}},{{scale:1,opacity:1,duration:0.1,'
                  f'ease:"back.out(2.2)"}},{t0:.3f});')
    return chunks, "\n".join(parts), "\n        ".join(js)


PAGE = """<!doctype html>
<html lang="es">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width={W}, height={H}" />
    <title>Subtítulos — prueba</title>
    <script src="assets/gsap.min.js"></script>
    <style>
      @font-face {{ font-family: "Anton"; src: url("assets/Anton-Regular.ttf") format("truetype"); }}
      :root {{ --amarillo: {YELLOW}; --blanco: #FFFFFF; --contorno: #000000; }}
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: {W}px; height: {H}px; background: #000; overflow: hidden; }}
      #root {{ position: relative; width: {W}px; height: {H}px; background: #000; }}
      #video {{ position: absolute; inset: 0; width: {W}px; height: {H}px; object-fit: cover; }}
      .cap {{ position: absolute; left: {SAFE_L}px; width: {CAPW}px; top: {CAP_TOP}px; height: {CAP_H}px;
              display: flex; align-items: center; justify-content: center; z-index: 10;
              transform-origin: 50% 50%; }}
      #root {{ --subs: 1; }}
      .cap p {{ opacity: var(--subs, 1); }}
      .cap p {{ font-family: "Anton", sans-serif; font-size: {FONT_PX}px; line-height: 1.04;
                text-transform: uppercase; text-align: center; letter-spacing: 0.01em; color: var(--blanco);
                -webkit-text-stroke: {STROKE_PX}px var(--contorno); paint-order: stroke fill;
                stroke-linejoin: round; text-shadow: 0 6px 0 rgba(0,0,0,.55); }}
      .w {{ display: inline-block; color: var(--blanco); transform-origin: 50% 70%; margin: 0 0.07em; }}
{HOOK_CSS}
{VAR_CSS}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{DUR:.3f}"
         data-width="{W}" data-height="{H}">
      <video id="video" class="clip" src="assets/corte.mp4" data-start="0" data-duration="{DUR:.3f}"
             data-track-index="0" data-has-audio="false" muted playsinline></video>
      <audio id="voz" src="{AUDIO}" data-start="0" data-duration="{DUR:.3f}" data-track-index="1"></audio>
{CAPS}
{HOOK}
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});
      tl.set("#root", {{ "--subs": 1 }}, 0);
        {JS}
        {HOOK_JS}
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""


def variant_css(cfg, d):
    """Ajustes de variante: color del vídeo, zoom de base y fuente de subtítulos."""
    out = []
    if cfg.get("video_filtro"):
        out.append(f'      #video {{ filter: {cfg["video_filtro"]}; }}')
    z = cfg.get("video_zoom")
    if z and z != 1:
        cx, cy = cfg.get("centro_cara", [W / 2, H / 2])
        out.append(f'      #video {{ inset: auto; left: {cx - cx * z:.0f}px; top: {cy - cy * z:.0f}px; '
                   f'width: {W * z:.0f}px; height: {H * z:.0f}px; }}')
    f = cfg.get("subtitulos", {}).get("fuente")
    if f:
        src = f["archivo"]
        if not (d / "assets" / src).exists():
            raise SystemExit(f"fuente {src} no está en {d / 'assets'}")
        out.append(f'      @font-face {{ font-family: "{f["nombre"]}"; src: url("assets/{src}"); font-weight: 200 700; }}')
        out.append(f'      .cap p {{ font-family: "{f["nombre"]}", "Anton", sans-serif; '
                   f'font-size: {f.get("px", FONT_PX)}px; font-weight: {f.get("peso", 400)}; '
                   f'letter-spacing: {f.get("espaciado", "0.01em")}; }}')
    return "\n".join(out)


MARCA_AGUA = {"texto": kit.usuario(), "opacidad": 0.38, "px": 54, "y": None}
SIN_MARCA = ("pizarra", "niveles", "ranking")   # mueven los subtítulos o llenan esa zona


def marca_agua(cfg, cap_top):
    """(css, html) de la marca de agua, o ("", "") si la receta no la pide."""
    m = cfg.get("marca_agua")
    if not m:
        return "", ""
    choca = [k for k in SIN_MARCA if cfg.get(k)]
    if choca:
        print(f"marca de agua: no sale con {', '.join(choca)}")
        return "", ""
    m = MARCA_AGUA | ({"texto": m} if isinstance(m, str) else m if isinstance(m, dict) else {})
    y = m["y"] if m["y"] is not None else cap_top - 70
    css = (f'      #marca-agua {{ position: absolute; left: 0; width: {W}px; top: {y}px; z-index: 9; text-align: center;'
           f' font-family: "Anton", sans-serif; font-size: {m["px"]}px; letter-spacing: 0.04em; color: #FFFFFF;'
           f' opacity: calc(var(--subs, 1) * {m["opacidad"]}); pointer-events: none; }}')
    return css, f'      <div id="marca-agua">{html.escape(m["texto"])}</div>'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="subtitulos")
    ap.add_argument("--receta", default=None, help="JSON de receta (gancho, datos, logos, impactos)")
    args = ap.parse_args()
    d = Path(args.dir)
    receta = Path(args.receta) if args.receta else d / "recetas/ref1.json"
    if args.receta and not receta.exists():  # también vale el nombre: «golpe-y-cuentas»
        receta = d / "recetas" / f"{args.receta.removesuffix('.json')}.json"
        if not receta.exists():
            sys.exit(f"no existe la receta {args.receta} (ni {receta})")
    # color de acento de la receta: las piezas de otra marca (p. ej. un podcast con su color) cambian
    # el amarillo por el suyo en la palabra activa y en todo lo que usa var(--amarillo). Sin la clave, #FFC800.
    # Se lee antes de build(), que pinta la palabra activa.
    global YELLOW
    YELLOW = (json.loads(receta.read_text()) if receta.exists() else {}).get("acento", YELLOW)
    words = load_words(d / "palabras.json")
    words, log_nombre = fix_name(words)
    log = log_nombre + apply_fixes(words)
    total = round(words[-1]["t1"] + 0.0, 3)
    # duración real del vídeo
    import subprocess
    total = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                 "-of", "default=nw=1:nk=1", str(d / "assets/audio.m4a")],
                                capture_output=True, text=True).stdout.strip())
    rcfg = json.loads(receta.read_text()) if receta.exists() else {}
    chunks, caps, js = build(words, total, rcfg.get("subtitulos", {}).get("resaltar", ()))
    hook_css = hook = hook_js = ""
    audio_src = "assets/audio.m4a"
    sys.path.insert(0, str(Path(__file__).parent))
    from plantilla import comprobar  # una receta sacada de plantilla no se monta con huecos sin rellenar
    rcfg = {k: v for k, v in comprobar(rcfg | {"_ruta": str(receta)}).items() if k != "_ruta"}
    sub = rcfg.get("subtitulos", {})
    safe_l, cap_top = sub.get("izq", SAFE_L), sub.get("top", CAP_TOP)
    safe_r = sub.get("der", SAFE_R)  # margen derecho propio (p. ej. cuando la lista del ranking va a la derecha)
    var_css = variant_css(rcfg, d)
    if rcfg.get("subtitulos", {}).get("resaltar"):
        var_css += (f'\n      .caja {{ display: inline-block; background: var(--amarillo); padding: 0.02em 0.1em 0; margin: 0 0.04em;'
                    f' border-radius: 6px; }}\n      .caja .w {{ color: #000 !important; -webkit-text-stroke: 0;'
                    f' text-shadow: none; margin: 0 0.05em; }}')
    if rcfg.get("pizarra") and not (d / "assets/fuentes/Oswald-Variable.ttf").exists():
        import shutil  # la pizarra usa Oswald para los textos secundarios
        (d / "assets/fuentes").mkdir(parents=True, exist_ok=True)
        shutil.copy(Path(__file__).parent.parent / "marca/fuentes/Oswald-Variable.ttf", d / "assets/fuentes/")
    if receta.exists():
        sys.path.insert(0, str(Path(__file__).parent))
        from gancho import build_hook
        hook_css, hook, hook_js, eventos = build_hook(receta, safe_l, W - safe_l - safe_r, words, total, d)
        if eventos:
            from sfx import mix
            mix(d / "assets/audio.m4a", eventos, d / "assets/sfx", d / "assets/audio_mix.m4a")
            audio_src = "assets/audio_mix.m4a"
        print(f"receta: {receta.name}")
    ma_css, ma_html = marca_agua(rcfg, cap_top)
    if ma_css:
        var_css += "\n" + ma_css
        caps += "\n" + ma_html
        # mientras está la tarjeta «Sígueme» (que ya lleva la @), la marca de agua se esconde
        m = re.search(r'id="seguir" data-start="([\d.]+)" data-duration="([\d.]+)"', hook)
        if m:
            t0, dur = float(m.group(1)), float(m.group(2))
            hook_js += (f'\n        tl.to("#marca-agua",{{autoAlpha:0,duration:0.2}},{t0:.3f});'
                        f'tl.to("#marca-agua",{{autoAlpha:1,duration:0.2}},{t0 + dur:.3f});')
    # un solo punto de color: el #FFC800 de las piezas pasa al acento de tu marca (igual si es el mismo)
    (d / "index.html").write_text(kit.pinta(PAGE.format(W=W, H=H, YELLOW=YELLOW, CAPW=W - safe_l - safe_r, SAFE_L=safe_l, CAP_TOP=cap_top, CAP_H=CAP_H,
                                              FONT_PX=FONT_PX, STROKE_PX=STROKE_PX, DUR=total,
                                              CAPS=caps, JS=js, HOOK_CSS=hook_css, HOOK=hook, HOOK_JS=hook_js, AUDIO=audio_src, VAR_CSS=var_css)))
    print(f"{len(words)} palabras → {len(chunks)} subtítulos · {total:.2f}s")
    print("correcciones aplicadas (revisar):" if log else "sin correcciones")
    for l in log:
        print("  ", l)
    for c in chunks:
        print(f"  {c[0]['t0']:6.2f}  " + " ".join(clean(w['raw']) for w in c))


if __name__ == "__main__":
    main()
