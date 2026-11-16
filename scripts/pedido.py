#!/usr/bin/env python3
"""Fase previa de /editor: antes de editar, el creador dice para qué marca es el vídeo y elige en la biblioteca
primero el molde (una receta del catálogo) y luego los retoques (efectos sueltos). Claude arma la receta con eso.
Cada marca tiene su kit para que los estilos no se mezclen.

Kits: `marca/kits/<id>.json` (personal, una marca con la que colaboras, un programa de podcast…):
  nombre, tipo (personal | socio | cliente | puntual | programa), estado (aprobado | borrador | pendiente), publica, colabora,
  logo, colores {acento, principal, secundario}, receta (claves que se mezclan en la receta: acento, seguir…),
  cierres (los que admite la marca; la rotación de cierre.py sigue mandando), moldes (recomendados), sin_efectos
  (no se ofrecen con esta marca), proyectos (vídeos de antes de los kits, con comodines), notas.
  Un vídeo sin `"marca"` en la receta cuenta como personal. Sin marca/kits/personal.json, el kit personal sale de
  marca/marca.json (tu acento y todos tus cierres).

Pedido: un documento por vídeo en la colección «pedidos» de la página de la biblioteca (su URL, en editor.json →
  "biblioteca_url", tras publicarla con galeria.py pagina)
  {video, marca, molde, idea, efectos: [{codigo, nota}], estado: abierto | listo, actualizado}.

  python3 scripts/pedido.py kits                         → los kits, con su estado
  python3 scripts/pedido.py abrir <VIDEO> [--marca id]  → el documento para ArtifactData (set en «pedidos/<id>»)
  python3 scripts/pedido.py leer <carpeta> --video V [--proyecto P]  → lee el pedido (ArtifactData list con out_dir),
                                                           dice cómo se arma y lo deja en proyectos/P/pedido.json
  python3 scripts/pedido.py aplicar <VIDEO> --receta R  → mete en la receta la marca y las claves de su kit
  python3 scripts/pedido.py comprobar <VIDEO> --receta R → ¿la receta lleva el molde, los retoques, el acento y un
                                                           cierre de la marca? (sale con error si falta algo)
  python3 scripts/pedido.py cerrar <VIDEO> [--proyecto P] → al entregar: deja de salir en el panel
  python3 scripts/pedido.py nueva-marca "Nombre" [--tipo puntual|socio|cliente]  → kit nuevo en borrador
  (abrir, leer y cerrar apuntan el pedido en proyectos/_pedidos.json, fuera de git: el panel lo enseña)
  python3 scripts/pedido.py usados                       → efectos ya usados con cada marca (de _entregas.md)
  python3 scripts/pedido.py probar                       → pruebas
"""
import argparse
import fnmatch
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import kit as kitmod  # noqa: E402  (como módulo aparte: aquí kit() es el kit de una marca)

KITS = ROOT / "marca/kits"
PLANTILLAS = ROOT / "subtitulos/recetas/plantillas"
PAGINA = kitmod.ajustes().get("biblioteca_url")   # la página de la biblioteca (galeria.py pagina); None sin publicar
REGISTRO = ROOT / "proyectos/_pedidos.json"  # fuera de git; lo lee estado.py para el panel
TIPOS = ("personal", "socio", "cliente", "puntual", "programa")
ESTADOS = ("aprobado", "borrador", "pendiente")
HEX = re.compile(r"#[0-9A-Fa-f]{6}$")


def pagina():
    """La URL de la página de la biblioteca, o cómo ponerla si aún no está."""
    return PAGINA or "<URL de la biblioteca: publícala (galeria.py pagina) y ponla en editor.json → \"biblioteca_url\">"


def slug(texto):
    t = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-") or "sin-nombre"


# ── kits ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def kit_personal():
    """El kit personal cuando no hay marca/kits/personal.json: tu marca de marca/marca.json."""
    import cierre
    return {"id": "personal", "nombre": "Marca personal", "tipo": "personal", "estado": "aprobado",
            "publica": f"En {kitmod.usuario()}, sin colaboración", "colabora": None, "logo": None,
            "colores": {"acento": kitmod.acento()}, "receta": {}, "cierres": list(cierre.CIERRES), "moldes": [],
            "sin_efectos": ["E-35"], "proyectos": [],
            "notas": "Kit por defecto (no hay marca/kits/personal.json): tu acento y todos tus cierres."}


def kits():
    """{id: kit}, con «personal» el primero."""
    out = {}
    for f in sorted(KITS.glob("*.json"), key=lambda p: (p.stem != "personal", p.stem)):
        k = json.loads(f.read_text())
        k["id"] = f.stem
        out[f.stem] = k
    if "personal" not in out:
        out = {"personal": kit_personal(), **out}
    return out


def kit(marca):
    ks = kits()
    if marca not in ks:
        sys.exit(f"no hay kit «{marca}» en marca/kits/ (hay: {', '.join(ks)}). Uno nuevo: pedido.py nueva-marca")
    return ks[marca]


def marca_de(proyecto, receta=None, ks=None):
    """La marca de un vídeo: la de su receta, o la del kit cuyo «proyectos» lo nombra; si no, personal."""
    if receta and receta.get("marca"):
        return receta["marca"]
    for k in (ks or kits()).values():
        if any(fnmatch.fnmatch(proyecto, p) for p in k.get("proyectos", [])):
            return k["id"]
    return "personal"


def usados():
    """{marca: [códigos]} de los efectos que ya salieron en vídeos de cada marca (cruza _entregas.md y recetas)."""
    import efectos_indice
    idx, ks, out = efectos_indice.cargar(), kits(), {}
    for fila in efectos_indice.entregas():
        r, ctx = efectos_indice.receta_de(fila)
        if r is None:
            continue
        m = marca_de(fila["proyecto"], r, ks)
        out.setdefault(m, set()).update(e["codigo"] for e in idx["efectos"] if efectos_indice.usa(e, r, ctx))
    return {m: sorted(cs) for m, cs in out.items()}


def problemas_kit(k):
    """Lo que está mal en un kit (lista vacía si está bien)."""
    import cierre
    import efectos_indice
    cods = {e["codigo"] for e in efectos_indice.cargar()["efectos"]}
    mal = []
    for campo in ("nombre", "tipo", "estado", "cierres", "sin_efectos", "receta"):
        if campo not in k:
            mal.append(f"falta «{campo}»")
    if k.get("tipo") not in TIPOS:
        mal.append(f"tipo «{k.get('tipo')}» (vale: {', '.join(TIPOS)})")
    if k.get("estado") not in ESTADOS:
        mal.append(f"estado «{k.get('estado')}» (vale: {', '.join(ESTADOS)})")
    for c in k.get("cierres", []):
        if c not in cierre.CIERRES:
            mal.append(f"cierre «{c}» no existe")
    for c in k.get("sin_efectos", []):
        if c not in cods:
            mal.append(f"efecto {c} no está en el índice")
    for nombre, col in list(k.get("colores", {}).items()) + [("receta.acento", k.get("receta", {}).get("acento"))]:
        if col is not None and not HEX.match(str(col)):
            mal.append(f"color {nombre} «{col}» no es #RRGGBB")
    for campo in ("logo", "logo_alt"):
        if k.get(campo) and not (ROOT / k[campo]).exists():
            mal.append(f"{campo} {k[campo]} no existe")
    if k.get("estado") != "pendiente" and not k.get("receta", {}).get("acento") and k.get("tipo") != "personal":
        mal.append("sin acento en «receta» (sin él sale tu color de acento y se mezcla)")
    for m in k.get("moldes", []):
        if not (PLANTILLAS / f"{m}.json").exists():
            mal.append(f"molde «{m}» no es una plantilla")
    return mal


def moldes():
    """Las recetas del catálogo como moldes: id de plantilla, nombre, cuándo y su ejemplo entregado."""
    out = []
    for f in sorted(PLANTILLAS.glob("*.json")):
        if f.name.endswith(".montaje.json"):
            continue
        p = json.loads(f.read_text()).get("_plantilla", {})
        if p.get("receta"):
            out.append({"id": f.stem, "nombre": p["receta"], "cuando": p.get("cuando", ""),
                        "ejemplo": p.get("ejemplo_entregado", ""), "receta_ejemplo": p.get("ejemplo", "")})
    return out


def nueva_marca(nombre, tipo="puntual"):
    mid = slug(nombre)
    f = KITS / f"{mid}.json"
    if f.exists():
        sys.exit(f"ya existe {f.relative_to(ROOT) if f.is_relative_to(ROOT) else f}")
    k = {"id": mid, "nombre": nombre, "tipo": tipo, "estado": "pendiente",
         "publica": f"En {kitmod.usuario()}, en colaboración con {nombre}", "colabora": None, "logo": None,
         "colores": {}, "receta": {}, "cierres": ["conversacion", "info"], "moldes": [], "sin_efectos": ["E-35"],
         "proyectos": [], "notas": "Falta el logo y sus colores. Hasta tenerlos sale con tu color de acento."}
    KITS.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(k, ensure_ascii=False, indent=1) + "\n")
    print(f"kit nuevo: {f.relative_to(ROOT) if f.is_relative_to(ROOT) else f} (pendiente)")
    print("  falta: el logo (a marca/logos/), su @ si colabora y el color de la palabra activa;")
    print("  luego estado «borrador» y, con su visto bueno, «aprobado». Rehaz la página: galeria.py pagina")
    return k


# ── pedido ────────────────────────────────────────────────────────────────────────────────────────────────────────
def registro():
    """Pedidos apuntados en este ordenador: {doc_id: {video, marca, estado, abierto, proyecto?}}. Los lee estado.py
    para el panel, que no puede leer la página. La página sigue mandando: esto es solo el aviso."""
    try:
        return json.loads(REGISTRO.read_text())
    except (OSError, ValueError):
        return {}


def registrar(video, **campos):
    reg = registro()
    k = slug(video)
    reg[k] = {**reg.get(k, {"video": video}), **{c: v for c, v in campos.items() if v is not None}}
    REGISTRO.parent.mkdir(parents=True, exist_ok=True)
    tmp = REGISTRO.with_suffix(".tmp")
    tmp.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n")
    tmp.replace(REGISTRO)
    return reg[k]


def abrir(video, marca=None):
    from datetime import date
    if marca:
        kit(marca)
    doc = {"video": video, "marca": marca, "molde": None, "idea": "", "efectos": [], "estado": "abierto"}
    registrar(video, marca=marca or "personal", estado="abierto", abierto=date.today().isoformat())
    print(f"ArtifactData set · url {pagina()} · collection «pedidos» · doc_id «{slug(video)}»")
    print(json.dumps(doc, ensure_ascii=False))
    return doc


def cerrar(video, proyecto=None):
    """Al entregar: el pedido deja de salir en el panel (en la página, ArtifactData update «entregado»)."""
    r = registrar(video, estado="entregado", proyecto=proyecto)
    print(f"pedido «{r['video']}» cerrado en {REGISTRO.name}")
    print(f"ArtifactData update · url {pagina()} · «pedidos/{slug(video)}» · "
          f"{json.dumps({'estado': 'entregado', 'entregado_en': proyecto or video}, ensure_ascii=False)}")


def leer_pedidos(carpeta):
    """Documentos de la colección «pedidos» guardados por ArtifactData (list con out_dir)."""
    docs = []
    for f in sorted(Path(carpeta).rglob("*.json")):
        try:
            d = json.loads(f.read_text())
        except ValueError:
            continue
        d = d.get("data", d) if isinstance(d, dict) and isinstance(d.get("data"), dict) else d
        if isinstance(d, dict) and d.get("video") and "efectos" in d:
            docs.append(d)
    return docs


def buscar(docs, video):
    for d in docs:
        if d["video"] == video or slug(d["video"]) == slug(video):
            return d
    return None


def cierres_ahora(k):
    """(los de la marca que pueden ir hoy, los que deja la rotación)."""
    import cierre
    libres = cierre.libres()[0]
    return [c for c in k.get("cierres", []) if c in libres], libres


def leer(carpeta, video, proyecto=None):
    import efectos_indice
    d = buscar(leer_pedidos(carpeta), video)
    if not d:
        sys.exit(f"no hay pedido de «{video}» en {carpeta}. ¿Lo abrió en la página? (colección «pedidos»)")
    marca = d.get("marca") or "personal"
    k = kit(marca)
    por = {e["codigo"]: e for e in efectos_indice.cargar()["efectos"]}
    ms = {m["id"]: m for m in moldes()}
    print(f"Pedido de «{d['video']}» · {d.get('estado', 'abierto')}")
    if d.get("estado") != "listo":
        print("  ¡ojo! no ha pulsado «Listo»: puede que siga eligiendo")
    print(f"\nMarca: {k['nombre']} ({k['estado']}) · {k.get('publica', '')}")
    if not d.get("marca"):
        print("  no eligió marca: va como personal")
    if k["estado"] != "aprobado":
        print(f"  kit en {k['estado']}: enséñale cómo queda y que lo apruebe ({k.get('notas', '')})")
    if k.get("receta"):
        print(f"  la receta lleva: {json.dumps(k['receta'], ensure_ascii=False)}  (pedido.py aplicar lo pone)")
    molde = d.get("molde")
    print("\nMolde:", end=" ")
    if molde in ms:
        m = ms[molde]
        print(f"{m['nombre']} (ejemplo: {m['ejemplo']})")
        print(f"  python3 scripts/plantilla.py nueva \"{m['nombre']}\" {proyecto or '<PROYECTO>'} --tema \"…\""
              + ("" if proyecto else "   (el proyecto es la carpeta de proyectos/ que deja preparar.py)"))
    elif molde == "claude":
        print("que lo proponga Claude (recomienda uno con «Cómo elegir» del catálogo, dentro del kit)")
    else:
        print("sin elegir: pregúntale o recomiéndalo tú")
    if k.get("moldes") and molde in ms and molde not in k["moldes"]:
        print(f"  aviso: el kit recomienda {', '.join(k['moldes'])}")
    if d.get("idea"):
        print(f"\nLo que tiene en la cabeza: «{d['idea']}»")
    efs = d.get("efectos") or []
    print(f"\nRetoques ({len(efs)}):")
    for x in efs:
        c, e = x.get("codigo"), por.get(x.get("codigo"))
        if not e:
            print(f"  {c}: no está en el índice")
            continue
        aviso = "  ¡no es de esta marca (sin_efectos)!" if c in k.get("sin_efectos", []) else ""
        print(f"  {c} {e['nombre']}{aviso}")
        if x.get("nota"):
            print(f"      nota: «{x['nota']}»")
        print(f"      se activa con: {', '.join(e['cubre'])} · ejemplo: "
              f"{json.dumps(efectos_indice.ejemplo(c), ensure_ascii=False)[:260]}")
    if k.get("cierres"):
        hoy, libres = cierres_ahora(k)
        print(f"\nCierre: la marca admite {', '.join(k['cierres'])}; la rotación deja {', '.join(libres)}.")
        print(f"  → puede ir: {', '.join(hoy)}" if hoy else
              "  → ninguno de la marca puede ir hoy: díselo y que elija entre esperar o usar uno de la rotación")
    else:
        print("\nCierre: el propio de la marca (sin «Comenta» ni cierre que rota)")
    dst = ROOT / "proyectos" / (proyecto or video) / "pedido.json"
    dst.parent.mkdir(parents=True, exist_ok=True)
    guardado = {"pagina": PAGINA, "video": d["video"], "marca": marca, "molde": molde, "idea": d.get("idea", ""),
                "efectos": [{"codigo": x.get("codigo"), "nota": x.get("nota", "")} for x in efs],
                "estado": d.get("estado", "abierto")}
    dst.write_text(json.dumps(guardado, ensure_ascii=False, indent=1) + "\n")
    registrar(d["video"], marca=marca, estado=d.get("estado", "abierto"), proyecto=proyecto or video)
    print(f"\napuntado en {dst.relative_to(ROOT)}: aplicar y comprobar lo leen de ahí")
    return guardado


def _pedido(video):
    f = ROOT / "proyectos" / video / "pedido.json"
    if not f.exists():
        sys.exit(f"{video} no tiene pedido.json: primero pedido.py leer")
    return json.loads(f.read_text())


def aplicar(video, receta, simular=False):
    p = _pedido(video)
    k = kit(p["marca"])
    rf = Path(receta)
    r = json.loads(rf.read_text())
    cambios = {"marca": p["marca"], **k.get("receta", {})}
    hechos = {c: v for c, v in cambios.items() if r.get(c) != v}
    for c, v in hechos.items():
        print(f"  {c}: {json.dumps(r.get(c), ensure_ascii=False)} → {json.dumps(v, ensure_ascii=False)}")
    if not hechos:
        print("  la receta ya lleva el kit")
    elif not simular:
        r.update(hechos)
        rf.write_text(json.dumps(r, ensure_ascii=False, indent=2) + "\n")
        print(f"kit «{k['nombre']}» aplicado a {rf}")
    return hechos


def comprobar(video, receta):
    import cierre
    import efectos_indice
    p = _pedido(video)
    k = kit(p["marca"])
    r = json.loads(Path(receta).read_text())
    mal, bien = [], []
    if r.get("marca") != p["marca"]:
        mal.append(f"la receta no lleva \"marca\": \"{p['marca']}\" (pedido.py aplicar)")
    for c, v in k.get("receta", {}).items():
        if r.get(c) != v:
            mal.append(f"la receta no lleva {c} = {json.dumps(v, ensure_ascii=False)} del kit")
    ms = {m["id"]: m for m in moldes()}
    if p.get("molde") in ms:
        nombre = ms[p["molde"]]["nombre"]
        if not str(r.get("_receta", "")).startswith(nombre):
            mal.append(f"el molde pedido es «{nombre}» y la receta dice «{str(r.get('_receta', '¿?'))[:40]}»")
        else:
            bien.append(f"molde {nombre}")
    idx = efectos_indice.cargar()
    ctx = efectos_indice.receta_de({"proyecto": video, "receta": Path(receta).name}, receta)[1]
    lleva = {e["codigo"] for e in idx["efectos"] if efectos_indice.usa(e, r, ctx)}
    for x in p.get("efectos", []):
        (bien if x["codigo"] in lleva else mal).append(
            f"{x['codigo']} {'en la receta' if x['codigo'] in lleva else 'pedido y no está en la receta'}")
    for c in sorted(lleva & set(k.get("sin_efectos", []))):
        mal.append(f"{c} no va con {k['nombre']} (sin_efectos)")
    c = cierre.de_receta(r)
    if k.get("cierres"):
        if not c:
            mal.append("la receta no lleva \"cierre\"")
        elif c["tipo"] not in k["cierres"]:
            mal.append(f"cierre «{c['tipo']}» no es de {k['nombre']} (admite {', '.join(k['cierres'])})")
        else:
            bien.append(f"cierre {c['tipo']}")
    elif c and r.get("comenta") is not False:
        mal.append(f"{k['nombre']} lleva su cierre propio, no «{c['tipo']}»")
    for b in bien:
        print(f"  ✓ {b}")
    for m in mal:
        print(f"  ✗ {m}")
    print("pedido cumplido" if not mal else f"{len(mal)} cosa(s) por arreglar")
    return mal


# ── pruebas ───────────────────────────────────────────────────────────────────────────────────────────────────────
def probar():
    import contextlib
    import io
    import shutil
    import tempfile
    fallos = []

    def ok(cond, txt):
        print(f"  {'✓' if cond else '✗'} {txt}")
        if not cond:
            fallos.append(txt)

    ks = kits()   # los tuyos (o solo el personal por defecto, si aún no hay ninguno)
    ok(list(ks)[0] == "personal", "personal es el primer kit")
    for k in ks.values():
        mal = problemas_kit(k)
        ok(not mal, f"kit {k['id']}: {'bien' if not mal else '; '.join(mal)}")
    acentos = [k["receta"].get("acento") for k in ks.values() if k["receta"].get("acento")]
    ok(len(acentos) == len(set(acentos)), "ningún acento repetido entre marcas")
    ok(kitmod.acento().upper() not in [a.upper() for a in acentos], "ninguna marca usa tu color de acento")
    socio = {"nombre": "Socio de prueba", "tipo": "socio", "estado": "borrador", "publica": "En colaboración",
             "colabora": None, "logo": None, "colores": {"acento": "#34C6B6"}, "receta": {"acento": "#34C6B6"},
             "cierres": ["conversacion", "info"], "moldes": [], "sin_efectos": ["E-35"], "proyectos": ["RUTA_*"]}
    falsos = {"personal": kit_personal(), "socio-prueba": {**socio, "id": "socio-prueba"}}
    ok(not problemas_kit(falsos["socio-prueba"]), "el kit de prueba está bien hecho")
    ok(marca_de("RUTA_X", {}, falsos) == "socio-prueba", "un proyecto nombrado en «proyectos» es de ese kit")
    ok(marca_de("VIDEO_1", {}, falsos) == "personal", "un vídeo sin marca es personal")
    ok(marca_de("X", {"marca": "otra"}, falsos) == "otra", "la marca de la receta manda")
    ok(len(moldes()) >= 9, f"{len(moldes())} moldes del catálogo")
    ok(slug("manicura short") == "manicura-short" and slug("Áñ ¿x?") == "an-x", "slug de vídeo")
    global REGISTRO, KITS
    tmp = Path(tempfile.mkdtemp())
    registro_real, REGISTRO = REGISTRO, tmp / "_pedidos.json"  # las pruebas no tocan el registro de verdad
    kits_reales, KITS = KITS, tmp / "kits"                       # ni tus kits: uno de prueba
    try:   # pedido de punta a punta con un vídeo falso
        KITS.mkdir()
        (KITS / "socio-prueba.json").write_text(json.dumps(socio, ensure_ascii=False))
        ok(list(kits()) == ["personal", "socio-prueba"], "sin personal.json, el personal sale de marca.json")
        with contextlib.redirect_stdout(io.StringIO()):
            nueva_marca("Marca Nueva")
        ok(kits()["marca-nueva"]["publica"].startswith(f"En {kitmod.usuario()}"), "nueva-marca crea el kit con tu @")
        video = "_prueba_pedido"
        (tmp / "pedidos").mkdir()
        (tmp / "pedidos" / "x.json").write_text(json.dumps({"data": {
            "video": video, "marca": "socio-prueba", "molde": "golpe-y-cuentas", "idea": "algo",
            "efectos": [{"codigo": "E-05", "nota": "el precio"}, {"codigo": "E-11"}], "estado": "listo"}}))
        with contextlib.redirect_stdout(io.StringIO()):
            p = leer(tmp, video)
        ok(p["marca"] == "socio-prueba" and len(p["efectos"]) == 2, "leer guarda marca y retoques")
        rec = tmp / "r.json"
        rec.write_text(json.dumps({"tema": "x", "_receta": "Golpe y cuentas (plantilla …)",
                                   "datos": [{"frase": "a", "valor": 1}], "cierre": {"tipo": "info", "pregunta": "¿?"}}))
        with contextlib.redirect_stdout(io.StringIO()):
            mal1 = comprobar(video, rec)
            aplicar(video, rec)
            mal2 = comprobar(video, rec)
        ok(any("marca" in m for m in mal1), "comprobar avisa si falta la marca")
        ok(json.loads(rec.read_text())["acento"] == socio["receta"]["acento"], "aplicar pone el acento")
        ok(mal2 == ["E-11 pedido y no está en la receta"], f"comprobar ve solo el retoque que falta ({mal2})")
        r = json.loads(rec.read_text())
        import cierre
        otro = next((c for c in cierre.CIERRES if c not in socio["cierres"]), None)   # uno tuyo de palabra
        if otro:
            r["cierre"] = {"tipo": otro}
            rec.write_text(json.dumps(r))
            with contextlib.redirect_stdout(io.StringIO()):
                mal3 = comprobar(video, rec)
            ok(any(f"cierre «{otro}»" in m for m in mal3), "comprobar no deja un cierre que la marca no admite")
        with contextlib.redirect_stdout(io.StringIO()):
            abrir("Otro vídeo", "personal")
        reg = registro()
        ok(reg.get("prueba-pedido", {}).get("estado") == "listo" and reg["prueba-pedido"].get("proyecto") == video,
           "leer apunta el pedido con su proyecto para el panel")
        ok(reg.get("otro-video", {}).get("estado") == "abierto", "abrir apunta el pedido para el panel")
        with contextlib.redirect_stdout(io.StringIO()):
            cerrar("Otro vídeo", "OTRO")
        ok(registro()["otro-video"]["estado"] == "entregado", "cerrar lo quita del panel")
    finally:
        REGISTRO, KITS = registro_real, kits_reales
        shutil.rmtree(tmp)
        shutil.rmtree(ROOT / "proyectos" / "_prueba_pedido", ignore_errors=True)
    print("todo en verde" if not fallos else f"{len(fallos)} fallo(s)")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("kits")
    s = sub.add_parser("abrir"); s.add_argument("video"); s.add_argument("--marca")
    s = sub.add_parser("leer"); s.add_argument("carpeta"); s.add_argument("--video", required=True)
    s.add_argument("--proyecto", help="carpeta de proyectos/ si no se llama como el vídeo del pedido")
    s = sub.add_parser("aplicar"); s.add_argument("video"); s.add_argument("--receta", required=True)
    s.add_argument("--simular", action="store_true")
    s = sub.add_parser("comprobar"); s.add_argument("video"); s.add_argument("--receta", required=True)
    s = sub.add_parser("nueva-marca"); s.add_argument("nombre"); s.add_argument("--tipo", default="puntual", choices=TIPOS)
    s = sub.add_parser("cerrar"); s.add_argument("video"); s.add_argument("--proyecto")
    sub.add_parser("usados")
    sub.add_parser("probar")
    a = ap.parse_args()
    if a.cmd == "kits":
        for k in kits().values():
            mal = problemas_kit(k)
            print(f"{k['id']:<24} {k['nombre']:<24} {k['estado']:<10} acento {k.get('receta', {}).get('acento') or '—':<8}"
                  f" cierres {', '.join(k['cierres']) or 'propio'}{'  ¡' + '; '.join(mal) + '!' if mal else ''}")
    elif a.cmd == "abrir":
        abrir(a.video, a.marca)
    elif a.cmd == "cerrar":
        cerrar(a.video, a.proyecto)
    elif a.cmd == "leer":
        leer(a.carpeta, a.video, a.proyecto)
    elif a.cmd == "aplicar":
        aplicar(a.video, a.receta, a.simular)
    elif a.cmd == "comprobar":
        sys.exit(1 if comprobar(a.video, a.receta) else 0)
    elif a.cmd == "nueva-marca":
        nueva_marca(a.nombre, a.tipo)
    elif a.cmd == "usados":
        for m, cs in usados().items():
            print(f"{m:<24} {len(cs):>2}  {' '.join(cs)}")
    elif a.cmd == "probar":
        probar()
