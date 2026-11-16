---
name: editor
description: Edita un vídeo corto del creador (su marca está en marca/marca.json) con una receta con nombre del catálogo (Gancho titular, Golpe y cuentas, Ranking de pie, Top con sueldo, Sketch con IA, Pizarra, Pizarra círculo, Pizarra viajera, Titular detrás; capa Episodio completo), de principio a fin y siempre por el mismo camino. Prepara el vídeo, busca tomas repetidas, propone el gancho de frase cortada, recomienda receta si no se dice, la rellena desde su plantilla, saca muestra, espera el visto bueno y entrega con tema y letra. Úsala cuando el creador diga «/editor», «edita <VIDEO>», «hay un vídeo nuevo», «móntalo con la pizarra viajera», «haz otra variante de X», «qué receta le va a este vídeo» o «busca las tomas repetidas». No la uses para carruseles (eso es /carrusel), guiones (eso es /guion) ni para construir efectos nuevos.
---

# editor

Monta un vídeo corto con una **receta con nombre** del catálogo `subtitulos/recetas/README.md`. El catálogo es la fuente única: fichas, cómo elegir, claves de cada pieza. Esta skill fija el **camino**. Lo que monta cada receta está en su ficha y en su plantilla (`subtitulos/recetas/plantillas/`).

Trabajas con un creador que no es técnico. Háblale claro y corto. Las decisiones de estilo son suyas; las técnicas, tuyas, y se las explicas en una frase si importan.

Uso: `/editor [receta] [VIDEO]`. Las dos cosas son opcionales: sin vídeo, mira «1 Para editar»; sin receta, la recomiendas.

## Antes de nada

- Lee `CLAUDE.md` (reglas de edición y trampas) y `marca/marca.json` (su @, su color de acento, su fuente, sus redes y sus palabras de «Comenta»).
- Lee `marca/voz.md`. Si no existe, se crea en la primera sesión (`INSTALAR.md`, apartado «Su marca»; plantilla en `marca/voz.ejemplo.md`).
- `python3 scripts/kit.py` dice dónde está su carpeta de trabajo, qué python tiene OpenCV y si a FFmpeg le falta algo.
- `HYPERFRAMES_SKIP_SKILLS=1 npx --yes hyperframes@0.8.78 …` en **todo** comando de HyperFrames que escribas a mano. Sin esa variable copia 19 skills de terceros a la carpeta global de Claude. Los scripts que renderizan (`entregar.py`, `carrusel.py`, `ruta.py`, `variantes.py`, `plantilla.py`) ya la ponen solos.
- Lista las recetas con `python3 scripts/plantilla.py lista`.

## El camino (siempre este orden)

### 0. El pedido: marca, molde y retoques (opcional)
Solo si el creador publica para **varias marcas** (kits en `marca/kits/`) **y** tiene publicada la página de la biblioteca de efectos (`python3 scripts/galeria.py pagina`, publicada como página privada con base de datos). Si no, sáltalo: el vídeo es de su marca personal (`marca/marca.json`) y en el paso 3 recomiendas tú.

Para qué sirve: el creador decide el estilo antes de que propongas. Cada marca tiene su kit (color de la palabra activa, logo, cierres que admite, efectos que no van con ella) para que los estilos no se mezclen.
1. **Pregunta para qué marca es.** `python3 scripts/pedido.py kits` las lista.
   - Una marca nueva, una colaboración puntual o una publicidad: `python3 scripts/pedido.py nueva-marca "Nombre" --tipo puntual` y pídele el logo (a `marca/logos/`) y su color. Queda registrada para la próxima.
2. **Abre su pedido** en la página de la biblioteca: `python3 scripts/pedido.py abrir "<nombre del vídeo>" --marca <id>` imprime el documento; guárdalo en la colección `pedidos` de la página con el `doc_id` que imprime. Dale el enlace: ahí elige el **molde** (una receta del catálogo, con su clip), los **retoques** (efectos sueltos; primero salen los ya usados con esa marca y no salen los que no van con ella) y escribe **lo que tiene en la cabeza**. Pulsa «Listo».
3. Mientras elige, haz los pasos 1 y 2 (preparar, tomas repetidas): no dependen del pedido.
4. Cuando diga «listo»: baja la colección `pedidos` a una carpeta del scratchpad y `python3 scripts/pedido.py leer <carpeta> --video "<nombre>"` (si la carpeta de `proyectos/` no se llama como el vídeo, mira `pedido.py leer -h`). Dice el molde con su plantilla, cada retoque con cómo se activa, su idea y qué cierres deja la rotación. Lo guarda en `proyectos/<VIDEO>/pedido.json`.
5. Si dice «sin pedido», «tú decides» o tiene prisa, sigue como siempre (el paso 3 recomienda).
- El pedido manda sobre tu recomendación: el molde que eligió es la receta. Si crees que otro le va mejor, díselo en una línea, pero no lo cambies sin su sí.
- Kit en `borrador` o `pendiente`: en la muestra dile qué estrena (el color, el logo) para que lo apruebe. Con su sí, `"estado": "aprobado"` en `marca/kits/<id>.json`.

### 1. Localizar y preparar
- **Vídeo nuevo:** mira «1 Para editar» en su carpeta de trabajo (`python3 scripts/kit.py` dice dónde está). Si la carpeta está sincronizada en la nube, comprueba que el vídeo ya se bajó del todo (que tenga su tamaño real) antes de procesarlo.
  ```bash
  python3 scripts/preparar.py <VIDEO>
  ```
  Lo deja en `proyectos/<VIDEO>/`: sin silencios, a −14 LUFS, en 9:16 SDR y transcrito palabra a palabra (`palabras.json`).
- **Una carpeta con `Guion.pdf` o `.guion`** (viene de «0 Guiones», ver `/guion`): es un vídeo grabado con guion. `preparar.py` encuentra el vídeo dentro de la carpeta. El archivo `.guion` dice qué carpeta de `guiones/` es: abre su `guion.md` y mira la receta, los ganchos, la tabla «En pantalla» (cada tarjeta con su `fuente` de `fuentes.md`) y las dudas que el creador confirmó. Comprueba qué gancho grabó.
- **Una carpeta sin guion** (varias tomas, dos móviles o planos de IA) es un montaje. Ve a la ficha de **Sketch con IA** y a `scripts/montaje.py`. Convención: dentro, `…_A` es la toma principal (con micrófono) y `…_B` la otra.

### 2. Tomas repetidas y cortes (no te lo saltes)
Whisper con contexto junta las tomas casi iguales. Hay que buscarlas en el **original**:
1. Transcribe sin contexto, palabra a palabra:
   ```bash
   whisper-cli -m models/ggml-large-v3-turbo-q5_0.bin -f <original a 16 kHz> -l es -mc 0 -ml 1 -sow -oj
   ```
   (Cambia `-l es` si el creador habla otro idioma.) Para un tramo dudoso, ventanas de 1,6 s.
2. Busca frases dichas dos veces, palabras sueltas repetidas («sociolaboral… laboral, si alguien…») y arranques de preparación («Voy. Dale.», saludos que no enganchan).
3. Confirma cada caso con la energía cada 100 ms: antes de cada reintento hay una caída de volumen.
4. Propón al creador los cortes en segundos del original. Con su sí:
   ```bash
   python3 scripts/preparar.py <VIDEO> --quitar a-b [--quitar c-d]
   ```
   `preparar.py` ya avisa de candidatas (`scripts/repeticiones.py`), pero no te fíes solo de eso.
5. Si whisper se inventa una palabra al principio del corte, comprueba transcribiendo desde un poco antes. Si no está en el audio, vacía ese segmento en `palabras.json`.
6. Lapsus que no se pueden cortar: avísalos, no los «arregles» en los subtítulos. Antes de llamarlo lapsus, escúchalo: a veces es una frase hecha suya mal transcrita (mira `marca/voz.md`).
7. Nombres propios mal escritos por whisper (su nombre, su marca): corrígelos en `FIXES` de `scripts/subtitulos.py` una vez, y ya salen bien siempre.
8. En grabaciones con cámara, ojo a la cuenta atrás («3, 2») bajita al principio: mídela y empieza donde arranca su voz.

### 3. Elegir receta
- **Con pedido, la receta es su molde** (paso 0). Sin pedido, si el creador no la dice, recomienda una con «Cómo elegir» del catálogo y explica por qué en dos líneas.
- **Gancho de frase cortada, en todos los vídeos nuevos** (el arranque que mejor funciona): nada más transcribir, propón la frase más impactante del vídeo (una cifra, una promesa falsa o una contradicción) y el segundo exacto donde se corta en seco, justo al acabar la idea.
  - Se monta con `montaje.py`: ese tramo, `"entrada": "impacto"` y el vídeo desde el principio (un JSON en `proyectos/_montajes/<NOMBRE>.json`; la forma está en la cabecera de `scripts/montaje.py`). Después, `python3 scripts/preparar.py <NOMBRE> --sin-silencios`.
  - Enseña ese corte limpio y espera su sí antes de seguir con la receta.
  - Si el vídeo no tiene una frase así, dilo y propón el arranque de siempre. Si los primeros 3 s son un saludo, empieza en la frase con más tensión.
  - No todos los vídeos la necesitan: si su pedido o su idea dicen otro arranque, manda lo suyo.
- Si es una **variante** de algo ya entregado (reel de prueba):
  - otra receta con el mismo `"tema"`, para que caiga en la misma carpeta con la letra siguiente;
  - otro arranque, otra duración y otro encuadre: cambiar solo los rótulos no basta.

### 3b. Efectos elegidos en la biblioteca (opcional)
Solo si tiene publicada la página de la biblioteca. Con pedido, sus retoques son lo primero (salen en `pedido.py leer`). Además, sin pedido abierto, el creador puede marcar en la página los efectos que quiere «en el próximo»:
1. Baja la colección `elegidos` de la página a una carpeta del scratchpad.
2. `python3 scripts/efectos_indice.py elegidos <carpeta> --video <VIDEO>` dice cómo se activa cada uno (su clave y un ejemplo), su nota y los apunta en `proyectos/<VIDEO>/elegidos.json`.
3. Propón dónde va cada uno en este vídeo (en qué frase) y mételo en la receta. Si uno no encaja con el vídeo, dilo y déjalo para otro: no lo fuerces.
4. Antes de la muestra, `… elegidos <carpeta> --video <VIDEO> --receta <receta>` marca cuáles lleva ya la receta y cuáles faltan.
Los ya usados (con `usado_en`) no salen: esperan a que los vuelva a pedir.
Sin página, el creador puede pedirlos por código («la E-14 en el golpe»): `python3 scripts/efectos_indice.py lista` los enseña.

### 4. Datos (regla de la casa)
- Cada número dicho lleva tarjeta, y por eso tiene que ser verdad.
- Si una cifra o un plazo legal no está verificado, pregunta antes («¿los 30 días están bien o lo busco en la fuente oficial?»). Si el creador lo confirma, no lo vuelvas a preguntar.
- Datos propios verificables (p. ej. su nota y número de opiniones en Google) también llevan tarjeta, con la fuente y la fecha de la captura anotadas en la receta.
- `subtitulos.py` avisa de los números dichos que no tienen tarjeta.

### 5. Rellenar la plantilla
```bash
python3 scripts/plantilla.py nueva "<receta>" <VIDEO> --tema "<Tema corto>" [--capa episodio-completo]
```
- **Qué hace:** crea `proyectos/<VIDEO>/recetas/<receta>.json`, calcula `centro_cara` con YuNet y lista los huecos `__ASÍ__`.
- **Cómo se rellena:** con lo que dice el vídeo, **anclado a frases** de la transcripción, nunca a segundos. La plantilla ya trae la forma y la ficha del catálogo dice qué lleva cada pieza. Cuando el creador ya tenga vídeos entregados con esa receta, copia la forma de la de su último vídeo aprobado.
- **«Titular detrás»** va en dos pasos: `nueva` crea primero el montaje con el arranque y te da los pasos siguientes.
- **Centro de la cara:** YuNet falla con perfiles y sombreros. Compruébalo con un recorte con rejilla de 3-4 fotogramas antes de fiarte (a veces se desvía 30 px o más).
- **Cierre:** antes de rellenarlo, `python3 scripts/cierre.py sugerir` (ver «Reglas que no se saltan»).
- **Comprobación:**
  ```bash
  python3 scripts/plantilla.py comprobar proyectos/<VIDEO>/recetas/<receta>.json
  ```
  Tiene que decir «sin huecos». `subtitulos.py`, `entregar.py` y `montaje.py` no montan una receta con huecos.
- **Con pedido** (paso 0), justo después de `nueva`:
  ```bash
  python3 scripts/pedido.py aplicar <VIDEO> --receta proyectos/<VIDEO>/recetas/<receta>.json
  ```
  Pone en la receta `"marca"` y las claves de su kit (el color de la palabra activa; en un programa con cuenta propia, sin «Comenta» ni «Sígueme» y con su cierre). Mete los retoques donde dice su nota o su idea y, antes de la muestra, `python3 scripts/pedido.py comprobar <VIDEO> --receta …`: tiene que decir «pedido cumplido» (molde, retoques, kit y un cierre que la marca admite). Si un retoque no encaja con el vídeo, díselo; no lo fuerces ni lo quites en silencio.

**Comentarios de seguidores** (si el vídeo sale de un guion con comentarios públicos): en la receta,
`"comentarios": [{"guion": "<carpeta>", "capturas": ["captura-1.jpg", …], "frase": "Me escribieron", "dur": 4.5}]`
(opcionales: `"y"` 230, `"ancho"` 940, `"alto_max"` 600, `"cada"` 0,45 s). Sale la captura real con la foto difuminada y el nombre visible; un DM se niega. Ficha en el catálogo.

### 6. Revisar con fotogramas (antes de renderizar)
```bash
python3 scripts/subtitulos.py --dir proyectos/<VIDEO> --receta proyectos/<VIDEO>/recetas/<receta>.json
cd proyectos/<VIDEO> && HYPERFRAMES_SKIP_SKILLS=1 npx --yes hyperframes@0.8.78 lint
HYPERFRAMES_SKIP_SKILLS=1 npx --yes hyperframes@0.8.78 snapshot --at <10-15 momentos> --no-end --describe false
```
Lint con 0 errores. Mira los fotogramas en una hoja y revisa:
- textos que no se salen ni se pisan;
- subtítulos en su sitio, en zona segura;
- la cara entera en el círculo o la franja;
- etiquetas de sección y logos sin chocar;
- tarjetas en el momento justo;
- piezas que entran con rebote y escalonadas, no todas a la vez (regla de movimiento del catálogo).

Corrige y vuelve a mirar hasta que esté limpio.

### 7. Muestra
```bash
python3 scripts/entregar.py <VIDEO> --receta proyectos/<VIDEO>/recetas/<receta>.json --muestra
```
- Saca `out/<VIDEO>_<receta>_muestra.mp4` a −14 LUFS (con el outro si lo lleva) y una copia ligera (540 px).
- **Caption y portada**, antes de enseñarla:
  ```bash
  python3 scripts/textos.py <VIDEO> --receta proyectos/<VIDEO>/recetas/<receta>.json --borrador
  ```
  Crea `proyectos/<VIDEO>/caption.md` desde `subtitulos/recetas/plantillas/caption.md` con lo fijo ya puesto: la línea de la llamada si el cierre lleva palabra, el cierre del episodio si hay outro y las reglas de la portada **9:16** (la tapa del reel). Rellena los huecos `__ASI__` con lo que dice el vídeo; las pistas que imprime dan el gancho, la descripción y cómo elegir el segundo de la captura (míralo en un fotograma de la muestra: caras de frente y sin tarjetas encima). Comprueba con `--comprobar` (huecos, primera línea, palabra montada, 9:16; avisa de cifras que no están en el vídeo).
  - **Con cierre de palabra:** la llamada es la **primera** línea del caption («Comenta PALABRA y revisa tus mensajes: …»): casi todos leen solo la primera línea.
  - **Sin palabra:** el gancho va en la primera línea y la pregunta al final, antes de los hashtags.
  - **Primer comentario** (`## Primer comentario`): lo publica el creador nada más subir el reel y lo fija. Su propia respuesta a la pregunta del vídeo (o un dato que no cupo); en un short de episodio, el título del episodio para buscarlo en YouTube. Acaba siempre con «Sígueme en @tucuenta para…» y el porqué (la @ se puede tocar; un enlace en un comentario, no). Misma palabra que el vídeo o ninguna.
- **Página de revisión** (opcional, la mejor forma de enseñarla):
  ```bash
  python3 scripts/revision.py <VIDEO> --receta proyectos/<VIDEO>/recetas/<receta>.json [--version v2]
  ```
  Saca `out/revision_<VIDEO>_<receta>/` (página, copia de vídeo < 14 MB y `piezas.json`). Cada pieza (segundo, lo que dice, qué se ve, fuente) lleva Aprobado / Cambios / Pendiente + comentario; las cifras dudosas salen en «Necesita». La primera pieza, **p00**, es el caption y la portada; sin `caption.md` listo la página no se hace (`--sin-caption` solo para vídeos antiguos). Si p00 vuelve con «Cambios», se corrige `caption.md`: no hace falta otra muestra.
  - Publícala con el Artifact tool: `file_path` = su `index.html`, `files` = `{"muestra.mp4": …}`, `capabilities` = `{"db": {}}`. La primera vez apunta la URL en `proyectos/<VIDEO>/revision.json`; las siguientes versiones se publican en la misma URL.
  - El creador la revisa en el móvil y escribe «revisada». Entonces lees con ArtifactData las colecciones `marcas` (documentos `<version>-pNN`: estado y comentario), `notas`, `envios` y `ajustes`, le devuelves el resumen y rehaces solo lo marcado como «Cambios» y lo que digan las notas.
- **Ajustes desde la página:** en cada pieza editable (golpes, zooms, pantallas partidas, tarjetas flotantes y datos) el creador cambia campos sin escribir. Se guardan en `ajustes` (documentos `<version>-pNN` con `{pieza, clip, cambios: {campo: valor}}`) y marcan la pieza como «Cambios». Al decir «revisada»:
  1. Baja con ArtifactData `list` (y `out_dir` en el scratchpad) las colecciones `ajustes`, `marcas`, `notas` y `envios`.
  2. `python3 scripts/ajustes.py cambiadas --base <out_dir> --version v1`: las piezas que se rehacen y, debajo, las notas por segundo. Una marcada «Cambios» sin ajuste, o una pieza con nota, es un comentario («dame otro diseño»): se hace a mano.
  3. `python3 scripts/ajustes.py aplicar <VIDEO> --receta <receta> --ajustes <out_dir>/ajustes/*.json` escribe los ajustes **solo en la receta** (`--simular` enseña los cambios sin escribir). Si avisa de una cifra nueva no escribe nada: pregunta al creador y repite con `--confirmar`.
  4. `entregar.py … --muestra`, luego `revision.py … --version v2 --cambiadas p02 …` y publícala en la misma URL.
  5. `python3 scripts/ajustes.py heredar --base <out_dir> --antes v1 --version v2 --piezas out/revision_<VIDEO>_<receta>/piezas.json` deja `heredar_v2.json`: pásalo a ArtifactData `batch` y las piezas ya aprobadas siguen aprobadas; solo lo rehecho queda pendiente.
- **Notas por segundo:** bajo el vídeo, «✎ Nota en este segundo» pausa, guarda el segundo exacto y el texto en la colección `notas` (documentos `<version>-<id>` con `{t, pieza, clip, titulo, texto}`) y lo marca en la barra. `pieza` es la que entró la última en ese segundo, o `null` si solo había subtítulos. Son lo que no tiene pieza: un ruido en el corte, un logo que tapa la cara, un corte brusco. En el resumen de «revisada» van con su segundo; una nota con pieza cuenta como «Cambios» de esa pieza (no se hereda como aprobada en la v2) y una sin pieza se arregla en el montaje o en la receta. Solo las notas: `python3 scripts/ajustes.py notas --base <out_dir> --version v1`.
  Campos ajustables: `python3 scripts/ajustes.py campos`. Las pruebas: `python3 scripts/ajustes.py probar`.
- **Sin página:** envíale la copia ligera (o la muestra) por donde pueda verla en el móvil y pídele los cambios en segundos.
- **No entregues nada sin su visto bueno.** Si pide cambios, vuelve al paso 5 o 6 y saca otra muestra.

### 8. Entrega (con el visto bueno)
```bash
python3 scripts/entregar.py <VIDEO> --receta proyectos/<VIDEO>/recetas/<receta>.json --usar-muestra
```
- Entrega exactamente la muestra aprobada en la carpeta de entregas de su carpeta de trabajo: `<AAAA-MM-DD Tema>/<AAAA-MM-DD Tema - Letra variante>.mp4` (una carpeta por vídeo, todas sus variantes dentro; la letra A, B, C… sirve para que diga «la C funcionó mejor»). La apunta en `proyectos/_entregas.md` (arranca vacío; tiene la columna «Publicado» para cruzarlo con sus métricas).
- Al lado deja el `.txt` del mismo nombre (`scripts/textos.py`): caption, primer comentario y portada de `caption.md`, reglas para otra IA, transcripción limpia (gancho aparte) y datos con fuente. Revísalo antes con `python3 scripts/textos.py <VIDEO> --receta …`.
- Mueve el original a «3 Originales usados» y deja la letra en la receta.
- Apunta en la columna «Efectos» de `_entregas.md` los códigos E-NN que lleva y pone al día el índice de la biblioteca (`efectos_indice.py usos`) solo.
- Si usas la página de la biblioteca y dice «elegidos usados: E-NN», márcalos: ArtifactData `update` de `elegidos/E-NN` con `{"usado_en": "<VIDEO>"}` (con su `if_version`). Así salen como «Ya usado en…». No los borres.
- Si usa la galería de efectos y en esta sesión tocaste un efecto o añadiste uno al índice: `python3 scripts/galeria.py al-dia` (necesita su fondo en `proyectos/_escaparate/`) y publica la página otra vez (mismo `out/galeria/pagina/index.html`, `files` con `clips/E-NN.mp4` y `posters/E-NN.jpg`).
- Si la receta cambió después de la muestra, se niega: saca otra muestra.
- Con pedido: `python3 scripts/pedido.py cerrar "<nombre del vídeo>"` y ArtifactData `update` de `pedidos/<doc_id>` con `{"estado": "entregado", "entregado_en": "<VIDEO>"}` (deja de salir en la página).
- Uno al día y sin ráfagas: un reel publicado a menos de una hora de otro suele quedarse corto de vistas. Díselo si va a subir dos seguidos.

### 9. Git (solo si el creador lo pide)
- Commit en español. Lo nuevo, mejor en rama y pull request.
- Al repositorio no va nada pesado ni de terceros (`.gitignore`): vídeos, audio, renders, modelos, capturas de comentarios.

## Reglas que no se saltan
- **Paradas:** con una receta del catálogo, una sola parada (la muestra del paso 7; los cortes de tomas repetidas se proponen antes, en segundos). Con una receta nueva o un formato sin probar, dos: antes de los subtítulos se enseña el corte limpio (`out/<VIDEO>_corte_916.mp4`) y se espera el sí.
- **Cierre que rota:** cada receta nueva lleva `"cierre"` (`scripts/cierre.py`): `conversacion`, `info` o una por cada palabra de `marca/marca.json` (en minúsculas, sin tildes). Antes de rellenarlo, `python3 scripts/cierre.py sugerir`: nunca el mismo dos vídeos seguidos y como mucho 2 de embudo (con palabra) cada 7. Los de conversación e info necesitan `"pregunta"` (la que dice al final, 70 caracteres como mucho) y, si la dice, `"frase"`. Al grabar, `python3 scripts/cierre.py guia` le dice cómo decir cada uno.
- **Palabras de «Comenta»:** solo las de `marca/marca.json`, que son las que tiene montadas en su herramienta de mensajes automáticos (p. ej. ManyChat). Siempre en MAYÚSCULAS y con «revisa tus mensajes» (si la persona no le sigue, el DM le llega a «Solicitudes»). Si en el vídeo dice una palabra que no está montada, avísale antes de publicar: nadie respondería.
- **Kit de la marca:** con pedido, la receta lleva su `"marca"` y su kit (`pedido.py comprobar`). Nunca el estilo de una marca en el vídeo de otra.
- **Marca:** logo al nombrar una marca (clave `"logos"`; en la pizarra círculo, como nodo del diagrama); «Sígueme» en todos, salvo la capa Episodio completo o cuando publica un cliente.
- **Carpeta de entregas:** solo la versión para publicar, y solo con `entregar.py --usar-muestra`. Nada de copias de trabajo ahí.
- **IA de imagen o vídeo** (si la usa): solo con su permiso, porque gasta créditos; nunca para logos, texto, documentos ni su cara.
- **Plantillas:** si cambias una plantilla o un script de montaje, `python3 scripts/plantilla.py probar` tiene que seguir en verde.
- **Receta nueva aprobada:** se añade al catálogo (tabla, ficha y «Cómo elegir») y se saca su plantilla de la receta real.
- **Nada global sin preguntar:** `~/.claude/settings.json`, skills globales, tareas programadas del sistema.
