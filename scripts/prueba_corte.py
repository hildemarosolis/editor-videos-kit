#!/usr/bin/env python3
"""Primera prueba: mide silencio, corta, normaliza a -14 LUFS y deja 9:16 en SDR.

Uso: python3 scripts/prueba_corte.py ENTRADA.MOV [--work DIR] [--out DIR]
Solo FFmpeg/ffprobe del sistema. Nada de red.

Pasos
  1. HDR HLG (iPhone) -> SDR BT.709 (en Mac, por el chip; en Windows y Linux, con zscale: kit.vf_a_sdr),
     aplicando la rotación del móvil. Intermedio de alta calidad en --work.
  2. silencedetect sobre el audio original -> lista de silencios (out/silencio.txt).
  3. Segmentos a conservar: cada pausa larga se deja en 2*KEEP, cabeza y cola recortadas.
  4. loudnorm en dos pasadas a -14 LUFS / -1.5 dBTP sobre el audio YA cortado.
  5. Un solo encode final (libx264 CRF 18 + AAC 192k).
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kit  # noqa: E402

NOISE_DB = -35      # umbral de silencio; estable entre -30 y -35 dB en esta toma
MIN_SIL = 0.35      # s: pausas más cortas que esto no se tocan
KEEP = 0.12         # s de aire que se deja a cada lado de una pausa cortada
TAIL_KEEP = 0.25    # s que se dejan al final tras la última palabra
FADE = 0.015        # s de fundido en cada unión de audio (evita clics)
FPS = 30
TARGET_I, TARGET_TP, TARGET_LRA = -14.0, -1.5, 11.0
AUDIO = "0:a:0"     # pista de audio del original; main() la cambia con pista_audio()


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def probe_duration(path):
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", str(path)])
    return float(r.stdout.strip())


def probe_video(src):
    """Transferencia de color, rotación y tamaño: decide si hace falta HDR→SDR y girar."""
    r = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
             "stream=width,height,color_transfer:stream_side_data=rotation", "-of", "json", str(src)])
    st = json.loads(r.stdout)["streams"][0]
    rot = next((int(sd["rotation"]) for sd in st.get("side_data_list", []) if "rotation" in sd), 0)
    return st.get("color_transfer", ""), rot, st["width"], st["height"]


def pista_audio(src):
    """Primera pista de audio que FFmpeg sabe leer. El iPhone graba a veces audio espacial
    (apple_apac) antes de la estéreo AAC, y este FFmpeg no trae decodificador para él."""
    r = run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
             "stream=codec_name", "-of", "csv=p=0", str(src)])
    codecs = r.stdout.split()
    return next((f"0:a:{i}" for i, c in enumerate(codecs) if "apac" not in c), "0:a:0")


def detect_silences(src, dur):
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(src), "-vn", "-map", AUDIO,
             "-af", f"silencedetect=n={NOISE_DB}dB:d={MIN_SIL}", "-f", "null", "-"])
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
    if len(ends) < len(starts):          # silencio abierto hasta el final
        ends.append(dur)
    sil = []
    for a, b in zip(starts, ends):
        if sil and a - sil[-1][1] < 0.02:  # une silencios pegados
            sil[-1] = (sil[-1][0], b)
        else:
            sil.append((a, b))
    return sil


def keep_segments(sil, dur, extra=()):
    cuts = list(extra)  # tramos a quitar a mano (tomas repetidas), en segundos del original
    for a, b in sil:
        if a <= 0.01:                                  # cabeza
            cuts.append((0.0, max(0.0, b - KEEP)))
        elif b >= dur - 0.05:                          # cola
            cuts.append((a + TAIL_KEEP, dur))
        elif b - a > 2 * KEEP + 0.02:                  # pausa intermedia
            cuts.append((a + KEEP, b - KEEP))
    cuts = sorted((a, b) for a, b in cuts if b - a > 0.02)
    merged = []
    for a, b in cuts:
        if merged and a <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(b, merged[-1][1]))
        else:
            merged.append((a, b))
    cuts = merged
    segs, pos = [], 0.0
    for a, b in cuts:
        if a - pos > 0.05:
            segs.append((pos, a))
        pos = b
    if dur - pos > 0.05:
        segs.append((pos, dur))
    fr = lambda x: round(x * FPS) / FPS          # alinea a fotograma: vídeo y audio miden lo mismo
    segs = [(fr(s), fr(e)) for s, e in segs]
    return [(s, e) for s, e in segs if e > s], cuts


def audio_graph(segs):
    parts, labels = [], []
    for i, (s, e) in enumerate(segs):
        d = e - s
        parts.append(f"[{AUDIO}]atrim=start={s:.3f}:end={e:.3f},asetpts=PTS-STARTPTS,"
                     f"afade=t=in:st=0:d={FADE},afade=t=out:st={max(0, d - FADE):.3f}:d={FADE}[a{i}]")
        labels.append(f"[a{i}]")
    parts.append("".join(labels) + f"concat=n={len(segs)}:v=0:a=1[acut]")
    return parts


def measure_loudnorm(src, segs):
    graph = ";".join(audio_graph(segs)) + \
        f";[acut]loudnorm=I={TARGET_I}:TP={TARGET_TP}:LRA={TARGET_LRA}:print_format=json[o]"
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(src), "-filter_complex", graph,
             "-map", "[o]", "-f", "null", "-"])
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.S)
    if not m:
        sys.exit("loudnorm no devolvió medidas:\n" + r.stderr[-1500:])
    return json.loads(m.group(0))


def final_encode(src_a, sdr, segs, meas, dest, target_i=TARGET_I):
    vparts, vl = [], []
    for i, (s, e) in enumerate(segs):
        vparts.append(f"[1:v:0]trim=start={s:.3f}:end={e:.3f},setpts=PTS-STARTPTS[v{i}]")
        vl.append(f"[v{i}]")
    vgraph = ";".join(vparts) + ";" + "".join(vl) + f"concat=n={len(segs)}:v=1:a=0,fps=30,scale=1080:1920:flags=lanczos[vout]"
    ln = (f"loudnorm=I={target_i}:TP={TARGET_TP}:LRA={TARGET_LRA}"
          f":measured_I={meas['input_i']}:measured_TP={meas['input_tp']}"
          f":measured_LRA={meas['input_lra']}:measured_thresh={meas['input_thresh']}"
          f":offset={meas['target_offset']}:linear=true:print_format=summary")
    graph = vgraph + ";" + ";".join(audio_graph(segs)) + f";[acut]{ln},aresample=48000[aout]"
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-y", "-i", str(src_a), "-i", str(sdr),
           "-filter_complex", graph, "-map", "[vout]", "-map", "[aout]",
           "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-color_primaries", "bt709", "-color_trc", "bt709",
           "-colorspace", "bt709", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
           "-movflags", "+faststart", str(dest)]
    r = run(cmd)
    if r.returncode:
        sys.exit("encode final falló:\n" + r.stderr[-2000:])
    return r.stderr


def verify(path):
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-vn",
             "-af", "ebur128=peak=true", "-f", "null", "-"])
    g = lambda k: re.findall(k, r.stderr)[-1]
    return {"I": float(g(r"I:\s+(-?[\d.]+) LUFS")), "LRA": float(g(r"LRA:\s+([\d.]+) LU")),
            "TP": float(g(r"Peak:\s+(-?[\d.]+) dBFS"))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("entrada")
    ap.add_argument("--work", default="/tmp/editor-work")
    ap.add_argument("--out", default="out")
    ap.add_argument("--quitar", action="append", default=[], help="tramo a quitar del original, p. ej. 79.68-83.42")
    ap.add_argument("--sin-silencios", action="store_true",
                    help="no recortar pausas (sketches y montajes: el silencio es parte del chiste)")
    a = ap.parse_args()
    src, work, out = Path(a.entrada), Path(a.work), Path(a.out)
    global AUDIO
    AUDIO = pista_audio(src)
    work.mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)

    dur = probe_duration(src)
    if dur > 300:  # 300 s como máximo (un ranking largo puede pasar de 180 s antes de quitar pausas)
        sys.exit(f"{dur:.0f}s: el corte admite 300 s como máximo")

    trc, rot, w, h = probe_video(src)
    if trc in ("arib-std-b67", "smpte2084") or rot:
        # iPhone: HEVC HLG grabado girado → SDR BT.709 vertical
        sdr = work / "sdr_916.mp4"
        ent, vf = kit.vf_a_sdr("clock")
        print(f"[1/5] HDR→SDR + rotación ({'chip del Mac' if ent else 'zscale'}) … {dur:.1f}s de origen")
        r = run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *ent, "-i", str(src), "-an",
                 "-vf", vf, *kit.h264("40M"), str(sdr)])
        if r.returncode:
            sys.exit(r.stderr[-1500:])
    elif w * 16 == h * 9:
        # ya vertical 9:16 y en SDR (recortes de un vídeo largo a 1080×1920; cámaras en vertical a 1728×3072):
        # se corta tal cual, sin girar ni convertir; el encode final lo deja en 1080×1920
        sdr = src
        print(f"[1/5] ya es {w}×{h} SDR (9:16): sin conversión … {dur:.1f}s de origen")
    else:
        sys.exit(f"{w}×{h} SDR sin rotación: no es vertical; pásalo antes a 9:16 con scripts/reencuadre.py")

    print("[2/5] midiendo silencio")
    sil = [] if a.sin_silencios else detect_silences(src, dur)
    extra = [tuple(float(x) for x in q.split("-")) for q in a.quitar]
    segs, cuts = keep_segments(sil, dur, extra)
    removed = sum(b - a for a, b in cuts)
    new_dur = sum(e - s for s, e in segs)
    lines = [f"origen: {dur:.2f}s · umbral {NOISE_DB} dB · pausa mínima {MIN_SIL}s · aire {KEEP}s",
             f"silencios detectados: {len(sil)} ({sum(b - a for a, b in sil):.2f}s)", ""]
    lines += [f"  silencio {a:7.2f} → {b:7.2f}  ({b - a:.2f}s)" for a, b in sil]
    lines += ["", f"cortado: {removed:.2f}s · resultado: {new_dur:.2f}s · segmentos: {len(segs)}", ""]
    lines += [f"  conservar {s:7.2f} → {e:7.2f}" for s, e in segs]
    (out / f"{src.stem}_silencio.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:2]), f"\n  cortado {removed:.2f}s → {new_dur:.2f}s en {len(segs)} segmentos")

    print("[3/5] midiendo loudness del audio cortado")
    meas = measure_loudnorm(src, segs)
    print(f"  antes: {meas['input_i']} LUFS · pico {meas['input_tp']} dBTP · LRA {meas['input_lra']}")

    dest = out / f"{src.stem}_corte_916.mp4"
    print("[4/5] encode final")
    log = final_encode(src, sdr, segs, meas, dest)
    v = verify(dest)
    if abs(v["I"] - TARGET_I) > 0.15:   # el modo dinámico de loudnorm suele quedarse corto: un reajuste
        adj = round(TARGET_I + (TARGET_I - v["I"]), 1)
        print(f"  salió {v['I']} LUFS; reajusto objetivo de pasada a {adj}")
        log = final_encode(src, sdr, segs, meas, dest, target_i=adj)
    (out / f"{src.stem}_loudnorm.log").write_text(log[-3000:])

    print("[5/5] verificando")
    v = verify(dest)
    print(f"  después: {v['I']} LUFS · pico {v['TP']} dBFS · LRA {v['LRA']}")
    print(f"  → {dest}  ({probe_duration(dest):.2f}s)")


if __name__ == "__main__":
    main()
