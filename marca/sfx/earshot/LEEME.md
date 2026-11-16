# Sonidos de Earshot (banco «mezcla»)

Elegidos tras compararlos con los sintetizados con FFmpeg: whoosh, pop, tic e impacto salen de Earshot y el resto de FFmpeg.

Hechos en código por [Earshot](https://github.com/Leonxlnx/earshot) 0.4.0 (licencia MIT, Leon Lin), sin grabaciones de terceros. Se renderizaron con `earshot sfx render`, a 48 kHz y pico −1 dBFS:

| Nuestro nombre | Id de Earshot | Opciones | Semilla |
|---|---|---|---|
| whoosh | swish/soft | `--dur 0.6 --apex 0.30` | 1007119508 |
| pop | pro_pop_in/round | — | 276866903 (la suya) |
| tic | pro_click/tink | — | 1162705466 (la suya) |
| impacto | pro_impact/short | — | 0 (la suya) |

Adelanto y ganancia en la mezcla: `EARSHOT` en `scripts/sfx.py` (ganancias igualadas a los de FFmpeg por el RMS máximo en 50 ms).

Earshot NO está instalado en el proyecto: estos WAV bastan. Para rehacerlos, instálalo en un entorno aparte desde el repositorio original (`pip install --no-deps "git+https://github.com/Leonxlnx/earshot@v0.4.0"` + numpy, scipy, soundfile, soxr). Ojo: el paquete «earshot» de PyPI es otro programa.
