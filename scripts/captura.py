"""Captura de una web oficial para la escena «captura» de la Pizarra.

    python3 scripts/captura.py <url> proyectos/<VIDEO>/assets/capturas/<nombre>.png --busca "plazo de tres meses" [--busca …]

Hace una foto de la página (ancho de ordenador, sin las barras fijas ni los avisos de cookies, que se
quitan sin aceptar nada) y apunta dónde está cada texto de `--busca`. Deja junto a la imagen un .json
con la dirección, la fecha y la posición de cada texto: la Pizarra baja la página hasta ahí y lo resalta.

Solo páginas oficiales y públicas, sin datos personales. Usa el Chrome y el puppeteer-core que ya
trae HyperFrames 0.8.78: no instala nada.
"""
import argparse
import datetime
import glob
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse

NPX = Path.home() / ".npm/_npx"

JS = r"""
const puppeteer = require(process.env.PPT);
const [url, dst, ancho, dpr, buscasJson, antes, despues, maxAlto] = process.argv.slice(2);
const buscas = JSON.parse(buscasJson);
(async () => {
  const b = await puppeteer.launch({executablePath: process.env.CHROME, headless: true,
                                    args: ["--no-sandbox", "--hide-scrollbars", "--lang=es-ES"]});
  const p = await b.newPage();
  await p.setViewport({width: +ancho, height: 1000, deviceScaleFactor: +dpr});
  await p.setExtraHTTPHeaders({"Accept-Language": "es-ES,es;q=0.9"});
  const resp = await p.goto(url, {waitUntil: "networkidle2", timeout: 60000});
  const estado = resp ? resp.status() : 0;
  await new Promise(r => setTimeout(r, 800));
  // fuera barras fijas y avisos de cookies (no se acepta nada: solo se ocultan para la foto)
  await p.evaluate(() => {
    for (const el of document.querySelectorAll("body *")) {
      const s = getComputedStyle(el);
      if (s.position === "fixed" || s.position === "sticky") el.style.setProperty("display", "none", "important");
    }
    document.documentElement.style.overflow = "visible";
    document.body.style.overflow = "visible";
  });
  const marcas = await p.evaluate((buscas) => {
    const nodos = [], partes = [];
    const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    let total = 0;
    while (w.nextNode()) {
      const n = w.currentNode;
      const el = n.parentElement;
      if (!el || !n.textContent) continue;
      const s = getComputedStyle(el);
      if (s.display === "none" || s.visibility === "hidden") continue;
      nodos.push([n, total]); partes.push(n.textContent); total += n.textContent.length;
    }
    const texto = partes.join("");
    const esc = q => q.trim().split(/\s+/).map(x => x.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("\\s+");
    const donde = i => { let k = 0; while (k + 1 < nodos.length && nodos[k + 1][1] <= i) k++; return [nodos[k][0], i - nodos[k][1]]; };
    const out = {};
    for (const q of buscas) {
      const re = new RegExp(esc(q), "giu");
      let m, hecho = false;
      while (!hecho && (m = re.exec(texto))) {
        const [n0, o0] = donde(m.index), [n1, o1] = donde(m.index + m[0].length - 1);
        const r = document.createRange(); r.setStart(n0, o0); r.setEnd(n1, o1 + 1);
        const c = r.getBoundingClientRect();
        if (c.width < 1 || c.height < 1) continue;
        // un recuadro por renglón (si la frase parte línea, cada trozo va en su sitio)
        const lineas = [];
        for (const q of r.getClientRects()) {
          if (q.width < 2 || q.height < 2) continue;
          const l = lineas.find(z => Math.abs(z.y - (q.top + scrollY)) < q.height * 0.5);
          if (l) { const x1 = Math.max(l.x + l.w, q.right + scrollX); l.x = Math.min(l.x, q.left + scrollX); l.w = x1 - l.x; l.h = Math.max(l.h, q.height); }
          else lineas.push({x: q.left + scrollX, y: q.top + scrollY, w: q.width, h: q.height});
        }
        out[q] = {x: c.left + scrollX, y: c.top + scrollY, w: c.width, h: c.height, lineas}; hecho = true;
      }
    }
    return out;
  }, buscas);
  const alto = await p.evaluate(() => Math.max(document.body.scrollHeight, document.documentElement.scrollHeight));
  const ys = Object.values(marcas).map(m => m.y);
  let y0 = 0, y1 = Math.min(alto, +maxAlto);
  if (ys.length && Math.max(...ys) + +despues > +maxAlto) {   // la frase está muy abajo: ventana alrededor
    y0 = Math.max(0, Math.min(...ys) - +antes); y1 = Math.min(alto, Math.max(...ys) + +despues);
  }
  await p.screenshot({path: dst, clip: {x: 0, y: y0, width: +ancho, height: y1 - y0}, captureBeyondViewport: true});
  for (const k in marcas) { marcas[k].y -= y0; for (const l of marcas[k].lineas) l.y -= y0; }
  console.log(JSON.stringify({marcas, ancho: +ancho, alto: y1 - y0, desde: y0, estado, titulo: await p.title()}));
  await b.close();
})().catch(e => { console.error(String(e)); process.exit(1); });
"""


def _puppeteer():
    for pj in sorted(glob.glob(str(NPX / "*/node_modules/hyperframes/package.json"))):
        if json.loads(Path(pj).read_text()).get("version") == "0.8.78":
            ppt = Path(pj).parent.parent / "puppeteer-core"
            if ppt.exists():
                return ppt
    sys.exit("captura: no encuentro puppeteer-core de HyperFrames 0.8.78 "
             "(ejecuta una vez: HYPERFRAMES_SKIP_SKILLS=1 npx --yes hyperframes@0.8.78 --version)")


def _chrome():
    shell = sorted(glob.glob(str(Path.home() / ".cache/hyperframes/chrome/chrome-headless-shell/*/*/chrome-headless-shell")))
    if shell:
        return shell[-1]
    app = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if Path(app).exists():
        return app
    sys.exit("captura: no encuentro Chrome")


def capturar(url, dst, buscas, ancho=1000, dpr=2, antes=1500, despues=1400, max_alto=5000):
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        js = Path(tmp) / "captura.cjs"
        js.write_text(JS)
        r = subprocess.run(["node", str(js), url, str(dst), str(ancho), str(dpr), json.dumps(buscas),
                            str(antes), str(despues), str(max_alto)], capture_output=True, text=True, timeout=180,
                           env={**os.environ, "PPT": str(_puppeteer()), "CHROME": _chrome()})
    if r.returncode or not dst.exists():
        sys.exit(f"captura: falló con {url}: {(r.stderr or r.stdout)[-600:]}")
    info = json.loads(r.stdout.strip().splitlines()[-1])
    info.update(url=url, dominio=urlparse(url).netloc.removeprefix("www."), dpr=dpr,
                fecha=datetime.date.today().isoformat())
    dst.with_suffix(".json").write_text(json.dumps(info, ensure_ascii=False, indent=2))
    if info["estado"] >= 400:
        dst.unlink()
        dst.with_suffix(".json").unlink()
        sys.exit(f"captura: la página respondió {info['estado']} («{info['titulo']}»): no hay foto. Algunas sedes no dejan "
                 "entrar a un navegador automático: haz la captura a mano (ver la escena «captura» en el catálogo).")
    faltan = [b for b in buscas if b not in info["marcas"]]
    print(f"captura: {dst} ({info['ancho']}×{info['alto']:.0f}, desde y={info['desde']:.0f}) · «{info['titulo']}»")
    for b, m in info["marcas"].items():
        print(f"  «{b}» en y={m['y']:.0f}")
    if faltan:
        print(f"  ¡no encontré en la página! {', '.join('«%s»' % f for f in faltan)}")
    return info


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url")
    ap.add_argument("destino", help="ruta .png (se guarda también un .json con el mismo nombre)")
    ap.add_argument("--busca", action="append", default=[], help="texto de la página que se resalta (varias veces)")
    ap.add_argument("--ancho", type=int, default=1000, help="ancho de la ventana en px (1000 = ordenador estrecho)")
    a = ap.parse_args()
    info = capturar(a.url, a.destino, a.busca, a.ancho)
    if a.busca and not info["marcas"]:
        sys.exit(1)
