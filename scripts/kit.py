"""Lo que cambia de un creador a otro, en un solo sitio.

- marca/marca.json  → tu marca: usuario, nombre, color de acento, fuente, redes y palabras de «Comenta».
- editor.json       → tu ordenador: dónde está la carpeta de trabajo y el python con OpenCV
                      (no va a git; se crea copiando editor.ejemplo.json).

Los scripts nunca escriben tu @ ni tus rutas: las piden aquí.

Variables de entorno:
  EDITOR_MARCA=<ruta>   usa otro marca.json (p. ej. para probar con la marca de otra persona).
  EDITOR_SIN_VT=1       en Mac, no usa VideoToolbox (fuerza el camino de software, el de Windows y Linux).
"""
import json
import os
import platform
import shutil
import sys
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# El color por defecto con el que están escritas las piezas: kit.pinta() lo cambia por tu acento.
ACENTO_BASE = "#FFC800"

CARPETAS = {
    "referencias": "0 Referencias",
    "comentarios": "0 Comentarios",
    "guiones": "0 Guiones",
    "entrada": "1 Para editar",
    "terminados": "2 Terminados",
    "originales": "3 Originales usados",
    "publicados": "4 Publicados",
    "recursos": "Recursos",
}


def _leer(p):
    p = Path(p)
    return json.loads(p.read_text()) if p.exists() else {}


@lru_cache(None)
def marca():
    m = {"usuario": "tucuenta", "nombre": "Tu nombre", "acento": ACENTO_BASE, "fuente": "Anton",
         "redes": ["instagram", "tiktok", "youtube", "facebook"], "palabras": {}, "palabra_por_defecto": None}
    m.update(_leer(os.environ.get("EDITOR_MARCA") or ROOT / "marca/marca.json"))
    m["usuario"] = m["usuario"].lstrip("@")
    m["palabras"] = {k.upper(): v for k, v in (m.get("palabras") or {}).items()}
    pd = (m.get("palabra_por_defecto") or "").upper()
    if pd not in m["palabras"]:  # una palabra por defecto que no está montada no vale: nadie respondería
        pd = next(iter(m["palabras"]), None)
    m["palabra_por_defecto"] = pd
    return m


def usuario(arroba=True):
    """Tu usuario en redes: «@tucuenta» (o sin @)."""
    u = marca()["usuario"]
    return f"@{u}" if arroba else u


def nombre():
    return marca()["nombre"]


def acento():
    return marca()["acento"]


def palabras():
    """Las palabras de «Comenta X» que tienes montadas (ManyChat u otra), en mayúsculas."""
    return set(marca()["palabras"])


def palabra_por_defecto():
    """La palabra que sale si una receta no dice otra. None si no tienes ninguna montada."""
    return marca()["palabra_por_defecto"]


def aviso_palabra(palabra, defecto="Te escribo por mensaje"):
    v = marca()["palabras"].get((palabra or "").upper()) or {}
    return v.get("aviso", defecto) if isinstance(v, dict) else defecto


def _rgb(hexa):
    h = hexa.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def pinta(texto):
    """Cambia el acento base (#FFC800) por el de tu marca en un HTML, CSS o filtro de FFmpeg ya escrito."""
    a = acento()
    if a.upper() == ACENTO_BASE:
        return texto
    r, g, b = _rgb(a)
    for viejo, nuevo in (("#FFC800", a), ("#ffc800", a.lower()), ("0xFFC800", "0x" + a.lstrip("#").upper()),
                         ("rgba(255,200,0,", f"rgba({r},{g},{b},"), ("rgba(255, 200, 0,", f"rgba({r}, {g}, {b},")):
        texto = texto.replace(viejo, nuevo)
    return texto


# --- tu ordenador -------------------------------------------------------------------------------

@lru_cache(None)
def ajustes():
    return _leer(ROOT / "editor.json")


def carpeta_editor():
    """La carpeta de trabajo con «1 Para editar», «2 Terminados»… (por defecto ~/Editor)."""
    return Path(os.path.expanduser(ajustes().get("carpeta_editor", "~/Editor")))


def carpeta(clave):
    """carpeta("entrada") → …/1 Para editar. Claves: referencias, comentarios, guiones, entrada,
    terminados, originales, publicados, recursos."""
    return carpeta_editor() / CARPETAS[clave]


def python_opencv():
    """El python que tiene OpenCV y Pillow (por defecto, el .venv del repo; si no, el que está corriendo)."""
    p = ajustes().get("python_opencv")
    if p:
        p = Path(os.path.expanduser(p))
        return str(p if p.is_absolute() else ROOT / p)
    for c in (ROOT / ".venv/bin/python", ROOT / ".venv/Scripts/python.exe"):
        if c.exists():
            return str(c)
    return sys.executable


# --- vídeo según el sistema -------------------------------------------------------------------

def es_mac():
    return platform.system() == "Darwin"


def usa_videotoolbox():
    """En Mac se codifica con el chip (VideoToolbox); en Windows y Linux, con libx264."""
    return es_mac() and not os.environ.get("EDITOR_SIN_VT")


def h264(bitrate, maxrate=None):
    """Argumentos de FFmpeg para codificar en H.264 con el bitrate dado («12M», «1800k»)."""
    if usa_videotoolbox():
        a = ["-c:v", "h264_videotoolbox", "-b:v", str(bitrate)]
    else:
        a = ["-c:v", "libx264", "-preset", "medium", "-b:v", str(bitrate)]
    if maxrate:
        a += ["-maxrate", str(maxrate)]
    return a


def hwaccel():
    """Decodificación por el chip en Mac; nada en los demás sistemas."""
    return ["-hwaccel", "videotoolbox"] if usa_videotoolbox() else []


def vf_a_sdr(giro=""):
    """Filtro para pasar un vídeo del iPhone (HDR HLG, 10 bits) a SDR BT.709, con un giro opcional
    ('clock' o 'cclock'). Devuelve (argumentos de entrada, filtro de vídeo)."""
    if usa_videotoolbox():
        g = f"transpose_vt=dir={giro}," if giro else ""
        return (["-hwaccel", "videotoolbox", "-hwaccel_output_format", "videotoolbox_vld"],
                g + "scale_vt=color_matrix=bt709:color_primaries=bt709:color_transfer=bt709")
    # Sin el chip, FFmpeg ya gira solo el vídeo según su marca de rotación (autorotate): el giro no se añade,
    # o saldría girado dos veces. zscale viene en las compilaciones de FFmpeg de Windows (gyan.dev, BtbN) y de Linux.
    return ([], "zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,"
                    "zscale=t=bt709:m=bt709:r=tv,format=yuv420p")


def comprobar_ffmpeg():
    """Dice qué le falta a este FFmpeg para el camino que va a usar."""
    if not shutil.which("ffmpeg"):
        return ["ffmpeg no está instalado"]
    import subprocess
    f = subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True).stdout
    falta = []
    if usa_videotoolbox():
        falta += [x for x in ("scale_vt", "transpose_vt") if x not in f]
    else:
        falta += [x for x in ("zscale", "tonemap") if x not in f]
    return falta


def crear_carpetas():
    """Crea la carpeta de trabajo con sus subcarpetas (no toca lo que ya exista)."""
    for clave in CARPETAS:
        carpeta(clave).mkdir(parents=True, exist_ok=True)
    for sub in ("Tomas de apoyo", "Outros e intros", "Música"):
        (carpeta("recursos") / sub).mkdir(exist_ok=True)
    for d in ("proyectos", "out", "raw", "models"):
        (ROOT / d).mkdir(exist_ok=True)
    print(f"Carpetas listas en {carpeta_editor()}")


if __name__ == "__main__":
    if sys.argv[1:] == ["carpetas"]:
        crear_carpetas()
        sys.exit()
    m = marca()
    print(f"Marca: {usuario()} · {m['nombre']} · acento {m['acento']} · palabras {sorted(palabras()) or 'ninguna'}"
          f" · por defecto {palabra_por_defecto() or 'ninguna (cierres sin palabra)'}")
    print(f"Carpeta de trabajo: {carpeta_editor()}" + ("" if carpeta_editor().exists() else "  (no existe todavía)"))
    print(f"Python con OpenCV: {python_opencv()}")
    print(f"Vídeo: {'VideoToolbox (Mac)' if usa_videotoolbox() else 'libx264 + zscale (software)'}")
    falta = comprobar_ffmpeg()
    print("FFmpeg: " + ("listo" if not falta else "le falta " + ", ".join(falta)))
