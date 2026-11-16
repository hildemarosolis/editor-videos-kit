#!/usr/bin/env python3
"""Episodios largos (horizontales) de un podcast, con la marca de su programa.

Cada programa es un kit de marca/kits/<id>.json con su bloque "programa": intro, cierre, fuentes, canal de la
tarjeta de suscribirse, estilo de los rótulos y colores de la muestra (los campos, en AYUDA_PROGRAMA más abajo).
largo.json lo elige con "programa"; sin él, el de editor.json → "programa_por_defecto". Se empieza con la skill /podcast.

Va aparte de los shorts: no toca preparar.py ni las recetas de 9:16; entregar.py solo gana el modo --largo
(para que la guarda de las entregas del mod editor-videos cubra también los episodios).
Episodio ya montado (cámaras cambiadas) → corte de la preparación, intro, rótulos,
tarjetas de suscribirse, cierre con hueco para la pantalla final de YouTube y −14 LUFS.

  python3 scripts/largo.py marca [--programa id]     # prepara la intro y el cierre del programa
  python3 scripts/largo.py momentos <EPISODIO>       # candidatos al arranque en frío: clip con cartones numerados
  python3 scripts/largo.py corte <EPISODIO>          # 1.ª parada: intro + episodio [desde, hasta] + cierre, a −14 LUFS
  python3 scripts/largo.py revision <EPISODIO>       #   clip ligero con el principio y el final, para el móvil
  python3 scripts/largo.py montar <EPISODIO>         # el episodio con sus rótulos y tarjetas (~10 min)
  python3 scripts/largo.py muestra <EPISODIO> [--version v2 --cambiadas p04]
                                                     # 2.ª parada: tramos con pieza + página de revisión (Artifact con db)
  python3 scripts/largo.py texto <EPISODIO>          # el .txt de YouTube (título, descripción, capítulos), sin entregar
  python3 scripts/entregar.py <EPISODIO> --largo --usar-muestra   # con el visto bueno: entrega vídeo + .txt

Cada episodio lleva su `proyectos/<NOMBRE>/largo.json`:
  {"original": "3 Originales usados/<archivo>.mp4",   # relativo a la carpeta de trabajo (o ruta absoluta)
   "tema": "La hostelería en España",
   "desde": 66.0, "hasta": 3825.0,                    # segundos del original donde empieza y acaba la conversación
   "rotulos": [{"nombre", "cargo", "en", "lado": "izq"|"der", "usuario"}],   # "en": segundo del original
   "programa": "<id>",                                # el kit del programa (marca/kits/<id>.json)
   "arranque": {"momentos": [{"de", "a", "texto"}]},   # arranque en frío antes de la intro: el primero es el gancho
                                                      # (~5 s) y los demás, destellos de lo que viene (los elige el creador)
   "tarjetas": [264.3, 1998.6, 3642.1],               # tarjeta de suscribirse al canal del programa, en esos segundos
   "capitulos": [{"en", "titulo"}],                   # el primero cae en el 0:00 del vídeo
   "youtube": {"titulo", "descripcion", "pie", "canal"}}
Cada pieza, en un segundo tras una frase y sin cifras justo después; nunca encima de una cara.

Las piezas son composiciones de HyperFrames en 1920×1080 a 25 fps (lo mismo que el episodio). La intro y el cierre
del programa pueden ser composiciones ("comp", se renderizan con `marca`) o vídeos ya hechos ("fuente").
Las fuentes con licencia que no va a git se copian desde las rutas de "fuentes" del programa.
"""
import argparse
import json
import os
import re
import time
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kit  # noqa: E402
import sfx  # noqa: E402
import largo_piezas as lp  # noqa: E402

ED = Path(__file__).resolve().parent.parent
EDITOR = kit.carpeta_editor()
OUT = ED / "out/largo"
HF = ["npx", "--yes", "hyperframes@0.8.78"]
FPS = 25
FUNDIDO = 0.3       # fundido a negro entre la intro y el episodio (sale y entra: 0,6 s en total)
FUNDIDO_FIN = 0.5   # fundido a negro del episodio al cierre
VIDEO_KBPS = "9M"   # YouTube recomienda 8 Mbps para 1080p a 25 fps; el original va a 8
KITS = ED / "marca/kits"
DESTELLO = 0.12     # fundido a blanco entre los momentos del arranque en frío
ARRANQUE_SONIDOS = ["impacto", "whoosh"]   # cae al empezar el gancho / en cada salto a otro momento


AYUDA_PROGRAMA = """Cada podcast es un kit: marca/kits/<id>.json con un bloque "programa":
  "nombre", "corto"        el nombre del programa y su forma corta («Suscríbete a <corto>»)
  "intro", "cierre"        {"mp4": ruta de salida, "comp": composición de HyperFrames o "fuente": vídeo ya hecho
                           (relativo a la carpeta de trabajo), "sonidos": [[segundo, "whoosh"|"pop"|…], …]}
  "fuentes"                [rutas de los .ttf que usan las piezas], "fuentes_nota": de dónde bajarlas si faltan
  "canal"                  {"nombre", "usuario": "@…", "avatar": ruta de la imagen, "suscriptores_de": opcional,
                           un JSON con {"youtube": {"suscriptores": N}} para poner la cifra}
  "estilo"                 opcional: colores y fuentes de los rótulos (claves de largo_piezas.ESTILO)
  "carton"                 {"fondo", "texto", "acento", "barra", "fuente_grande", "fuente_peque"} de la muestra
  "logos"                  carpeta de logos (si largo.json pone "logo" en una esquina)
  "canal_youtube", "pantalla_final"   textos del .txt de YouTube
Para sus shorts (clips.py), el mismo kit lleva un bloque "clips": {"prefijo", "reencuadre", "tema", "receta"}.
Elige el programa en largo.json ("programa": "<id>"), con --programa, o pon uno por defecto en editor.json
("programa_por_defecto": "<id>")."""


def programa(cfg=None, pid=None):
    """El bloque "programa" del kit (marca/kits/<id>.json): intro, cierre, fuentes, canal, estilo, cartón."""
    pid = pid or (cfg or {}).get("programa") or kit.ajustes().get("programa_por_defecto")
    if not pid:
        raise SystemExit(f"No sé de qué programa es este episodio.\n{AYUDA_PROGRAMA}")
    f = KITS / f"{pid}.json"
    if not f.exists() or "programa" not in json.loads(f.read_text()):
        raise SystemExit(f"No hay programa «{pid}»: falta marca/kits/{pid}.json con su bloque \"programa\".\n{AYUDA_PROGRAMA}")
    prog = json.loads(f.read_text())["programa"]
    prog["id"] = pid
    canal = prog.get("canal", {})
    if canal.get("suscriptores_de"):   # la cifra del canal, de la misma fuente que la tarjeta de los shorts
        fs = ED / canal["suscriptores_de"]
        if fs.exists():
            n = json.loads(fs.read_text())["youtube"]["suscriptores"]
            canal["suscriptores"] = suscriptores_yt(int(n))
        else:
            print(f"  aviso: falta {canal['suscriptores_de']}: la tarjeta sale sin cifra de suscriptores", file=sys.stderr)
    return prog


def suscriptores_yt(n):
    """Como lo escribe YouTube en español, truncando: 39769 → «39,7 mil». Copia de gancho.suscriptores_yt: gancho.py
    no se puede importar desde el python del venv de vídeo (clips.py lo usa), que es más antiguo."""
    if n < 1000:
        return str(n)
    if n < 100_000:
        return f"{n // 100 / 10:.1f}".replace(".0", "").replace(".", ",") + " mil"
    if n < 1_000_000:
        return f"{n // 1000} mil"
    return f"{n // 100_000 / 10:.1f}".replace(".0", "").replace(".", ",") + " M"


def marca_mp4(prog, cual):
    return ED / prog[cual]["mp4"]


def arranque_de(cfg):
    """Momentos del arranque en frío [(de, a)] en el orden en que salen (el primero es el gancho)."""
    # cada momento dura un número entero de fotogramas: si no, el vídeo redondea hacia arriba en cada trozo y con
    # 8 momentos ya no mide lo mismo que el audio (0,13 s de diferencia)
    return [(float(m["de"]), float(m["de"]) + round((float(m["a"]) - float(m["de"])) * FPS) / FPS)
            for m in (cfg.get("arranque") or {}).get("momentos", []) if m.get("usar", True)]


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode:
        raise SystemExit(f"falló: {' '.join(map(str, cmd[:4]))}…\n{(r.stderr or r.stdout)[-1500:]}")
    return r


def duracion(path):
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)])
    return float(r.stdout.strip())


def fuentes(comp, prog):
    """Copia las fuentes del programa a la composición si faltan (Chillax no va a git por licencia)."""
    for f in prog["fuentes"]:
        src = ED / f
        dest = comp / "assets" / src.name
        if dest.exists():
            continue
        if not src.exists():
            raise SystemExit(f"Falta {src}. {prog.get('fuentes_nota', '')}")
        shutil.copy(src, dest)


def render_con_sonido(comp, dest, eventos, prog):
    """Renderiza la composición a 25 fps y le pone los sonidos de Earshot.

    Los sonidos van con la ganancia de sfx.EARSHOT, la misma que llevan en los shorts sobre una
    voz a −14 LUFS; aquí no se normaliza la pista porque el episodio entero se lleva a −14 al montar.
    """
    fuentes(comp, prog)
    env = dict(os.environ, HYPERFRAMES_SKIP_SKILLS="1")
    with tempfile.TemporaryDirectory() as td:
        mudo = Path(td) / "mudo.mp4"
        run(HF + ["render", "-o", str(mudo), "--fps", str(FPS), "--quiet"], cwd=comp, env=env)
        dur = duracion(mudo)
        cmd = ["ffmpeg", "-hide_banner", "-y", "-i", str(mudo),
               "-f", "lavfi", "-t", f"{dur:.3f}", "-i", "anullsrc=r=48000:cl=stereo"]
        chains, labels = [], ["[1:a]"]
        for k, (t, nombre) in enumerate(eventos, start=2):
            _, adelanto, ganancia = sfx.EARSHOT[nombre]
            cmd += ["-i", str(sfx.EARSHOT_DIR / f"{nombre}.wav")]
            ms = max(0, int(round((t - adelanto) * 1000)))
            chains.append(f"[{k}:a]adelay={ms}:all=1,volume={ganancia}[s{k}]")
            labels.append(f"[s{k}]")
        # mismo limitador que sfx.mix (sobremuestreado x4, techo −2 dBFS): el impacto solo pasa de 0 dBFS
        graph = ";".join(chains + ["".join(labels) + f"amix=inputs={len(labels)}:normalize=0:duration=first,"
                                   f"aresample={sfx.SR * 4},alimiter=limit={sfx.LIMIT}:attack=2:release=60:"
                                   f"level=disabled,aresample={sfx.SR}[a]"])
        run(cmd + ["-filter_complex", graph, "-map", "0:v", "-map", "[a]", "-c:v", "copy",
                   "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-t", f"{dur:.3f}", str(dest)])
    _, pico = sfx.loudness(dest)
    print(f"{dest.relative_to(ED)} · {duracion(dest):.2f} s · pico {pico} dBFS")


def preparar_video(src, dest):
    """Un vídeo de marca ya hecho (p. ej. una tapa) a 1920×1080, 25 fps y −14 LUFS, como el episodio."""
    m = medir(src, 0.0, duracion(src))
    ln = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    dest.parent.mkdir(parents=True, exist_ok=True)
    run(["ffmpeg", "-hide_banner", "-y", "-i", str(src),
         "-vf", f"fps={FPS},scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:-1:-1,setsar=1,format=yuv420p",
         "-af", f"{ln},aresample=48000", "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-c:a", "aac", "-b:a", "256k",
         "-ar", "48000", "-movflags", "+faststart", str(dest)])
    i, pico = sfx.loudness(dest)
    print(f"{dest.relative_to(ED)} · {duracion(dest):.2f} s · {i} LUFS · pico {pico} dBFS")


def cmd_marca(args):
    prog = programa(pid=args.programa)
    for nombre in args.piezas or ["intro", "cierre"]:
        p = prog[nombre]
        if p.get("comp"):
            render_con_sonido(ED / p["comp"], ED / p["mp4"], [tuple(x) for x in p.get("sonidos", [])], prog)
        else:
            src = Path(p["fuente"])
            preparar_video(src if src.is_absolute() else EDITOR / src, ED / p["mp4"])


# ---------------------------------------------------------------- rótulos y tarjetas

def piezas_de(cfg):
    """Lista de piezas del episodio con su segundo (del original), sitio, duración y sonidos."""
    prog = programa(cfg)
    out = []
    for r in cfg.get("rotulos", []):
        out.append({"id": "rotulo_" + r["nombre"].split()[0].lower(), "tipo": "Rótulo", "en": float(r["en"]),
                    "html": lp.rotulo_html(r["nombre"], r["cargo"], r.get("lado", "izq"), r.get("usuario") if r.get("con_ig") else None, prog.get("estilo")),
                    "xy": lp.rotulo_xy(r.get("lado", "izq"), r.get("usuario") if r.get("con_ig") else None), "dur": lp.ROTULO_DUR, "sonidos": lp.ROTULO_SONIDOS,
                    "titulo": f"{r['nombre']} · {r['cargo']}",
                    "necesita": [r["necesita"]] if r.get("necesita") else [],
                    "hace": f"Rótulo abajo a la {'derecha' if r.get('lado') == 'der' else 'izquierda'} con el nombre y "
                            f"el cargo, {str(lp.ROTULO_DUR).replace('.', ',')} s." + (f" {r['nota']}" if r.get("nota") else "")})
    for k, t in enumerate(cfg.get("tarjetas", []), start=1):
        out.append({"id": "tarjeta", "tipo": "Suscríbete", "en": float(t),
                    "html": lp.tarjeta_html(prog["canal"], f"Suscríbete a {prog['corto']}"),
                    "xy": lp.TARJETA_XY, "dur": lp.TARJETA_DUR, "sonidos": lp.TARJETA_SONIDOS,
                    "titulo": f"Suscríbete a {prog['corto']} ({k} de {len(cfg['tarjetas'])})",
                    "necesita": [],
                    "hace": f"Tarjeta de YouTube abajo, en el centro: logo de {prog['corto']}, nombre y @; «Suscribirse» pasa a "
                            "«¡Suscrito!» con la campana. " + (f"Con {prog['canal']['suscriptores']} suscriptores."
                                                               if prog["canal"].get("suscriptores") else "Sin cifra de suscriptores.")})
    return sorted(out, key=lambda p: p["en"])


def render_pieza(nombre, p, prog):
    """Renderiza la pieza a MOV con alfa; se reutiliza si su HTML no ha cambiado."""
    d = OUT / "piezas" / nombre / p["id"]
    mov = d.with_suffix(".mov")
    if mov.exists() and (d / "index.html").exists() and (d / "index.html").read_text() == p["html"]:
        return mov
    if d.exists():
        shutil.rmtree(d)
    (d / "assets").mkdir(parents=True)
    shutil.copy(ED / "subtitulos/assets/gsap.min.js", d / "assets")
    for f in prog["fuentes"]:
        shutil.copy(ED / f, d / "assets")
    shutil.copy(ED / prog["canal"]["avatar"], d / "assets")
    shutil.copy(ED / "subtitulos/hyperframes.json", d)
    (d / "meta.json").write_text(json.dumps({"id": p["id"], "name": p["id"]}))
    (d / "package.json").write_text(json.dumps({"name": p["id"].replace("_", "-"), "private": True}))
    (d / "index.html").write_text(p["html"])
    env = dict(os.environ, HYPERFRAMES_SKIP_SKILLS="1")
    run(HF + ["render", "--format", "mov", "--fps", str(FPS), "-o", str(mov), "--quiet"], cwd=d, env=env)
    return mov


# ---------------------------------------------------------------- corte limpio

def episodio(nombre):
    f = ED / "proyectos" / nombre / "largo.json"
    if not f.exists():
        raise SystemExit(f"Falta {f.relative_to(ED)} (con original, desde y hasta)")
    cfg = json.loads(f.read_text())
    orig = Path(cfg["original"])
    orig = orig if orig.is_absolute() else EDITOR / orig
    if not orig.exists():
        raise SystemExit(f"No encuentro el original: {orig}")
    st = orig.stat()
    if getattr(st, "st_blocks", None) is not None and st.st_blocks * 512 < st.st_size * 0.9:   # solo un marcador
        raise SystemExit(f"El original aún no está descargado de iCloud: brctl download \"{orig}\"")
    return cfg, orig


def medir(orig, desde, hasta):
    """Primera pasada de loudnorm sobre el tramo del episodio."""
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-ss", f"{desde}", "-t", f"{hasta - desde:.3f}", "-i", str(orig),
             "-vn", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"])
    return json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr).group(0))


def ajustar_volumen(dest, objetivo=-14.0, margen=0.2):
    """loudnorm dinámico sobre una hora de charla se queda a ±0,5 LU. Si se pasa de ±0,2, se corrige
    solo el audio con una ganancia fija (el vídeo se copia, sin recodificar): 1 min en vez de 8.
    """
    i, tp = sfx.loudness(dest)
    for _ in range(3):
        if abs(i - objetivo) <= margen:
            break
        gain = objetivo - i
        af = f"volume={gain:.2f}dB"
        if tp + gain > -1.0:
            # Subir sin pasar de −1 dBFS: antes se recortaba la ganancia y el episodio se quedaba en −14,8
            # Ahora un limitador sobremuestreado sujeta los pocos picos.
            af += (f",aresample={sfx.SR * 4},alimiter=limit=0.84:attack=2:release=60:level=disabled,"
                   f"aresample={sfx.SR}")
        tmp = dest.with_suffix(".tmp.mp4")
        run(["ffmpeg", "-hide_banner", "-y", "-i", str(dest), "-map", "0", "-c:v", "copy",
             "-af", af, "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
             "-movflags", "+faststart", str(tmp)])
        tmp.replace(dest)
        print(f"  volumen corregido {gain:+.2f} dB")
        i, tp = sfx.loudness(dest)
    return i, tp


def comprobar_audio(dest, d0, d1, maximo=8.0):
    """Guarda: ningún silencio de más de `maximo` s dentro del episodio (una charla nunca calla tanto).

    El 6-nov-2026 el audio y el vídeo largos en un mismo filtro de concat dejaron el episodio mudo desde el
    minuto 12:25; la revisión de principio y final no lo vio. Si vuelve a pasar, aquí se para.
    """
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(dest), "-vn", "-af",
             f"silencedetect=n=-60dB:d={maximo}", "-f", "null", "-"])
    inicios = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r.stderr)]
    fines = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
    malos = [(s, e) for s, e in zip(inicios, fines + [duracion(dest)]) if d0 + 1 < s < d0 + d1 - 2]
    if malos:
        raise SystemExit("AUDIO ROTO: silencio dentro del episodio en " +
                         ", ".join(f"{int(s // 60)}:{s % 60:04.1f}–{int(e // 60)}:{e % 60:04.1f}" for s, e in malos))
    print(f"  audio comprobado: ningún silencio de más de {maximo:g} s dentro del episodio")


def audio_arranque(orig, momentos, ln, a, dest):
    """Audio del arranque en frío en dos pasadas, cada momento a su WAV exacto y luego juntos con sus golpes.

    En un solo filtro con el resto del episodio, los momentos se iban adelantando (0,12 s al final de 8) y el
    episodio quedaba desfasado de la imagen. Así cada trozo mide lo que tiene que medir.
    """
    partes, golpes, acum = [], [], 0.0
    for j, (de, hasta_m) in enumerate(momentos):
        dm = hasta_m - de
        parte = dest.with_name(f"{dest.stem}_{j:02d}.wav")
        # por muestras, no por tiempos: loudnorm deja huecos en los tiempos y atrim por segundos dejaba trozos
        # 20-80 ms cortos
        ns = int(round(dm * 48000))
        run(["ffmpeg", "-hide_banner", "-y", "-ss", f"{de}", "-t", f"{dm + 0.5:.3f}", "-i", str(orig), "-vn",
             "-af", f"{ln},{a},asetpts=N/SR/TB,atrim=end_sample={ns},afade=t=in:st=0:d=0.015,"
                    f"afade=t=out:st={dm - 0.015:.3f}:d=0.015,apad=whole_len={ns},atrim=end_sample={ns}",
             "-c:a", "pcm_s24le", "-ar", "48000", str(parte)])
        if abs(duracion(parte) - dm) > 0.001:
            raise SystemExit(f"El momento {j + 1} del arranque mide {duracion(parte):.3f} s y debería medir {dm:.3f} s")
        partes.append(parte)
        golpes.append((ARRANQUE_SONIDOS[0 if j == 0 else 1], acum - (0 if j == 0 else DESTELLO)))
        acum += dm
    entradas, graph = [], []
    for k, parte in enumerate(partes):
        entradas += ["-i", str(parte)]
    n = len(partes)
    mix = []
    for k, (s_, t) in enumerate(golpes):
        _, adelanto, ganancia = sfx.EARSHOT[s_]
        entradas += ["-i", str(sfx.EARSHOT_DIR / f"{s_}.wav")]
        # cada golpe dura lo mismo que el arranque: si una entrada de amix acaba antes, la mezcla se adelanta
        graph.append(f"[{n}:a]{a},adelay={max(0, int(round((t - adelanto) * 1000)))}:all=1,volume={ganancia},"
                     f"apad,atrim=0:{sum(h - d for d, h in momentos):.3f}[g{k}]")
        mix.append(f"[g{k}]")
        n += 1
    graph += [f"{''.join(f'[{k}:a]' for k in range(len(partes)))}concat=n={len(partes)}:v=0:a=1[rr]",
              f"[rr]{''.join(mix)}amix=inputs={len(mix) + 1}:normalize=0:duration=first,apad,atrim=0:{acum:.3f}[x]"]
    run(["ffmpeg", "-hide_banner", "-y", *entradas, "-filter_complex", ";".join(graph), "-map", "[x]",
         "-c:a", "pcm_s24le", "-ar", "48000", str(dest)])
    for parte in partes:
        parte.unlink()
    if abs(duracion(dest) - acum) > 0.01:
        raise SystemExit(f"El audio del arranque mide {duracion(dest):.3f} s y debería medir {acum:.3f} s")
    return dest


def montar(nombre, dest, con_piezas):
    """intro + episodio [desde, hasta] (con sus piezas encima, si las lleva) + cierre.

    Audio y vídeo van en pasadas separadas y se juntan al final: en un solo filtro, el concat dejaba el
    audio del episodio mudo a partir de los ~12 min (6-nov-2026). Cada tramo se recorta a su duración
    exacta para que los dos caminos midan lo mismo.
    Devuelve las piezas con su segundo en el vídeo final ("t") para la muestra.
    """
    cfg, orig = episodio(nombre)
    prog = programa(cfg)
    desde, hasta = float(cfg["desde"]), float(cfg["hasta"])
    intro, cierre = marca_mp4(prog, "intro"), marca_mp4(prog, "cierre")
    for p in (intro, cierre):
        if not p.exists():
            raise SystemExit(f"Falta {p.relative_to(ED)}: python3 scripts/largo.py marca --programa {prog['id']}")
    d0, d2, d1 = duracion(intro), duracion(cierre), hasta - desde
    momentos = arranque_de(cfg)   # arranque en frío: va antes de la intro (12-nov-2026)
    dA = sum(a - de for de, a in momentos)
    t0 = time.time()
    piezas = [p for p in piezas_de(cfg) if desde <= p["en"] <= hasta - p["dur"]] if con_piezas else []
    for p in piezas:
        p["mov"] = render_pieza(nombre, p, prog)
        p["t"] = round(dA + d0 + p["en"] - desde, 2)
    OUT.mkdir(parents=True, exist_ok=True)
    tmp_a, tmp_v = dest.with_suffix(".audio.wav"), dest.with_suffix(".video.mp4")

    # 1) audio: intro + voz del episodio a −14 con los sonidos de las piezas + cierre
    m = medir(orig, desde, hasta)
    print(f"episodio {d1/60:.1f} min · {len(piezas)} piezas · volumen original {m['input_i']} LUFS, pico {m['input_tp']} dBFS")
    ln = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    a = "aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo"
    entradas = ["-i", str(intro), "-ss", f"{desde}", "-t", f"{d1:.3f}", "-i", str(orig), "-i", str(cierre)]
    graph, sonidos, n = [], [], 3
    for p in piezas:
        for t, s in p["sonidos"]:
            _, adelanto, ganancia = sfx.EARSHOT[s]
            entradas += ["-i", str(sfx.EARSHOT_DIR / f"{s}.wav")]
            ms = max(0, int(round((p["en"] - desde + t - adelanto) * 1000)))
            graph.append(f"[{n}:a]{a},adelay={ms}:all=1,volume={ganancia}[s{len(sonidos)}]")
            sonidos.append(f"[s{len(sonidos)}]")
            n += 1
    # los sonidos se mezclan después de llevar la voz a −14, con la misma ganancia que en los shorts
    mezcla = (f"[l]{''.join(sonidos)}amix=inputs={len(sonidos) + 1}:normalize=0:duration=first," if sonidos else "[l]")
    graph += [f"[0:a]{a},apad,atrim=0:{d0:.3f}[a0]",
              f"[1:a]{ln},{a}[l]",
              f"{mezcla}afade=t=in:st=0:d={cfg.get('fundido_voz', FUNDIDO)},afade=t=out:st={d1 - FUNDIDO_FIN:.3f}:d={FUNDIDO_FIN},"
              f"apad,atrim=0:{d1:.3f}[a1]",
              f"[2:a]{a},apad,atrim=0:{d2:.3f}[a2]"]
    if momentos:   # el arranque llega ya hecho y medido (audio_arranque): en el mismo filtro se desfasaba
        arr = audio_arranque(orig, momentos, ln, a, dest.with_suffix(".arranque.wav"))
        entradas += ["-i", str(arr)]
        graph += [f"[{n}:a]{a},apad,atrim=0:{dA:.3f}[aA]", "[aA][a0][a1][a2]concat=n=4:v=0:a=1[a]"]
        n += 1
    else:
        graph.append("[a0][a1][a2]concat=n=3:v=0:a=1[a]")
    run(["ffmpeg", "-hide_banner", "-y", *entradas, "-filter_complex", ";".join(graph), "-map", "[a]",
         "-c:a", "pcm_s24le", "-ar", "48000", str(tmp_a)])

    # 2) vídeo: intro + episodio con sus piezas encima + cierre, sin audio
    v = f"fps={FPS},scale=1920:1080,setsar=1,format=yuv420p"
    entradas = ["-i", str(intro), *kit.hwaccel(), "-ss", f"{desde}", "-t", f"{d1:.3f}", "-i", str(orig),
                "-i", str(cierre)]
    graph = [f"[0:v]{v},trim=duration={d0:.3f},fade=t=out:st={d0 - FUNDIDO:.3f}:d={FUNDIDO}[v0]", f"[1:v]{v}[e0]"]
    n = 3
    for k, p in enumerate(piezas):  # cada pieza entra en su segundo del episodio y desaparece al acabar
        entradas += ["-i", str(p["mov"])]
        x, y = p["xy"]
        graph += [f"[{n}:v]setpts=PTS-STARTPTS+{p['en'] - desde:.3f}/TB[o{k}]",
                  f"[e{k}][o{k}]overlay=x={x}:y={y}:eof_action=pass:format=auto[e{k + 1}]"]
        n += 1
    ult = len(piezas)
    lg = cfg.get("logo")  # logo del programa fijo y discreto en una esquina durante el episodio
    if lg:
        m_ = lg.get("margen", 40)
        x = f"main_w-overlay_w-{m_}" if lg.get("esquina", "sup_der").endswith("der") else f"{m_}"
        y = f"{m_}" if lg.get("esquina", "sup_der").startswith("sup") else f"main_h-overlay_h-{m_}"
        entradas += ["-loop", "1", "-framerate", str(FPS), "-i", str(ED / prog["logos"] / lg["archivo"])]
        graph += [f"[{n}:v]scale={lg.get('ancho', 200)}:-1,format=rgba,colorchannelmixer=aa={lg.get('opacidad', 0.8)}[lg]",
                  f"[e{ult}][lg]overlay=x={x}:y={y}:shortest=1:format=auto[e{ult + 1}]"]
        n += 1
        ult += 1
    graph += [f"[e{ult}]trim=duration={d1:.3f},fade=t=in:st=0:d={FUNDIDO},"
              f"fade=t=out:st={d1 - FUNDIDO_FIN:.3f}:d={FUNDIDO_FIN}[v1]",
              f"[2:v]{v},trim=duration={d2:.3f},fade=t=in:st=0:d={FUNDIDO_FIN}[v2]"]
    if momentos:   # el gancho entra en seco; entre momentos, destello blanco; el último funde a negro hacia la intro
        trozos = []
        for j, (de, hasta_m) in enumerate(momentos):
            dm = hasta_m - de
            entradas += [*kit.hwaccel(), "-ss", f"{de}", "-t", f"{dm:.3f}", "-i", str(orig)]
            f_in = f",fade=t=in:st=0:d={DESTELLO}:color=white" if j else ""
            f_out = (f",fade=t=out:st={dm - DESTELLO:.3f}:d={DESTELLO}:color=white" if j < len(momentos) - 1
                     else f",fade=t=out:st={dm - FUNDIDO:.3f}:d={FUNDIDO}")
            graph.append(f"[{n}:v]{v},trim=duration={dm:.3f},setpts=PTS-STARTPTS{f_in}{f_out}[m{j}]")
            trozos.append(f"[m{j}]")
            n += 1
        graph.append(f"{''.join(trozos)}[v0][v1][v2]concat=n={len(trozos) + 3}:v=1:a=0[v]")
    else:
        graph.append("[v0][v1][v2]concat=n=3:v=1:a=0[v]")
    run(["ffmpeg", "-hide_banner", "-y", *entradas, "-filter_complex", ";".join(graph), "-map", "[v]", "-an",
         *kit.h264(VIDEO_KBPS, "12M"), "-profile:v", "high", "-g", str(FPS * 2),
         "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-r", str(FPS), str(tmp_v)])

    # 3) juntar: el vídeo se copia; el audio se lleva a −14 con una ganancia fija y se codifica una vez
    da, dv = duracion(tmp_a), duracion(tmp_v)
    if abs(da - dv) > 0.1:
        raise SystemExit(f"El audio ({da:.2f} s) y el vídeo ({dv:.2f} s) no miden lo mismo")
    i, tp = sfx.loudness(tmp_a)
    gain = min(-14.0 - i, -1.2 - tp)  # sin pasar de −1,2 dBFS de pico antes del AAC
    run(["ffmpeg", "-hide_banner", "-y", "-i", str(tmp_v), "-i", str(tmp_a), "-map", "0:v", "-map", "1:a",
         "-c:v", "copy", "-af", f"volume={gain:.2f}dB", "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
         "-movflags", "+faststart", str(dest)])
    tmp_a.unlink()
    tmp_v.unlink()
    dest.with_suffix(".arranque.wav").unlink(missing_ok=True)
    i, tp = ajustar_volumen(dest)
    comprobar_audio(dest, dA + d0, d1)
    esperado = dA + d0 + d1 + d2
    real = duracion(dest)
    print(f"{dest.relative_to(ED) if dest.is_relative_to(ED) else dest}\n"
          f"  duración {real/60:.2f} min ({real:.2f} s; esperado {esperado:.2f} s) · {i} LUFS · pico {tp} dBFS"
          f" · {dest.stat().st_size/1e9:.2f} GB · {(time.time()-t0)/60:.1f} min de render")
    for p in piezas:
        print(f"  {int(p['t'] // 60):02d}:{p['t'] % 60:04.1f}  {p['tipo']:<10} {p['titulo']}")
    return piezas


def cmd_corte(args):
    montar(args.nombre, Path(args.salida) if args.salida else OUT / f"{args.nombre}_corte.mp4", con_piezas=False)


def cmd_montar(args):
    dest = OUT / f"{args.nombre}_montado.mp4"
    piezas = montar(args.nombre, dest, con_piezas=True)
    (OUT / f"{args.nombre}_piezas.json").write_text(json.dumps(
        [{k: v for k, v in p.items() if k not in ("html", "mov")} for p in piezas], ensure_ascii=False, indent=1))


SEPARADOR = 1.6  # s de cartón entre tramos de la muestra
PIL_PY = kit.python_opencv()  # el python del sistema no siempre trae PIL


def carton(dest, arriba, abajo, prog=None):
    """Cartón 960×540 con los colores del programa entre tramos de la muestra («Minuto 32:18» + qué pieza).

    Sin él, las uniones de la muestra parecían cortes del episodio."""
    c = (prog or programa())["carton"]
    codigo = (
        "import sys; from PIL import Image, ImageDraw, ImageFont\n"
        "dest, arriba, abajo, f1, f2 = sys.argv[1:6]\n"
        f"im = Image.new('RGB', (960, 540), '{c['fondo']}'); d = ImageDraw.Draw(im)\n"
        "a = ImageFont.truetype(f1, 76); b = ImageFont.truetype(f2, 30)\n"
        f"d.rectangle([440, 300, 520, 305], fill='{c['barra']}')\n"
        f"d.text((480, 250), arriba, font=a, fill='{c['texto']}', anchor='ms')\n"
        f"d.text((480, 360), abajo, font=b, fill='{c['acento']}', anchor='ms')\n"
        "im.save(dest)\n")
    try:
        run([str(PIL_PY), "-c", codigo, str(dest), arriba, abajo,
             str(ED / c["fuente_grande"]), str(ED / c["fuente_peque"])])
        return True
    except SystemExit:
        return False


def cmd_muestra(args):
    """Muestra de la fase 3: solo los tramos con pieza (2 s antes y 1,5 s después de cada una), en una
    página de revisión como la de los shorts (scripts/revision_pagina.html): Aprobado / Cambios + comentario."""
    import html as h
    import revision as rv
    nombre = args.nombre
    montado = OUT / f"{nombre}_montado.mp4"
    lista = json.loads((OUT / f"{nombre}_piezas.json").read_text())
    if not montado.exists() or not lista:
        raise SystemExit(f"Falta el montaje: python3 scripts/largo.py montar {nombre}")
    cfg, _ = episodio(nombre)
    prog = programa(cfg)
    # textos y avisos según el largo.json de ahora (el montaje solo da el segundo); las tres tarjetas comparten id
    actual = {(q["id"], round(q["en"], 1)): q for q in piezas_de(cfg)}
    tr = json.loads((ED / "proyectos" / nombre / "palabras_raw.json").read_text())["transcription"]
    ws = [(s["offsets"]["from"] / 1000, s["text"].strip()) for s in tr if s["text"].strip()]
    out = OUT / f"revision_{nombre}"
    out.mkdir(parents=True, exist_ok=True)
    entradas, cadenas, piezas, acum, n = [], [], [], 0.0, 0
    vf = "fps=25,scale=960:540,setsar=1,format=yuv420p"
    af = "aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo"
    momentos = arranque_de(cfg)
    if momentos:   # la apertura (arranque en frío + intro + 3 s del episodio) es la primera pieza a aprobar
        dA = sum(a - de for de, a in momentos)
        d0 = duracion(marca_mp4(prog, "intro"))
        lista = [{"id": "arranque", "tipo": "Arranque", "en": float(cfg["desde"]), "t": 0.0, "dur": dA + d0,
                  "titulo": f"Arranque en frío ({len(momentos)} momentos) y {prog['nombre']}",
                  "hace": f"Gancho en seco, {len(momentos) - 1} destellos con fundido blanco y la intro del programa "
                          f"({dA:.1f} s + {d0:.1f} s).", "necesita": []}] + lista
    for k, p in enumerate(lista):
        ini, fin = (0.0, p["dur"] + 3.0) if p["id"] == "arranque" else (max(0.0, p["t"] - 2.0), p["t"] + p["dur"] + 1.5)
        minuto = f"{int(p['t'] // 60)}:{int(p['t'] % 60):02d}"
        png = out / f"carton_{k + 1:02d}.png"
        if carton(png, "Apertura" if p["id"] == "arranque" else f"Minuto {minuto}", actual.get((p["id"], round(p["en"], 1)), p)["titulo"], prog):
            entradas += ["-loop", "1", "-framerate", "25", "-t", f"{SEPARADOR}", "-i", str(png)]
        else:
            entradas += ["-f", "lavfi", "-t", f"{SEPARADOR}", "-i", f"color=c={prog['carton']['fondo']}:s=960x540:r=25"]
        entradas += ["-f", "lavfi", "-t", f"{SEPARADOR}", "-i", "anullsrc=r=48000:cl=stereo"]
        entradas += ["-ss", f"{ini:.3f}", "-t", f"{fin - ini:.3f}", "-i", str(montado)]
        d = fin - ini
        cadenas += [f"[{n}:v]{vf}[c{k}];[{n + 1}:a]{af}[ca{k}]",
                    f"[{n + 2}:v]{vf},fade=t=in:st=0:d=0.25,fade=t=out:st={d - 0.3:.3f}:d=0.3[t{k}]",
                    f"[{n + 2}:a]{af},afade=t=in:st=0:d=0.25,afade=t=out:st={d - 0.3:.3f}:d=0.3[ta{k}]"]
        n += 3
        acum += SEPARADOR
        dice = (" / ".join(m.get("texto", "") for m in cfg["arranque"]["momentos"] if m.get("usar", True))
                if p["id"] == "arranque" else " ".join(w for s, w in ws if p["en"] - 1.8 <= s <= p["en"] + min(p["dur"], 4.0)))
        piezas.append({"id": f"p{k + 1:02d}", "clip": p["id"], "tipo": p["tipo"], "t": round(acum + p["t"] - ini, 2),
                       "dur": p["dur"], "titulo": actual.get((p["id"], round(p["en"], 1)), p)["titulo"],
                       "dice": re.sub(r"\s+([,.;:?!])", r"\1", dice),
                       "hace": f"{actual.get((p['id'], round(p['en'], 1)), p)['hace']} En el vídeo, en el minuto {minuto}.",
                       "fuente": "", "necesita": actual.get((p["id"], round(p["en"], 1)), {}).get("necesita", []), "ajustes": [],
                       "cambiada": f"p{k + 1:02d}" in args.cambiadas})
        acum += d
    orden = "".join(f"[c{k}][ca{k}][t{k}][ta{k}]" for k in range(len(lista)))
    kbps = max(600, min(int(rv.MAX_MB * 8000 * 0.92 / acum) - 96, 2500))
    run(["ffmpeg", "-hide_banner", "-y", *entradas, "-filter_complex",
         ";".join(cadenas) + f";{orden}concat=n={2 * len(lista)}:v=1:a=1[v][a]", "-map", "[v]", "-map", "[a]",
         *kit.h264(f"{kbps}k", f"{int(kbps * 1.2)}k"),
         "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", str(out / "muestra.mp4")])
    mb = (out / "muestra.mp4").stat().st_size / 1e6
    if mb > rv.MAX_MB:
        raise SystemExit(f"La muestra ocupa {mb:.1f} MB (máximo {rv.MAX_MB}).")
    datos = {"video": nombre, "receta": "largo", "version": args.version, "tema": f"{prog['nombre']} · {cfg.get('tema', nombre)}",
             "letra": "", "variante": "episodio completo", "duracion": round(acum, 2), "piezas": piezas}
    (out / "piezas.json").write_text(json.dumps(datos, ensure_ascii=False, indent=2))
    pagina = rv.PLANTILLA.read_text().replace("__TITULO__", h.escape(f"Revisión {cfg.get('tema', nombre)}"))
    pagina = pagina.replace("__DATOS__", json.dumps(datos, ensure_ascii=False).replace("</", "<\\/"))
    # la plantilla es de shorts (vídeo 9:16): aquí el vídeo es horizontal y habla más de una persona
    horizontal = ("/* episodio largo (largo.py): vídeo 16:9 */\n"
                  "video { aspect-ratio: 16 / 9; }\n"
                  ".mesa { grid-template-columns: minmax(0, 560px) minmax(0, 1fr); }\n"
                  "@media (max-width: 760px) { .visor { flex-direction: column; } "
                  "video { width: 100%; height: auto; max-height: none; } }\n</style>")
    assert pagina.count("</style>") == 1 and pagina.count("<b>Lo que dices</b>") == 1
    pagina = pagina.replace("</style>", horizontal).replace("<b>Lo que dices</b>", "<b>Lo que se dice</b>")
    (out / "index.html").write_text(pagina)
    print(f"{out.relative_to(ED)}/ · {len(piezas)} piezas · muestra {acum:.0f} s, {mb:.1f} MB")
    for p in piezas:
        aviso = f"  ⚠ {' / '.join(p['necesita'])}" if p["necesita"] else ""
        print(f"  {p['id']} {p['t']:5.1f}s {p['tipo']:<10} {p['titulo']}{aviso}")


def cmd_momentos(args):
    """Clip ligero para elegir el arranque en frío: cada candidato cortado en seco tras su frase, con un cartón
    numerado delante («Momento 3» · minuto). El creador elige cuáles y en qué orden (el primero es el gancho)."""
    cfg, orig = episodio(args.nombre)
    prog = programa(cfg)
    cands = (cfg.get("arranque") or {}).get("candidatos", [])
    if not cands:
        raise SystemExit(f"Sin candidatos: \"arranque\": {{\"candidatos\": [{{\"n\", \"de\", \"a\", \"texto\"}}]}} en largo.json")
    out = OUT / f"momentos_{args.nombre}"
    out.mkdir(parents=True, exist_ok=True)
    vf = "fps=25,scale=960:540,setsar=1,format=yuv420p"
    af = "aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo"
    entradas, cadenas, orden, n = [], [], "", 0
    for k, c in enumerate(cands):
        png = out / f"carton_{c['n']:02d}.png"
        carton(png, f"Momento {c['n']}", f"minuto {minuto(c['de'])} · {c['a'] - c['de']:.1f} s".replace(".", ","), prog)
        dm = c["a"] - c["de"]
        entradas += ["-loop", "1", "-framerate", "25", "-t", f"{SEPARADOR}", "-i", str(png),
                     "-f", "lavfi", "-t", f"{SEPARADOR}", "-i", "anullsrc=r=48000:cl=stereo",
                     "-ss", f"{c['de']}", "-t", f"{dm:.3f}", "-i", str(orig)]
        cadenas += [f"[{n}:v]{vf}[c{k}];[{n + 1}:a]{af}[ca{k}]",
                    f"[{n + 2}:v]{vf}[t{k}];[{n + 2}:a]{af},afade=t=in:st=0:d=0.015,"
                    f"afade=t=out:st={dm - 0.015:.3f}:d=0.015[ta{k}]"]
        orden += f"[c{k}][ca{k}][t{k}][ta{k}]"
        n += 3
    dest = out / "momentos.mp4"
    run(["ffmpeg", "-hide_banner", "-y", *entradas, "-filter_complex",
         ";".join(cadenas) + f";{orden}concat=n={2 * len(cands)}:v=1:a=1[v][a0];[a0]loudnorm=I=-16:TP=-1.5[a]",
         "-map", "[v]", "-map", "[a]", *kit.h264("1800k"), "-c:a", "aac", "-b:a", "128k",
         "-ar", "48000", "-movflags", "+faststart", str(dest)])
    print(f"{dest.relative_to(ED)} · {duracion(dest):.0f} s · {dest.stat().st_size / 1e6:.1f} MB")
    for c in cands:
        print(f"  {c['n']}. {minuto(c['de'])} ({c['a'] - c['de']:.1f} s) {c['texto']}")


def cmd_revision(args):
    """Clip ligero (720p) con el principio y el final del corte, para verlo en el móvil."""
    src = OUT / f"{args.nombre}_corte.mp4"
    if not src.exists() and (OUT / f"{args.nombre}_montado.mp4").exists():
        src = OUT / f"{args.nombre}_montado.mp4"   # sin corte limpio aparte (flujo /podcast): el montado
    if not src.exists():
        raise SystemExit(f"Falta {src.relative_to(ED)}: python3 scripts/largo.py corte {args.nombre}")
    dur = duracion(src)
    fin = dur - args.final
    dest = OUT / f"{args.nombre}_corte_revision.mp4"
    graph = "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v0][a];[v0]scale=1280:720[v]"
    run(["ffmpeg", "-hide_banner", "-y", "-t", f"{args.principio}", "-i", str(src), "-ss", f"{fin:.3f}", "-i", str(src),
         "-filter_complex", graph, "-map", "[v]", "-map", "[a]",
         *kit.h264("2500k"), "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(dest)])
    print(f"{dest.relative_to(ED)} · {duracion(dest):.1f} s · {dest.stat().st_size/1e6:.1f} MB "
          f"(principio 0–{args.principio} s y final desde el {int(fin // 60)}:{fin % 60:04.1f})")


# ---------------------------------------------------------------- entrega (fase 4)

def minuto(s):
    s = int(round(s))
    return f"{s // 3600}:{s % 3600 // 60:02d}:{s % 60:02d}" if s >= 3600 else f"{s // 60}:{s % 60:02d}"


def texto_youtube(nombre):
    """El .txt que acompaña al episodio: título, descripción con capítulos y lo que hay que hacer al subirlo."""
    cfg, _ = episodio(nombre)
    yt = cfg.get("youtube") or {}
    if not yt.get("titulo") or not yt.get("descripcion"):
        raise SystemExit(f"Falta \"youtube\": {{\"titulo\", \"descripcion\"}} en proyectos/{nombre}/largo.json")
    prog = programa(cfg)
    desde, hasta = float(cfg["desde"]), float(cfg["hasta"])
    dA = sum(a - de for de, a in arranque_de(cfg))
    d0 = dA + duracion(marca_mp4(prog, "intro"))   # el arranque en frío y la intro van antes del 0 del episodio
    caps = []
    for c in cfg.get("capitulos", []):
        t = 0.0 if c["en"] <= desde else c["en"] - desde + d0
        caps.append(f"{minuto(t)} {c['titulo']}")
    if caps and not caps[0].startswith("0:00"):
        raise SystemExit("El primer capítulo tiene que estar en el 0:00 (si no, YouTube no los muestra)")
    fin = d0 + hasta - desde  # donde empieza el cierre de 20 s
    gente = "\n".join(f"- {r['nombre']}{' (' + r['usuario'] + ')' if r.get('usuario') else ''} · {r['cargo']}"
                      for r in cfg.get("rotulos", []))
    return f"""{yt['titulo']}

== TÍTULO ==
{yt['titulo']}

== DESCRIPCIÓN (pegar tal cual) ==
{yt['descripcion'].strip()}

Capítulos:
{chr(10).join(caps)}

{yt.get('pie', '').strip()}

== AL SUBIRLO A YOUTUBE ==
- Canal: {yt.get('canal', prog['canal_youtube'])}.
- Pantalla final: los últimos 20 s (desde el {minuto(fin)}) son el cierre con dos huecos. En YouTube Studio → Pantalla final,
  {prog['pantalla_final']}.
- Los capítulos salen solos si la descripción lleva la lista con el 0:00 primero (ya lo lleva).
- Los shorts de este episodio pueden llevarlo como «vídeo relacionado».

== QUIÉN SALE (rótulos) ==
{gente}
"""


def entregar(nombre):
    """Entrega el episodio montado y revisado (lo llama `entregar.py <NOMBRE> --largo --usar-muestra`)."""
    import terminados
    cfg, _ = episodio(nombre)
    prog = programa(cfg)
    montado = OUT / f"{nombre}_montado.mp4"
    lista = OUT / f"{nombre}_piezas.json"
    if not montado.exists() or not lista.exists():
        raise SystemExit(f"No hay montaje revisado: python3 scripts/largo.py montar {nombre} y su muestra")
    # lo que se entrega es exactamente lo que se revisó: mismas piezas, en el mismo sitio, y el mismo corte
    clave = lambda p: (p["id"], round(p["en"], 1), p["titulo"], tuple(p["xy"]))
    if sorted(map(clave, json.loads(lista.read_text()))) != sorted(map(clave, piezas_de(cfg))):
        raise SystemExit("Las piezas de largo.json cambiaron después del montaje: vuelve a montar y a revisar")
    dA = sum(a - de for de, a in arranque_de(cfg))
    d0, d2 = dA + duracion(marca_mp4(prog, "intro")), duracion(marca_mp4(prog, "cierre"))
    d1 = float(cfg["hasta"]) - float(cfg["desde"])
    if abs(duracion(montado) - (d0 + d1 + d2)) > 0.2:
        raise SystemExit("El corte (desde/hasta) cambió después del montaje: vuelve a montar y a revisar")
    comprobar_audio(montado, d0, d1)
    txt = texto_youtube(nombre)  # antes de copiar: si falla, no queda un vídeo sin su texto
    receta = ED / "proyectos" / nombre / "largo.json"
    datos = {"tema": f"{prog['corto']} {cfg.get('tema', nombre)}", "variante": "episodio", "letra": cfg.get("letra")}
    dst = terminados.entregar(montado, datos, receta, nombre)
    dst.with_suffix(".txt").write_text(dst.stem + txt[txt.index("\n"):])
    if not cfg.get("letra"):  # se queda con su letra: si se vuelve a entregar, es la misma variante
        cfg["letra"] = dst.name.split(" - ")[1][0]
        receta.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n")
    print(f"{nombre}: entregado {dst.parent.name}/{dst.name} ({dst.stat().st_size / 1e9:.2f} GB) y su .txt")


def cmd_texto(args):
    dest = OUT / f"{args.nombre}_youtube.txt"
    dest.write_text(texto_youtube(args.nombre))
    print(dest.read_text())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="orden", required=True)
    m = sub.add_parser("marca", help="prepara la intro y el cierre del programa con sus sonidos")
    m.add_argument("piezas", nargs="*", choices=["intro", "cierre"], help="por defecto, las dos")
    m.add_argument("--programa", help="kit del programa (marca/kits/<id>.json); por defecto, "
                                      "el de editor.json → programa_por_defecto")
    m.set_defaults(func=cmd_marca)
    c = sub.add_parser("corte", help="corte limpio: intro + episodio + cierre, a −14 LUFS")
    c.add_argument("nombre", help="carpeta en proyectos/ con su largo.json")
    c.add_argument("--salida", help=f"por defecto, {OUT.relative_to(ED)}/<nombre>_corte.mp4")
    c.set_defaults(func=cmd_corte)
    mo = sub.add_parser("montar", help="episodio con rótulos y tarjetas de largo.json (fase 3)")
    mo.add_argument("nombre")
    mo.set_defaults(func=cmd_montar)
    mu = sub.add_parser("muestra", help="muestra de los tramos con pieza + página de revisión")
    mu.add_argument("nombre")
    mu.add_argument("--version", default="v1")
    mu.add_argument("--cambiadas", nargs="*", default=[], help="piezas rehechas en esta versión (p04 …)")
    mu.set_defaults(func=cmd_muestra)
    mm = sub.add_parser("momentos", help="clip para elegir el arranque en frío (candidatos con cartón numerado)")
    mm.add_argument("nombre")
    mm.set_defaults(func=cmd_momentos)
    r = sub.add_parser("revision", help="clip ligero con el principio y el final del corte")
    r.add_argument("nombre")
    r.add_argument("--principio", type=float, default=40.0, help="segundos del principio (por defecto 40)")
    r.add_argument("--final", type=float, default=45.0, help="segundos del final (por defecto 45)")
    r.set_defaults(func=cmd_revision)
    tx = sub.add_parser("texto", help="enseña el .txt de YouTube (título, descripción, capítulos) sin entregar nada")
    tx.add_argument("nombre")
    tx.set_defaults(func=cmd_texto)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
