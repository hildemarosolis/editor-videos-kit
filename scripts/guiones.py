#!/usr/bin/env python3
"""Guiones desde comentarios, en tu carpeta de trabajo (la de kit.carpeta_editor(), p. ej. en iCloud o Dropbox).

  python3 scripts/guiones.py publicar <carpeta-del-guion> | --todos
  python3 scripts/guiones.py pendientes
  python3 scripts/guiones.py recoger <carpeta-del-guion> <captura> [<captura> …]

- publicar: copia guiones/<carpeta>/ a tu carpeta de trabajo → «0 Guiones» → «<fecha> <tema>/», para leerlo en el
  móvil: Guion.pdf, Fuentes.pdf, las capturas («Comentario N.jpg») y `.guion` (qué carpeta del proyecto es).
  El original sigue en guiones/ (en git, sin capturas); la copia se rehace cada vez que se publica.
- pendientes: capturas sueltas en «0 Comentarios» que aún no tienen guion.
- recoger: mete esas capturas en guiones/<carpeta>/captura-N.jpg y mueve el original a «0 Comentarios/Procesadas».

Después el creador graba, guarda el vídeo dentro de la carpeta de «0 Guiones» y arrastra la carpeta a
«1 Para editar»: `.guion` dice de qué guion es y `/editor` arranca con ese guion.

El PDF se hace con Chrome o Chromium sin ventana (el de HyperFrames vale). En Mac, las capturas HEIC se pasan a
JPG con `sips`; en Windows y Linux, con FFmpeg.
"""
import argparse
import html
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kit  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
EDITOR = kit.carpeta_editor()
GUIONES_TRABAJO = kit.carpeta("guiones")
COMENTARIOS = kit.carpeta("comentarios")
IMAGEN = {".jpg", ".jpeg", ".png", ".heic"}
MARCA = ".guion"  # dentro de cada carpeta de «0 Guiones»: el nombre de su carpeta en guiones/

CSS = """
@page { size: 105mm 187mm; margin: 7mm 6mm; }
body { font: 10.5pt/1.42 -apple-system, "Helvetica Neue", Arial, sans-serif; color: #111; }
h1 { font-size: 15pt; line-height: 1.15; margin: 0 0 8pt; }
h1 .ac { background: #FFC800; padding: 0 3pt; }
h2 { font-size: 12pt; margin: 14pt 0 4pt; border-bottom: 2pt solid #FFC800; padding-bottom: 2pt; }
h3 { font-size: 11pt; margin: 10pt 0 3pt; }
p { margin: 4pt 0; }
ul, ol { margin: 3pt 0; padding-left: 13pt; }
li { margin: 2pt 0; }
blockquote { margin: 5pt 0; padding: 4pt 7pt; background: #f4f4f4; border-left: 3pt solid #FFC800; }
blockquote p { margin: 3pt 0; }
table { border-collapse: collapse; width: 100%; font-size: 8pt; margin: 4pt 0; }
th, td { border: 0.5pt solid #bbb; padding: 2pt 3pt; vertical-align: top; text-align: left; }
th { background: #FFC800; }
code { font: 8.5pt Menlo, monospace; background: #f0f0f0; padding: 0 2pt; }
a { color: #0a58ca; word-break: break-all; }
"""


def _inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?!\w)", r"<i>\1</i>", t)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', t)
    t = re.sub(r"(?<![\"'>=])(https?://[^\s<)]+)", r'<a href="\1">\1</a>', t)
    return t


def md_a_html(md):
    """Lo justo de Markdown para nuestros guiones: títulos, listas (anidadas por sangría), citas, tablas, negritas."""
    out, lineas, i = [], md.splitlines(), 0
    pila = []  # listas abiertas: (sangría, "ul"|"ol")

    def cerrar_listas(hasta=-1):
        while pila and pila[-1][0] > hasta:
            out.append(f"</li></{pila.pop()[1]}>")

    while i < len(lineas):
        l = lineas[i]
        m = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", l)
        if m and not l.lstrip().startswith(">"):
            sang, tipo = len(m.group(1)), "ol" if m.group(2)[0].isdigit() else "ul"
            if pila and sang > pila[-1][0]:
                out.append(f"<{tipo}>")
                pila.append((sang, tipo))
            else:
                cerrar_listas(sang)
                if pila and pila[-1][0] == sang:
                    out.append("</li>")
                else:
                    out.append(f"<{tipo}>")
                    pila.append((sang, tipo))
            num = f' value="{m.group(2)[:-1]}"' if tipo == "ol" else ""  # «16.» sigue siendo 16 tras un blanco
            out.append(f"<li{num}>{_inline(m.group(3))}")
            i += 1
            continue
        if pila and not l.strip():  # un blanco entre puntos no cierra la lista si sigue otro punto
            j = i + 1
            while j < len(lineas) and not lineas[j].strip():
                j += 1
            if j < len(lineas) and (lineas[j].startswith(" ") or re.match(r"^([-*]|\d+\.)\s", lineas[j])):
                i = j
                continue
        if pila and l.startswith(" ") and l.strip():  # continuación de un punto (o una cita dentro de él)
            s = l.strip()
            out.append(f"<blockquote>{_inline(s[1:].strip())}</blockquote>" if s.startswith(">") else " " + _inline(s))
            i += 1
            continue
        cerrar_listas()
        if l.startswith("|"):
            filas = []
            while i < len(lineas) and lineas[i].startswith("|"):
                if not re.match(r"^\|[\s:|-]+\|$", lineas[i]):
                    filas.append([c.strip() for c in lineas[i].strip().strip("|").split("|")])
                i += 1
            out.append("<table>" + "".join(
                "<tr>" + "".join(f"<{'th' if k == 0 else 'td'}>{_inline(c)}</{'th' if k == 0 else 'td'}>" for c in f)
                + "</tr>" for k, f in enumerate(filas)) + "</table>")
            continue
        if l.lstrip().startswith(">"):
            bloque = []
            while i < len(lineas) and lineas[i].lstrip().startswith(">"):
                bloque.append(re.sub(r"^\s*>\s?", "", lineas[i]))
                i += 1
            out.append("<blockquote>" + md_a_html("\n".join(bloque)) + "</blockquote>")
            continue
        m = re.match(r"^(#{1,3})\s+(.*)$", l)
        if m:
            n = len(m.group(1))
            out.append(f"<h{n}>{_inline(m.group(2))}</h{n}>")
        elif l.strip():
            out.append(f"<p>{_inline(l.strip())}</p>")
        i += 1
    cerrar_listas()
    return "\n".join(out)


def _chrome():
    """Chrome o Chromium para imprimir el PDF: el de Mac, el del sistema o el que trae HyperFrames."""
    app = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if Path(app).exists():
        return app
    for n in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome", "msedge"):
        if shutil.which(n):
            return shutil.which(n)
    shell = sorted(Path.home().glob(".cache/hyperframes/chrome/chrome-headless-shell/*/*/chrome-headless-shell*"))
    if shell:
        return str(shell[-1])
    sys.exit("no encuentro Chrome ni Chromium para hacer el PDF (instala Google Chrome)")


def a_pdf(md, destino, titulo):
    doc = (f'<!doctype html><html lang="es"><head><meta charset="utf-8"><title>{html.escape(titulo)}</title>'
           f"<style>{CSS}</style></head><body>{md_a_html(md)}</body></html>")
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "guion.html"
        f.write_text(kit.pinta(doc))
        pdf = Path(tmp) / "guion.pdf"
        r = subprocess.run([_chrome(), "--headless", "--disable-gpu", "--no-pdf-header-footer",
                            f"--print-to-pdf={pdf}", f.as_uri()], capture_output=True, text=True, timeout=120)
        if not pdf.exists():
            sys.exit(f"no pude hacer el PDF de {titulo}: {r.stderr[-400:]}")
        kit.copiar(pdf, destino)


def tema_de(carpeta):
    """«2026-10-25 Los 7.200 € de la estancia por estudios»: la fecha de la carpeta y el título del guion hasta «:»."""
    md = (carpeta / "guion.md").read_text()
    h1 = next((l[2:] for l in md.splitlines() if l.startswith("# ")), carpeta.name)
    t = re.search(r"«(.+?)»", h1)
    t = re.split(r"[:?(]", (t.group(1) if t else h1.replace("Guion:", "")))[0]  # hasta «:», «?» o «(»
    t = re.sub(r'[/\\?*"<>|¿]', "", t).strip(" .¿?¡!")
    if len(t) > 60:  # que se lea entero en el iPhone
        t = t[:60].rsplit(" ", 1)[0]
    fecha = carpeta.name[:10] if re.match(r"\d{4}-\d{2}-\d{2}", carpeta.name) else ""
    return f"{fecha} {t}".strip()


def destino_de(carpeta):
    """La carpeta de trabajo de este guion: la que ya lo lleva (aunque el creador la haya movido o renombrado),
    o una nueva en «0 Guiones»."""
    for base in (GUIONES_TRABAJO, kit.carpeta("entrada")):
        if base.exists():
            for d in base.iterdir():
                m = d / MARCA
                if d.is_dir() and m.exists() and m.read_text().strip() == carpeta.name:
                    return d
    return GUIONES_TRABAJO / tema_de(carpeta)


def capturas(carpeta):
    return sorted(carpeta.glob("captura-*"), key=lambda p: int(re.sub(r"\D", "", p.stem) or 0))


def publicar(nombre):
    carpeta = ROOT / "guiones" / nombre
    if not (carpeta / "guion.md").exists():
        sys.exit(f"no hay guiones/{nombre}/guion.md")
    dst = destino_de(carpeta)
    dst.mkdir(parents=True, exist_ok=True)
    a_pdf((carpeta / "guion.md").read_text(), dst / "Guion.pdf", tema_de(carpeta))
    if (carpeta / "fuentes.md").exists():
        a_pdf((carpeta / "fuentes.md").read_text(), dst / "Fuentes.pdf", "Fuentes")
    for k, c in enumerate(capturas(carpeta), 1):
        kit.copiar(c, dst / f"Comentario {k}{c.suffix.lower()}")
    (dst / MARCA).write_text(carpeta.name + "\n")
    print(f"{nombre} → {dst.relative_to(EDITOR)}/ (Guion.pdf, Fuentes.pdf, {len(capturas(carpeta))} comentario(s))")
    return dst


def pendientes():
    if not COMENTARIOS.exists():
        return []
    return [p for p in sorted(COMENTARIOS.iterdir()) if p.is_file() and p.suffix.lower() in IMAGEN
            and not p.name.startswith(".")]


def recoger(nombre, archivos):
    carpeta = ROOT / "guiones" / nombre
    carpeta.mkdir(parents=True, exist_ok=True)
    hecho = COMENTARIOS / "Procesadas"
    hecho.mkdir(parents=True, exist_ok=True)
    n = len(capturas(carpeta))
    for a in archivos:
        p = Path(a) if Path(a).is_absolute() else COMENTARIOS / a
        if shutil.which("brctl"):  # iCloud en Mac: que el archivo esté bajado, no solo su marcador
            subprocess.run(["brctl", "download", str(p)], capture_output=True)
        n += 1
        dst = carpeta / f"captura-{n}.jpg"
        if p.suffix.lower() in {".heic", ".png"}:  # todo en jpg: lo leen igual el PDF, la tarjeta y el móvil
            if shutil.which("sips"):
                subprocess.run(["sips", "-s", "format", "jpeg", str(p), "--out", str(dst)], capture_output=True, check=True)
            else:
                subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(p), "-q:v", "2", str(dst)],
                               check=True)
        else:
            shutil.copy2(p, dst)
        kit.copiar(p, hecho / p.name, mover=True)
        print(f"{p.name} → guiones/{nombre}/{dst.name}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    pu = sub.add_parser("publicar")
    pu.add_argument("carpeta", nargs="?")
    pu.add_argument("--todos", action="store_true")
    sub.add_parser("pendientes")
    rc = sub.add_parser("recoger")
    rc.add_argument("carpeta")
    rc.add_argument("capturas", nargs="+")
    a = ap.parse_args()
    if a.cmd == "publicar":
        nombres = ([d.name for d in sorted((ROOT / "guiones").iterdir()) if (d / "guion.md").exists()]
                   if a.todos else [a.carpeta])
        if not nombres or nombres == [None]:
            sys.exit("di qué carpeta de guiones/ publicar, o --todos")
        for n in nombres:
            publicar(n)
    elif a.cmd == "pendientes":
        ps = pendientes()
        print(f"{len(ps)} comentario(s) por guionizar en «0 Comentarios»" + "".join(f"\n  {p.name}" for p in ps))
    else:
        recoger(a.carpeta, a.capturas)


if __name__ == "__main__":
    main()
