#!/usr/bin/env python3
"""Montaje: une tramos de varios vídeos en uno solo, antes del flujo de siempre (preparar → receta → entregar).

  python3 scripts/montaje.py proyectos/_montajes/PROMO.json

El JSON lista los tramos en orden:
  {"carpeta": "<carpeta con los archivos>", "salida": "raw/PROMO.mp4",
   "tramos": [{"archivo": "a.MOV", "de": 0.0, "a": 2.1},
              {"archivo": "ia.mp4", "de": 0.0, "a": 4.2, "entrada": "glitch"},
              {"archivo": "ia2.mp4", "de": 0.6, "a": 5.4, "entrada": "glitch", "audio": "silencio",
               "capas": [{"sonido": "silbido", "en": 0.1},
                         {"archivo": "a.MOV", "de": 2.1, "a": 4.17, "en": 2.4}]}]}
- Todo sale a 1080×1920, 30 fps, SDR; los clips de IA (720p, 24 fps) se amplían.
- "entrada": "glitch" → 0,3 s de separación de color, ruido y destello, y sonido de glitch.
- "entrada": "impacto" → transición fuerte: el tramo anterior acaba con una subida de aire y este entra con
  destello blanco, golpe de zoom (1,35 → 1) y separación de color, con boom + glitch. Para cortar un gancho en seco.
- Cada tramo se iguala de volumen (los clips de IA vienen más bajos); el total lo deja a −14 LUFS preparar.py.
- "audio": "silencio" quita el audio propio del tramo; "capas" añade sonidos (scripts/sfx.py) o audio de otro archivo.
- "encima": {"centro_cara": [x, y], "segmentos": [{"archivo", "de", "a"}, …]} (opcional "corte_y" 1100, "cara_y" 1360)
  → vídeo de reacción: los segmentos (sin su audio) van seguidos en una franja abajo, desde corte_y, con la cara
  centrada en cara_y y una raya del color de tu marca encima, como la franja de la pizarra. Si se acaban antes que el tramo,
  se queda quieto el último fotograma. Arriba sigue el tramo (p. ej. el clip al que se reacciona).
- "difuminar": [[x0, y0, x1, y1], …] → desenfoca esas zonas del tramo (los subtítulos que ya trae un clip ajeno).
- Una capa de archivo admite "efecto": "terror" (voz más grave + eco, doblada con la original: grito espeluznante).
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import kit  # noqa: E402
import sfx  # noqa: E402

# grito espeluznante: la voz original + una copia una cuarta más grave con eco largo
TERROR = ("asplit=2[{p}a][{p}b];[{p}b]asetrate=48000*0.75,aresample=48000,atempo=1.3333,"
          "aecho=0.8:0.85:90|210|380:0.55|0.4|0.25,volume=1.4[{p}c];[{p}a][{p}c]amix=inputs=2:normalize=0")

GLITCH = ("rgbashift=rh=-28:bh=28:enable='lt(t,0.3)',noise=alls=80:allf=t:enable='lt(t,0.3)',"
          "eq=brightness=0.3:enable='lt(t,0.07)'")
IMPACTO = ("scale=w='trunc(1080*(1+0.35*pow(max(0,1-t/0.4),2))/2)*2':h='trunc(1920*(1+0.35*pow(max(0,1-t/0.4),2))/2)*2'"
           ":eval=frame:flags=bicubic,crop=1080:1920,"
           "rgbashift=rh=-36:bh=36:enable='lt(t,0.25)',eq=brightness=0.75:enable='lt(t,0.1)',"
           "eq=brightness=0.3:enable='between(t,0.1,0.18)'")


def main():
    cfg_path = Path(sys.argv[1])
    cfg = json.loads(cfg_path.read_text())
    from plantilla import comprobar
    comprobar(cfg | {"_ruta": str(cfg_path)})  # sin huecos de plantilla
    base = Path(cfg["carpeta"]).expanduser()
    sfx.make_sounds(ROOT / "marca/sfx")
    ins, graph, vl, al = [], [], [], []

    files = []

    def add_input(path):
        files.append(path)
        ins.extend(["-i", str(path)])
        return len(files) - 1

    for k, t in enumerate(cfg["tramos"]):
        dur = t["a"] - t["de"]
        i = add_input(base / t["archivo"])
        v = (f"[{i}:v]trim={t['de']:.3f}:{t['a']:.3f},setpts=PTS-STARTPTS,"
             f"scale=1080:1920:flags=lanczos,fps=30,setsar=1,format=yuv420p")
        if t.get("entrada") == "glitch":
            v += "," + GLITCH
        elif t.get("entrada") == "impacto":
            v += "," + IMPACTO
        for m, (x0, y0d, x1, y1d) in enumerate(t.get("difuminar", [])):
            # tapa una zona (p. ej. los subtítulos que ya trae un clip ajeno): desenfoque fuerte y oscurecido (banda)
            graph.append(v + f",split[d{k}m{m}a][d{k}m{m}b]")
            graph.append(f"[d{k}m{m}b]crop={x1 - x0}:{y1d - y0d}:{x0}:{y0d},boxblur=28:3,drawbox=x=0:y=0:w=iw:h=ih:color=black@0.55:t=fill[d{k}m{m}c]")
            graph.append(f"[d{k}m{m}a][d{k}m{m}c]overlay={x0}:{y0d}[d{k}m{m}]")
            v = f"[d{k}m{m}]null"
        enc = t.get("encima")
        if enc:  # reacción: otro vídeo (sin su audio) en una franja abajo, como la franja de la pizarra
            corte_y, cara_y = enc.get("corte_y", 1100), enc.get("cara_y", 1360)
            vy = cara_y - enc.get("centro_cara", [540, 620])[1]  # cuánto baja ese vídeo
            y0 = corte_y - vy
            if not (0 <= y0 and vy >= 0):
                raise SystemExit(f"encima: la cara no cabe en la franja (corte_y {corte_y}, vy {vy})")
            segs = []
            for m, s in enumerate(enc["segmentos"]):
                j = add_input(base / s["archivo"])
                graph.append(f"[{j}:v]trim={s['de']:.3f}:{s['a']:.3f},setpts=PTS-STARTPTS,"
                             f"scale=1080:1920:flags=lanczos,fps=30,setsar=1,format=yuv420p[e{k}s{m}]")
                segs.append(f"[e{k}s{m}]")
            alto = 1920 - corte_y
            graph.append(f"{''.join(segs)}concat=n={len(segs)}:v=1:a=0,tpad=stop_mode=clone:stop_duration={dur:.3f},"
                         f"trim=0:{dur:.3f},setpts=PTS-STARTPTS,crop=1080:{alto}:0:{y0}[e{k}]")
            graph.append(v + f"[v{k}c]")
            graph.append(f"[v{k}c][e{k}]overlay=0:{corte_y}:shortest=1,"
                         f"drawbox=x=0:y={corte_y - 4}:w=1080:h=8:color=0xFFC800:t=fill[v{k}]")
        else:
            graph.append(v + f"[v{k}]")
        if t.get("audio") == "silencio":
            graph.append(f"anullsrc=r=48000:cl=stereo,atrim=0:{dur:.3f}[a{k}base]")
        else:
            graph.append(f"[{i}:a]atrim={t['de']:.3f}:{t['a']:.3f},asetpts=PTS-STARTPTS,"
                         f"loudnorm=I=-16:TP=-2:LRA=11,aresample=48000,aformat=channel_layouts=stereo[a{k}base]")
        capas = list(t.get("capas", []))
        if t.get("entrada") == "glitch":
            capas.insert(0, {"sonido": "glitch", "en": 0.0})
        elif t.get("entrada") == "impacto":
            capas[:0] = [{"sonido": "boom", "en": 0.0}, {"sonido": "glitch", "en": 0.0}]
        siguiente = cfg["tramos"][k + 1] if k + 1 < len(cfg["tramos"]) else {}
        if siguiente.get("entrada") == "impacto":
            capas.append({"sonido": "subida", "en": max(0.0, dur - 0.6)})
        mix = [f"[a{k}base]"]
        for m, c in enumerate(capas):
            ms = int(c.get("en", 0) * 1000)
            if "sonido" in c:
                j = add_input(ROOT / "marca/sfx" / f"{c['sonido']}.wav")
                chain = f"[{j}:a]volume={sfx.SOUNDS[c['sonido']][2]}"
            else:
                j = add_input(base / c["archivo"])
                chain = (f"[{j}:a]atrim={c['de']:.3f}:{c['a']:.3f},asetpts=PTS-STARTPTS,aresample=48000,"
                         f"loudnorm=I=-16:TP=-2:LRA=11")
                if c.get("efecto") == "terror":
                    chain += "," + TERROR.format(p=f"t{k}_{m}")
            graph.append(f"{chain},aresample=48000,aformat=channel_layouts=stereo,adelay={ms}|{ms}[a{k}c{m}]")
            mix.append(f"[a{k}c{m}]")
        if len(mix) > 1:
            graph.append(f"{''.join(mix)}amix=inputs={len(mix)}:normalize=0:duration=first,"
                         f"alimiter=limit={sfx.LIMIT}:level=0[a{k}]")
        else:
            graph.append(f"[a{k}base]anull[a{k}]")
        vl.append(f"[v{k}][a{k}]")
    graph.append(f"{''.join(vl)}concat=n={len(vl)}:v=1:a=1[v][a]")
    out = ROOT / cfg["salida"]
    out.parent.mkdir(exist_ok=True)
    # un solo punto de color: la raya 0xFFC800 pasa al acento de tu marca (igual si es el mismo)
    r = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *ins, "-filter_complex", kit.pinta(";".join(graph)),
                        "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "16", "-preset", "slow",
                        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
                        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out)],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stderr[-2000:])
    d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(out)],
                             capture_output=True, text=True).stdout)
    print(f"montaje: {len(cfg['tramos'])} tramos → {out} ({d:.1f} s)")


if __name__ == "__main__":
    main()
