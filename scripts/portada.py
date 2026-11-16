"""Portada del reel: foto REAL del creador recortada, fondo hecho por una IA de imágenes (sin personas ni texto)
y titular puesto aquí con la marca exacta. La IA nunca hace la cara (no se parece lo bastante) ni el texto (lo deforma).

    .venv/bin/python scripts/portada.py <fondo.png> <salida.png> --persona marca/fotos/<foto>.jpg \\
        --l1 "LO QUE NADIE" --l2 "TE CUENTA" [--nota "PASO 1 · EMPADRONARTE"]

SOLO MAC con `--persona`: el recorte usa Vision de Apple (`recorte.swift`, compilado con `swiftc`, de las Command
Line Tools de Xcode). En Windows o Linux, o sin swiftc, `--persona` se para con un aviso; pasa una máscara ya hecha
como `<salida>_mascara.png` o usa la portada sin `--persona` (fondo + titular, eso va en cualquier sistema).

- `--persona`: una foto tuya (pose y gesto que cuenten la idea). Se escala a 1080 de ancho, se apoya abajo
  y se recorta con Vision (el binario de `recorte.py`, como la pegatina); la máscara se guarda al lado como
  `<salida>_mascara.png` y no se recalcula si ya existe. Sin `--persona`, `<fondo>` se usa tal cual.
- El fondo se pide a una IA de imágenes (9:16): el lugar del vídeo, sin personas, sin texto, desenfocado como si
  hubiera alguien delante. Gasta créditos: pídelo solo con permiso del creador.
- 1080×1920. Titular en dos líneas apiladas, centrado, entre el 15 % y el 30 % del alto: la primera en blanco y la
  segunda en el acento de tu marca (marca/marca.json), Anton en mayúsculas, contorno negro de 8 px y sombra suave.
- `--nota`: una nota de papel con cinta, abajo a la derecha, dentro del recuadro central 1080×1440 (la cuadrícula
  del perfil corta lo de fuera); el 15 % de abajo queda libre para los botones de Instagram.
- Sale también `<salida>_cuadricula.png`: cómo se ve recortada en la cuadrícula del perfil (3:4), para comprobarla.
"""
import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kit  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ANTON = ROOT / "marca/fuentes/Anton-Regular.ttf"
OSWALD = ROOT / "marca/fuentes/Oswald-Variable.ttf"
AMARILLO = tuple(int(kit.acento().lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))  # el acento: (255, 200, 0) con #FFC800
W, H = 1080, 1920


def ajustar(foto):
    """Recorta la foto a 9:16 por el centro y la lleva a 1080×1920."""
    im = Image.open(foto).convert("RGB")
    r = im.width / im.height
    if r > W / H:
        nw = int(im.height * W / H)
        im = im.crop(((im.width - nw) // 2, 0, (im.width - nw) // 2 + nw, im.height))
    else:
        nh = int(im.width * H / W)
        im = im.crop((0, (im.height - nh) // 2, im.width, (im.height - nh) // 2 + nh))
    return im.resize((W, H), Image.LANCZOS)


def linea(lienzo, texto, y, color, alto_letra, ancho_max=960):
    """Una línea centrada en Anton; baja el cuerpo si no cabe. Devuelve la y de abajo."""
    px = alto_letra
    while True:
        f = ImageFont.truetype(str(ANTON), px)
        x0, y0, x1, y1 = f.getbbox(texto, stroke_width=8)
        if x1 - x0 <= ancho_max or px < 60:
            break
        px -= 4
    x = (W - (x1 - x0)) // 2 - x0
    sombra = Image.new("RGBA", lienzo.size, (0, 0, 0, 0))
    ImageDraw.Draw(sombra).text((x + 6, y + 10), texto, font=f, fill=(0, 0, 0, 150), stroke_width=8, stroke_fill=(0, 0, 0, 150))
    lienzo.alpha_composite(sombra.filter(ImageFilter.GaussianBlur(8)))
    ImageDraw.Draw(lienzo).text((x, y), texto, font=f, fill=color, stroke_width=8, stroke_fill=(0, 0, 0))
    return y + (y1 - y0) - 6


def nota(lienzo, texto):
    """Nota de papel con un trozo de cinta, ligeramente girada."""
    f = ImageFont.truetype(str(ANTON), 54)
    partes = [p.strip() for p in texto.split("·")]
    anchos = [f.getbbox(p)[2] for p in partes]
    w, h = max(anchos) + 80, 70 * len(partes) + 60
    papel = Image.new("RGBA", (w + 40, h + 60), (0, 0, 0, 0))
    d = ImageDraw.Draw(papel)
    d.rectangle((20, 30, 20 + w, 30 + h), fill=(250, 247, 238, 255))
    for k, p in enumerate(partes):
        col = (17, 17, 17) if k else (200, 30, 30)
        d.text((20 + (w - anchos[k]) // 2, 55 + k * 70), p, font=f, fill=col)
    d.rectangle(((w + 40) // 2 - 70, 12, (w + 40) // 2 + 70, 50), fill=(235, 225, 190, 210))  # la cinta
    papel = papel.rotate(-4, expand=True, resample=Image.BICUBIC)
    sombra = Image.new("RGBA", lienzo.size, (0, 0, 0, 0))
    x, y = W - papel.width - 70, 1440 + 240 - papel.height - 60  # dentro del recuadro 3:4 y fuera del 15 % de abajo
    sombra.paste((0, 0, 0, 130), (x + 10, y + 16), papel)
    lienzo.alpha_composite(sombra.filter(ImageFilter.GaussianBlur(12)))
    lienzo.alpha_composite(papel, (x, y))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("foto")
    ap.add_argument("salida")
    ap.add_argument("--l1", required=True)
    ap.add_argument("--l2", required=True)
    ap.add_argument("--nota")
    ap.add_argument("--persona", help="tu foto real: se recorta con Vision (solo Mac) y se pega encima del fondo")
    a = ap.parse_args()
    out = Path(a.salida)
    lienzo = ajustar(a.foto).convert("RGBA")
    if a.persona:  # la cara es la de la foto real, nunca la de la IA: la IA solo pone el fondo
        foto = Image.open(a.persona).convert("RGB")
        alto = round(foto.height * W / foto.width)
        persona = Image.new("RGB", (W, H), (0, 0, 0))
        persona.paste(foto.resize((W, alto), Image.LANCZOS), (0, H - alto))  # apoyada abajo, a lo ancho
        mpath = out.with_name(out.stem + "_mascara.png")
        if not mpath.exists():
            import tempfile
            if sys.platform != "darwin":  # sin swiftc, recorte.compilar() se para con su propio aviso
                sys.exit("portada: --persona recorta con Vision de Apple y solo funciona en Mac. Pasa la máscara "
                         f"hecha como {mpath.name} o haz la portada sin --persona.")
            sys.path.insert(0, str(ROOT / "scripts"))
            from pegatina import _vision
            with tempfile.TemporaryDirectory() as tmp:
                lp = Path(tmp) / "lienzo.png"
                persona.save(lp)
                Image.frombytes("L", (W, H), _vision(lp, W, H)).save(mpath)
        persona = persona.convert("RGBA")
        m = Image.open(mpath).convert("L").filter(ImageFilter.GaussianBlur(1.2))
        persona.putalpha(m)
        sombra = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sombra.paste((0, 0, 0, 120), (14, 18), m)
        lienzo.alpha_composite(sombra.filter(ImageFilter.GaussianBlur(18)))
        lienzo.alpha_composite(persona)
    # degradado oscuro arriba para que el titular se lea sobre cualquier foto
    grad = Image.new("L", (1, H), 0)
    for yy in range(H):
        grad.putpixel((0, yy), int(150 * max(0.0, 1 - yy / 760)))
    negro = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    negro.putalpha(grad.resize((W, H)))
    lienzo.alpha_composite(negro)
    letra = int(H * 0.09)
    y = linea(lienzo, a.l1.upper(), int(H * 0.145), (255, 255, 255), letra)
    linea(lienzo, a.l2.upper(), y + 4, AMARILLO, letra)
    if a.nota:
        nota(lienzo, a.nota)
    lienzo.convert("RGB").save(out)
    lienzo.crop((0, 240, W, 240 + 1440)).convert("RGB").save(out.with_name(out.stem + "_cuadricula.png"))
    print(f"portada: {out} (y {out.stem}_cuadricula.png)")


if __name__ == "__main__":
    main()
