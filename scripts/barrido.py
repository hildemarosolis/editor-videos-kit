"""Barrido de color (grade-wipe): una raya del color de acento cruza la pantalla y, a su paso, el vídeo
queda con color de cine (más contraste, tonos cálidos y viñeta). Se hace una vez, al principio, y se queda.

Receta:
  "barrido": {"frase": "Y te voy a decir", "dur": 1.1, "etiquetas": true,
              "antes": "ANTES", "despues": "DESPUÉS", "hasta_frase": "..." | "seg": 6.0}
- Sin `hasta_frase` ni `seg`, el color de cine se queda hasta el final.
- `etiquetas`: dos pastillas («ANTES» a la derecha y «DESPUÉS» a la izquierda) mientras cruza la raya.
- `intensidad` (1 por defecto; 0,6 más suave, 1,3 más fuerte).
- La copia con color es el mismo `assets/corte.mp4` con filtro, sincronizada como la silueta. Las pegatinas
  congeladas que vengan después se tiñen igual. La silueta de «detrás de ti» (`silueta.webm`) no: no se usa
  con un titular detrás después del barrido.
"""
import html

from efectos import _find, _norm


def filtro(k=1.0):
    return (f"contrast({1 + 0.16 * k:.3f}) saturate({1 + 0.2 * k:.3f}) sepia({0.17 * k:.3f}) "
            f"hue-rotate({-7 * k:.1f}deg) brightness({1 - 0.04 * k:.3f})")


CSS = """
      .bw-video {{ position: absolute; inset: 0; width: 1080px; height: 1920px; object-fit: cover; z-index: 1;
                   filter: {F}; clip-path: inset(0px 1080px 0px 0px); }}
      .bw-vin {{ position: absolute; inset: 0; width: 1080px; height: 1920px; z-index: 1; pointer-events: none;
                 background: radial-gradient(120% 75% at 50% 42%, rgba(0,0,0,0) 52%, rgba(10,6,0,{V:.2f}) 100%),
                             linear-gradient(rgba(0,40,50,{T:.2f}), rgba(0,0,0,0) 40%, rgba(0,0,0,0) 70%, rgba(0,40,50,{T:.2f}));
                 clip-path: inset(0px 1080px 0px 0px); }}
      .bw-lin {{ position: absolute; top: 0; left: -8px; width: 12px; height: 1920px; z-index: 9; opacity: 0;
                 background: var(--amarillo); box-shadow: 0 0 26px 8px rgba(255,200,0,.55); pointer-events: none; }}
      .bw-tag {{ position: absolute; top: 210px; z-index: 9; opacity: 0; font: 46px/1 "Anton", sans-serif;
                 letter-spacing: .08em; padding: 14px 24px 10px; border-radius: 10px; text-transform: uppercase; }}
      .bw-tag.a {{ right: 190px; background: #111; color: #fff; }}
      .bw-tag.d {{ left: 110px; background: var(--amarillo); color: #111; }}
"""


def build_barrido(cfg, words, total):
    b = cfg["barrido"]
    seq = [(_norm(w["raw"]), w["t0"], w["t1"]) for w in words]

    def at(frase, after=0.0):
        i = _find(seq, frase, after)
        if i is None:
            raise SystemExit(f"barrido: no encuentro la frase «{frase}» (después de {after:.1f}s)")
        return seq[i][1]

    t0 = max(0.0, at(b["frase"], b.get("despues_de", 0.0)) - b.get("antes_s", 0.05)) if b.get("frase") else b.get("t", 1.0)
    dw = b.get("dur", 1.1)
    fin = at(b["hasta_frase"], t0) if b.get("hasta_frase") else (t0 + b["seg"] if b.get("seg") else total)
    k = b.get("intensidad", 1.0)
    css = CSS.format(F=filtro(k), V=0.5 * k, T=0.10 * k)
    data = f'data-start="0" data-duration="{total:.3f}"'
    parts = [f'      <video id="bwv" class="clip bw-video" src="assets/corte.mp4" {data} data-track-index="50" '
             f'data-has-audio="false" muted playsinline></video>',
             f'      <div class="clip bw-vin" id="bwn" {data} data-track-index="51"></div>',
             f'      <div class="clip bw-lin" id="bw0" data-start="{t0:.3f}" data-duration="{dw + 0.2:.3f}" data-track-index="52"></div>']
    js = []
    if b.get("etiquetas", True):
        parts.append(f'      <div class="clip bw-tag a" id="bwa" data-start="{t0:.3f}" data-duration="{dw + 0.7:.3f}" '
                     f'data-track-index="53">{html.escape(b.get("antes", "ANTES"))}</div>')
        parts.append(f'      <div class="clip bw-tag d" id="bwd" data-start="{t0:.3f}" data-duration="{dw + 0.7:.3f}" '
                     f'data-track-index="54">{html.escape(b.get("despues", "DESPUÉS"))}</div>')
        js.append(f'tl.fromTo("#bwa",{{opacity:0,y:-30}},{{opacity:1,y:0,duration:0.25,ease:"back.out(2)"}},{t0:.3f});')
        js.append(f'tl.to("#bwa",{{opacity:0,x:60,duration:0.2}},{t0 + dw * 0.75:.3f});')
        js.append(f'tl.fromTo("#bwd",{{opacity:0,scale:0.4}},{{opacity:1,scale:1,duration:0.35,ease:"back.out(2.4)"}},'
                  f'{t0 + dw * 0.45:.3f});')
        js.append(f'tl.to("#bwd",{{opacity:0,duration:0.25}},{t0 + dw + 0.4:.3f});')
    cerrado, abierto = '"inset(0px 1080px 0px 0px)"', '"inset(0px 0px 0px 0px)"'
    for sel in ("#bwv", "#bwn"):
        js.append(f'gsap.set("{sel}",{{clipPath:{cerrado}}});tl.set("{sel}",{{clipPath:{cerrado}}},0);')
        js.append(f'tl.to("{sel}",{{clipPath:{abierto},duration:{dw:.3f},ease:"power2.inOut"}},{t0:.3f});')
    js.append(f'tl.fromTo("#bw0",{{opacity:1,x:0}},{{x:1096,duration:{dw:.3f},ease:"power2.inOut"}},{t0:.3f});')
    js.append(f'tl.to("#bw0",{{opacity:0,duration:0.15}},{t0 + dw:.3f});')
    if fin < total - 0.05:  # vuelve al color normal con un fundido
        js.append(f'tl.to(["#bwv","#bwn"],{{opacity:0,duration:0.4}},{fin - 0.4:.3f});')
    ev = [(t0, "subida"), (t0 + dw * 0.5, "whoosh")]
    cfg["_grade"] = (t0 + dw * 0.5, fin, filtro(k))  # las pegatinas congeladas de después se tiñen igual
    print(f"barrido: color de cine desde {t0:.2f}s ({dw:.1f}s de barrido) hasta {fin:.2f}s")
    return css, "\n".join(parts), js, ev, [(t0, t0 + dw + 0.7)]
