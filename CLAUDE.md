# Editor de vídeos cortos

Editor de vídeos cortos (Reels, TikTok, Shorts) que se maneja hablando con Claude Code. Claude decide los cortes,
el encuadre, los subtítulos y los efectos; los scripts de `scripts/` los ejecutan con FFmpeg, whisper.cpp y HyperFrames.

**Si es la primera vez:** sigue `INSTALAR.md` de principio a fin antes de editar nada.

## Quién es quién
- **Su marca:** `marca/marca.json` (usuario, nombre, color de acento, fuente, redes, palabras de «Comenta») y
  `marca/voz.md` (cómo habla). Todo lo lee `scripts/kit.py`: los scripts nunca llevan un @ ni un color escritos a fuego.
- **Su ordenador:** `editor.json` (no va a git): dónde está la carpeta de trabajo y el python con OpenCV.
- Comprobar todo: `python3 scripts/kit.py`.

## Cómo se edita: siempre con `/editor`
`.claude/skills/editor/SKILL.md` fija el camino. En resumen:
1. `python3 scripts/preparar.py <VIDEO> [--quitar a-b]`: de «1 Para editar» a `proyectos/<VIDEO>/`, sin silencios, a −14 LUFS y transcrito palabra a palabra.
2. Buscar tomas repetidas en el original y proponer los cortes en segundos.
3. Proponer el **gancho de frase cortada** y elegir una **receta con nombre** del catálogo (`subtitulos/recetas/README.md`):
   `python3 scripts/plantilla.py nueva "<receta>" <VIDEO> --tema "…"`. Rellenar los huecos anclando a **frases**, no a segundos.
4. Revisar con fotogramas (`hyperframes snapshot`).
5. `python3 scripts/entregar.py <VIDEO> --receta … --muestra`: muestra y copia ligera en `out/`.
6. Con su visto bueno, `--usar-muestra`: entrega exactamente esa muestra en «2 Terminados/<fecha tema>/» con su letra.

Otras skills: `/carrusel` (carruseles animados de Instagram) y `/guion` (de un comentario de un seguidor a un guion con fuentes).

## Reglas de edición (probadas en vídeos reales)
- **Cada dato dicho en voz alta lleva tarjeta**: número que sube hasta su valor justo cuando se dice, o lista que se marca
  línea a línea. Por eso cada cifra tiene que ser verdad: si no está verificada, se pregunta antes.
- **Gancho de frase cortada**: arrancar con la frase más fuerte del vídeo, cortada en seco, transición «impacto» y el
  vídeo desde el principio. Se propone en todos los vídeos nuevos.
- **Tarjeta «Sígueme»** con el usuario y los iconos de sus redes: al decir «sígueme» o, si no lo dice, en los últimos 3,5 s.
- **Cierres que rotan** (`scripts/cierre.py`): pregunta + «te leo en los comentarios», la variante «info», o
  «Comenta PALABRA y revisa tus mensajes» (solo con palabras montadas). Nunca el mismo dos vídeos seguidos y como mucho
  2 de embudo (con palabra) cada 7. `python3 scripts/cierre.py sugerir` dice cuál toca; `guia`, cómo decirlo al grabar.
- **Caption**: con cierre de palabra, la llamada va en la primera línea; sin palabra, el gancho en la primera línea y la pregunta al final.
- **Movimiento de las piezas** (para que no parezca un PowerPoint): entran con curva y rebote (`back.out`), nunca lineal;
  las listas entran escalonadas; con capas, cada una a su velocidad; una pantalla quieta lleva un micromovimiento.
- **Sonido en cada aparición**: whoosh al entrar una tarjeta, pop al salir un logo, tic por línea marcada; todo
  mezclado y devuelto a −14 LUFS (`scripts/sfx.py`).
- **Subtítulos**: fuente condensada gruesa en mayúsculas, blanco con contorno negro, palabra activa en el color de acento,
  dentro de la zona segura de Reels/TikTok (margen izquierdo 110 px, derecho 170 px, caja y=960–1220).
- **Variantes**: para probar, otra receta con el mismo `"tema"` (cae en la misma carpeta con la letra siguiente) y otro
  arranque, otra duración o encuadre; cambiar solo los rótulos no basta.

## Enseñar antes de terminar
- **Receta del catálogo:** una parada. Los cortes se proponen antes; luego se enseña la muestra completa.
- **Receta nueva o formato sin probar:** dos paradas. Primero el corte limpio, sin subtítulos; con su sí, la muestra completa.
- **Nada entra en «2 Terminados» sin su visto bueno.**

## Trampas
- **`HYPERFRAMES_SKIP_SKILLS=1` delante de TODO comando de HyperFrames** (`npx --yes hyperframes@0.8.78 …`). Sin eso
  copia 19 skills de terceros a la carpeta global de Claude.
- **`hyperframes snapshot` manda los fotogramas a Gemini** si existe `GEMINI_API_KEY`: añade siempre `--describe false`.
- **Whisper con contexto junta tomas casi iguales.** Para buscar repeticiones: `whisper-cli … -mc 0` (sin contexto) y la
  energía cada 100 ms: cada reintento deja una caída de volumen justo antes.
- **Whisper escribe mal los nombres propios.** Las correcciones fijas van en `FIXES` de `scripts/subtitulos.py`.
- **Vídeos del iPhone en HDR (HLG 10 bits):** `prueba_corte.py` los pasa a SDR BT.709. En Mac usa VideoToolbox; en
  Linux/WSL, zscale + tonemap (comprueba con `python3 scripts/kit.py` que este FFmpeg los trae).
- **Volumen:** −14 LUFS con `loudnorm` en dos pasadas, en modo dinámico.
- **Carpetas sincronizadas (iCloud, Drive):** un vídeo puede no estar descargado del todo; espera a que tenga su tamaño real.

## No
- Nada global sin preguntar (`~/.claude/settings.json`, skills globales, tareas programadas del sistema).
- Nada pesado ni de terceros en git: vídeos, audio, renders, modelos, capturas de comentarios con nombres y fotos.
- Palabras de «Comenta» que no estén montadas en su herramienta de mensajes.
- Inventar datos, cifras, cuentas o fuentes.
