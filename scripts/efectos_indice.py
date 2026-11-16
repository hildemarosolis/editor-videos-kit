#!/usr/bin/env python3
"""Índice de la biblioteca de efectos (`subtitulos/efectos/indice.json`, plan del 8-nov-2026).

  python3 scripts/efectos_indice.py comprobar   ¿hay alguna clave de receta del código sin efecto en el índice?
                                                ¿algún efecto sin vídeo ni marca «sin usar todavía»? (sale con 1 si hay huecos)
  python3 scripts/efectos_indice.py usos        rellena «videos» de cada efecto cruzando las recetas con proyectos/_entregas.md
  python3 scripts/efectos_indice.py lista       tabla corta: código, familia, nombre, nº de vídeos
  python3 scripts/efectos_indice.py receta <archivo.json>   qué efectos lleva una receta
  python3 scripts/efectos_indice.py columna     rellena la columna «Efectos» de proyectos/_entregas.md en las filas sin ella
  python3 scripts/efectos_indice.py elegidos <carpeta> [--video V] [--receta R.json]
                                                los «elegidos» de la página (ArtifactData list con out_dir → <carpeta>):
                                                cómo se activa cada uno y, con --receta, cuáles lleva ya y cuáles faltan.
                                                Con --video los apunta en proyectos/V/elegidos.json (entregar.py los mira).

Al entregar (scripts/terminados.py → registrar), cada fila de _entregas.md lleva sus códigos en la columna «Efectos»
y el índice se pone al día solo (`usos`).

El índice es la fuente: nombre, familia y «para qué» se escriben a mano. Este script solo cruza y comprueba.
La comprobación lee el código: cada `cfg.get("clave")` de los scripts de montaje, cada `estilo/tipo/aspecto == "x"`,
cada escena de la pizarra, cada bloque del carrusel y cada entrada de montaje tiene que estar en el «cubre» de un
efecto o en «no_efecto» (con su motivo). Así un efecto nuevo no se queda fuera de la biblioteca.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kit  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
INDICE = ROOT / "subtitulos/efectos/indice.json"
ENTREGAS = ROOT / "proyectos/_entregas.md"
# scripts que montan piezas sobre el vídeo (los que leen la receta)
SCRIPTS = ["subtitulos", "gancho", "efectos", "ranking", "pizarra", "detras", "pegatina", "barrido", "niveles"]


def cargar():
    return json.loads(INDICE.read_text())


def guardar(idx):
    INDICE.write_text(json.dumps(idx, ensure_ascii=False, indent=1) + "\n")


def claves_del_codigo():
    """Claves de receta y variantes que el código sabe montar → {token: dónde}."""
    out = {}
    for s in SCRIPTS:
        txt = (ROOT / f"scripts/{s}.py").read_text()
        for m in re.finditer(r'cfg(?:\.get\(|\[)"([a-z_]+)"', txt):
            out.setdefault(m.group(1), f"{s}.py")
        for m in re.finditer(r'\.get\("(estilo|tipo|aspecto)"\)\s*[!=]=\s*"([a-z_]+)"', txt):
            out.setdefault(f"{m.group(1)}={m.group(2)}", f"{s}.py")
    esc = re.search(r"ESCENAS = \{(.*?)\}", (ROOT / "scripts/pizarra.py").read_text(), re.S).group(1)
    for t in re.findall(r'"([a-z_]+)":', esc):
        out[f"pizarra.escenas.tipo={t}"] = "pizarra.py"
    for t in re.findall(r'if tipo == "([a-z_]+)"', (ROOT / "scripts/carrusel.py").read_text()):
        out[f"carrusel.bloque={t}"] = "carrusel.py"
    for t in re.findall(r'\.get\("entrada"\) == "([a-z_]+)"', (ROOT / "scripts/montaje.py").read_text()):
        out[f"entrada={t}"] = "montaje.py"
    return out


def cubierto(tok, cubre, no_efecto):
    if tok in no_efecto:
        return True
    if "=" in tok and "." not in tok:   # variante suelta (estilo=alarma): vale en cualquier clave
        return any(c == tok or c.endswith("." + tok) for c in cubre)
    return tok in cubre


def comprobar():
    idx = cargar()
    cubre = {c for e in idx["efectos"] for c in e["cubre"]}
    huecos = [(t, d) for t, d in sorted(claves_del_codigo().items()) if not cubierto(t, cubre, idx["no_efecto"])]
    codigos = [e["codigo"] for e in idx["efectos"]]
    malos = [c for n, c in enumerate(codigos) if c != f"E-{n + 1:02d}"]
    sin = [e["codigo"] for e in idx["efectos"] if e["estado"] == "activo" and not e.get("videos") and not e.get("sin_usar")]
    for t, d in huecos:
        print(f"  ✗ «{t}» ({d}) no está en ningún efecto del índice ni en «no_efecto»")
    for c in malos:
        print(f"  ✗ {c}: los códigos van seguidos y no se reutilizan")
    for c in sin:
        print(f"  ✗ {c}: sin vídeos y sin «sin_usar» (pasa `efectos_indice.py usos`)")
    n = len(idx["efectos"])
    act = sum(e["estado"] == "activo" for e in idx["efectos"])
    if huecos or malos or sin:
        sys.exit(f"índice con huecos: {len(huecos)} claves sin efecto, {len(sin)} efectos sin uso apuntado")
    print(f"índice completo: {n} efectos ({act} activos), {len(claves_del_codigo())} claves del código cubiertas")
    try:   # la galería no bloquea la comprobación, solo avisa
        import galeria
        des = galeria.desfasados()
        if des:
            print(f"  aviso: {len(des)} clip(s) de la galería por rehacer ({' '.join(des)}): python3 scripts/galeria.py al-dia")
    except Exception:  # noqa: BLE001
        pass


# ---------- uso en recetas ----------

def _valores(r, ruta):
    """Valores en la ruta con puntos; las listas se aplanan («pizarra.escenas» → cada escena)."""
    vs = [r]
    for p in ruta.split("."):
        nx = []
        for v in vs:
            v = v.get(p) if isinstance(v, dict) else None
            if v is None or v is False:
                continue
            nx.extend(v if isinstance(v, list) else [v])
        vs = nx
    return vs


def _cumple(item, donde):
    for k, v in donde.items():
        x = item.get(k) if isinstance(item, dict) else None
        if v is None and x not in (None, False, ""):
            return False
        if v is True and not x:
            return False
        if v not in (None, True) and x != v:
            return False
    return True


def _alt(a, r, ctx):
    if a.get("siempre"):   # los subtítulos y demás piezas fijas no van en carruseles ni en episodios largos
        return ctx.get("formato") not in SIN_PIEZAS
    if "montaje" in a:
        return a["montaje"] in ctx.get("entradas", ())
    if "proyecto" in a:
        return ctx.get("formato") == a["proyecto"]
    if "auto" in a:
        if r.get(a["auto"]) is False or ctx.get("formato") in SIN_PIEZAS:
            return False
        return not any(_alt(s, r, ctx) for s in a.get("salvo", []))
    vs = _valores(r, a["ruta"])
    if "contiene" in a:
        return any(a["contiene"] in str(v) for v in vs)
    return any(_cumple(v, a.get("donde", {})) for v in vs)


SIN_PIEZAS = ("carrusel", "largo")


def usa(efecto, r, ctx=None):
    return any(_alt(a, r, ctx or {}) for a in efecto["usa"])


def entregas():
    """Filas de _entregas.md: vídeo, proyecto, receta, publicado."""
    out = []
    for ln in ENTREGAS.read_text().splitlines():
        c = [x.strip() for x in ln.strip().strip("|").split("|")]
        if len(c) < 6 or not re.match(r"\d{4}-\d\d-\d\d$", c[0]):
            continue
        pub = c[5]
        out.append({"video": re.sub(r"\.mp4$", "", c[2]), "proyecto": c[3], "receta": c[4],
                    "publicado": bool(pub) and not pub.lower().startswith("no")})
    return out


def receta_de(fila, ruta=None):
    """(receta, contexto) de una entrega; `ruta` es el archivo de la receta si se sabe (al entregar)."""
    p, r = fila["proyecto"], fila["receta"]
    if p.startswith("carrusel "):
        # El carrusel.json cuenta como receta (15-nov-2026): así se ven sus bloques (p. ej. "foto", E-65).
        c = ROOT / "carruseles" / p.split(" ", 1)[1] / "carrusel.json"
        return (json.loads(c.read_text()) if c.exists() else {}), {"formato": "carrusel"}
    ctx = {"formato": "largo"} if r == "largo.json" else {}
    if (ROOT / "proyectos/_rutas" / f"{p}.json").exists():
        ctx["formato"] = "ruta"
    m = ROOT / "proyectos/_montajes" / f"{p}.json"
    if m.exists():
        ctx["entradas"] = {t.get("entrada") for t in json.loads(m.read_text()).get("tramos", [])}
    cands = [Path(ruta)] if ruta else []
    cands += [ROOT / "proyectos" / p / "recetas" / r, ROOT / "proyectos" / p / r, ROOT / "subtitulos/recetas" / r]
    for f in cands:
        if r.endswith(".json") and f.exists():
            return json.loads(f.read_text()), ctx
    return None, ctx


def codigos(proyecto, receta, ruta=None, idx=None):
    """Códigos E-NN que lleva una entrega, o None si no hay receta guardada."""
    idx = idx or cargar()
    r, ctx = receta_de({"proyecto": proyecto, "receta": Path(receta).name}, ruta)
    if r is None:
        return None
    return [e["codigo"] for e in idx["efectos"] if usa(e, r, ctx)]


def texto_codigos(cs):
    return "—" if cs is None else (" ".join(cs) or "ninguno")


def usos():
    idx = cargar()
    for e in idx["efectos"]:
        e["videos"] = []
    sin_receta = []
    for f in entregas():
        r, ctx = receta_de(f)
        if r is None:
            sin_receta.append(f["video"])
            continue
        for e in idx["efectos"]:
            if usa(e, r, ctx):
                e["videos"].append({k: f[k] for k in ("video", "proyecto", "publicado")})
    for e in idx["efectos"]:
        if e["videos"]:
            e.pop("sin_usar", None)
        else:
            e["sin_usar"] = True
    guardar(idx)
    usados = sum(bool(e["videos"]) for e in idx["efectos"])
    print(f"{usados} efectos con vídeo, {len(idx['efectos']) - usados} sin usar todavía")
    for v in sin_receta:
        print(f"  (sin receta guardada, no cuenta: {v})")


# ---------- columna «Efectos» de _entregas.md ----------

CAB, SEP = "| Efectos |", "|---|"


def columna():
    """Añade la columna «Efectos» a la tabla y la rellena en las filas que no la tienen (no toca las que ya la tienen)."""
    idx, out, n = cargar(), [], 0
    for ln in ENTREGAS.read_text().splitlines():
        c = [x.strip() for x in ln.strip().strip("|").split("|")]
        if ln.startswith("| Entregado |") and "Efectos" not in c:
            ln = ln.rstrip() + " Efectos |"
        elif ln.startswith("|---") and len(c) == 6:
            ln = ln.rstrip() + "---|"
        elif len(c) == 6 and re.match(r"\d{4}-\d\d-\d\d$", c[0]):
            ln = ln.rstrip() + f" {texto_codigos(codigos(c[3], c[4], idx=idx))} |"
            n += 1
        out.append(ln)
    ENTREGAS.write_text("\n".join(out) + "\n")
    print(f"columna «Efectos»: {n} filas rellenadas")


# ---------- elegidos de la página ----------

PAGINA = kit.ajustes().get("biblioteca_url", "")  # la página de la biblioteca (editor.json → biblioteca_url)


def leer_elegidos(carpeta):
    """Documentos de la colección «elegidos» guardados por ArtifactData (list con out_dir). Sin los ya usados."""
    docs = []
    for f in sorted(Path(carpeta).rglob("*.json")):
        try:
            d = json.loads(f.read_text())
        except ValueError:
            continue
        d = d.get("data", d) if isinstance(d.get("data"), dict) else d
        if d.get("codigo") and not d.get("usado_en"):
            docs.append(d)
    return docs


def ejemplo(cod):
    """La receta del escaparate de ese efecto, sin su clave de galería: cómo se escribe en una receta real."""
    f = ROOT / "proyectos/_escaparate/recetas" / f"{cod}.json"
    if not f.exists():
        return None
    r = json.loads(f.read_text())
    return {k: v for k, v in r.items() if not k.startswith("_") and k not in ("tema", "centro_cara", "seguir", "comenta", "cierre")}


def elegidos(carpeta, video=None, receta=None):
    idx = cargar()
    por = {e["codigo"]: e for e in idx["efectos"]}
    docs = leer_elegidos(carpeta)
    if not docs:
        print(f"ningún efecto elegido en la página ({PAGINA or 'sin enlace: ponlo en editor.json → biblioteca_url'})")
        return []
    lleva = set()
    if receta:
        r = json.loads(Path(receta).read_text())
        ctx = {}
        if video:
            ctx = receta_de({"proyecto": video, "receta": Path(receta).name}, receta)[1]
        lleva = {e["codigo"] for e in idx["efectos"] if usa(e, r, ctx)}
    print(f"{len(docs)} elegido(s) en la página:")
    for d in docs:
        c, e = d["codigo"], por.get(d["codigo"])
        if not e:
            print(f"  {c}: no está en el índice (¿código viejo?)")
            continue
        marca = "" if not receta else ("  ✓ ya en la receta" if c in lleva else "  · falta en la receta")
        print(f"  {c} {e['nombre']} ({e['familia']}){marca}")
        print(f"      para qué: {e['para_que']}")
        if e["estado"] != "activo":
            print(f"      ¡ojo! está {e['estado']}")
        if d.get("nota"):
            print(f"      nota del creador: «{d['nota']}»")
        print(f"      se activa con: {', '.join(e['cubre'])} · ejemplo: {json.dumps(ejemplo(c), ensure_ascii=False)[:300]}")
    if video:
        dst = ROOT / "proyectos" / video / "elegidos.json"
        dst.write_text(json.dumps({"pagina": PAGINA, "elegidos": [d["codigo"] for d in docs]}, indent=1) + "\n")
        print(f"apuntados en {dst.relative_to(ROOT)}: entregar.py dirá cuáles usó el vídeo")
    return [d["codigo"] for d in docs]


def lista():
    for e in cargar()["efectos"]:
        n = len(e.get("videos", []))
        print(f"{e['codigo']}  {e['familia']:<10} {e['nombre']:<38} {n:>3} vídeos{'' if e['estado'] == 'activo' else '  [' + e['estado'] + ']'}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "comprobar"
    if cmd == "receta":
        idx, r = cargar(), json.loads(Path(sys.argv[2]).read_text())
        print(" ".join(e["codigo"] for e in idx["efectos"] if usa(e, r)))
    elif cmd == "elegidos":
        import argparse
        ap = argparse.ArgumentParser(prog="efectos_indice.py elegidos")
        ap.add_argument("carpeta")
        ap.add_argument("--video")
        ap.add_argument("--receta")
        a = ap.parse_args(sys.argv[2:])
        elegidos(a.carpeta, a.video, a.receta)
    else:
        {"comprobar": comprobar, "usos": usos, "lista": lista, "columna": columna}[cmd]()
