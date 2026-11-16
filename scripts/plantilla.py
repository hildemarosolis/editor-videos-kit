#!/usr/bin/env python3
"""Recetas con nombre (22-oct-2026): plantillas en subtitulos/recetas/plantillas/.

  python3 scripts/plantilla.py lista
  python3 scripts/plantilla.py nueva "pizarra viajera" MI_VIDEO --tema "Mi tema" [--capa episodio-completo]
  python3 scripts/plantilla.py comprobar proyectos/MI_VIDEO/recetas/pizarra-viajera.json
  python3 scripts/plantilla.py probar [nombre]

- Una plantilla es una receta aprobada con lo propio del vídeo cambiado por huecos «__ASI__».
  «__ASI?__» es opcional: si no se rellena, la clave se quita.
- `nueva` copia la plantilla al proyecto, pone tema y variante, calcula el centro de la cara
  (cara.py) y dice qué huecos quedan. La de «titular detrás» deja también su montaje.
- `comprobar` falla si queda algún hueco: subtitulos.py y entregar.py lo usan y no montan
  una receta a medias.
- `probar` rellena cada plantilla con la receta de su vídeo de ejemplo y comprueba que sale la
  misma composición (index.html) que se aprobó; las diferencias documentadas se avisan.
"""
import argparse
import datetime
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kit  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / "subtitulos/recetas/plantillas"
HUECO = re.compile(r"__[A-ZÁÉÍÓÚÑ0-9_]+\??__")
NADA = object()


def slug(nombre):
    s = unicodedata.normalize("NFD", nombre.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def plantillas():
    return {p.stem: json.loads(p.read_text()) for p in sorted(DIR.glob("*.json")) if not p.stem.endswith(".montaje")}


def cargar(nombre):
    ps = plantillas()
    s = slug(nombre)
    if s not in ps:
        sys.exit(f"no hay receta «{nombre}». Recetas: {', '.join(ps)}")
    return s, ps[s]


def es_hueco(v):
    return isinstance(v, str) and bool(HUECO.fullmatch(v))


def huecos(v, ruta=""):
    """Rutas de los huecos que quedan en una receta."""
    if isinstance(v, dict):
        return [h for k, x in v.items() if not k.startswith("_") for h in huecos(x, f"{ruta}.{k}" if ruta else k)]
    if isinstance(v, list):
        return [h for i, x in enumerate(v) for h in huecos(x, f"{ruta}[{i}]")]
    if isinstance(v, str) and HUECO.search(v):
        return [f"{ruta} = {v}"]
    return []


def sin_opcionales(v):
    """Quita las claves con hueco opcional («__X?__»)."""
    if isinstance(v, dict):
        return {k: sin_opcionales(x) for k, x in v.items() if not (es_hueco(x) and x.endswith("?__"))}
    if isinstance(v, list):
        return [sin_opcionales(x) for x in v]
    return v


def comprobar(receta):
    """Para subtitulos.py y entregar.py: corta si la receta tiene huecos sin rellenar."""
    r = json.loads(Path(receta).read_text()) if not isinstance(receta, dict) else receta
    nombre = r.get("_ruta", receta) if isinstance(receta, dict) else receta
    limpia = sin_opcionales(r)
    if limpia != r:  # los opcionales («__X?__») sin rellenar se quitan, como dice la cabecera
        quitados = len(huecos(r)) - len(huecos(limpia))
        r = limpia
        if not isinstance(receta, dict):
            Path(receta).write_text(json.dumps(r, ensure_ascii=False, indent=2) + "\n")
            print(f"{nombre}: quitados {quitados} huecos opcionales sin rellenar", file=sys.stderr)
    h = huecos(r)
    if h:
        sys.exit(f"{nombre}: faltan {len(h)} huecos de la plantilla por rellenar:\n  " + "\n  ".join(h))


def rellenar(plant, ejemplo, ruta, dif):
    """Rellena los huecos con el valor del ejemplo; lo fijo de la plantilla manda (y se anota si difiere)."""
    if es_hueco(plant):
        return ejemplo
    if isinstance(plant, dict):
        base = dict(ejemplo) if isinstance(ejemplo, dict) else {}
        for k, v in plant.items():
            if k.startswith("_"):
                continue
            r = rellenar(v, base.get(k, NADA), f"{ruta}.{k}" if ruta else k, dif)
            if r is NADA:
                base.pop(k, None)
            else:
                base[k] = r
        return base
    nombre = ruta.rsplit(".", 1)[-1]
    if nombre in ("tema", "letra", "variante"):  # nombres, no cambian el vídeo
        return plant
    if nombre == "logos" and isinstance(ejemplo, list):
        # mismas marcas con el mismo logo: el orden, los alias y la duración son ajustes de cada vídeo
        clave = lambda l: sorted((x["frase"], x["archivo"], x.get("fondo")) for x in l)
        if clave(plant) == clave(ejemplo):
            return ejemplo
    if ejemplo is not NADA and plant != ejemplo:
        dif.append(f"{ruta}: plantilla {json.dumps(plant, ensure_ascii=False)} · ejemplo {json.dumps(ejemplo, ensure_ascii=False)}")
    return plant


def generar(dir_, receta):
    r = subprocess.run([sys.executable, str(ROOT / "scripts/subtitulos.py"), "--dir", str(dir_), "--receta", str(receta)],
                       capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr[-800:] or r.stdout[-800:])
    return (Path(dir_) / "index.html").read_text()


def probar(solo=None):
    fallos = saltadas = 0
    for nombre, p in plantillas().items():
        if solo and slug(solo) != nombre:
            continue
        m = p["_plantilla"]
        ej = ROOT / m["ejemplo"]
        if not ej.exists():
            print(f"– {nombre:<16} saltada: el ejemplo {m['ejemplo']} no está en este ordenador (fuera de git)")
            saltadas += 1
            continue
        ejemplo = json.loads(ej.read_text())
        # los vídeos y audios no van a git: en otro ordenador la prueba de ese ejemplo se salta
        medios = ["assets/audio.m4a", "assets/corte.mp4"] + (["assets/silueta.webm"] if "detras" in ejemplo else [])
        faltan = [f for f in medios if not (ej.parent.parent / f).exists()]
        if faltan:
            print(f"– {nombre:<16} saltada: en este ordenador no están los medios del ejemplo ({', '.join(faltan)})")
            saltadas += 1
            continue
        dif = []
        relleno = rellenar(p, ejemplo, "", dif)
        quedan = huecos(relleno)
        documentadas = m.get("diferencias_con_el_ejemplo", [])
        dir_ = ej.parent.parent
        guardado = {f: (dir_ / f).read_bytes() for f in ("index.html", "assets/audio_mix.m4a") if (dir_ / f).exists()}
        tmp = ej.parent / f"_prueba_{nombre}.json"
        tmp.write_text(json.dumps(relleno, ensure_ascii=False, indent=2))
        try:
            a = generar(dir_, ej)
            b = generar(dir_, tmp)
        except RuntimeError as e:
            print(f"✗ {nombre}: no genera: {e}")
            fallos += 1
            for f, datos in guardado.items():
                (dir_ / f).write_bytes(datos)
            continue
        finally:
            tmp.unlink()
        lint = subprocess.run(["npx", "--yes", "hyperframes@0.8.78", "lint", "--json"], cwd=dir_, capture_output=True,
                              text=True, env={**__import__("os").environ, "HYPERFRAMES_SKIP_SKILLS": "1"})
        errores = [f.get("code") for f in (json.loads(lint.stdout or "{}").get("findings") or []) if f.get("severity") == "error"]
        for f, datos in guardado.items():  # el proyecto queda exactamente como estaba
            (dir_ / f).write_bytes(datos)
        igual = a == b
        # vale si sale lo mismo; si no, solo con diferencias documentadas en la plantilla
        sin_doc = [d for d in dif if not any(d.startswith(x.split(":")[0]) for x in documentadas)]
        ok = not quedan and not errores and not sin_doc and (igual or dif)
        fallos += not ok
        estado = "✓" if ok else "✗"
        print(f"{estado} {nombre:<16} ejemplo {m['ejemplo_entregado']:<32} "
              f"{'misma composición' if igual else 'composición distinta'}"
              f"{'' if not errores else f' · lint {errores}'}{'' if not quedan else f' · huecos {quedan}'}")
        for d in dif:
            print(f"    diferencia: {d}{'  (NO documentada)' if d in sin_doc else '  (documentada)'}")
    aviso = f" ({saltadas} saltada(s) por faltar sus medios en este ordenador)" if saltadas else ""
    print(("todas las comprobadas reproducen su ejemplo" if not fallos else f"{fallos} plantilla(s) con problemas") + aviso)
    return fallos


def nueva(nombre, video, tema, capas):
    s, p = cargar(nombre)
    m = p["_plantilla"]
    mont = DIR / f"{s}.montaje.json"
    suf = m.get("montaje_sufijo")
    if mont.exists() and suf and not video.endswith(f"_{suf}"):
        # primero el montaje (arranque con la frase fuerte); la receta va en el vídeo que sale de él
        if not (ROOT / "out" / f"{video}_corte_916.mp4").exists():
            sys.exit(f"{video}: falta preparar el vídeo (python3 scripts/preparar.py {video})")
        md = ROOT / "proyectos/_montajes" / f"{video}_{suf}.json"
        if md.exists():
            sys.exit(f"ya existe {md.relative_to(ROOT)}: no lo piso")
        md.write_text(mont.read_text().replace("__VIDEO__", video).replace("__NOMBRE__", f"{video}_{suf}"))
        print(f"montaje: {md.relative_to(ROOT)}\nsiguientes pasos:\n"
              f"  1. rellenar sus huecos (la frase más fuerte, en segundos de out/{video}_corte_916.mp4)\n"
              f"  2. python3 scripts/montaje.py {md.relative_to(ROOT)}\n"
              f"  3. python3 scripts/preparar.py {video}_{suf} --sin-silencios\n"
              f"  4. python3 scripts/recorte.py proyectos/{video}_{suf}\n"
              f"  5. python3 scripts/plantilla.py nueva \"{m['receta']}\" {video}_{suf} --tema \"…\"")
        return
    d = ROOT / "proyectos" / video
    if not (d / "palabras.json").exists():
        sys.exit(f"{video}: falta preparar el vídeo (python3 scripts/preparar.py {video})")
    r = {k: v for k, v in p.items() if k != "_plantilla"}
    r = {"tema": tema or r["tema"], **{k: v for k, v in r.items() if k != "tema"}}
    r["_receta"] = f"{m['receta']} (plantilla {s}, ejemplo: {m['ejemplo_entregado']}). {datetime.date.today():%d-%b-%Y}."
    for c in capas:
        capa = json.loads((DIR / "capas" / f"{slug(c)}.json").read_text())
        r.update({k: v for k, v in capa.items() if not k.startswith("_")})
    try:  # centro de la cara con YuNet; si no hay entorno de OpenCV, queda el hueco
        out = subprocess.run([kit.python_opencv(), str(ROOT / "scripts/cara.py"), str(d)],
                             capture_output=True, text=True, cwd=ROOT).stdout
        cx, cy = map(int, re.search(r"\[(\d+),\s*(\d+)\]", out).groups())
        r["centro_cara"] = [cx, cy]
        if isinstance(r.get("ranking"), dict) and es_hueco(r["ranking"].get("centro")):
            r["ranking"]["centro"] = f"{cx}px {cy}px"
    except Exception:
        pass
    dst = d / "recetas" / f"{s}.json"
    dst.parent.mkdir(exist_ok=True)
    if dst.exists():
        sys.exit(f"ya existe {dst.relative_to(ROOT)}: no la piso")
    dst.write_text(json.dumps(r, ensure_ascii=False, indent=2) + "\n")
    print(f"receta: {dst.relative_to(ROOT)}  ({m['receta']}; ejemplo: {m['ejemplo_entregado']} → {m['ejemplo']})")
    if m.get("montaje") and not suf:
        print(f"montaje de referencia: {m['montaje']} (este tipo se monta a mano antes de la receta)")
    print("cómo rellenarla:\n  - " + "\n  - ".join(m["rellenar"]))
    print("huecos:\n  " + "\n  ".join(huecos(r)))


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="orden", required=True)
    sp.add_parser("lista")
    n = sp.add_parser("nueva")
    n.add_argument("receta")
    n.add_argument("video")
    n.add_argument("--tema")
    n.add_argument("--capa", action="append", default=[])
    c = sp.add_parser("comprobar")
    c.add_argument("receta")
    pr = sp.add_parser("probar")
    pr.add_argument("nombre", nargs="?")
    a = ap.parse_args()
    if a.orden == "lista":
        for s, p in plantillas().items():
            m = p["_plantilla"]
            print(f"{m['receta']:<18} {s:<16} {m['cuando']}\n{'':<35}ejemplo: {m['ejemplo_entregado']}")
        for p in sorted((DIR / "capas").glob("*.json")):
            m = json.loads(p.read_text())["_capa"]
            print(f"capa {m['nombre']:<13} {p.stem:<16} {m['cuando']}")
    elif a.orden == "nueva":
        nueva(a.receta, a.video, a.tema, a.capa)
    elif a.orden == "comprobar":
        comprobar(a.receta)
        print("sin huecos")
    else:
        sys.exit(1 if probar(a.nombre) else 0)


if __name__ == "__main__":
    main()
