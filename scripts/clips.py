#!/usr/bin/env python3
"""Shorts verticales de un episodio largo de podcast (skill /clips).

El programa sale de su kit (el mismo de largo.py), marca/kits/<id>.json → bloque "clips":
  {"prefijo": "PODCAST", "reencuadre": ["--tres"], "tema": "Short Podcast {num} {tema}",
   "receta": {"variante", "acento", "seguir", "comenta", "outro"}}   # claves que se ponen en la receta del short
(los campos del bloque "programa", en largo.AYUDA_PROGRAMA).

Los cortes de cada short van en proyectos/<EPISODIO>/cortes.json (segundos del original):
  {"PODCAST_01": {"tema": "…", "gancho": [de, a], "cuerpo": [[de, a], …]}}
  Un tramo con un tercer elemento ("exacto") ya se revisó a oído y no se mueve; los demás se ajustan al mínimo de
  energía más cercano (para no cortar a mitad de palabra).

  python3 scripts/clips.py montar <EPISODIO> [SHORT …] [--sin-render]
        reencuadra cada tramo del cuerpo (reencuadre.py con las opciones del programa) y escribe
        proyectos/_montajes/<SHORT>.json: gancho de frase cortada + «impacto» + cuerpo
  python3 scripts/clips.py preparar <EPISODIO> [SHORT …]     # montaje.py + preparar.py --sin-silencios
  python3 scripts/clips.py receta <EPISODIO> <SHORT> "<receta del catálogo>"
        crea la receta del short desde su plantilla con las claves del programa (variante, acento, cierre…)
  python3 scripts/clips.py lista <EPISODIO>                 # los shorts de cortes.json con su duración
  python3 scripts/clips.py propuesta <EPISODIO>             # clip con el gancho de cada candidato + PROPUESTA_SHORTS.md
  python3 scripts/clips.py probar [EPISODIO]                # los montajes salen igual que los que hay en git

El original: raw/largos/<EPISODIO>.mp4 si existe (copia local); si no, el "original" de su largo.json.
"""
import argparse
import json
import subprocess
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import kit  # noqa: E402

VENV_PY = Path(kit.python_opencv())   # reencuadre.py necesita OpenCV


def episodio(ep):
    """(cortes, programa, clips del kit, original, carpeta)."""
    import largo
    d = ROOT / "proyectos" / ep
    f = d / "cortes.json"
    if not f.exists():
        raise SystemExit(f"Falta proyectos/{ep}/cortes.json (los shorts elegidos, en segundos del original)")
    cortes = json.loads(f.read_text())
    cfg = json.loads((d / "largo.json").read_text()) if (d / "largo.json").exists() else {}
    prog = largo.programa(cfg)
    kp = json.loads((ROOT / "marca/kits" / f"{prog['id']}.json").read_text())
    if "clips" not in kp:
        raise SystemExit(f"El kit {prog['id']} no tiene bloque \"clips\" (prefijo, reencuadre, tema, receta).\n"
                         f"{largo.AYUDA_PROGRAMA}")
    local = ROOT / "raw/largos" / f"{ep}.mp4"
    if local.exists():
        src = local
    else:
        src = Path(cfg["original"])
        src = src if src.is_absolute() else largo.EDITOR / src
    if not src.exists():
        raise SystemExit(f"No encuentro el original de {ep}: {src}")
    st = src.stat()
    if getattr(st, "st_blocks", None) is not None and st.st_blocks * 512 < st.st_size * 0.9:   # solo un marcador
        raise SystemExit(f"El original aún no está descargado de iCloud: brctl download \"{src}\"")
    return cortes, prog, kp["clips"], src, d


def shorts_de(cortes, pedidos=None):
    todos = [k for k in cortes if not k.startswith("_")]
    if pedidos:
        falta = [p for p in pedidos if p not in todos]
        if falta:
            raise SystemExit(f"No están en cortes.json: {' '.join(falta)}")
        return pedidos
    return todos


class Energia:
    """Energía de 60 ms del audio a 16 kHz del episodio, para mover cada corte a la pausa más cercana."""

    def __init__(self, wav):
        import numpy as np
        self.np = np
        w = wave.open(str(wav))
        self.A = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32)

    def rms(self, t):
        i, h = int(t * 16000), 480
        seg = self.A[max(0, i - h):i + h]
        return float(self.np.sqrt((seg ** 2).mean() + 1e-9))

    def ajusta(self, t, inicio):
        np = self.np
        rango = np.arange(t - 0.4, t + 0.2, 0.01) if inicio else np.arange(t - 0.2, t + 0.4, 0.01)
        return round(float(min(rango, key=self.rms)), 2)


def vertical(src, f, pa, pb, opciones, sin_render):
    """Reencuadra [pa, pb] del original a out/<f>, salvo que ya exista de ese mismo origen, tramo y opciones.

    La ficha out/<f>.fuente.json dice de dónde salió: si se mueve un corte aunque dure lo mismo, se rehace
    (antes solo se miraba la duración y se reutilizaba un vertical de otro tramo)."""
    dest = ROOT / "out" / f
    ficha = dest.with_suffix(".fuente.json")
    quiero = {"src": str(src), "pa": round(pa, 2), "pb": round(pb, 2), "opciones": list(opciones)}
    hecho = dest.exists() and ficha.exists() and json.loads(ficha.read_text()) == quiero
    if not sin_render and not hecho:
        subprocess.run([str(VENV_PY), str(ROOT / "scripts/reencuadre.py"), str(src), f"{pa:.2f}", f"{pb:.2f}",
                        str(dest), *opciones], check=True)
        ficha.write_text(json.dumps(quiero, ensure_ascii=False) + "\n")


def montar(ep, pedidos=None, sin_render=False):
    cortes, prog, cl, src, d = episodio(ep)
    en = None
    salida = []
    for n in shorts_de(cortes, pedidos):
        s = cortes[n]
        exactos = all(len(t) > 2 for t in [s["gancho"], *s["cuerpo"]])
        if not exactos and en is None:
            en = Energia(d / "audio_16k.wav")
        # un tramo con "exacto" (3.er elemento) ya está revisado a oído en el corte: no se reajusta
        fija = lambda t: [t[0], t[1]] if len(t) > 2 else [en.ajusta(t[0], True), en.ajusta(t[1], False)]
        cuerpo = [fija(t) for t in s["cuerpo"]]
        g = fija(s["gancho"])
        tramos, gancho = [], None
        for k, (a, b) in enumerate(cuerpo):
            pa, pb = max(0, a - 0.5), b + 0.5       # margen para el reencuadre
            f = f"{n}_p{k + 1}_vertical.mp4"
            vertical(src, f, pa, pb, cl.get("reencuadre", []), sin_render)
            tramos.append({"archivo": f, "de": round(a - pa, 2), "a": round(b - pa, 2)})
            if pa <= g[0] and g[1] <= pb:
                gancho = {"archivo": f, "de": round(g[0] - pa, 2), "a": round(g[1] - pa, 2)}
        if gancho is None:   # el gancho cae fuera del cuerpo: su propio tramo reencuadrado
            pa, pb = max(0, g[0] - 0.5), g[1] + 0.5
            f = f"{n}_g_vertical.mp4"
            vertical(src, f, pa, pb, cl.get("reencuadre", []), sin_render)
            gancho = {"archivo": f, "de": round(g[0] - pa, 2), "a": round(g[1] - pa, 2)}
        tramos[0]["entrada"] = "impacto"
        opciones = " ".join(cl.get("reencuadre", []))
        m = {"_nota": f"Short de «{prog['nombre']}» ({ep}): {s['tema']}. Gancho de frase cortada {g[0]}–{g[1]} s del "
                      f"original + impacto + cuerpo {cuerpo}. Archivos: reencuadre.py{' ' + opciones if opciones else ''} "
                      f"de cada tramo (con 0,5 s de margen).",
             "carpeta": "out", "salida": f"raw/{n}.mp4", "tramos": [gancho] + tramos}
        (ROOT / "proyectos/_montajes" / f"{n}.json").write_text(json.dumps(m, ensure_ascii=False, indent=1))
        print(n, "gancho", g, "cuerpo", cuerpo, f"≈{g[1]-g[0]+sum(b-a for a,b in cuerpo):.0f} s")
        salida.append(m)
    return salida


def preparar(ep, pedidos=None):
    cortes, *_ = episodio(ep)
    for n in shorts_de(cortes, pedidos):
        subprocess.run([sys.executable, str(ROOT / "scripts/montaje.py"), str(ROOT / "proyectos/_montajes" / f"{n}.json")],
                       check=True, cwd=ROOT)   # "carpeta": "out" es relativa a la raíz del editor
        subprocess.run([sys.executable, str(ROOT / "scripts/preparar.py"), n, "--sin-silencios"], check=True)


def receta(ep, n, nombre_receta):
    """Receta del short desde la plantilla del catálogo, con las claves del programa (cierre, acento, sin Sígueme…)."""
    cortes, prog, cl, _, _ = episodio(ep)
    if n not in cortes:
        raise SystemExit(f"{n} no está en proyectos/{ep}/cortes.json")
    num = n.rsplit("_", 1)[-1]
    tema = cl["tema"].format(num=num, tema=cortes[n]["tema"])
    subprocess.run([sys.executable, str(ROOT / "scripts/plantilla.py"), "nueva", nombre_receta, n, "--tema", tema], check=True)
    plantilla = next((p for p in (ROOT / "subtitulos/recetas/plantillas").glob("*.json")
                      if json.loads(p.read_text()).get("_plantilla", {}).get("receta") == nombre_receta), None)
    if plantilla is None:
        raise SystemExit(f"No hay plantilla «{nombre_receta}»")
    f = ROOT / "proyectos" / n / "recetas" / plantilla.name
    r = json.loads(f.read_text())
    # el gancho del short es la frase cortada del montaje: sin titular encima, y sin el zoom de golpe, que no va
    # por defecto
    quitadas = [k for k in ("gancho",) if k in r]
    for k in quitadas:
        r.pop(k)
    if "impactos" in r:
        r["impactos"] = []
    r.update(cl.get("receta", {}))
    r["marca"] = prog["id"]
    r["_episodio"] = ep
    f.write_text(json.dumps(r, ensure_ascii=False, indent=2) + "\n")
    print(f"{f.relative_to(ROOT)}: claves de «{prog['nombre']}» puestas ({', '.join(cl.get('receta', {}))})"
          + (f"; sin {', '.join(quitadas)} (el gancho es la frase cortada) y sin impactos" if quitadas else ""), flush=True)
    subprocess.run([sys.executable, str(ROOT / "scripts/plantilla.py"), "comprobar", str(f)])
    return f


def propuesta(ep):
    """Fase 2: clip ligero (16:9, 960×540) con el gancho de cada candidato tras un cartón numerado, y
    proyectos/<EP>/PROPUESTA_SHORTS.md con título, duración, gancho, tramos y por qué. El creador elige viendo."""
    import largo
    cortes, prog, cl, src, d = episodio(ep)
    out = ROOT / "out" / f"propuesta_{ep}"
    out.mkdir(parents=True, exist_ok=True)
    vf = "fps=25,scale=960:540,setsar=1,format=yuv420p"
    af = "aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo"
    entradas, cadenas, orden, n, filas = [], [], "", 0, []
    for k, nombre in enumerate(shorts_de(cortes)):
        s = cortes[nombre]
        g0, g1 = s["gancho"][0], s["gancho"][1]
        dur = g1 - g0 + sum(t[1] - t[0] for t in s["cuerpo"])
        png = out / f"carton_{k + 1:02d}.png"
        largo.carton(png, f"Short {k + 1}", f"{s['tema']} · {dur:.0f} s", prog)
        dg = g1 - g0
        entradas += ["-loop", "1", "-framerate", "25", "-t", "1.6", "-i", str(png),
                     "-f", "lavfi", "-t", "1.6", "-i", "anullsrc=r=48000:cl=stereo",
                     "-ss", f"{g0}", "-t", f"{dg:.3f}", "-i", str(src)]
        cadenas += [f"[{n}:v]{vf}[c{k}];[{n + 1}:a]{af}[ca{k}]",
                    f"[{n + 2}:v]{vf}[t{k}];[{n + 2}:a]{af},asetpts=N/SR/TB,afade=t=in:st=0:d=0.015,"
                    f"afade=t=out:st={dg - 0.015:.3f}:d=0.015[ta{k}]"]
        orden += f"[c{k}][ca{k}][t{k}][ta{k}]"
        n += 3
        tramos = " + ".join(f"{largo.minuto(t[0])}–{largo.minuto(t[1])}" for t in s["cuerpo"])
        filas.append(f"| {k + 1} | **{s['tema']}** (`{nombre}`) | {largo.minuto(g0)} | {tramos} | {dur:.0f} s | {s.get('por', '')} |")
    dest = out / "ganchos.mp4"
    largo.run(["ffmpeg", "-hide_banner", "-y", *entradas, "-filter_complex",
               ";".join(cadenas) + f";{orden}concat=n={2 * len(filas)}:v=1:a=1[v][a0];[a0]loudnorm=I=-16:TP=-1.5[a]",
               "-map", "[v]", "-map", "[a]", *kit.h264("1800k"), "-c:a", "aac", "-b:a", "128k",
               "-movflags", "+faststart", str(dest)])
    md = d / "PROPUESTA_SHORTS.md"
    md.write_text(f"# {ep}: shorts de «{prog['nombre']}»\n\n"
                  f"Candidatos de Claude. Cada uno: gancho de frase cortada + «impacto» + cuerpo, reencuadrado a 9:16, "
                  f"con el estilo y el cierre de {prog['nombre']}. Los cortes, en `cortes.json` (todos revisados palabra "
                  f"a palabra). El clip `out/propuesta_{ep}/ganchos.mp4` enseña el gancho de cada uno.\n\n"
                  "| # | Short | Gancho | Cuerpo | Dura | Por qué |\n|---|---|---|---|---|---|\n" + "\n".join(filas) + "\n")
    print(f"{dest.relative_to(ROOT)} · {largo.duracion(dest):.0f} s · {dest.stat().st_size / 1e6:.1f} MB")
    print(f"{md.relative_to(ROOT)}")
    return dest, md


def lista(ep):
    cortes, prog, cl, src, _ = episodio(ep)
    print(f"{ep} · {prog['nombre']} · original {src.name} · reencuadre {' '.join(cl.get('reencuadre', [])) or 'normal'}")
    for n in shorts_de(cortes):
        s = cortes[n]
        dur = s["gancho"][1] - s["gancho"][0] + sum(t[1] - t[0] for t in s["cuerpo"])
        print(f"  {n:<16} {dur:5.0f} s  {s['tema']}")


def probar(ep=None):
    """Los montajes que salen de clips.py (sin renderizar) son los que hay en git, en cada episodio con cortes.json
    (o solo en EPISODIO); y cada kit con bloque "clips" tiene prefijo, tema y un cierre que existe."""
    import contextlib
    import io
    fallos = []
    eps = [ep] if ep else sorted(f.parent.name for f in (ROOT / "proyectos").glob("*/cortes.json"))
    for e in eps:
        try:
            cortes, *_ = episodio(e)
        except SystemExit as ex:
            print(f"  – {e}: saltado ({str(ex).splitlines()[0]})")
            continue
        mont = {n: ROOT / "proyectos/_montajes" / f"{n}.json" for n in shorts_de(cortes)}
        antes = {}
        for n in mont:
            r = subprocess.run(["git", "show", f"HEAD:proyectos/_montajes/{n}.json"], cwd=ROOT, capture_output=True, text=True)
            antes[n] = None if r.returncode else r.stdout
        copia = {n: (f.read_text() if f.exists() else None) for n, f in mont.items()}  # se devuelve tal cual
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                montar(e, sin_render=True)
            for n, txt in antes.items():
                if txt is None:
                    print(f"  – {n}: no está en git, no hay con qué comparar")
                    continue
                # "carpeta" no cuenta: los montajes antiguos llevaban una ruta absoluta y ahora va "out"
                limpio = lambda t: {k: v for k, v in json.loads(t).items() if k != "carpeta"}
                ok = limpio(mont[n].read_text()) == limpio(txt)
                print(f"  {'✓' if ok else '✗'} {n} {'igual que en git' if ok else 'CAMBIA'}")
                if not ok:
                    fallos.append(n)
        finally:
            for n, txt in copia.items():
                if txt is None:
                    mont[n].unlink(missing_ok=True)
                else:
                    mont[n].write_text(txt)
    import pedido
    kits_clips = 0
    for k in pedido.kits().values():
        f = ROOT / "marca/kits" / f"{k['id']}.json"
        c = json.loads(f.read_text()).get("clips") if f.exists() else None
        if c is None:
            continue
        kits_clips += 1
        outro = (c.get("receta") or {}).get("outro")
        ok = (not outro or (ROOT / outro).exists()) and "{num}" in c.get("tema", "") and "{tema}" in c.get("tema", "")
        print(f"  {'✓' if ok else '✗'} kit {k['id']}: bloque clips con tema y cierre que existe")
        if not ok:
            fallos.append(k["id"])
    if not eps and not kits_clips:
        print("nada que probar: no hay episodios con cortes.json ni kits con bloque \"clips\"")
    print("todo en verde" if not fallos else f"{len(fallos)} fallo(s): {' '.join(fallos)}")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    try:   # ajustar los cortes necesita numpy, que solo está en el venv de vídeo: se relanza allí
        import numpy  # noqa: F401
    except ImportError:
        import os
        if VENV_PY.exists() and Path(sys.executable).resolve() != VENV_PY.resolve():
            os.execv(str(VENV_PY), [str(VENV_PY), __file__, *sys.argv[1:]])
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("montar"); s.add_argument("episodio"); s.add_argument("shorts", nargs="*")
    s.add_argument("--sin-render", action="store_true")
    s = sub.add_parser("preparar"); s.add_argument("episodio"); s.add_argument("shorts", nargs="*")
    s = sub.add_parser("receta"); s.add_argument("episodio"); s.add_argument("short"); s.add_argument("receta")
    s = sub.add_parser("lista"); s.add_argument("episodio")
    s = sub.add_parser("propuesta"); s.add_argument("episodio")
    s = sub.add_parser("probar"); s.add_argument("episodio", nargs="?")
    a = ap.parse_args()
    if a.cmd == "montar":
        montar(a.episodio, a.shorts, a.sin_render)
    elif a.cmd == "preparar":
        preparar(a.episodio, a.shorts)
    elif a.cmd == "receta":
        receta(a.episodio, a.short, a.receta)
    elif a.cmd == "lista":
        lista(a.episodio)
    elif a.cmd == "propuesta":
        propuesta(a.episodio)
    else:
        probar(a.episodio)
