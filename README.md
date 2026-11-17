# Editor de vídeos cortos con Claude Code

Edita Reels, TikToks y Shorts hablando con Claude Code: tú grabas y dejas el vídeo en una carpeta. Claude:
- corta silencios y tomas repetidas;
- propone el gancho;
- elige una receta de edición;
- pone subtítulos, tarjetas para cada dato, efectos y sonidos;
- te enseña una muestra antes de entregarte la versión para publicar.

Todo corre en tu ordenador, sin suscripciones: FFmpeg, whisper.cpp y HyperFrames.

Es el método con el que edita sus vídeos [@hildemarosolis](https://www.instagram.com/hildemarosolis/), sin nada de su marca: tú pones la tuya.
No hace falta saber programar: Claude instala, pregunta y edita; tú decides.

## Cómo funciona

```
Grabas con el móvil → lo dejas en «1 Para editar» → /editor
   → Claude corta, transcribe y busca tomas repetidas
   → te propone el gancho y una receta (o eliges la tuya)
   → monta subtítulos, tarjetas, efectos y sonido con tu marca
   → te enseña una muestra → con tu sí, te deja la versión para publicar y su caption
```

¿Te gusta el estilo del vídeo de otra persona? Se saca su **receta** (qué pasa en cada momento) y se aplica a tu
vídeo, con tu marca.

## Empezar

1. Instala [Claude Code](https://claude.com/claude-code).
2. Clona este repo y abre Claude Code dentro de la carpeta:

   ```bash
   git clone https://github.com/hildemarosolis/editor-videos-kit.git && cd editor-videos-kit && claude
   ```
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
| Windows 11 | Verificado con WSL2 (Ubuntu) |
| Linux | Mismos pasos que en WSL; sin probar fuera de Windows |

Si lo pruebas fuera del Mac y algo falla, abre un issue con el comando y el error.

## Licencias

El código y las guías van con licencia [MIT](LICENSE): úsalo, cámbialo y compártelo, manteniendo el aviso de copyright.
Lo de terceros que viene dentro conserva su licencia:

| Qué | Licencia |
|---|---|
| Fuentes Anton, Bebas Neue, Barlow Condensed y Oswald | SIL OFL 1.1 (`marca/fuentes/OFL-*.txt`) |
| Sonidos whoosh, pop, tic e impacto, hechos con [Earshot](https://github.com/Leonxlnx/earshot) | MIT (`marca/sfx/earshot/LICENSE-earshot.txt`) |
| Iconos de redes, de [Simple Icons](https://simpleicons.org) | CC0 1.0 |
| [GSAP](https://gsap.com) 3.15 (`subtitulos/assets/gsap.min.js`) | [Licencia estándar gratuita de GSAP](https://gsap.com/standard-license) (Webflow): no quites su cabecera ni lo uses para hacer un editor visual de animaciones sin código |
| HyperFrames, FFmpeg, whisper.cpp, OpenCV | Se instalan aparte, cada uno con la suya |

## Créditos

Hecho por [Hildemaro Solís](https://www.instagram.com/hildemarosolis/) con Claude Code, sin saber programar.
Si te sirve, deja una ⭐ y sígueme en [@hildemarosolis](https://www.instagram.com/hildemarosolis/).
