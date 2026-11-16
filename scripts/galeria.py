#!/usr/bin/env python3
"""Galería de la biblioteca de efectos: un clip corto en bucle por efecto.

  python3 scripts/galeria.py fondo              prepara proyectos/_escaparate/ con el tramo de fondo (fondo.json)
  python3 scripts/galeria.py E-11 E-14 …        renderiza esos efectos
  python3 scripts/galeria.py todos              renderiza todos los activos del índice
  python3 scripts/galeria.py hoja               hoja de fotogramas de todos los clips (out/galeria/hoja.png)
  python3 scripts/galeria.py pagina             página de la biblioteca → out/galeria/pagina/ (index.html, clips/, posters/)
                                                Claude la publica como página privada (Artifact con `db`, colecciones «elegidos» y «pedidos»;
                                                los pedidos, moldes y kits por marca son la fase previa de /editor: pedido.py).
                                                Su URL va en editor.json → "biblioteca_url".
  python3 scripts/galeria.py al-dia [--simular] la pone al día sola: clip para cada efecto nuevo, rehace los que cambiaron
                                                (su receta del escaparate o el script que lo monta) y la página si cambió algo.
                                                Pásalo siempre después de tocar un efecto o de añadir uno al índice.

El fondo de todos los clips es un tramo de uno de tus vídeos: proyectos/_escaparate/fondo.json
  {"origen": "<proyecto de proyectos/>", "de": 44.85, "a": 59.4, "copiar": {destino: origen}, "plantilla": opcional}
  ("plantilla": el proyecto del que se copian hyperframes.json y los assets de marca; por defecto, el de "origen").
Cada efecto tiene su receta mínima en proyectos/_escaparate/recetas/E-NN.json, con el texto que llevó en un vídeo
entregado (o de un tema real del canal) anclado a frases del fondo. Su clave "_galeria" dice qué se enseña:
  {"frase": "albañiles", "antes": 0.4, "dur": 3.8}   ventana del clip, desde esa frase del fondo
  {"tipo": "montaje"}       la receta es un JSON de montaje.py (entradas impacto/glitch) sobre el fondo
  {"tipo": "outro", "outro": "marca/outros/…"}       final del fondo + outro pegado como en entregar.py
  {"tipo": "archivo", "archivo": "out/…", "de": 2.0} se corta de un render ya hecho (ruta, carrusel)
Salida: out/galeria/E-NN.mp4 (540 px de ancho, sin audio, ~300 KB) y out/galeria/hojas/E-NN.png.
HyperFrames va siempre con HYPERFRAMES_SKIP_SKILLS=1.
"""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import kit  # noqa: E402

ESC = ROOT / "proyectos/_escaparate"
OUT = ROOT / "out/galeria"
HF = ["npx", "--yes", "hyperframes@0.8.78"]
ENV = {**os.environ, "HYPERFRAMES_SKIP_SKILLS": "1"}
VENV_PY = kit.python_opencv()   # OpenCV (para la hoja con rótulos)
SIN_ESCAPARATE = ("Falta proyectos/_escaparate/fondo.json: la galería pone cada efecto sobre un tramo de uno de tus "
                  "vídeos.\nCréalo con {\"origen\": \"<proyecto de proyectos/>\", \"de\": segundo, \"a\": segundo} y "
                  "escribe la receta de cada efecto en proyectos/_escaparate/recetas/E-NN.json (ver galeria.py).")


def hay_escaparate():
    return (ESC / "fondo.json").exists()
ANCHO, KB = 540, 300
FIRMAS = OUT / "firmas.json"   # con qué receta y qué script se hizo cada clip (para saber cuáles rehacer)


def run(cmd, **kw):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, **kw)
    if r.returncode:
        raise RuntimeError(f"falló: {' '.join(map(str, cmd))}\n{(r.stderr or r.stdout)[-1500:]}")
    return r.stdout


def duracion(f):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f]).strip())


# ---------- fondo ----------

def fondo():
    """El tramo de fondo como un proyecto más: corte, audio, palabras (desplazadas) y assets de marca."""
    if not hay_escaparate():
        raise SystemExit(SIN_ESCAPARATE)
    cfg = json.loads((ESC / "fondo.json").read_text())
    src = ROOT / "proyectos" / cfg["origen"]
    plantilla = ROOT / "proyectos" / cfg.get("plantilla", cfg["origen"])   # de aquí, config y assets de marca
    a = ESC / "assets"
    a.mkdir(parents=True, exist_ok=True)
    de, hasta = cfg["de"], cfg["a"]
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{de}", "-i", src / "assets/corte.mp4",
         "-t", f"{hasta - de}", "-c:v", "libx264", "-crf", "16", "-preset", "fast", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", a / "corte.mp4"])
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", a / "corte.mp4", "-vn", "-c:a", "copy", a / "audio.m4a"])
    pal = json.loads((src / "palabras.json").read_text())
    segs = []
    for s in pal["transcription"]:
        t0, t1 = s["offsets"]["from"] / 1000, s["offsets"]["to"] / 1000
        if t0 >= de - 0.01 and t1 <= hasta + 0.05 and s["text"].strip():
            segs.append({**s, "offsets": {"from": round((t0 - de) * 1000), "to": round((min(t1, hasta) - de) * 1000)}})
    (ESC / "palabras.json").write_text(json.dumps({"transcription": segs}, ensure_ascii=False, indent=1))
    for f in ["hyperframes.json", "package.json"]:
        shutil.copy2(plantilla / f, ESC / f)
    (ESC / "meta.json").write_text(json.dumps({"id": "escaparate", "name": "_escaparate"}, indent=2))
    for item in ["Anton-Regular.ttf", "gsap.min.js", "logos", "fuentes"]:
        s, t = plantilla / "assets" / item, a / item
        if not s.exists() and item in ("logos", "fuentes"):   # opcionales: solo los usan algunas piezas
            continue
        shutil.copytree(s, t, dirs_exist_ok=True) if s.is_dir() else shutil.copy2(s, t)
    for dst, org in cfg.get("copiar", {}).items():   # material de otros vídeos que piden algunas piezas
        if (ROOT / org).exists():
            shutil.copytree(ROOT / org, ESC / dst, dirs_exist_ok=True)
        else:
            print(f"  aviso: falta {org} (las piezas que lo usan fallarán)")
    print(f"fondo: {cfg['origen']} {de}–{hasta} s → {ESC} ({len(segs)} palabras)")


def silueta():
    if not (ESC / "assets/silueta.webm").exists():
        print("silueta del fondo (recorte.py)…")
        run([sys.executable, ROOT / "scripts/recorte.py", ESC], cwd=ROOT)


DETRAS = {"detras"}   # claves que necesitan la silueta del fondo


def _con_dichos(orig, dice):
    """Transcripción del fondo con frases puestas a mano en esos segundos (el clip no lleva audio)."""
    segs = json.loads(orig)["transcription"]
    for t, texto in dice:
        toks = texto.split()
        fin = t + 0.3 * len(toks)
        segs = [x for x in segs if not (t - 0.05 <= x["offsets"]["from"] / 1000 < fin)]
        segs += [{"text": " " + w, "offsets": {"from": round((t + 0.3 * k) * 1000), "to": round((t + 0.3 * k + 0.28) * 1000)}}
                 for k, w in enumerate(toks)]
    segs.sort(key=lambda x: x["offsets"]["from"])
    return json.dumps({"transcription": segs}, ensure_ascii=False)


def ventana(g):
    """(desde, dur) del clip en el fondo: por frase (y «antes») o en segundos."""
    if "frase" in g:
        from efectos import _find, _norm
        from subtitulos import load_words
        seq = [(_norm(w["raw"]), w["t0"], w["t1"]) for w in load_words(ESC / "palabras.json")]
        i = _find(seq, g["frase"], g.get("despues_de", 0.0))
        if i is None:
            raise RuntimeError(f"galería: no encuentro «{g['frase']}» en el fondo")
        return max(0.0, seq[i][1] - g.get("antes", 0.4)), g.get("dur", 3.8)
    return g.get("desde", 0.0), g.get("dur", 3.8)


def ligero(src, de, dur, dst):
    """Clip de la galería: 540 px de ancho (9:16, con bandas si hace falta), 30 fps, sin audio, ~300 KB."""
    kbps = int(KB * 8 / dur * 0.92)
    vf = (f"scale={ANCHO}:-2:flags=lanczos,pad={ANCHO}:{ANCHO * 16 // 9}:(ow-iw)/2:(oh-ih)/2:color=black,"
          f"fps=30,format=yuv420p")
    tmp = dst.with_suffix(".tmp.mp4")
    log = OUT / f"_full/{dst.stem}_2pass"
    for n in (1, 2):
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{de:.3f}", "-i", src, "-t", f"{dur:.3f}",
             "-an", "-vf", vf, "-c:v", "libx264", "-preset", "slow", "-profile:v", "high", "-b:v", f"{kbps}k",
             "-pass", str(n), "-passlogfile", log, "-movflags", "+faststart",
             *(["-f", "mp4", "/dev/null"] if n == 1 else [tmp])])
    tmp.replace(dst)
    for f in OUT.glob(f"_full/{dst.stem}_2pass*"):
        f.unlink()


def hoja_clip(clip, dst, n=8):
    d = duracion(clip)
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", clip, "-vf",
         f"fps={n / d:.4f},scale=180:-2,tile={n}x1", "-frames:v", "1", dst])


def render(cod):
    rec = ESC / "recetas" / f"{cod}.json"
    if not rec.exists():
        raise RuntimeError(f"galería: {cod} no tiene receta en el escaparate (proyectos/_escaparate/recetas/{cod}.json)")
    cfg = json.loads(rec.read_text())
    g = cfg["_galeria"]
    full = OUT / "_full" / f"{cod}.mp4"
    full.parent.mkdir(parents=True, exist_ok=True)
    tipo = g.get("tipo", "receta")
    if tipo == "receta":
        if DETRAS & set(cfg):
            silueta()
        pal = ESC / "palabras.json"
        orig = pal.read_text()
        if g.get("dice"):   # piezas que esperan oír algo que el fondo no dice («puesto 4»): solo para esta muestra
            pal.write_text(_con_dichos(orig, g["dice"]))
        try:
            run([sys.executable, ROOT / "scripts/subtitulos.py", "--dir", ESC, "--receta", rec], cwd=ROOT)
            run(HF + ["render", "-o", full, "--quality", "draft", "--quiet"], cwd=ESC, env=ENV)
            de, dur = ventana(g)
        finally:
            pal.write_text(orig)
    elif tipo == "montaje":
        # la frase «Esto no lo digo yo», cortada en seco, y el fondo desde el principio con la entrada
        m = {"carpeta": str(ESC / "assets"), "salida": str(full.relative_to(ROOT)),
             "tramos": [{"archivo": "corte.mp4", "de": 10.3, "a": 11.3},
                        {"archivo": "corte.mp4", "de": 0.0, "a": 3.0, "entrada": g["entrada"]}]}
        mj = OUT / "_full" / f"{cod}_montaje.json"
        mj.write_text(json.dumps(m, ensure_ascii=False))
        run([sys.executable, ROOT / "scripts/montaje.py", mj], cwd=ROOT)
        de, dur = 0.0, duracion(full)
    elif tipo == "outro":
        from entregar import pegar_outro
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-sseof", "-2.0", "-i", ESC / "assets/corte.mp4",
             "-c:v", "libx264", "-crf", "16", "-c:a", "aac", "-ar", "48000", full])
        pegar_outro(full, ROOT / g["outro"])
        de, dur = 0.6, g.get("dur", 4.0)
    elif tipo == "archivo":
        src = ROOT / g["archivo"]
        if not src.exists():
            raise RuntimeError(f"galería: falta {g['archivo']} (se rehace con su script: ruta.py o carrusel.py)")
        full = src
        de, dur = g.get("de", 0.0), g.get("dur", 4.0)
    else:
        raise RuntimeError(f"galería: tipo «{tipo}» desconocido")
    clip = OUT / f"{cod}.mp4"
    ligero(full, de, dur, clip)
    apuntar_firma(cod)
    (OUT / "hojas").mkdir(exist_ok=True)
    hoja_clip(clip, OUT / "hojas" / f"{cod}.png")
    kb = clip.stat().st_size // 1024
    print(f"{cod}: {clip.relative_to(ROOT)} · {dur:.1f} s · {kb} KB")
    return kb


# ---------- al día ----------

def _sha(f):
    import hashlib
    return hashlib.sha1(Path(f).read_bytes()).hexdigest()[:12] if Path(f).exists() else None


def firma(e):
    return {"receta": _sha(ESC / "recetas" / f"{e['codigo']}.json"), "script": _sha(ROOT / e.get("script", ""))}


def leer_firmas():
    return json.loads(FIRMAS.read_text()) if FIRMAS.exists() else {}


def apuntar_firma(cod):
    import efectos_indice
    e = next(x for x in efectos_indice.cargar()["efectos"] if x["codigo"] == cod)
    fs = leer_firmas()
    fs[cod] = firma(e)
    FIRMAS.write_text(json.dumps(fs, indent=1, sort_keys=True) + "\n")


def desfasados():
    """{código: motivo} de los efectos activos cuyo clip falta o se hizo con otra receta u otro script.
    Vacío si la galería no está montada (sin proyectos/_escaparate/fondo.json): no hay nada que rehacer."""
    import efectos_indice
    if not hay_escaparate():
        return {}
    idx, fs, out = efectos_indice.cargar(), leer_firmas(), {}
    for e in idx["efectos"]:
        c = e["codigo"]
        if e["estado"] != "activo":
            continue
        if not (ESC / "recetas" / f"{c}.json").exists():
            out[c] = "sin receta en el escaparate (escríbela en proyectos/_escaparate/recetas/)"
        elif not (OUT / f"{c}.mp4").exists():
            out[c] = "nuevo: sin clip"
        elif c in fs:
            ahora = firma(e)
            if ahora["receta"] != fs[c].get("receta"):
                out[c] = "cambió su receta del escaparate"
            elif ahora["script"] != fs[c].get("script"):
                out[c] = f"cambió {e.get('script')}"
    return out


def al_dia(simular=False):
    import efectos_indice
    if not hay_escaparate():
        print(f"aviso: {SIN_ESCAPARATE}\n  (la página se rehace igual, con los clips que haya)")
    if not FIRMAS.exists():
        # primera vez: los clips que hay se dan por buenos y se apuntan con lo que hay ahora
        fs = {e["codigo"]: firma(e) for e in efectos_indice.cargar()["efectos"] if (OUT / f"{e['codigo']}.mp4").exists()}
        if not simular:
            OUT.mkdir(parents=True, exist_ok=True)
            FIRMAS.write_text(json.dumps(fs, indent=1, sort_keys=True) + "\n")
        print(f"firmas: {len(fs)} clips apuntados tal como están (primera vez)")
    des = desfasados()
    for c, m in des.items():
        print(f"  {c}: {m}")
    rehacer = [c for c, m in des.items() if not m.startswith("sin receta")]
    pag = OUT / "pagina/index.html"
    fuentes = [efectos_indice.INDICE, ROOT / "scripts/galeria_pagina.html", *(ROOT / "marca/kits").glob("*.json"),
               *(ROOT / "subtitulos/recetas/plantillas").glob("*.json")]   # índice, plantilla de la página, kits y moldes
    vieja = not pag.exists() or any(pag.stat().st_mtime < f.stat().st_mtime for f in fuentes)
    if simular:
        print(f"{len(rehacer)} clip(s) por rehacer · página {'por rehacer' if vieja or rehacer else 'al día'} (simulado)")
        return
    if not (ESC / "assets/corte.mp4").exists() and rehacer:
        fondo()
    fallos = []
    for c in rehacer:
        try:
            render(c)
        except Exception as ex:   # noqa: BLE001 — sigue con los demás
            fallos.append(c)
            print(f"{c}: FALLA\n{ex}")
    if rehacer and (OUT / "hojas").exists():
        hoja()
    if rehacer or vieja:
        pagina()
        import pedido
        print(f"→ publica la página otra vez (Artifact, mismo index.html, files clips/ y posters/): {pedido.pagina()}")
    else:
        print("galería al día: nada que rehacer")
    if fallos:
        sys.exit(f"fallaron: {' '.join(fallos)}")


def hoja():
    """Todas las hojas en una, con el código a la izquierda (OpenCV del venv)."""
    hs = sorted((OUT / "hojas").glob("E-*.png"))
    code = f"""
import cv2, numpy as np, sys
hs = {[str(h) for h in hs]!r}
filas = []
for h in hs:
    im = cv2.imread(h)
    lab = np.full((im.shape[0], 120, 3), 24, np.uint8)
    cv2.putText(lab, h.split('/')[-1][:-4], (8, im.shape[0] // 2 + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 200, 255), 2)
    filas.append(np.hstack([lab, im]))
w = max(f.shape[1] for f in filas)
filas = [np.pad(f, ((0, 4), (0, w - f.shape[1]), (0, 0))) for f in filas]
mitad = (len(filas) + 1) // 2
a, b = np.vstack(filas[:mitad]), np.vstack(filas[mitad:])
b = np.pad(b, ((0, a.shape[0] - b.shape[0]), (0, 0), (0, 0)))
cv2.imwrite(sys.argv[1], np.hstack([a, np.full((a.shape[0], 16, 3), 0, np.uint8), b]))
"""
    run([VENV_PY, "-c", code, OUT / "hoja.png"])
    print(f"hoja: {(OUT / 'hoja.png').relative_to(ROOT)} ({len(hs)} efectos)")


MOLDE_RESPALDO = {"ranking-de-pie": "E-39", "top-con-sueldo": "E-40"}   # sin muestra guardada: el clip del efecto


def _fuente_molde(m):
    """El vídeo del que sale el clip de un molde: la muestra de su ejemplo aprobado, o el clip de su efecto."""
    r = Path(m["receta_ejemplo"])
    if len(r.parts) > 2:
        v, st = r.parts[1], r.stem
        for f in [OUT.parent / f"{v}_{st}_muestra.mp4", OUT.parent / f"{v}_{st}_916.mp4",
                  *sorted(OUT.parent.glob(f"{v}_{st}*_916.mp4"))]:
            if f.exists():
                return f, 1.0
    cod = MOLDE_RESPALDO.get(m["id"])
    if cod and (OUT / f"{cod}.mp4").exists():
        return OUT / f"{cod}.mp4", 0.0
    return None, 0


def moldes_y_kits(dst):
    """Fase previa de /editor (pedido.py): moldes con su clip de 6 s, kits de marca con su logo y efectos usados."""
    import pedido
    (dst / "moldes").mkdir(exist_ok=True)
    (dst / "logos").mkdir(exist_ok=True)
    ms = []
    for m in pedido.moldes():
        src, t0 = _fuente_molde(m)
        clip, pos = dst / "moldes" / f"{m['id']}.mp4", dst / "moldes" / f"{m['id']}.jpg"
        if src and (not clip.exists() or clip.stat().st_mtime < src.stat().st_mtime):
            run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{t0}", "-t", "6", "-i", src, "-an",
                 "-vf", "scale=360:-2,fps=25", "-c:v", "libx264", "-preset", "veryfast", "-crf", "30",
                 "-pix_fmt", "yuv420p", "-movflags", "+faststart", clip])
            run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", "2.5", "-i", clip, "-frames:v", "1",
                 "-q:v", "6", pos])
        ms.append({k: m[k] for k in ("id", "nombre", "cuando", "ejemplo")} | {"clip": clip.exists()})
    ks = []
    for k in pedido.kits().values():
        logo = None
        if k.get("logo"):
            logo = f"logos/{k['id']}.png"
            out = dst / logo
            src = ROOT / k["logo"]
            if not out.exists() or out.stat().st_mtime < src.stat().st_mtime:
                run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", src, "-vf", "scale=240:-2", out])
        ks.append({c: k.get(c) for c in ("id", "nombre", "tipo", "estado", "publica", "colores", "cierres", "moldes",
                                         "sin_efectos", "notas")} | {"logo": logo})
    return {"moldes": ms, "kits": ks, "usados": pedido.usados()}


def pagina():
    """La página de la biblioteca: datos del índice + un póster por clip (para que se vea entera sin cargar vídeos)."""
    import efectos_indice
    idx = efectos_indice.cargar()
    dst = OUT / "pagina"
    (dst / "posters").mkdir(parents=True, exist_ok=True)
    efs, faltan = [], []
    for e in idx["efectos"]:
        if e["estado"] != "activo":
            continue
        clip = OUT / f"{e['codigo']}.mp4"
        if not clip.exists():
            faltan.append(e["codigo"])
            continue
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{duracion(clip) * 0.55:.2f}", "-i", clip,
             "-frames:v", "1", "-vf", "scale=360:-2", "-q:v", "6", dst / "posters" / f"{e['codigo']}.jpg"])
        efs.append({k: e.get(k) for k in ("codigo", "nombre", "familia", "para_que", "ref")} |
                   {"videos": [{"video": v["video"], "publicado": v["publicado"]} for v in e.get("videos", [])]})
    datos = {"familias": idx["familias"], "efectos": efs} | moldes_y_kits(dst)
    import html as h
    # primero tu @ y tu color en la plantilla; los datos (colores de cada kit) van después, sin repintar
    html = kit.pinta((ROOT / "scripts/galeria_pagina.html").read_text().replace("__USUARIO__", h.escape(kit.usuario())))
    (dst / "index.html").write_text(html.replace("__DATOS__", json.dumps(datos, ensure_ascii=False).replace("</", "<\\/")))
    mb = sum(f.stat().st_size for f in list(OUT.glob("E-*.mp4")) + list((dst / "posters").glob("*.jpg"))) / 1e6
    print(f"página: {dst.relative_to(ROOT)}/index.html · {len(efs)} efectos · {mb:.1f} MB de clips y pósteres")
    if faltan:
        print(f"  sin clip todavía (no salen): {' '.join(faltan)}")


if __name__ == "__main__":
    args = sys.argv[1:] or ["todos"]
    if args[0] == "pagina":
        pagina()
    elif args[0] == "al-dia":
        al_dia(simular="--simular" in args)
    elif args[0] == "fondo":
        fondo()
    elif args[0] == "hoja":
        hoja()
    else:
        import efectos_indice
        idx = efectos_indice.cargar()
        cods = [e["codigo"] for e in idx["efectos"] if e["estado"] == "activo"] if args[0] == "todos" else args
        if not (ESC / "assets/corte.mp4").exists():
            fondo()
        fallos = []
        for c in cods:
            try:
                render(c)
            except Exception as ex:   # sigue con los demás; al final, la lista
                fallos.append(c)
                print(f"{c}: FALLA\n{ex}")
        if (OUT / "hojas").exists():
            hoja()
        if fallos:
            sys.exit(f"fallaron: {' '.join(fallos)}")
