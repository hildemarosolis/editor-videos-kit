"""Nombres y carpetas de lo entregado.

Una carpeta por vídeo en la carpeta de entregas (kit.carpeta("terminados")), con todas sus variantes dentro:

  <entregas>/2026-10-22 Mi tema/2026-10-22 Mi tema - C titular detrás.mp4

- La carpeta lleva la fecha de la PRIMERA entrega de ese tema; las variantes que lleguen después
  caen en la misma carpeta (también si ya está en la de publicados: se crea una igual en la de entregas).
- El archivo lleva su propia fecha, el tema y la letra de variante (A, B, C…) + la receta en corto,
  para que «la C funcionó mejor» baste para saber cuál es.
- La receta dice `"tema"` (obligatorio), `"variante"` (si no, se deduce del modelo) y `"letra"`
  (si no, la siguiente libre de ese tema).
- Cada entrega se apunta en `proyectos/_entregas.md` (columna «Publicado» para cruzar con tus métricas).
"""
import datetime
import re
import shutil
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kit  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
EDITOR = kit.carpeta_editor()
TERMINADOS, PUBLICADOS = kit.carpeta("terminados"), kit.carpeta("publicados")
REGISTRO = ROOT / "proyectos/_entregas.md"

# nombre corto de la receta según el modelo (stem del archivo de receta)
VARIANTE = {"m1": "gancho", "ref1": "gancho", "m2": "golpe", "ref4": "golpe", "m3": "ranking", "ranking": "ranking",
            "ranking_completa": "ranking completa", "m6": "esto o aquello", "m7": "top", "m8": "sketch",
            "m9": "explicador", "m10": "torneo", "m11": "pizarra", "v3": "titular detrás"}

CABECERA = f"""# Registro de entregas

Una fila por archivo entregado a «{kit.CARPETAS["terminados"]}» (lo escribe `scripts/terminados.py`).
«Publicado»: se rellena al subirlo (fecha · prueba/normal · enlace) para cruzarlo con tus métricas.

| Entregado | Carpeta | Archivo | Proyecto | Receta | Publicado | Efectos |
|---|---|---|---|---|---|---|
"""


def limpio(s):
    return re.sub(r'[/:\\"*?<>|]', "-", s).strip()


def nfc(s):
    """macOS guarda los nombres de archivo con las tildes descompuestas (NFD): se comparan en NFC."""
    return unicodedata.normalize("NFC", s)


def carpeta_de(tema):
    """Nombre de la carpeta del tema si ya existe (en Terminados o Publicados), o None."""
    hay = [nfc(p.name) for base in (TERMINADOS, PUBLICADOS) if base.exists() for p in base.iterdir()
           if p.is_dir() and re.fullmatch(r"\d{4}-\d{2}-\d{2} " + re.escape(nfc(tema)), nfc(p.name))]
    return min(hay) if hay else None  # la fecha más antigua: la de la primera entrega


def letras_usadas(tema):
    usadas = set()
    pat = re.compile(r"\d{4}-\d{2}-\d{2} " + re.escape(nfc(tema)) + r" - ([A-Z]) ")
    for base in (TERMINADOS, PUBLICADOS):
        if base.exists():
            for f in base.rglob("*.mp4"):
                m = pat.match(nfc(f.name))
                if m:
                    usadas.add(m.group(1))
    if REGISTRO.exists():
        usadas |= set(re.findall(re.escape(nfc(tema)) + r" - ([A-Z]) ", nfc(REGISTRO.read_text())))
    return usadas


def destino(cfg, receta_path, fecha=None):
    """Ruta final en la carpeta de entregas para la receta (crea la carpeta)."""
    tema = cfg.get("tema")
    if not tema:
        raise SystemExit(f"{receta_path}: falta «tema» en la receta (p. ej. \"tema\": \"Mi tema\")")
    tema = limpio(tema)
    fecha = fecha or datetime.date.today().isoformat()
    variante = limpio(cfg.get("variante") or VARIANTE.get(Path(receta_path).stem, Path(receta_path).stem))
    letra = cfg.get("letra") or next(c for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if c not in letras_usadas(tema))
    carpeta = TERMINADOS / nfc(carpeta_de(tema) or f"{fecha} {tema}")
    carpeta.mkdir(parents=True, exist_ok=True)
    return carpeta / f"{fecha} {tema} - {letra} {variante}.mp4"


def registrar(dst, proyecto, receta_path, fecha=None):
    if not REGISTRO.exists():
        REGISTRO.write_text(CABECERA)
    fecha = fecha or datetime.date.today().isoformat()
    cods = efectos_de(proyecto, receta_path)
    with REGISTRO.open("a") as f:
        f.write(f"| {fecha} | {dst.parent.name} | {dst.name} | {proyecto} | {Path(receta_path).name} | | {cods} |\n")
    poner_al_dia_indice()


def efectos_de(proyecto, receta_path):
    """Códigos E-NN de la biblioteca que lleva la entrega (columna «Efectos»). Nunca para una entrega: si falla, «?»."""
    try:
        import efectos_indice
        return efectos_indice.texto_codigos(efectos_indice.codigos(proyecto, receta_path, ruta=receta_path))
    except Exception as ex:  # noqa: BLE001 — la entrega manda; el código se rellena luego con `efectos_indice.py columna`
        print(f"  aviso: no pude apuntar los efectos ({ex})")
        return "?"


def poner_al_dia_indice():
    """Los «videos» de cada efecto del índice, al día tras cada entrega (efectos_indice.py usos)."""
    try:
        import contextlib
        import io
        import efectos_indice
        with contextlib.redirect_stdout(io.StringIO()):
            efectos_indice.usos()
    except Exception as ex:  # noqa: BLE001
        print(f"  aviso: el índice de efectos no se puso al día ({ex}); pasa `python3 scripts/efectos_indice.py usos`")


def entregar(src, cfg, receta_path, proyecto, mover=False, fecha=None):
    """Copia (o mueve) el render a su carpeta con su nombre y lo apunta en el registro."""
    PUBLICADOS.mkdir(exist_ok=True)
    dst = destino(cfg, receta_path, fecha)
    (shutil.move if mover else shutil.copy2)(str(src), dst)
    registrar(dst, proyecto, receta_path, fecha)
    return dst
