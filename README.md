# Editor de vídeos cortos con Claude Code

Edita Reels, TikToks y Shorts hablando con Claude Code: tú grabas y dejas el vídeo en una carpeta. Claude:
- corta silencios y tomas repetidas;
- propone el gancho;
- elige una receta de edición;
- pone subtítulos, tarjetas para cada dato, efectos y sonidos;
- te enseña una muestra antes de entregarte la versión para publicar.

Todo corre en tu ordenador, sin suscripciones: FFmpeg, whisper.cpp y HyperFrames.

Es el método con el que edita sus vídeos [@hildemarosolis](https://www.instagram.com/hildemarosolis/), sin nada de su marca: tú pones la tuya.

## Empezar

1. Instala [Claude Code](https://claude.com/claude-code).
2. Clona este repo y abre Claude Code dentro de la carpeta.
3. Escríbele:

   > Lee INSTALAR.md y ayúdame a instalar el editor paso a paso.

Claude instala los programas, baja los modelos, crea tu carpeta de trabajo y te hace unas preguntas para configurar tu
marca: tu @, tu color, tu fuente, tus redes y tu voz. Después, para cada vídeo: `/editor`.

## Qué trae

- **Recetas con nombre** (`subtitulos/recetas/`), cada una con su plantilla:
  - Gancho titular, Golpe y cuentas, Ranking de pie, Top con sueldo, Sketch con IA;
  - Pizarra, Pizarra círculo, Pizarra viajera;
  - Titular detrás.
- **Una biblioteca de 65 efectos** con código fijo (`subtitulos/efectos/indice.json`).
- **Skills de Claude Code:**
  - `/editor`: el camino completo de cada vídeo;
  - `/carrusel`: carruseles animados de Instagram;
  - `/guion`: de un comentario de un seguidor a un guion con fuentes.
- **Reglas del método** en `CLAUDE.md`:
  - un dato dicho, una tarjeta;
  - gancho de frase cortada;
  - cierres que rotan;
  - movimiento de las piezas;
  - enseñar antes de entregar.

## Sistemas

| | Estado |
|---|---|
| Mac con chip Apple | Verificado |
| Linux | Pendiente de verificar (camino de software) |
| Windows | Con WSL2 (Ubuntu), pendiente de verificar |

Si lo pruebas fuera del Mac y algo falla, abre un issue con el comando y el error.

## Licencias de terceros

| Qué | Licencia |
|---|---|
| Fuentes Anton, Bebas Neue, Barlow Condensed y Oswald | SIL OFL 1.1 (`marca/fuentes/OFL-*.txt`) |
| Sonidos whoosh, pop, tic e impacto, hechos con [Earshot](https://github.com/Leonxlnx/earshot) | MIT (`marca/sfx/earshot/LICENSE-earshot.txt`) |
| Iconos de redes, de [Simple Icons](https://simpleicons.org) | CC0 1.0 |
| [GSAP](https://gsap.com) 3.15 (`subtitulos/assets/gsap.min.js`) | Licencia estándar gratuita de GSAP |
| HyperFrames, FFmpeg, whisper.cpp, OpenCV | Se instalan aparte, cada uno con la suya |
