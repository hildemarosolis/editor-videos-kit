#!/usr/bin/env python3
"""Ajustes de una receta desde la página de revisión (editor, opción A, fase 3).

La receta es la única fuente de verdad: este script escribe los ajustes SOLO en
`proyectos/<VIDEO>/recetas/<receta>.json`, nunca en la composición (`index.html`), que `subtitulos.py`
regenera desde la receta al sacar la muestra. Así `entregar.py` no pierde ningún cambio.

Uso:
  python3 scripts/ajustes.py campos
  python3 scripts/ajustes.py aplicar <VIDEO> --receta <receta> --ajustes <archivo.json …> [--confirmar] [--simular]
  python3 scripts/ajustes.py cambiadas --base <carpeta de ArtifactData> --version v1
  python3 scripts/ajustes.py notas --base <carpeta de ArtifactData> --version v1
  python3 scripts/ajustes.py heredar --base <carpeta de ArtifactData> --antes v1 --version v2 --piezas <piezas.json de la v2>
  python3 scripts/ajustes.py probar

Formato del archivo de ajustes (lo que Claude saca de la base de la página en la fase 4):
  [{"clip": "golpe1", "campo": "texto", "valor": "NIE DENEGADO"}, {"clip": "golpe1", "campo": "dur", "valor": 2.4}]
`clip` es el identificador de la pieza en la composición (el mismo que `piezas.json` de revision.py).

Todo o nada: si un solo ajuste no vale, no se escribe ninguno. Una cifra nueva en un texto no se aplica sin
`--confirmar` (regla de la casa: cada dato lleva su fuente). Cada ajuste aplicado se apunta, con su valor
anterior, en `proyectos/<VIDEO>/ajustes_aplicados.jsonl`.
"""
import argparse
import copy
import json
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SONIDOS = ("error", "pop", "whoosh", "impacto", "boom", "tic")  # los de sfx.py que valen para un golpe
ZONAS = ("arriba", "abajo", "cerrado")  # FL_SITIOS de efectos.py
# prefijo del identificador de clip (golpe1, imp0, dato0…) → lista de la receta; el número es la posición en la lista
LISTAS = {"golpe": "golpes", "imp": "impactos", "partida": "partidas", "flotantes": "flotantes", "dato": "datos"}
MAX_TEXTO = {("golpes", "texto"): 40, ("golpes", "sub"): 60, ("datos", "texto"): 60}
# lo que hace el código cuando la receta no dice nada (efectos.py y gancho.py): la página lo enseña como valor de hoy
DUR_POR_DEFECTO = {"golpes": 0.9, "impactos": 1.0, "partidas": 1.6, "datos": 2.2}


class AjusteError(ValueError):
    pass


# --- validadores: cada uno devuelve el valor limpio o levanta ValueError con el motivo -------------------------

def texto(maximo, vacio_vale=False):
    def v(x):
        if not isinstance(x, str):
            raise ValueError("tiene que ser un texto")
        x = x.strip()
        if not x and not vacio_vale:
            raise ValueError("no puede estar vacío")
        if len(x) > maximo:
            raise ValueError(f"máximo {maximo} caracteres")
        return x
    return v


def segundos(x):
    try:
        s = round(float(str(x).replace(",", ".")), 1)
    except ValueError:
        raise ValueError("tiene que ser un número de segundos")
    if not 0.5 <= s <= 6:
        raise ValueError("entre 0,5 y 6 segundos")
    return s


def si_no(x):
    if isinstance(x, bool):
        return x
    s = str(x).strip().lower()
    if s in ("sí", "si", "true", "1"):
        return True
    if s in ("no", "false", "0"):
        return False
    raise ValueError("sí o no")


def elegir(*opciones):
    def v(x):
        s = str(x).strip().lower()
        if s not in opciones:
            raise ValueError("uno de: " + ", ".join(opciones))
        return s
    return v


def pixeles(x):
    try:
        p = int(round(float(str(x).replace(",", "."))))
    except ValueError:
        raise ValueError("tiene que ser un número de píxeles")
    if not 0 <= p <= 600:
        raise ValueError("entre 0 y 600 píxeles")
    return p


# --- cómo se lee y se escribe cada campo en la receta ---------------------------------------------------------

def poner_clave(clave, quitar_si=None):
    """Escribe item[clave]; si el valor es el «vacío» de la receta (quitar_si), borra la clave para dejarla limpia."""
    def f(item, valor):
        if valor == quitar_si:
            item.pop(clave, None)
        else:
            item[clave] = valor
    return f


def poner_baja(item, y):
    item["baja"] = [y, (item.get("baja") or [300, 1.0])[1]]  # la escala se queda como está


def poner_estilo(item, valor):
    if valor == "normal":
        item.pop("estilo", None)
    else:
        item["estilo"] = valor


LEER = {
    "estilo": lambda it: it.get("estilo", "normal"),
    "tachado": lambda it: bool(it.get("tachado")),
    "baja": lambda it: (it.get("baja") or [300, 1.0])[0],
    "sub": lambda it: it.get("sub", ""),
}


def leer(item, campo):
    return LEER[campo](item) if campo in LEER else item.get(campo)


# lista de la receta → campo → (validador, escritor). Solo lo que se ha comprobado en efectos.py y gancho.py.
CAMPOS = {
    "golpes": {
        "texto": (texto(MAX_TEXTO["golpes", "texto"]), poner_clave("texto")),
        "sub": (texto(MAX_TEXTO["golpes", "sub"], vacio_vale=True), poner_clave("sub", quitar_si="")),   # solo lo dibuja el estilo alarma
        "estilo": (elegir("normal", "alarma"), poner_estilo),
        "tachado": (si_no, poner_clave("tachado", quitar_si=False)),
        "sonido": (elegir(*SONIDOS), poner_clave("sonido")),                      # solo lo suena el estilo alarma
        "dur": (segundos, poner_clave("dur")),
    },
    "impactos": {"dur": (segundos, poner_clave("dur"))},
    "partidas": {"baja": (pixeles, poner_baja), "dur": (segundos, poner_clave("dur"))},
    "flotantes": {"zona": (elegir(*ZONAS), poner_clave("zona"))},
    "datos": {"texto": (texto(MAX_TEXTO["datos", "texto"]), poner_clave("texto")), "dur": (segundos, poner_clave("dur"))},
}
SOLO_ALARMA = ("sub", "sonido")

# --- lo que la página necesita para dibujar cada campo (fase 4) -----------------------------------------------
# campo → (etiqueta, tipo de control, resto). Los valores que la página manda de vuelta los acepta tal cual `aplicar_cambios`.
UI = {
    "texto": ("Texto", "texto", {}),
    "sub": ("Línea de debajo", "texto", {}),
    "estilo": ("Estilo", "opciones", {"opciones": ["Normal", "Alarma"]}),
    "tachado": ("Tachado", "opciones", {"opciones": ["Sí", "No"]}),
    "sonido": ("Sonido", "opciones", {"opciones": list(SONIDOS)}),
    "dur": ("Duración", "segundos", {"min": 0.5, "max": 6, "paso": 0.1}),
    "baja": ("El vídeo baja", "pixeles", {"min": 0, "max": 600, "paso": 50}),
    "zona": ("Zona", "opciones", {"opciones": [z.capitalize() for z in ZONAS]}),
}


def pieza_y_posicion(clip):
    """('golpes', 1) para «golpe1»; None si esa pieza no se edita."""
    m = re.fullmatch(r"([a-z]+)(\d+)", str(clip))
    return (LISTAS[m.group(1)], int(m.group(2))) if m and m.group(1) in LISTAS else None


def mostrar(lista, item, campo):
    """El valor de hoy de un campo, con las palabras que enseña la página."""
    if campo == "estilo":
        return item.get("estilo", "normal").capitalize()
    if campo == "tachado":
        return "Sí" if item.get("tachado") else "No"
    if campo == "sonido":
        return item.get("sonido", "error")
    if campo == "dur":
        return item.get("dur", DUR_POR_DEFECTO[lista])
    if campo == "baja":
        return (item.get("baja") or [300, 1.0])[0]
    if campo == "zona":
        return item.get("zona", "abajo").capitalize()
    return item.get(campo, "")


def descriptores(receta, clip):
    """Los campos editables de una pieza con su valor de hoy, listos para la página; [] si la pieza no se edita."""
    donde = pieza_y_posicion(clip)
    if not donde or donde[1] >= len(receta.get(donde[0]) or []):
        return []
    lista, n = donde
    item = receta[lista][n]
    salida = []
    for campo in CAMPOS[lista]:
        etiqueta, tipo, resto = UI[campo]
        d = {"campo": campo, "etiqueta": etiqueta, "tipo": tipo, "valor": mostrar(lista, item, campo), **resto}
        if (lista, campo) in MAX_TEXTO:
            d["max"] = MAX_TEXTO[lista, campo]
        if lista == "golpes" and campo in SOLO_ALARMA:
            d["solo_si"] = {"estilo": "Alarma"}
        salida.append(d)
    return salida


def aplanar(datos):
    """Acepta la lista de ajustes tal cual o los documentos de la base de la página ({clip, cambios: {campo: valor}})."""
    salida = []
    for d in datos:
        if isinstance(d, dict) and isinstance(d.get("cambios"), dict):
            salida += [{"clip": d["clip"], "campo": k, "valor": v} for k, v in d["cambios"].items()]
        else:
            salida.append(d)
    return salida


def cifras(s):
    return {re.sub(r"[.,]", "", n) for n in re.findall(r"\d[\d.,]*\d|\d", str(s))}


# --- el aplicador, sin tocar disco ----------------------------------------------------------------------------

def aplicar_cambios(receta, cambios):
    """(receta nueva, cambios hechos, avisos). La receta que llega no se toca; si algo no vale, AjusteError con todo."""
    nueva = copy.deepcopy(receta)
    errores, avisos, hechos, golpes_con_solo_alarma = [], [], [], set()
    for c in cambios:
        try:
            clip, campo, valor = c["clip"], c["campo"], c["valor"]
        except (KeyError, TypeError):
            errores.append(f"ajuste mal formado: {c!r}")
            continue
        donde = pieza_y_posicion(clip)
        if not donde:
            errores.append(f"{clip}: esta pieza no se edita (se editan: golpes, zooms, pantallas partidas, tarjetas flotantes y datos)")
            continue
        lista, n = donde
        items = nueva.get(lista) or []
        if n >= len(items):
            errores.append(f"{clip}: la receta tiene {len(items)} en «{lista}»")
            continue
        if campo not in CAMPOS[lista]:
            errores.append(f"{clip}: «{campo}» no se edita aquí (se editan: {', '.join(CAMPOS[lista])})")
            continue
        validar, escribir = CAMPOS[lista][campo]
        try:
            v = validar(valor)
        except ValueError as e:
            errores.append(f"{clip} · {campo}: {e}")
            continue
        item = items[n]
        antes = leer(item, campo)
        escribir(item, v)
        despues = leer(item, campo)
        if lista == "golpes" and campo in SOLO_ALARMA:
            golpes_con_solo_alarma.add((clip, n))
        if antes == despues:
            continue
        hechos.append({"clip": clip, "campo": campo, "antes": antes, "despues": despues})
        if campo in ("texto", "sub") and lista in ("golpes", "datos") and cifras(despues) - cifras(antes):
            avisos.append(f"{clip} · {campo}: cifra nueva {sorted(cifras(despues) - cifras(antes))} en «{despues}»; "
                          "cada dato lleva su fuente: confírmalo")
    for clip, n in sorted(golpes_con_solo_alarma):
        if nueva["golpes"][n].get("estilo") != "alarma":
            errores.append(f"{clip}: la línea de debajo y el sonido solo se usan en el estilo alarma")
    if errores:
        raise AjusteError("\n".join(errores))
    return nueva, hechos, avisos


def escribir_receta(ruta, receta):
    """Con el formato que ya tiene: sangría de 2 y, como cada receta, con o sin salto de línea final (7 viejas no lo llevan)."""
    fin = "\n" if ruta.read_text(encoding="utf-8").endswith("\n") else ""
    ruta.write_text(json.dumps(receta, indent=2, ensure_ascii=False) + fin, encoding="utf-8")


def cmd_campos(_):
    for lista, campos in CAMPOS.items():
        print(f"{lista}: " + ", ".join(campos))


def ruta_receta(video, receta):
    """proyectos/<VIDEO>/recetas/<receta>.json, o la ruta tal cual si `receta` ya es una (como en entregar.py)."""
    if receta.endswith(".json") or "/" in receta:
        return Path(receta)
    return ROOT / "proyectos" / video / "recetas" / f"{receta}.json"


def corto(ruta):
    try:
        return str(Path(ruta).resolve().relative_to(ROOT))
    except ValueError:
        return str(ruta)


def cmd_aplicar(a):
    ruta = ruta_receta(a.video, a.receta)
    proyecto = ruta.resolve().parent.parent
    if not ruta.exists():
        sys.exit(f"no existe {corto(ruta)}")
    receta = json.loads(ruta.read_text(encoding="utf-8"))
    cambios = []
    for archivo in a.ajustes:   # una lista de ajustes, o los documentos que ArtifactData saca de la base de la página, uno por archivo
        datos = json.loads(Path(archivo).read_text(encoding="utf-8"))
        cambios += aplanar(datos if isinstance(datos, list) else [datos])
    try:
        nueva, hechos, avisos = aplicar_cambios(receta, cambios)
    except AjusteError as e:
        print(f"{a.video}: no se aplica nada.\n{e}")
        return 2
    for h in hechos:
        print(f"{h['clip']} · {h['campo']}: {h['antes']!r} → {h['despues']!r}")
    if not hechos:
        print(f"{a.video}: los ajustes ya estaban aplicados; no hay nada que cambiar.")
        return 0
    if avisos and not a.confirmar:
        print("\nNo escribo nada hasta que el creador lo confirme:\n  " + "\n  ".join(avisos))
        print("Con su visto bueno, repite el comando con --confirmar.")
        return 3
    if a.simular:
        print("(simulación: no se ha escrito nada)")
        return 0
    escribir_receta(ruta, nueva)
    ahora = datetime.now().isoformat(timespec="seconds")
    with open(proyecto / "ajustes_aplicados.jsonl", "a", encoding="utf-8") as f:
        for h in hechos:
            f.write(json.dumps({"fecha": ahora, "receta": ruta.stem, **h}, ensure_ascii=False) + "\n")
    print(f"{a.video}: {len(hechos)} ajuste(s) en {corto(ruta)}")
    print("cambiadas: " + ", ".join(sorted({h["clip"] for h in hechos})))
    return 0


# --- fase 5: tras «revisada» ----------------------------------------------------------------------------------

def leer_base(carpeta, coleccion):
    """Los documentos que ArtifactData dejó en <carpeta>/<coleccion>/*.json (action list con out_dir)."""
    return [json.loads(f.read_text(encoding="utf-8")) for f in sorted((Path(carpeta) / coleccion).glob("*.json"))]


def piezas_cambiadas(docs_ajustes, docs_marcas, version, docs_notas=()):
    """(piezas que se rehacen: con ajustes, marcadas «Cambios» o con una nota en su segundo; las que no tienen ajuste,
    que son un comentario o una nota y se hacen a mano). Una nota sin pieza no está aquí: se lee con `notas`."""
    con_ajustes = {d["pieza"] for d in docs_ajustes if d.get("version") == version and d.get("cambios")}
    marcadas = {m["pieza"] for m in docs_marcas if m.get("version") == version and m.get("estado") == "cambios"}
    con_nota = {n["pieza"] for n in docs_notas if n.get("version") == version and n.get("pieza")}
    return sorted(con_ajustes | marcadas | con_nota), sorted((marcadas | con_nota) - con_ajustes)


def notas_de(docs_notas, version):
    """Las notas por segundo de una versión, en orden de tiempo."""
    return sorted((n for n in docs_notas if n.get("version") == version and isinstance(n.get("t"), (int, float))), key=lambda n: n["t"])


def mmss(t):
    return f"{int(t // 60):02d}:{t % 60:04.1f}".replace(".", ",")


def marcas_heredadas(docs_marcas, cambiadas, piezas, antes, despues, ahora):
    """Escrituras para ArtifactData: las marcas «aprobado» de la versión anterior pasan a la nueva y solo lo rehecho queda pendiente.
    Solo si la pieza sigue siendo la misma en la composición nueva: el mismo clip en el mismo sitio, o, si al quitar o
    añadir una pieza se corrió la numeración (dt2 → dt1), una del mismo tipo con el mismo título."""
    por_id = {p["id"]: p for p in piezas}
    tipo = lambda clip: re.sub(r"\d+$", "", clip or "")
    norm = lambda s: " ".join((s or "").split()).casefold()
    viejas = [m for m in docs_marcas if m.get("version") == antes and m.get("estado") == "aprobado" and m["pieza"] not in cambiadas]
    pares = {}  # pieza vieja → pieza nueva
    for m in viejas:  # 1.º la misma pieza en el mismo sitio
        p = por_id.get(m["pieza"])
        if p and p["clip"] == m.get("clip"):
            pares[m["pieza"]] = p
    usadas = {p["id"] for p in pares.values()}
    for m in viejas:  # 2.º la numeración se corrió: mismo tipo de pieza y mismo título, en una que no esté ya cogida
        if m["pieza"] in pares:
            continue
        p = next((q for q in piezas if q["id"] not in usadas and tipo(q["clip"]) == tipo(m.get("clip"))
                  and norm(q.get("titulo")) and norm(q.get("titulo")) == norm(m.get("titulo"))), None)
        if p:
            pares[m["pieza"]] = p
            usadas.add(p["id"])
    escribir = []
    for m in viejas:
        p = pares.get(m["pieza"])
        if not p:
            continue
        escribir.append({"op": "set", "collection": "marcas", "doc_id": f"{despues}-{p['id']}",
                         "data": {"pieza": p["id"], "clip": p["clip"], "version": despues, "t": p["t"], "titulo": p["titulo"],
                                  "estado": "aprobado", "comentario": m.get("comentario", ""), "actualizado": ahora}})
    return escribir


def cmd_cambiadas(a):
    notas = leer_base(a.base, "notas")
    todas, a_mano = piezas_cambiadas(leer_base(a.base, "ajustes"), leer_base(a.base, "marcas"), a.version, notas)
    print("cambiadas: " + " ".join(todas))
    for p in a_mano:
        print(f"  {p}: sin ajuste (comentario o nota); se hace a mano")
    cmd_notas(a)
    return 0


def cmd_notas(a):
    lista = notas_de(leer_base(a.base, "notas"), a.version)
    print(f"notas en el vídeo ({a.version}): {len(lista) or 'ninguna'}")
    for n in lista:
        donde = f"{n['pieza']} · {n.get('titulo') or ''}" if n.get("pieza") else "sin pieza en ese segundo"
        print(f"  {mmss(n['t'])}  {donde}\n           «{n.get('texto', '')}»")
    return 0


def cmd_heredar(a):
    datos = json.loads(Path(a.piezas).read_text(encoding="utf-8"))
    marcas = leer_base(a.base, "marcas")
    cambiadas, _ = piezas_cambiadas(leer_base(a.base, "ajustes"), marcas, a.antes, leer_base(a.base, "notas"))
    ahora = datetime.now().astimezone().isoformat(timespec="seconds")
    escribir = marcas_heredadas(marcas, set(cambiadas), datos["piezas"], a.antes, a.version, ahora)
    salida = Path(a.base) / f"heredar_{a.version}.json"
    salida.write_text(json.dumps({"writes": escribir}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(escribir)} marcas «aprobado» pasan de {a.antes} a {a.version}; quedan pendientes: {' '.join(cambiadas) or 'ninguna'}")
    print(f"para ArtifactData batch: {salida}")
    return 0


# --- pruebas --------------------------------------------------------------------------------------------------

def recetas_rastreadas():
    """Las recetas que git rastrea. Las de ensayo, escritas a mano y sin rastrear, no cuentan para la prueba de formato."""
    r = subprocess.run(["git", "ls-files", "-z", "proyectos/*/recetas/*.json"], cwd=ROOT, capture_output=True, text=True)
    if r.returncode == 0 and r.stdout:
        return sorted(ROOT / f for f in r.stdout.split("\0") if f)
    return sorted(ROOT.glob("proyectos/*/recetas/*.json"))   # sin git, todas

def cmd_probar(_):
    sys.path.insert(0, str(ROOT / "scripts"))
    import sfx
    fallos = []

    def prueba(nombre, ok, detalle=""):
        print(("ok     " if ok else "FALLA  ") + nombre + (f" — {detalle}" if detalle and not ok else ""))
        if not ok:
            fallos.append(nombre)

    def falla(cambios, receta, trozo):
        try:
            aplicar_cambios(receta, cambios)
        except AjusteError as e:
            return trozo in str(e)
        return False

    recetas = recetas_rastreadas()
    distintas = [r for r in recetas if json.dumps(json.loads(r.read_text(encoding="utf-8")), indent=2, ensure_ascii=False)
                 != r.read_text(encoding="utf-8").rstrip("\n")]
    prueba(f"formato estable: {len(recetas)} recetas rastreadas se reescriben idénticas", not distintas, ", ".join(str(r) for r in distintas[:3]))
    prueba("los sonidos ofrecidos existen en sfx.py", all(s in sfx.SOUNDS for s in SONIDOS))
    with tempfile.TemporaryDirectory() as tmp:
        for fin in ("", "\n"):
            r = Path(tmp) / "r.json"
            r.write_text('{"a": 1}' + fin, encoding="utf-8")
            escribir_receta(r, {"a": 2, "b": "ñ"})
            prueba(f"al escribir se respeta el salto final ({'con' if fin else 'sin'})",
                   r.read_text(encoding="utf-8") == '{\n  "a": 2,\n  "b": "ñ"\n}' + fin)

    # receta de ejemplo (va aquí dentro para que la prueba no dependa de ningún proyecto del disco)
    base = {"tema": "Ejemplo", "variante": "golpe",
            "golpes": [{"frase": "no no basta", "texto": "NO BASTA", "dur": 1.3},
                       {"frase": "me lo denegaron dos veces", "despues_de": 10.0, "texto": "NIE DENEGADO", "tachado": True,
                        "estilo": "alarma", "sub": "2 veces · con pasaporte europeo", "sonido": "error", "dur": 2.2},
                       {"frase": "tres cuatro meses", "texto": "3-4 MESES", "dur": 1.4}],
            "impactos": [{"frase": "eso no es nada", "dur": 1.0, "zoom": 1.2}],
            "datos": [{"frase": "siete meses", "dur": 2.6, "antetitulo": "SIENDO EUROPEA", "numero": 7, "cuenta_s": 0.5,
                       "texto": "meses hasta tener su NIE", "fuente": "Testimonio en la entrevista"}]}
    alarma = base["golpes"][1]
    nueva, hechos, avisos = aplicar_cambios(base, [{"clip": "golpe1", "campo": "dur", "valor": "2,6"},
                                                   {"clip": "golpe1", "campo": "sonido", "valor": "boom"}])
    prueba("dur y sonido de un golpe alarma", nueva["golpes"][1]["dur"] == 2.6 and nueva["golpes"][1]["sonido"] == "boom"
           and len(hechos) == 2 and not avisos)
    prueba("la receta original no se toca", base["golpes"][1] == alarma)
    nueva, hechos, _ = aplicar_cambios(base, [{"clip": "golpe1", "campo": "estilo", "valor": "Normal"},
                                              {"clip": "golpe1", "campo": "tachado", "valor": "No"}])
    prueba("estilo normal y sin tachado quitan las claves", "estilo" not in nueva["golpes"][1] and "tachado" not in nueva["golpes"][1])
    _, hechos, _ = aplicar_cambios(base, [{"clip": "golpe1", "campo": "dur", "valor": 2.2}])
    prueba("repetir un valor igual no cuenta como cambio", hechos == [])
    prueba("sonido en un golpe normal se rechaza", falla([{"clip": "golpe0", "campo": "sonido", "valor": "pop"}], base, "estilo alarma"))
    prueba("pasar a normal y pedir sonido a la vez se rechaza",
           falla([{"clip": "golpe1", "campo": "estilo", "valor": "normal"}, {"clip": "golpe1", "campo": "sonido", "valor": "pop"}], base, "estilo alarma"))
    nueva, _, _ = aplicar_cambios(base, [{"clip": "golpe0", "campo": "estilo", "valor": "alarma"}, {"clip": "golpe0", "campo": "sonido", "valor": "pop"}])
    prueba("pasar a alarma y elegir sonido a la vez vale", nueva["golpes"][0]["sonido"] == "pop")
    prueba("campo desconocido", falla([{"clip": "golpe0", "campo": "color", "valor": "rojo"}], base, "no se edita aquí"))
    prueba("pieza que no se edita (comenta, sígueme…)", falla([{"clip": "comenta", "campo": "texto", "valor": "x"}], base, "no se edita"))
    prueba("posición fuera de la receta", falla([{"clip": "golpe9", "campo": "dur", "valor": 1}], base, "tiene 3"))
    prueba("duración fuera de rango", falla([{"clip": "golpe0", "campo": "dur", "valor": 9}], base, "0,5 y 6"))
    prueba("todo o nada: un error no aplica los buenos", falla([{"clip": "golpe0", "campo": "dur", "valor": 2},
                                                              {"clip": "golpe0", "campo": "dur", "valor": 99}], base, "0,5 y 6"))
    _, hechos, avisos = aplicar_cambios(base, [{"clip": "golpe0", "campo": "texto", "valor": "NO BASTAN 3 AÑOS"}])
    prueba("cifra nueva en un texto avisa", len(avisos) == 1 and "3" in avisos[0])
    _, _, avisos = aplicar_cambios(base, [{"clip": "golpe0", "campo": "texto", "valor": "NO ES SUFICIENTE"}])
    prueba("texto sin cifras no avisa", avisos == [])

    otras = {"partidas": [{"frase": "x", "baja": [300, 0.9]}], "flotantes": [{"items": []}], "impactos": [{"dur": 1.0, "zoom": 1.2}],
             "datos": [{"texto": "a", "numero": 5, "dur": 2.2}]}
    nueva, _, _ = aplicar_cambios(otras, [{"clip": "partida0", "campo": "baja", "valor": "350"}, {"clip": "flotantes0", "campo": "zona", "valor": "arriba"},
                                          {"clip": "imp0", "campo": "dur", "valor": 1.4}, {"clip": "dato0", "campo": "texto", "valor": "b"}])
    prueba("partida baja y conserva la escala", nueva["partidas"][0]["baja"] == [350, 0.9])
    prueba("zona, zoom y dato", nueva["flotantes"][0]["zona"] == "arriba" and nueva["impactos"][0]["dur"] == 1.4
           and nueva["datos"][0]["texto"] == "b" and nueva["datos"][0]["numero"] == 5)
    prueba("la página sabe dibujar todos los campos que se pueden editar",
           all(c in UI for campos in CAMPOS.values() for c in campos))
    d = descriptores(base, "golpe1")
    por = {x["campo"]: x for x in d}
    prueba("descriptores de un golpe alarma: valores de hoy",
           [x["campo"] for x in d] == list(CAMPOS["golpes"]) and por["estilo"]["valor"] == "Alarma" and por["tachado"]["valor"] == "Sí"
           and por["sonido"]["valor"] == "error" and por["dur"]["valor"] == 2.2 and por["texto"]["valor"] == "NIE DENEGADO"
           and por["texto"]["max"] == 40)
    prueba("la línea de debajo y el sonido solo salen con estilo alarma",
           por["sub"]["solo_si"] == {"estilo": "Alarma"} and por["sonido"]["solo_si"] == {"estilo": "Alarma"} and "solo_si" not in por["dur"])
    prueba("sin tocar nada, lo que enseña la página no cambia la receta",
           aplicar_cambios(base, [{"clip": "golpe1", "campo": x["campo"], "valor": x["valor"]} for x in d])[1] == [])
    prueba("valor por defecto cuando la receta no dice nada", {x["campo"]: x["valor"] for x in descriptores(base, "golpe0")}["dur"] == 1.3
           and {x["campo"]: x["valor"] for x in descriptores({"golpes": [{"texto": "A"}]}, "golpe0")}["dur"] == 0.9)
    prueba("una pieza que no se edita no tiene campos", descriptores(base, "comenta") == [] and descriptores(base, "golpe9") == [])
    prueba("aplanar: documentos de la base y lista tal cual",
           aplanar([{"clip": "golpe1", "cambios": {"dur": 2.6, "sonido": "boom"}}, {"clip": "golpe0", "campo": "dur", "valor": 2}])
           == [{"clip": "golpe1", "campo": "dur", "valor": 2.6}, {"clip": "golpe1", "campo": "sonido", "valor": "boom"},
               {"clip": "golpe0", "campo": "dur", "valor": 2}])
    aj = [{"pieza": "p02", "version": "v1", "cambios": {"dur": 2.6}}, {"pieza": "p03", "version": "v1", "cambios": {}}]
    mar = [{"pieza": "p01", "clip": "golpe0", "version": "v1", "estado": "aprobado", "comentario": "bien"},
           {"pieza": "p02", "clip": "golpe1", "version": "v1", "estado": "cambios", "comentario": ""},
           {"pieza": "p03", "clip": "dato0", "version": "v1", "estado": "pendiente"},
           {"pieza": "p04", "clip": "golpe2", "version": "v1", "estado": "aprobado"},
           {"pieza": "p05", "clip": "imp0", "version": "v1", "estado": "cambios", "comentario": "otro efecto"},
           {"pieza": "p06", "clip": "dato1", "version": "v1", "estado": "aprobado"}]
    todas, a_mano = piezas_cambiadas(aj, mar, "v1")
    prueba("cambiadas: con ajuste o con «Cambios»; el comentario sin ajuste se hace a mano", todas == ["p02", "p05"] and a_mano == ["p05"])
    notas = [{"version": "v1", "t": 12.4, "pieza": "p04", "texto": "el logo me tapa la cara"},
             {"version": "v1", "t": 0.03, "pieza": None, "texto": "se oye un dos"},
             {"version": "v0", "t": 5.0, "pieza": "p06", "texto": "de otra versión"}]
    t2, m2 = piezas_cambiadas(aj, mar, "v1", notas)
    prueba("cambiadas: una nota en el segundo de una pieza la rehace, aunque estuviera aprobada; sin pieza no cuenta",
           t2 == ["p02", "p04", "p05"] and m2 == ["p04", "p05"])
    prueba("notas: solo las de la versión y por orden de tiempo", [n["texto"] for n in notas_de(notas, "v1")] == ["se oye un dos", "el logo me tapa la cara"])
    prueba("notas: el segundo con décima", mmss(0.03) == "00:00,0" and mmss(72.46) == "01:12,5")
    nuevas = [{"id": "p01", "clip": "golpe0", "t": 19.1, "titulo": "NO BASTA"}, {"id": "p04", "clip": "golpe2", "t": 54.2, "titulo": "3-4 MESES"},
              {"id": "p06", "clip": "imp9", "t": 70.0, "titulo": "otra cosa"}]
    esc = marcas_heredadas(mar, set(todas), nuevas, "v1", "v2", "2026-10-29T12:00:00+00:00")
    prueba("heredar: solo las aprobadas que no se rehacen y siguen siendo la misma pieza",
           [e["doc_id"] for e in esc] == ["v2-p01", "v2-p04"] and esc[0]["data"]["comentario"] == "bien" and esc[0]["data"]["version"] == "v2"
           and esc[1]["data"]["titulo"] == "3-4 MESES" and all(e["op"] == "set" and e["collection"] == "marcas" for e in esc))
    # caso real: se quita el titular dt1 y entra una pizarra; dt2 y dt3 pasan a llamarse dt1 y dt2
    mb = [{"version": "v1", "pieza": "p01", "clip": "dt0", "titulo": "¿POR QUÉ ESPAÑA?", "estado": "aprobado"},
          {"version": "v1", "pieza": "p02", "clip": "dt1", "titulo": "DOS RUEDAS", "estado": "cambios"},
          {"version": "v1", "pieza": "p04", "clip": "dt2", "titulo": "1 AÑO EN EL VACÍO", "estado": "aprobado"},
          {"version": "v1", "pieza": "p07", "clip": "dt3", "titulo": "LIMBO JURÍDICO", "estado": "aprobado"},
          {"version": "v1", "pieza": "p09", "clip": "golpe2", "titulo": "El sistema se rompió", "estado": "aprobado"}]
    nb = [{"id": "p01", "clip": "dt0", "t": 0.0, "titulo": "¿POR QUÉ ESPAÑA?"}, {"id": "p02", "clip": "pz0", "t": 4.2, "titulo": "Pizarra · MIGRAR ES…"},
          {"id": "p04", "clip": "dt1", "t": 21.5, "titulo": "1 AÑO EN EL VACÍO"}, {"id": "p07", "clip": "dt2", "t": 47.2, "titulo": "LIMBO JURÍDICO"},
          {"id": "p09", "clip": "golpe2", "t": 67.1, "titulo": "El sistema se rompió"}]
    eb = marcas_heredadas(mb, {"p02"}, nb, "v1", "v2", "2026-11-05T20:00:00+01:00")
    prueba("heredar: si la numeración se corre, reconoce la pieza por su tipo y su título; la rehecha queda pendiente",
           sorted(e["doc_id"] for e in eb) == ["v2-p01", "v2-p04", "v2-p07", "v2-p09"]
           and next(e for e in eb if e["doc_id"] == "v2-p04")["data"]["clip"] == "dt1")
    with tempfile.TemporaryDirectory() as tmp:
        recetas = Path(tmp) / "proyectos" / "X" / "recetas"
        recetas.mkdir(parents=True)
        (recetas / "r.json").write_text(json.dumps(base, indent=2, ensure_ascii=False))
        prueba("--receta acepta una ruta (como entregar.py)", ruta_receta("X", str(recetas / "r.json")) == recetas / "r.json"
               and ruta_receta("MI_VIDEO", "golpe") == ROOT / "proyectos" / "MI_VIDEO" / "recetas" / "golpe.json")
    print(f"\n{'TODO EN VERDE' if not fallos else str(len(fallos)) + ' FALLO(S)'}")
    return 1 if fallos else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("campos").set_defaults(f=cmd_campos)
    p = sub.add_parser("aplicar")
    p.add_argument("video")
    p.add_argument("--receta", required=True)
    p.add_argument("--ajustes", required=True, nargs="+", help="uno o varios archivos JSON")
    p.add_argument("--confirmar", action="store_true", help="aplica aunque haya una cifra nueva (con el visto bueno del creador)")
    p.add_argument("--simular", action="store_true")
    p.set_defaults(f=cmd_aplicar)
    p = sub.add_parser("cambiadas", help="piezas que se rehacen según la base de la página")
    p.add_argument("--base", required=True, help="carpeta con ajustes/, marcas/ y notas/ sacados con ArtifactData")
    p.add_argument("--version", default="v1", help="la versión revisada")
    p.set_defaults(f=cmd_cambiadas)
    p = sub.add_parser("notas", help="las notas por segundo de la página, en orden de tiempo")
    p.add_argument("--base", required=True, help="carpeta con notas/ sacada con ArtifactData")
    p.add_argument("--version", default="v1", help="la versión revisada")
    p.set_defaults(f=cmd_notas)
    p = sub.add_parser("heredar", help="marcas «aprobado» que pasan de una versión a la siguiente (para ArtifactData batch)")
    p.add_argument("--base", required=True)
    p.add_argument("--antes", default="v1")
    p.add_argument("--version", required=True, help="la versión nueva")
    p.add_argument("--piezas", required=True, help="piezas.json de la página nueva (revision.py)")
    p.set_defaults(f=cmd_heredar)
    sub.add_parser("probar").set_defaults(f=cmd_probar)
    a = ap.parse_args()
    sys.exit(a.f(a))


if __name__ == "__main__":
    main()
