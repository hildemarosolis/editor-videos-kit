---
name: guion
description: Convierte un comentario o mensaje de un seguidor del creador (captura de Instagram, TikTok o YouTube) en un guion listo para grabar, en su voz (marca/voz.md), con 3 ganchos de arranque y cada dato respaldado por una fuente primaria u oficial de su tema. Agrupa comentarios que preguntan lo mismo, investiga solo en fuentes fiables, elige la receta del catálogo y el cierre que toca, y deja guion.md + fuentes.md en guiones/<fecha>-<tema>/. Úsala cuando el creador pegue capturas de comentarios, diga «/guion», «hazme un guion de esto», «me preguntaron esto», «saca un vídeo de este comentario» o deje capturas en «0 Comentarios». No la uses para editar un vídeo ya grabado (eso es /editor) ni para analizar reels de otros.
---

# guion

Del comentario de un seguidor a un guion que el creador graba tal cual.

## El circuito completo
1. El creador hace capturas de comentarios y las suelta en **«0 Comentarios»** de su carpeta de trabajo (`python3 scripts/kit.py` dice dónde está), o las pega en el chat. Al abrir sesión, mira `python3 scripts/guiones.py pendientes`.
2. Escribe **«/guion»** y tú haces esta skill: agrupar, investigar, escribir.
3. `python3 scripts/guiones.py publicar <carpeta>` → **«0 Guiones/<fecha> <tema>/»**: `Guion.pdf`, `Fuentes.pdf`, `Comentario N.jpg` y `.guion`. Es lo que lee en el móvil (si la carpeta de trabajo está sincronizada en la nube, le llega solo).
4. Graba, guarda el vídeo **dentro de esa carpeta** y la arrastra a «1 Para editar».
5. `/editor <VIDEO>`: `preparar.py` encuentra el vídeo dentro de la carpeta, y la receta se monta con el guion (tabla «En pantalla», fuentes) y la tarjeta de comentarios públicos. Al entregar, la carpeta entera pasa a «3 Originales usados».

## Antes de nada
- **Lee `marca/voz.md` (obligatorio, siempre).** Es su voz y su forma de pensar: tono, frases que repite, a quién le habla, cómo desmonta creencias y dónde va el sarcasmo (si lo usa: contra mitos, gurús y atajos; **nunca contra quien comenta**, ni con un DM, ni con alguien con miedo o en una situación difícil). Un guion correcto que no suena a él no vale.
  - Si `marca/voz.md` no existe, créalo antes con él (`INSTALAR.md`, apartado «Su marca»; plantilla en `marca/voz.ejemplo.md`): pídele 2-3 transcripciones de vídeos suyos que funcionaron y sácalo de ahí.
  - Si te cuenta algo nuevo de cómo piensa o habla, propón añadirlo a `marca/voz.md`.
- Si tiene notas propias sobre el tema (un cuaderno, un vault, documentos), pregúntale si quiere que las leas. Si encuentras una opinión suya, úsala con sus palabras y cítala en `fuentes.md` como «Notas: <nota>». **Solo lectura:** nunca escribas en ellas.
- Lee `CLAUDE.md`: regla de datos (cada cifra dicha lleva tarjeta), cierres que rotan y gancho de frase cortada.
- Mira el catálogo de recetas: `subtitulos/recetas/README.md` («Cómo elegir»).
- Si ya hay guiones en `guiones/`, copia la forma del último que grabó.

## El camino

### 1. Leer y agrupar
- De cada captura saca: red, qué pregunta o afirma, con qué palabras exactas, en qué tono (duda, queja, mito). **Nunca copies el nombre ni el @ al guion**: es un tercero.
- Agrupa las que preguntan lo mismo: tres comentarios sobre un tema son un vídeo, no tres.
- Un mito («ya no se puede», «se paga de una vez») vale más que una duda: el vídeo lo desmiente.
- Carpeta por tema: `guiones/<AAAA-MM-DD>-<tema-corto>/` con las capturas como `captura-N.jpg` (están en `.gitignore`: llevan nombre y foto de terceros).
  - Desde «0 Comentarios»: `python3 scripts/guiones.py recoger <carpeta> <captura> …` (las copia en jpg y mueve el original a «Procesadas»).
  - Desde el chat: guarda cada imagen como `captura-N.jpg` en la carpeta.
- **`comentarios.json`** en la carpeta, una entrada por captura: `{"captura", "tipo": "publico"|"dm", "red", "avatar": [cx, cy, r], "recorte"?: [x0, y0, x1, y1], "tapar"?: [[x0, y0, x1, y1]]}`.
  - Un DM (burbuja de chat) es `"dm"` y nunca sale en tarjeta. Un comentario lleva «comentó», «Responder» o «hace N días».
  - La foto de perfil se busca sola: `<python con OpenCV> scripts/comentario.py <captura> <prueba.png>` (`python3 scripts/kit.py` dice cuál es ese python). **Mira el PNG**: la cara tiene que quedar difuminada. Si no, pon el `avatar` a mano.
  - Quita los botones de debajo («Me gusta / Responder / Ver respuesta»): con `recorte` si están por debajo de la foto, o con `tapar` (se rellenan con el color de fondo) si están a su lado.

### 2. Investigar solo en fuentes primarias u oficiales de su tema
- Válidas: las fuentes primarias de su tema. En temas legales, la norma publicada y los organismos oficiales (si es España: BOE, EUR-Lex, ministerios, sedes electrónicas, consulados, INE). En salud, organismos sanitarios y estudios publicados. En finanzas, el regulador y los documentos oficiales del producto. En lo demás, la fuente original del dato (el estudio, la estadística, la web del organismo).
- **No valen** blogs, foros, despachos que venden el servicio ni medios: si un medio cita algo, ve a la fuente original.
- Algunas webs oficiales dan 403 a WebFetch: bájalas con `curl -sL -A "Mozilla/5.0"` y extrae el texto. Las que cargan con JavaScript, con un navegador.
- Cada dato: lenguaje llano · cifra exacta · norma y artículo (o documento y página) · URL · «consultado AAAA-MM-DD». Cita corta y literal si el matiz importa.
- Lo que no esté en fuente fiable o dependa del caso va a **Dudas**, no al guion. Si una cifra depende de la práctica de cada oficina o del caso, se le pregunta al creador: si es profesional del tema, su experiencia cuenta como fuente cuando él la confirma, y se anota así.
- Con varios temas a la vez, investiga uno tú y lanza el resto en subagentes en paralelo con este mismo formato de `fuentes.md`; revisa lo que traigan antes de usarlo.

### 3. Elegir receta y cierre
- Receta del catálogo según el contenido (datos que cuentan → «Golpe y cuentas»; pasos o requisitos → «Pizarra» o «Pizarra círculo»; varias opciones ordenadas → «Ranking de pie» o «Top con sueldo»; sin cara y es un recorrido → «Ruta en un mapa»). Dilo en el guion con una línea de por qué.
- Cierre: `python3 scripts/cierre.py sugerir` dice cuál toca (nunca el mismo dos seguidos; como mucho 2 de embudo cada 7).
  - **Sin palabra** (`conversacion` o `info`): una pregunta concreta al final + «te leo en los comentarios» (con info, además «y si quieres información, dímelo ahí y te escribo»).
  - **Con palabra:** solo una de `marca/marca.json` (las que tiene montadas en su herramienta de mensajes automáticos, p. ej. ManyChat), la que encaje con el tema (cada palabra lleva sus `temas` en `marca.json`). Siempre en MAYÚSCULAS y con «y revisa tus mensajes». Ninguna otra.
  - `python3 scripts/cierre.py guia` da la frase exacta de cada cierre.

### 4. Escribir `guion.md`
Forma fija:
1. **Cabecera:** título del vídeo, de qué comentario(s) sale (sin nombres), receta y cierre.
2. **3 ganchos para elegir** (0-5 s), distintos entre sí: uno que lee el comentario en voz alta («Me escribieron: …»), uno que desmiente o da la respuesta en seco, uno con la cifra o la consecuencia. Marca cuál recomiendas y la **frase candidata a gancho de frase cortada** (la más fuerte del cuerpo, para el montaje).
3. **Cómo se graba:** un móvil, plano, una toma, repetir la frase entera si se equivoca; cómo decir las cifras para que salgan las tarjetas (en palabras, como se dicen).
4. **Texto** por bloques cortos, **en su voz (`marca/voz.md`)**: arranque sin «hola», la creencia nombrada como la dice la gente, el corte («No es así»), su reencuadre («no se trata de X, se trata de Y»), el dato, una tríada si cabe, una o dos de sus muletillas, **un toque de sarcasmo contra el mito** (si el tema y su voz lo permiten) y la condición o acción final. 45-75 s en total. Las cifras escritas como se dicen y en **negrita**.
5. **En pantalla:** tabla momento → tarjeta/golpe → texto → fuente (alimenta la receta en `/editor`).
6. **Cierre:** la frase exacta del cierre que toca (de `cierre.py guia`).
7. **Antes de grabar:** dudas que el creador tiene que confirmar (de `fuentes.md`).

### 5. Escribir `fuentes.md`
`# Fuentes — <tema>` · `## Respuesta corta` · `## Datos` · `## Dudas o matices` · `## Errores comunes que el vídeo puede desmentir`.

### 6. Publicar y enseñar
- `python3 scripts/guiones.py publicar <carpeta>` (o `--todos`): PDF a «0 Guiones». Rehazlo cada vez que cambie el guion.
- Resume en el chat: temas agrupados, el gancho recomendado y las dudas.
- Cuando lo grabe, el vídeo entra por `/editor` como siempre; al rellenar la receta, usa la tabla «En pantalla» y las fuentes de `fuentes.md` (cada tarjeta lleva su `fuente`).

## Reglas que no se saltan
- Siempre en su voz (`marca/voz.md`). El tono nunca cambia un dato: positivo no es prometer.
- Ninguna cifra sin fuente fiable con fecha. Sin promesas («seguro que te lo aprueban»).
- Ningún nombre ni foto de quien comentó en el guion ni en git (las capturas y `proyectos/*/assets/comentarios/` están en `.gitignore`).
- **En el vídeo** (pieza `"comentarios"` de `efectos.py`): un **comentario público** puede salir como tarjeta con la **captura real**, la **foto difuminada** y el **nombre visible**. Un **DM nunca**: se lee en voz alta sin nombre. En el guion, marca cada captura como «pública → tarjeta» o «DM → solo voz».
- Solo las palabras de `marca/marca.json`.
- Normas y datos que cambian: anota la fecha de consulta; si el guion se graba semanas después, revisa las cifras antes.
