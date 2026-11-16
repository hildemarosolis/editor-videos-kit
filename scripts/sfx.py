"""Efectos de sonido sintetizados con FFmpeg (sin derechos de terceros) y mezcla
en una sola pista maestra a -14 LUFS.

  whoosh -> entrada de tarjeta (pico justo en el corte)
  pop    -> aparece un logo
  tic    -> se marca una línea de lista
  subida + boom -> transición al outro
  error  -> golpe «alarma» (cifra o idea que no es lo que parece)
  magia  -> golpe «magia» (arpegio de campanitas que sube)
  caja   -> caja registradora (dinero, inversión): golpe del cajón y campanilla

Banco «mezcla»: whoosh, pop, tic e impacto
salen de Earshot (marca/sfx/earshot/, MIT) y el resto, de FFmpeg. Cada carpeta de sonidos
guarda su banco en BANCO; una carpeta que ya tenía sonidos sin BANCO sigue con FFmpeg.

Banco «variado» (el de los proyectos nuevos): los mismos
sonidos que «mezcla», pero sin ametralladora. El mismo sonido no se repite a menos de 0,2 s; cada aparición
cambia un poco de tono (±3 %) y de volumen (hasta −2 dB), y baja 1,5 dB más si va pegada (< 0,7 s) a otra
igual. Los proyectos que ya tenían «mezcla» o «ffmpeg» suenan como siempre.
"""
import re
import shutil
import subprocess
from pathlib import Path

SR = 48000
SOUNDS = {
    # (fuente lavfi, adelanto en s para que el pico caiga en el evento, ganancia en la mezcla)
    "whoosh": ("anoisesrc=d=0.5:c=pink:r=48000:a=0.6:seed=7,highpass=f=300,lowpass=f=6000,"
               "afade=t=in:st=0:d=0.32:curve=qsin,afade=t=out:st=0.32:d=0.18:curve=qsin", 0.30, 1.6),
    "pop": ("aevalsrc='0.7*sin(2*PI*(250*t+1100*(1-exp(-30*t))/30))*(1-exp(-400*t))*exp(-18*t)'"
            ":s=48000:d=0.2", 0.0, 0.6),
    "impacto": ("aevalsrc='0.9*sin(2*PI*(55*t+60*(1-exp(-20*t))/20))*exp(-7*t)+0.3*(random(0)*2-1)*exp(-35*t)'"
                ":s=48000:d=0.5", 0.0, 0.8),
    # transición al outro: subida de aire que desemboca en un golpe grave
    "subida": ("anoisesrc=d=0.6:c=pink:r=48000:a=0.7:seed=11,highpass=f=500,lowpass=f=9000,"
               "afade=t=in:st=0:d=0.58:curve=exp,afade=t=out:st=0.58:d=0.02", 0.60, 0.9),
    "boom": ("aevalsrc='0.95*sin(2*PI*(38*t+55*(1-exp(-9*t))/9))*exp(-3.2*t)"
             "+0.45*(random(0)*2-1)*exp(-28*t)':s=48000:d=1.6,lowpass=f=2400", 0.0, 0.7),
    # montajes: glitch digital al cambiar a un plano de IA; silbido del Silbón (do-re-mi… que sube)
    "glitch": ("anoisesrc=d=0.32:c=white:r=48000:a=0.8:seed=5,tremolo=f=38:d=1,highpass=f=700,"
               "afade=t=out:st=0.2:d=0.12", 0.0, 0.8),
    "silbido": ("aevalsrc='0.35*sin(2*PI*(700+500*floor(t*3.2)/7+12*sin(2*PI*6*t))*t)"
                "*min(1,t*8)*(1-0.15*sin(2*PI*3.2*t))':s=48000:d=2.3,aecho=0.8:0.7:120|260:0.4|0.25,"
                "afade=t=out:st=1.9:d=0.4", 0.0, 0.9),
    # golpe «alarma»: zumbido de error, dos pitidos graves y ásperos
    "error": ("aevalsrc='0.55*(2*gt(sin(2*PI*150*t),0)-1)*lt(mod(t,0.19),0.14)*exp(-1.2*t)'"
              ":s=48000:d=0.42,lowpass=f=2600", 0.0, 0.55),
    "magia": ("aevalsrc='0.5*sin(2*PI*1047*(t-0.00))*gte(t,0.00)*exp(-8*(t-0.00))+0.5*sin(2*PI*1319*(t-0.06))*gte(t,0.06)*exp(-8*(t-0.06))+0.5*sin(2*PI*1568*(t-0.12))*gte(t,0.12)*exp(-8*(t-0.12))+0.5*sin(2*PI*2093*(t-0.18))*gte(t,0.18)*exp(-8*(t-0.18))+0.5*sin(2*PI*2637*(t-0.24))*gte(t,0.24)*exp(-8*(t-0.24))':s=48000:d=1.1,aecho=0.8:0.6:90|180:0.35|0.2,afade=t=out:st=0.8:d=0.3", 0.0, 0.7),
    "caja": ("aevalsrc='0.6*(random(0)*2-1)*exp(-70*t)+0.5*sin(2*PI*90*t)*exp(-40*t)"
             "+gte(t,0.09)*(0.4*sin(2*PI*2400*(t-0.09))+0.28*sin(2*PI*3610*(t-0.09))+0.14*sin(2*PI*5230*(t-0.09)))"
             "*exp(-4.5*(t-0.09))':s=48000:d=1.1,afade=t=out:st=0.85:d=0.25", 0.0, 0.75),
    "tic": ("aevalsrc='0.5*sin(2*PI*1900*t)*exp(-70*t)+0.25*sin(2*PI*3800*t)*exp(-110*t)'"
            ":s=48000:d=0.09", 0.0, 0.5),
    # pegatina congelada: obturador de cámara (dos chasquidos y el golpe del espejo)
    "obturador": ("aevalsrc='0.8*(random(0)*2-1)*exp(-130*t)+0.7*gte(t,0.075)*(random(0)*2-1)*exp(-110*(t-0.075))"
                  "+0.45*sin(2*PI*170*t)*exp(-55*t)':s=48000:d=0.3,highpass=f=700,lowpass=f=9000", 0.0, 0.6),
}
TARGET_I, LIMIT = -14.0, 0.79  # 0.79 ≈ -2 dBFS: deja margen al pico que añade el AAC
EARSHOT_DIR = Path(__file__).resolve().parent.parent / "marca/sfx/earshot"
# (id de Earshot, adelanto en s, ganancia igualada a la de FFmpeg); ver marca/sfx/earshot/LEEME.md
EARSHOT = {
    "whoosh": ("swish/soft", 0.30, 0.36),
    "pop": ("pro_pop_in/round", 0.019, 0.52),
    "tic": ("pro_click/tink", 0.004, 0.30),
    "impacto": ("pro_impact/short", 0.181, 1.57),
}


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(r.stderr[-1500:])
    return r.stderr


def banco(folder):
    f = folder / "BANCO"
    return f.read_text().strip() if f.exists() else "ffmpeg"


EARSHOT_BANCOS = ("mezcla", "variado")   # bancos que usan los WAV de Earshot
TONO = [1.0, 0.97, 1.03, 0.985, 1.015]   # «variado»: tono de cada aparición, en ciclo
GANA = [0.0, -1.5, -0.7, -2.0, -1.0]     # «variado»: dB de cada aparición, en ciclo
SEPARACION, PEGADO, PEGADO_DB = 0.2, 0.7, -1.5


def variar(events):
    """Banco «variado»: quita repeticiones a menos de SEPARACION s y da a cada aparición su filtro
    (tono y volumen). Devuelve [(t, nombre, filtro)] y cuántos sonidos quitó."""
    quedan, prev = [], {}
    for t, name in sorted(events):
        if t - prev.get(name, -9) >= SEPARACION:
            quedan.append((t, name))
            prev[name] = t
    out, n, ultimo = [], {}, {}
    for t, name in quedan:
        i = n.get(name, 0)
        n[name] = i + 1
        g = GANA[i % 5] + (PEGADO_DB if t - ultimo.get(name, -9) < PEGADO else 0)
        ultimo[name] = t
        out.append((t, name, f"asetrate={int(SR * TONO[i % 5])},aresample={SR},volume={g}dB,"))
    return out, len(events) - len(quedan)


def params(name, folder):
    """(adelanto, ganancia) del sonido según el banco de la carpeta."""
    if banco(folder) in EARSHOT_BANCOS and name in EARSHOT:
        return EARSHOT[name][1:]
    return SOUNDS[name][1:]


def make_sounds(folder, nuevo=None):
    """nuevo: banco para una carpeta sin sonidos todavía (None = FFmpeg, sin escribir BANCO)."""
    folder.mkdir(parents=True, exist_ok=True)
    if nuevo and not (folder / "BANCO").exists():
        (folder / "BANCO").write_text(("ffmpeg" if any(folder.glob("*.wav")) else nuevo) + "\n")
    mezcla = banco(folder) in EARSHOT_BANCOS
    for name, (src, _, _) in SOUNDS.items():
        out = folder / f"{name}.wav"
        if out.exists():
            continue
        if mezcla and name in EARSHOT:
            shutil.copy(EARSHOT_DIR / f"{name}.wav", out)
        else:
            run(["ffmpeg", "-hide_banner", "-y", "-f", "lavfi", "-i", src, "-ac", "2", "-ar", str(SR), str(out)])


def loudness(path):
    err = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128=peak=true",
               "-f", "null", "-"])
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", err)[-1]), float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", err)[-1])


def mix(voice, events, folder, dest):
    make_sounds(folder, nuevo="variado")
    quitados = 0
    if banco(folder) == "variado":
        lista, quitados = variar(events)
    else:
        lista = [(t, name, "") for t, name in events]
    cmd = ["ffmpeg", "-hide_banner", "-y", "-i", str(voice)]
    chains, labels = [], ["[0:a]"]
    for k, (t, name, filtro) in enumerate(lista, start=1):
        lead, gain = params(name, folder)
        cmd += ["-i", str(folder / f"{name}.wav")]
        ms = max(0, int(round((t - lead) * 1000)))
        chains.append(f"[{k}:a]{filtro}adelay={ms}|{ms},volume={gain}[s{k}]")
        labels.append(f"[s{k}]")
    tmp = dest.with_suffix(".tmp.wav")
    graph = ";".join(chains + ["".join(labels) + f"amix=inputs={len(labels)}:normalize=0:duration=first[m]"])
    run(cmd + ["-filter_complex", graph, "-map", "[m]", "-ar", str(SR), str(tmp)])
    i, _ = loudness(tmp)
    gain_db = TARGET_I - i
    # el limitador va sobremuestreado x4 (pico real, no de muestra). Si el AAC aún deja un pico por
    # encima de -1 dBFS, se repite con el techo 1 dB más bajo; si el limitador baja el volumen, se
    # compensa hasta -14 ±0,2.
    # En cada pasada se corrigen las dos cosas a la vez: si solo se bajara el techo cuando el pico se pasa,
    # se gastarían los intentos sin compensar el volumen (salía a −14,7).
    # 16 pasadas: con el techo bajado varias veces el volumen sube despacio y con 8 se quedaba en −14,4.
    limit = LIMIT
    for _ in range(16):
        run(["ffmpeg", "-hide_banner", "-y", "-i", str(tmp), "-af",
             f"volume={gain_db:.2f}dB,aresample={SR * 4},"
             f"alimiter=limit={limit:.3f}:attack=2:release=60:level=disabled,aresample={SR}",
             "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), str(dest)])
        i2, tp = loudness(dest)
        pico_ok, nivel_ok = tp <= -1.0, abs(i2 - TARGET_I) <= 0.2
        if pico_ok and nivel_ok:
            break
        if not pico_ok:
            limit *= 0.891
        if not nivel_ok:
            gain_db += TARGET_I - i2
    tmp.unlink()
    print(f"mezcla: {len(lista)} efectos{f' ({quitados} repetidos quitados)' if quitados else ''} · {i2} LUFS · pico {tp} dBFS → {dest.name}")
