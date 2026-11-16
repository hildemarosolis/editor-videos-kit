# Recetas de edición

Una receta dice cómo se monta un vídeo. Las probadas tienen **nombre** («este va con la pizarra viajera») y una **plantilla** en `plantillas/`. La plantilla es una receta que funcionó en un vídeo real, con lo propio de ese vídeo cambiado por huecos `__ASÍ__`.

Este catálogo es la **fuente única**: fichas, «Cómo elegir», referencia técnica, capas, banco de efectos y piezas técnicas. La skill `/editor` (`.claude/skills/editor/`) lo sigue paso a paso.

```bash
python3 scripts/plantilla.py lista                                   # las recetas con nombre y el ejemplo de cada una
python3 scripts/plantilla.py nueva "pizarra viajera" <VIDEO> --tema "Tema corto"
python3 scripts/plantilla.py comprobar proyectos/<VIDEO>/recetas/pizarra-viajera.json
python3 scripts/plantilla.py probar                                  # cada plantilla reproduce su vídeo de ejemplo
```

- `nueva` copia la plantilla a la carpeta del vídeo, pone el tema, calcula el centro de la cara y lista los huecos. Con `--capa episodio-completo` añade el outro de los shorts.
- `subtitulos.py`, `entregar.py` y `montaje.py` **no montan una receta con huecos**.
- Si se cambia una plantilla o un script de montaje, `probar` tiene que seguir en verde. Si en tu ordenador no están los vídeos de los ejemplos (no van a git), esas pruebas se saltan con un aviso.
- La plantilla es la referencia de la forma. Los vídeos de los que salieron no vienen en el kit (`proyectos/` no va a git), así que `probar` se salta sus pruebas hasta que tengas tus propios vídeos. Cuando tengas uno entregado con una receta, su receta es el mejor ejemplo para el siguiente.

## Recetas con nombre

| Receta | Plantilla | Para qué |
|---|---|---|
| **Gancho titular** | `gancho-titular` | Responder una duda o dar un consejo tajante |
| **Golpe y cuentas** | `golpe-y-cuentas` | Desmontar una idea equivocada, con números o un giro |
| **Ranking de pie** | `ranking-de-pie` | Ordenar 10 requisitos u opciones, grabado de pie |
| **Top con sueldo** | `top-con-sueldo` | Top 5 de oficios o trabajos con su sueldo |
| **Sketch con IA** | `sketch-con-ia` | Promo o sketch con planos transformados con IA |
| **Pizarra** | `pizarra` | Re-editar un monólogo: cara abajo, un dibujo por idea arriba |
| **Pizarra círculo** | `pizarra-circulo` | Explicar un proceso: cara en círculo, diagramas a toda pantalla |
| **Pizarra viajera** | `pizarra-viajera` | Lo mismo, con la cara alternando círculo, franja y pantalla completa |
| **Titular detrás** | `titular-detras` (+ montaje) | Variante para reels de prueba: frase más fuerte, glitch y titular gigante detrás de la persona |
| **Carrusel animado** | `carruseles/<nombre>/carrusel.json` (`scripts/carrusel.py`) | Carrusel de Instagram sin grabar: portada + diapositivas de 7 s en bucle + cierre |
| **Ruta en un mapa** | `proyectos/_rutas/<NOMBRE>.json` (`scripts/ruta.py`) + receta de capas | Ruta o viaje sin cara: voz en off, foto de cada parada arriba y el mapa que se dibuja abajo |
| Capa **Comentarios de seguidores** | pieza `"comentarios"` (con `guiones/<guion>/comentarios.json`) | El vídeo responde a comentarios públicos: la captura real entra con un pop, foto difuminada y nombre visible |
| Capa **Episodio completo** | `capas/episodio-completo` | Shorts sacados de un vídeo largo: outro de 5 s con destello y boom |

Por construir, con nombre provisional:
- **El que gana se queda** (M10).
- **Pizarra clara** (M11 claro).
- El **Explicador** (M9) ya queda cubierto por la pizarra círculo.

### Cómo elegir

**Primero manda el pedido**, si lo usas: si el creador eligió el molde en la página de la biblioteca (`scripts/pedido.py`, opcional), esa es la receta, con el kit de su marca. Esta lista es para cuando no hay pedido o te pide que lo propongas tú.

1. **¿Sale de un vídeo largo de YouTube?** Lleva la capa **Episodio completo**, además de su receta.
1b. **¿Reacciona a un clip ajeno (una entrevista, una noticia)?** **Reacción con lupa** (sobre Golpe y cuentas).
2. **¿Es una promo con planos de IA o un sketch con otra gente?** **Sketch con IA**.
3. **¿Enumera puestos?** De pie, 10 → **Ranking de pie**. Oficios con sueldo → **Top con sueldo**.
4. **¿Explica un proceso o un camino, con pasos?** **Pizarra círculo**. Si dura más de 60 s o el creador quiere verse más, **Pizarra viajera**.
5. **¿Desmonta una idea, con números o un giro?** **Golpe y cuentas**.
6. **¿Responde una duda o da un consejo?** **Gancho titular**.
7. **¿No hay vídeo grabado y el tema es una lista de pasos, trámites u opciones?** **Carrusel animado**.
7b. **¿No hay cara y el tema es un recorrido (un viaje, una ruta por una ciudad, del aeropuerto al centro)?** **Ruta en un mapa**, con su voz en off.
8. **¿Ya está publicado y hay que volver a subirlo en prueba?** Cambia de receta: **Pizarra**, **Pizarra viajera** o **Titular detrás**, con otro arranque. Cada variante va con su letra en la misma carpeta.

**Biblioteca de efectos:** cada efecto suelto tiene un código `E-NN` en `subtitulos/efectos/indice.json`. Para pedir uno basta su código («la E-14 en el golpe»). Si quieres verlos en clips, `scripts/galeria.py` hace una página con todos (opcional; ver la skill `/editor`).

## Fichas

### Gancho titular
- **Cuándo:** una duda o un consejo tajante, en monólogo.
- **Cómo se graba:** una toma, plano medio, mirando a cámara. Con buena luz, sirve cualquier sitio.
- **Qué lleva:**
  - titular que se escribe en los primeros segundos;
  - 2-4 golpes (palabra gigante; roja, tachada o en blanco y negro);
  - pastillas para listas de países u opciones;
  - una tarjeta por cada número dicho;
  - logo al nombrar una marca (clave `"logos"`);
  - el cierre que toque en la rotación y «Sígueme».
- **Qué no hacer:** más de 4 golpes; un titular de más de 4 palabras.

### Golpe y cuentas
- **Cuándo:** desmontar una idea equivocada («en este sector no hay trabajo», «eso ya no se puede hacer»).
- **Cómo se graba:** monólogo; o sketch de dos personas, con la otra fuera de cámara.
- **Qué lleva:**
  - gancho con la idea equivocada;
  - un impacto en el giro (zoom de golpe con líneas cómic y temblor);
  - golpes que desmontan («YA NO», «NO EXISTE»);
  - las cuentas en tarjetas.
- **Qué no hacer:** más de 2 impactos; ponen nervioso.
- **Variante con guion en varias tomas:** montaje con frase cortada al principio; una pizarra arriba con la cara en la franja solo al principio («¿Es para ti?» con el perfil: edad, sector); la conversación con quien está fuera de cámara como chat (capa **Conversación**); un golpe con estilo magia y un impacto con ondas.
- **Con fotos y titulares (opinión sobre política o noticias):** selfie andando o a cámara, frase cortada al principio y la pieza **`prensa`** (E-64, `scripts/prensa.py`):
  - al nombrar a alguien o algo que salió en prensa, caen arriba, apiladas como papeles, fotos con licencia libre (pie + crédito en pantalla) y titulares **reales** con medio y fecha;
  - `"prensa": [{"frase", "hasta_frase"|"dur", "items": [{"tipo": "foto", "frase"?, "imagen", "foco", "pie", "credito"} | {"tipo": "titular", "frase"?, "medio", "fecha", "titular", "url"}]}]`;
  - el titular se copia tal cual de la página (recortado solo con «…»), con su `url`; nada de capturas de periódicos ni fotos de agencia: no tienen licencia;
  - nunca una foto que muestre algo que no pasó (p. ej. dos personas juntas que no se reunieron); si lo dicho en voz alta no cuadra con la prensa, se avisa antes de montar;
  - las fotos van en `assets/fotos/` con su ficha en `fuentes.json` (las imágenes, fuera de git); medios y fotos se citan también en el caption.

### Ranking de pie
- **Cuándo:** del 1 al 10 (requisitos, errores, opciones).
- **Cómo se graba:** de pie, cuerpo entero, algo a la derecha para dejar libre la columna de la izquierda, fondo liso. Una toma, diciendo claro «Número diez…».
- **Qué lleva:**
  - columna 1-10 a toda la altura;
  - el elemento grande en el centro, que vuela a su miniatura;
  - sello y ritmo de zoom;
  - caja «Comenta» con una palabra de `marca/marca.json` (o el cierre que toque).
- **Qué no hacer:** grabarlo sentado (la columna te tapa); decir en voz alta una palabra que no está montada en tu herramienta de mensajes (nadie respondería: ese vídeo no se publica, se vuelve a grabar).

### Top con sueldo
- **Cuándo:** los 5 oficios o trabajos con su sueldo.
- **Cómo se graba:** de pie, plano medio, algo a la derecha. «Puesto cinco, soldador. Entre dos mil y dos mil seiscientos euros al mes».
- **Qué lleva:**
  - título fijo arriba;
  - monedas 1-5 que se rellenan;
  - «Nº», el oficio en tu color de acento y el sueldo contando;
  - foto o icono del oficio abajo;
  - el cierre que toque (encaja una palabra de embudo si tienes una para formación o empleo).
- **Qué no hacer:** sueldos sin comprobar (cada número lleva tarjeta).

### Sketch con IA
- **Cuándo:** promos de clientes o sketches con transformaciones (leyendas, personajes).
- **Cómo se graba:** el sketch completo en un vídeo; los planos de IA aparte (una IA de imagen o vídeo, si la usas; **con permiso del creador**, porque suele gastar créditos).
- **Qué lleva:**
  - montaje (`montaje.py`) con glitch en los cambios y voz con efecto «terror» si toca;
  - golpes del chiste;
  - tarjetas de precio y fecha;
  - pastillas de sedes o direcciones.
- **Qué no hacer:** cambiar el orden del vídeo largo, porque **el vídeo largo manda**: se respeta su orden y solo se meten los materiales nuevos donde corresponde. Si publica el cliente, sin «Sígueme» ni «Comenta».

### Pizarra
- **Cuándo:** re-editar un monólogo ya grabado para que parezca otro vídeo.
- **Cómo se graba:** lo ya grabado sirve. Sentado o de pie, plano medio.
- **Qué lleva:**
  - arranca a pantalla completa 2-3 s y pasa a la pizarra;
  - la cara queda en la franja de abajo y arriba sale una escena por idea: `titulo`, `iconos`, `lista`, `movil`, `campo`, `numero`, `curva`, `diagrama`, `captura`, `foto`, `bicicleta`, `escanos`, `mapa` o `evolucion`;
  - 1-2 respiros a pantalla completa.
- **Qué no hacer:**
  - escenas con más de 3-4 elementos (la franja deja 620 px);
  - títulos con icono y subtítulo a la vez, que no caben.
- **Escena `captura`** (sube los compartidos en vídeos de trámites o de normas):
  - la web oficial de verdad (boletín oficial, sede, ministerio) en una ventana de navegador con su dirección y la fecha de la captura; baja hasta la línea que importa, la marca en tu color de acento, hace zoom para que se lea en el móvil y saca una pastilla con el dato;
  - la imagen: `python3 scripts/captura.py <url> proyectos/<VIDEO>/assets/capturas/<nombre>.png --busca "texto exacto de la página"` (deja un `.json` con dónde está cada texto);
  - en la receta: `{"tipo": "captura", "frase": "…", "imagen": "assets/capturas/<nombre>.png", "resalta": "texto exacto", "resalta_frase": "…", "dato": {"texto": "PLAZO: 3 MESES", "frase": "…"}}`; opcionales `baja_frase` y `zoom` (1,9 por defecto);
  - si una sede no deja entrar al navegador automático (algunas responden 503), captura a mano desde el navegador, ponla en `assets/capturas/` y marca la línea en píxeles: `"resalta": {"y": 1840, "h": 40}` (con `"dpr": 2` si es de pantalla Retina);
  - solo páginas oficiales y públicas, sin datos personales en pantalla; la URL y la fecha quedan como fuente.
- **Escena `foto`** (E-63):
  - una foto real de apoyo en un marco que entra con rebote y se acerca despacio; varias fotos se suceden, cada una en su `frase`; antetítulo arriba (`ante`) y pastilla abajo (`dato`: texto y frase);
  - en la receta: `{"tipo": "foto", "frase": "…", "ante": "…", "fotos": [{"imagen": "assets/fotos/<nombre>.jpg", "credito": "Foto: Autor · CC BY-SA 4.0 · Wikimedia Commons", "foco": [50, 35], "frase": "…"}], "dato": {"texto": "…", "frase": "…"}}`; `foco` (en %) mueve el encuadre y la `frase` de la primera foto es opcional;
  - **solo fotos con licencia que permita reutilizar** (CC0, dominio público, CC BY o CC BY-SA; nunca NC ni ND), sacadas de Wikimedia Commons por su API; el `credito` es obligatorio (sin él no monta) y sale siempre en pantalla; autor, licencia y página van en `assets/fotos/fuentes.json` y en el caption;
  - nunca fotos de trámites, documentos ni personas reconocibles en un contexto que no es el suyo; las fotos no van a git.
- **Escena `bicicleta`** (una metáfora: un proceso con dos partes que tienen que funcionar a la vez):
  - la bicicleta se dibuja y las ruedas giran; al decir que una falla, la de atrás se pone roja y se suelta, sale «PROCESO EN PELIGRO», se arregla y cada rueda recibe su nombre (`ruedas`, `rueda_frases`) y su visto (`ok_frase`);
  - se puede meter un tramo de pizarra dentro de un **Titular detrás**: `entrada` con la frase donde empieza y `completo_desde` donde vuelve a pantalla completa, sin solaparse con los titulares.
- **Escena `escanos`** (un parlamento que se reparte):
  - hemiciclo que se llena partido a partido (de izquierda a derecha) con su contador, la raya de la mayoría y una pastilla con la suma (`suma`: texto y frase). Viene hecho para 350 escaños y mayoría 176 (p. ej. el Congreso de España);
  - `partidos` con `nombre`, `escanos` y `color`; lo que falte hasta el total sale en gris como «Otros»;
  - solo cifras comprobadas, con `fuente` en pantalla (p. ej. una media de encuestas con su fecha). Ojo con las leyes electorales: en España, los últimos 5 días antes de votar no se publican encuestas (LOREG, art. 69.7).
- **Escena `mapa`** (E-56): un mapa que se dibuja con un punto por sitio y su contador (viene hecho con el mapa de España; otro país hay que montarlo). Con `"lugares": [{"nombre", "lat", "lon"}]` pone cada punto en su sitio real, con su nombre y un aro que late, sin contador.
- **Escena `evolucion`** (para un vídeo sobre tu propia evolución como creador):
  - barras de seguidores por red que suben paso a paso, sin cifras;
  - un móvil con tus vídeos de cada época y el año debajo;
  - comentarios anónimos («alguien») que se acumulan.
  - Va en una toma sin voz: las escenas se anclan con `"t"` en segundos, `"zona": [120, 1090]` le da más alto, y `"completo_desde": {"frase": "…"}` pasa a pantalla completa al empezar a hablar.
  - Esa toma se prepara con `preparar.py --sin-silencios`.
  - Los clips antiguos se recortan y se pasan a SDR solos (`"clip"`, `"desde"`).
- **Entrada de la pizarra:** admite `"despues_de"` si la frase de entrada ya sale antes (p. ej. en el gancho).

### Pizarra círculo
- **Cuándo:** explicar un proceso o un camino (p. ej. en un vídeo de trámites: solicitud → permiso → renovación).
- **Cómo se graba:** cualquier plano en el que se te vea la cara; sirve un sketch con la otra persona fuera de cámara.
- **Qué lleva:**
  - la cara en un círculo arriba a la derecha y la pizarra a toda pantalla;
  - una etiqueta de sección por escena;
  - diagramas que se arman al nombrar cada paso;
  - las preguntas de la otra persona como chat en el móvil;
  - final a pantalla completa con el cierre y «Sígueme».
- **Qué no hacer:**
  - un zoom del círculo que corte la cabeza (de 0,7 a 0,9 en plano medio: mira los fotogramas);
  - el logo flotante arriba, que choca con el círculo; va como nodo del diagrama.

### Pizarra viajera
- **Cuándo:** como la pizarra círculo, en vídeos largos o cuando el creador quiere verse más.
- **Cómo se graba:** igual.
- **Qué lleva:**
  - cada escena elige su `"cara"`: `circulo` o `franja`;
  - la cara viaja de un sitio a otro; arranque, respiros y final a pantalla completa.
- **Qué no hacer:**
  - poner en franja las escenas altas (el móvil o un título con icono): van en círculo;
  - quedarse más de dos escenas seguidas en el mismo sitio.

### Titular detrás
- **Cuándo:** volver a subir en prueba un vídeo que ya funcionó, con otros primeros segundos.
- **Cómo se graba:** no se graba; sale del corte que ya hay.
- **Qué lleva:**
  1. montaje: la frase más fuerte primero y, con un glitch, el vídeo desde el principio;
  2. `recorte.py`, para la silueta;
  3. 2-3 titulares gigantes detrás de la cabeza (el de la frase fuerte, el del gancho y el dato clave).
- **Qué no hacer:**
  - titulares tan bajos que la cabeza los tape enteros (y≈60);
  - combinarlo con impactos, zoom lento o pizarra, que mueven el vídeo y no la silueta.

### Carrusel animado
- **Cuándo:** contenido de lista (pasos, trámites, papeles, opciones) sin grabar vídeo.
- **Formato:** 1080×1440 (3:4). Portada fija en PNG con el título, la lista y tu foto recortada (de `marca/fotos/`). Luego una diapositiva de 7 s por punto, en bucle, sin voz. Al final, el cierre que toque en la rotación (`python3 scripts/cierre.py sugerir`; los carruseles cuentan): la diapositiva «Comenta PALABRA» (`"cta"`, con una palabra de `marca/marca.json`), la diapositiva «Tu turno» con un cierre sin palabra (`"cierre": {"tipo": "info" | "conversacion", "pregunta": …}`) o nada con `"cta": false`. De 6 a 10 diapositivas en total, contando portada y cierre.
- **Portada y pieza 01:** la portada promete un resultado con algo de tensión y su antetítulo dice para quién es. La pieza 01 tiene que entenderse sola, porque Instagram vuelve a enseñar el carrusel desde ahí. Los ganchos adaptados están en la skill `/carrusel`.
- **Cada diapositiva:** antetítulo «01 / 05 — CATEGORÍA», título en la fuente de tu marca, pastilla del organismo, panel animado, dos líneas con **acentos**, y pastillas de fuente y aviso. Tu logo (o el de la marca con la que colaboras) arriba a la derecha.
- **Bloques del panel:** `campo` (se escribe), `checks` (✓ uno a uno), `calendario`, `huella`, `contador`, `precio`, `documento` (con sello), `tarjeta`, `estado` y `foto`. Una fila de dos va como lista `[a, b]`.
- **Historias:** `carrusel.py <nombre> --historias` saca las mismas piezas en 9:16 (1080×1920) para historias de Instagram, con el diseño en el centro y 240 px libres arriba y abajo para la barra del perfil y la caja de mensaje. «Desliza» pasa a «Toca» y el cierre a «Respóndeme a esta historia» (en historias no hay comentarios: con «Comenta PALABRA» se niega). El `pie.txt` dice cómo subirlas. Se entregan como la letra siguiente, en su propia carpeta «<fecha tema> - historias».
- **Foto de apoyo** (E-65): el bloque `foto` llena el panel por detrás, se acerca despacio y lleva su crédito; las cifras van compactas en el tercio de abajo. `{"tipo": "foto", "imagen": "x.jpg", "credito": "Foto: Autor · CC BY-SA 4.0 · Wikimedia Commons", "foco": [x, y], "zoom": 1.5}` (`foco` en %, `zoom` para subir lo importante por encima de las cifras). Las fotos van en `carruseles/<nombre>/fotos/` (fuera de git) y sus créditos en `fotos/fuentes.json` (en git). Solo licencias libres (CC0, dominio público, CC BY, CC BY-SA; nunca NC ni ND), y el autor también en el pie.
- **Paleta:** `"paleta": "marca"` (tu color de acento y negro) o `"logo"` (los colores del logo que lleve). Foto: `"foto"`, un archivo de `marca/fotos/`.
- **Datos:** cada cifra en pantalla, verificada y con su fuente en la pastilla, igual que las tarjetas de los vídeos. Primero se proponen los puntos y los datos; se anima con el sí del creador.
- **Comandos:**
  ```bash
  HYPERFRAMES_SKIP_SKILLS=1 python3 scripts/carrusel.py <nombre> --hoja                       # compone y renderiza → out/carrusel_<nombre>/
  HYPERFRAMES_SKIP_SKILLS=1 python3 scripts/carrusel.py <nombre> --paleta logo --solo 02      # probar otra paleta en una pieza
  ENTREGA_APROBADA=1 HYPERFRAMES_SKIP_SKILLS=1 python3 scripts/carrusel.py <nombre> --entregar  # con el visto bueno
  ```
- **Entrega:** en la carpeta de entregas, «<fecha tema>/<fecha tema> - A carrusel - 00 portada.png, 01.mp4…, pie.txt», en el orden en que se suben, con una fila en `proyectos/_entregas.md`.
- **Dos clases:** de servicio (pasos, papeles, opciones; con cierre) y de posición ante una noticia (opinión, luto; `"cta": false`, cifras con quién las da y a qué hora, versiones atribuidas). Detalle en la skill.
- **Skill:** `/carrusel` (`.claude/skills/carrusel/SKILL.md`). Tiene el camino, las dos clases de carrusel y las trampas.

### Ruta en un mapa
- **Cuándo:** un recorrido que se cuenta parada a parada, sin grabar cara: un viaje entre dos ciudades, una ruta por una ciudad, del aeropuerto al centro.
- **Formato:** 1080×1920. Portada con foto a pantalla completa, titular en dos líneas (blanco y color de acento) y chip. Después, arriba (y 0-800) la foto de cada parada con su etiqueta numerada y sus chips; abajo, el mapa oscuro donde la ruta se dibuja al nombrar cada parada: `"mundo"` (Natural Earth, Mercator, con el arco del vuelo) o `"madrid"` (teselas de OpenStreetMap con filtro oscuro, línea de metro y tramo a pie; es la ciudad que viene montada). Subtítulos con `"subtitulos": {"top": 815}`, sobre el borde del mapa.
- **Voz:** la del creador en off (una nota de voz del móvil vale). Se limpia a mano: se buscan las tomas repetidas con whisper sin contexto y energía, se cortan, se acortan las pausas y se normaliza a −14 LUFS (`raw/<NOMBRE>/voz_limpia.wav`). Las paradas se anclan a frases de `palabras.json` de esa voz limpia.
- **Fotos:** solo con licencia (Wikimedia Commons, con autor y licencia en `creditos.json`, que salen en pantalla y al final del caption) o propias. Nunca generadas con IA: son lugares reales. Mapas: atribución «© OpenStreetMap» o «Mapa: Natural Earth» siempre visible.
- **Datos:** cada requisito, precio o plazo de los chips y tarjetas, con fuente oficial (`guiones/<fecha>-<tema>/fuentes.md`). Los chips del fondo cuentan como tarjeta del dato; la cifra que necesite explicación va como tarjeta de la receta (`"datos"`).
- **Cuenta y llamada:** si publicas en colaboración con una marca, su logo sale al nombrarla (`"logos"`). La palabra de «Comenta» tiene que estar montada en **tu** herramienta de mensajes: por eso se publica en tu cuenta. «Sígueme» como siempre.
- **Comandos:**
  ```bash
  python3 scripts/ruta.py proyectos/_rutas/<NOMBRE>.json            # compone y revisa con snapshot
  python3 scripts/ruta.py proyectos/_rutas/<NOMBRE>.json --render   # → raw/<NOMBRE>.mp4
  python3 scripts/preparar.py <NOMBRE> --sin-silencios
  cp raw/<NOMBRE>/palabras.json proyectos/<NOMBRE>/palabras.json   # la transcripción de la voz limpia es mejor (sin efectos)
  python3 scripts/entregar.py <NOMBRE> --receta proyectos/<NOMBRE>/recetas/ruta.json --muestra
  ```
- **Fuera de git:** `proyectos/_rutas/*/assets/` (fotos, teselas, `madrid.png`, `countries-50m.json` de world-atlas@2.0.2 y audio). Las fotos se vuelven a bajar de Wikimedia Commons con `creditos.json`; el mapa de Madrid, con las teselas de `madrid_vista.json`. Para otra ciudad hay que montar su vista igual (de momento, a mano).
- **Trampas:** en GSAP, un `fromTo` que vuelve a enseñar un mapa al final necesita `immediateRender:false` (si no, lo oculta desde el segundo 0). Los trazos con extremo redondo se ven como un punto antes de dibujarse: van con opacidad 0 hasta que empiezan.

### Capa Episodio completo
- **Cuándo:** shorts recortados de un vídeo largo de YouTube.
- **Qué lleva:** outro de 5 s («el episodio completo en mi canal») con destello, subida y boom. Sustituye a «Sígueme».
- **Cómo se activa:** `"outro": "marca/outros/<tu outro de 5 s>.mp4"` y `"seguir": false` en la receta (o `plantilla.py nueva … --capa episodio-completo`). El outro se prepara una vez: los primeros 5 s de tu outro largo, sin el negro del principio y a −14 LUFS.
- Al publicar en YouTube Shorts, pon el episodio largo como «vídeo relacionado».

### Shorts de una entrevista horizontal
- **Cuándo:** sacar shorts de un episodio de entrevista o podcast (cualquier vídeo de YouTube en 16:9). Los hacemos nosotros: los recortes automáticos de otras herramientas suelen salir peor.
- **Camino:**
  1. Original de mejor calidad (la exportación de tu programa de edición, mejor que bajarlo de YouTube) → transcripción entera → propuesta de shorts con su gancho de frase cortada y sus segundos.
  2. `scripts/reencuadre.py <origen> <de> <a> out/<N>_vertical.mp4`, con el python que tiene OpenCV (`python3 scripts/kit.py` dice cuál): clasifica cada décima por el tamaño de las caras (YuNet); plano cerrado → recorte 9:16 en la cara; plano general → **pantalla partida**, una persona arriba y la otra abajo. Si el original se montó con fundidos, el corte va al centro de cada uno.
  3. `proyectos/_montajes/<N>.json` (gancho + `"entrada": "impacto"` + tramos del cuerpo, relativos al vertical) → `montaje.py` → `preparar.py <N> --sin-silencios` → corte limpio.
  4. Receta «Golpe y cuentas» **sin titular** + capa Episodio completo + tarjetas flotantes donde se nombren cursos, oficios o etapas.
- **Modos de `reencuadre.py`:**
  - `--tres`: tres personas (dos en la mesa y una aparte). Una cara = primer plano; dos = pantalla partida; tres = las dos de la mesa arriba y la otra abajo.
  - `--general`: dos personas de pie en un plano abierto todo el rato, con cámara en mano: pantalla partida que sigue cada cara con suavidad y, cuando la cámara se queda con una sola, primer plano vertical de esa persona.
  - `--modos <json>`: fija el encuadre por tramos según quién habla (p. ej. `"der"`, primer plano del invitado cuando habla él; `"dos"`, pantalla partida cuando pregunta el creador).
- **Mejor desde el original de la cámara:** un 4K se recorta en 4K (`reencuadre.py` lo hace solo).
- **Cámaras que graban cada micro en un canal:** los `modos` salen de qué canal domina en cada tramo (cuál es de quién cambia de grabación a grabación), y el audio se **centra** después de `montaje.py`; si no, se oye torcido en auriculares.
- **Whisper con contexto desplaza los tiempos** en estos montajes: `palabras.json` se rehace desde la transcripción sin contexto del original.
- **Shorts de un programa con su propia marca** (un podcast con otra cuenta, otros colores): receta con `"acento"` (el color del programa), `"outro"` con su cierre propio, `"seguir": false`, `"comenta": false` (se publica en colaboración con las cuentas del programa y de los invitados) y tarjetas flotantes con nombre y @ (`"icono": "instagram"`, `"ancho"`). Si es un programa fijo, dale un kit en `marca/kits/` con su bloque `"clips"` y usa `scripts/clips.py`.

### Reacción con lupa
- **Cuándo:** reaccionar a un clip ajeno (entrevista, noticia, declaración) y responderlo con la norma en la mano.
- **Cómo se graba:** guion toma a toma con `/guion`; entre toma y toma, unos segundos callado escuchando (salen en la franja mientras habla el clip).
- **Camino:**
  1. Cada toma por `prueba_corte.py` (sin silencios, para el cuerpo) y otra vez con `--sin-silencios --out out/escucha` (para los huecos donde escucha).
  2. `montaje.py` con los extractos del clip (fuente: el clip guardado en `referencias/`): el más fuerte como gancho de frase cortada (la persona del clip a pantalla completa) y los demás con `"encima"` (el creador escuchando en una franja abajo, desde y=1240, con raya de color) y `"difuminar"` sobre los subtítulos que trae el clip.
  3. `preparar.py <N> --sin-silencios` → receta «Golpe y cuentas» con `"variante": "reacción"`: rótulo de fuente con `chips` (`«MEDIO · FECHA»`, y=430 o más abajo si tapa una cara), golpes alarma para la promesa («¿48 HORAS? · Es una propuesta, no la ley») y tarjetas de datos con su fuente oficial.
- **Cuidado:** extractos cortos y siempre con su fuente; no se opina del partido ni de la persona; las cifras de terceros (encuestas) solo comprobadas y con fuente en pantalla.

---

# Referencia técnica (modelos, capas y piezas)

Los nombres técnicos (M1…M11) siguen funcionando en las recetas. Se monta a mano con:

```bash
python3 scripts/subtitulos.py --dir proyectos/<VIDEO> --receta proyectos/<VIDEO>/recetas/<receta>.json
```

## Base (va en todos los vídeos, siempre)

Corte de silencios · −14 LUFS · subtítulos en la fuente de `marca/marca.json` (Anton por defecto), en mayúsculas, blanco con contorno negro y palabra activa en tu color de acento (`acento` en `marca/marca.json`), en zona segura Reels/TikTok · logo al nombrar una marca (`"logos"`) · sonido en cada aparición · tarjeta para cada dato dicho · tarjeta «Sígueme» con tu usuario y tus redes · el cierre que toque en la rotación.

## Modelos (uno por vídeo)

| # | Modelo | Cuándo usarlo | Cómo se graba | Estado |
|---|---|---|---|---|
| M1 | **Promesa + prueba** | Explicar algo o responder una duda | Monólogo | Construido (es el Gancho titular) |
| M2 | **Golpe + cuentas** | Desmontar una idea equivocada con números | Monólogo; o sketch de dos personas | Construido |
| M3 | **Ranking 1-10** | Ordenar requisitos, errores, opciones | Una toma. Mejor de pie, cuerpo entero, algo a la derecha, fondo liso | Construido. Aspecto «pantalla completa» (`"aspecto": "completa"`): el de por defecto para rankings grabados de pie |
| M4 | **Utilidad con prueba** | Requisitos o trámites con fuente oficial | Monólogo en un sitio con autoridad | Falta el b-roll literal; la captura de la fuente ya existe (escena `captura`) |
| M5 | **Referencia donde señalo** | Lugares, ciudades, destinos | Plano abierto, señalando arriba | Falta un banco de fotos |
| M6 | **Esto o aquello** | Preguntas rápidas A/B | Dos personas con micrófono | Falta construir |
| M7 | **Top N errores** | «5 errores que…, el último es el peor» | Una toma por error, en lugares distintos | Falta construir |
| M8 | **Promo-sketch con transformaciones de IA** | Promoción para un cliente con sketch y planos de IA (p. ej. leyendas que se transforman) | El sketch completo en un vídeo; los clips de IA aparte | Construido (Sketch con IA): montaje con glitch, grito con efecto «terror», silbido; tarjetas de precio y fecha; pastillas de sedes; sin «Sígueme» ni «Comenta» si publica el cliente |
| M9 | **Explicador animado** | Explicar un proceso o sistema paso a paso | Una toma de cara; casi todo es gráfico | Construido como aspecto de la pizarra M11: `"cara": "circulo"` arriba a la derecha + escena `diagrama` (organigrama que se arma nodo a nodo) + etiqueta de sección (`"seccion"`) + `"final_completo"` (es la Pizarra círculo) |
| M10 | **El que gana se queda** (torneo de comparaciones) | Elegir entre opciones: cursos, ciudades, vías, trabajos | Una voz en off pregunta «¿A o B?» y tú eliges y explicas; el ganador se enfrenta al siguiente | Falta construir la capa `torneo` (fichas con icono, palabra gigante, el perdedor se va, empate) |
| M11 | **Pizarra arriba** | Cualquier monólogo; sobre todo para **re-editar vídeos ya publicados** y que parezcan otros | Lo ya grabado sirve | Construido (`scripts/pizarra.py`, clave `"pizarra"`). Es el modelo por defecto para las variantes de los reels de prueba. Escenas en la ficha de la Pizarra; `movil` lleva notificación y mensajes, con columna `lado` y `sello`. Además `entrada`: arranca con el plano completo y en esa frase pasa a la pizarra con una transición. Y `respiros`, para volver un momento a pantalla completa. La pizarra se aparta sola cuando salen un logo, «comenta» o «sígueme» |
| M11 claro | **Pizarra clara** | Utilidad con fuente oficial: requisitos, trámites, novedades | Webcam o móvil sentado; lo ya grabado sirve | Por construir: `"tema": "claro"` (fondo blanco), `"cara": "tarjeta"` (recuadro redondeado abajo), título de sección en caja negra y escena `navegador` con capturas reales de la fuente que se desplazan |

## Capas (se suman a cualquier modelo)

| Capa | Qué hace | Estado |
|---|---|---|
| **Gancho titular** | Antetítulo + titular que se escribe + etiquetas con icono | Construida |
| **Tarjetas de dato** | Número que sube, estrellas, lista, banda de cuentas, destello | Construida |
| **Golpe de reacción** | Zoom de golpe + líneas cómic + temblor | Construida. Sin rayos: `"estilo": "onda"` en el impacto (ondas que salen de la cara + destello). |
| **Golpes de palabra** | Palabra gigante; blanco y negro; tachado; `"estilo": "magia"` (chispas, brillo del vídeo y campanitas); `"estilo": "alarma"` | Construida |
| **Chips** | Pastillas por palabra (países, opciones) | Construida |
| **Cámara / planos** | Acercamientos y alejamientos lentos, golpe en el cierre, alternar tomas; columna de planos en el guion | Pendiente |
| **CTA comentario** | Caja de comentario que escribe la palabra clave | Construida (dentro del ranking; por sacar como capa) |
| **Pregunta del seguidor** | Burbuja tipo mensaje arriba con el texto de la pregunta que se responde | Por construir |
| **Conversación** | Alguien habla fuera de cámara: la charla sale como un chat, burbuja gris a la izquierda (fuera de cámara) y de color a la derecha (el creador), una al decir cada frase; los subtítulos se ocultan. `"conversacion": [{"lineas": [{"frase", "texto", "quien": "fuera"\|"yo"}], "queda"}]`. Si la otra voz está lejos del micro, va en tramos propios del montaje para igualar el volumen | Construida (`efectos.py`) |
| **Sonido en la tarjeta** | `"sonido": "caja"` en un dato: caja registradora cuando habla de dinero o inversión (`sfx.py`) | Construida |
| **Punch-in** | Zoom fuerte de golpe a primer plano en frases clave | Por construir (hay `zoom_ritmo` en el ranking e `impactos`) |
| **Top 5 con sueldo** | Ranking de N con «Nº», oficio, sueldo que cuenta y foto (o icono) del oficio abajo; título fijo arriba; monedas que se rellenan | Construido (`ranking.py`, `"aspecto": "top"`, `"prefijo": "puesto"`, `sueldo: [de, a]`) |
| **Variantes de prueba** | De cada vídeo, 4 versiones: v1 color (saturación), v2 gancho distinto, v3 zoom 10 %, v4 tipografía (Oswald Bold). `scripts/variantes.py` + `recetas/variantes.json` por vídeo | Construida |
| **Marca de agua** (E-61) | `"marca_agua": true`: tu @ en gris translúcido encima de los subtítulos todo el vídeo. Se esconde bajo «Sígueme» y no sale con pizarra, ranking ni niveles | Construida; no va por defecto |
| **Frase clave en caja** (E-62) | `"subtitulos": {"resaltar": ["frase", …]}`: esas palabras en negro sobre caja de tu color de acento, en vez de la palabra activa | Construida; no va por defecto |

## Banco de efectos

Efectos sueltos para meter **donde encajen con lo que se dice**, no todos en un vídeo. Muchos necesitan **recortar la silueta**. En Mac, Vision de Apple lo hace bien y sin instalar nada (`scripts/recorte.py`).

| Efecto | Cuándo usarlo | Recorte | Estado |
|---|---|---|---|
| **Titular gigante detrás de ti** | Gancho: la palabra clave detrás de la cabeza | sí | **Construido**: `scripts/recorte.py` (silueta con Vision → `assets/silueta.webm`) + `scripts/detras.py` (clave `"detras"`) |
| **Pegatina congelada** (freeze-frame) | Presentar cada idea nueva, trámite o persona: el plano se congela, sales recortado como pegatina y una etiqueta dice qué es | sí, del fotograma | **Construida**: `scripts/pegatina.py` (clave `"pegatina"`) |
| **Barrido de color** (grade-wipe) | Una vez, al principio: una raya de color cruza y el vídeo queda con color de cine | no | **Construido**: `scripts/barrido.py` (clave `"barrido"`) |
| **Ranking por niveles** (tier-list) | Clasificar países, trámites o herramientas en filas (S/A/B, SÍ/NO, 1-5) con bandera o logo | no | **Construido**: `scripts/niveles.py` (clave `"niveles"`) |
| **Antes y después a tu espalda** (over-the-shoulder) | Una comparación dicha en voz alta («3 meses → 48 horas») | sí | **Construido**: `"detras"` con `"tipo": "comparar"` |
| **Portada de revista** | Gancho o titular de noticia («NUEVA LEY») | sí | **Construida** (ver abajo) |
| **Gráfico a tu espalda** / chart grow | Cuando se dice una cifra que crece o compara | sí / no | Prioridad 1 |
| **Zoom de golpe con palabra** / digital zoom | Frase clave; ya existe a medias (`impactos`, golpes `bn`) | no | Prioridad 1 |
| **Headline wall** | Repasar titulares o mitos | no | Construido como lluvia de titulares |
| **Phone mockup** | Cuando cita un WhatsApp, un DM o una pregunta de seguidor | no | Construido como «Dentro del móvil» |
| **Te sales del marco** | Cierre o «sígueme» dentro de una tarjeta de post | sí | Prioridad 2 |
| **Pegatina de recortes** | Temas de estafas (letras de nota de rescate) | sí | Prioridad 2 |
| **Cuadrícula pop** / eco de clones | Enumerar perfiles («si eres A, B, C…») | sí | Prioridad 3 |
| **Órbita** (iconos o vídeos) | Enumerar opciones alrededor de ti | sí | Prioridad 3 |
| **Vértigo** | Una sola vez, para el giro dramático («y aquí viene lo grave») | sí | Prioridad 3 |
| UI world · doodle boil · glass type · zoom-through · partículas | Decorativos; solo si sobra tiempo | — | Prioridad 4 |

**Efectos construidos y sus claves:**
- **Portada de revista** (`"detras": [{"tipo": "revista", …}]`, necesita `silueta.webm`): fondo aclarado como papel, cabecera roja gigante detrás de la cabeza (se coloca sola según `centro_cara`), y delante el antetítulo y número grande (`ante`, `numero`, `numero_txt`), el titular (`titular`, `acento`), `fecha`, tu @ y código de barras. Para ganchos de noticia. Cada número es un dato: con su fuente.
- **Lluvia de titulares** (`"titulares": [{"frase", "hasta_frase" | "dur", "items": ["…", {"texto", "etiqueta"}], "etiqueta": "ÚLTIMA HORA"}]`): hasta 8 titulares de papel que caen uno tras otro alrededor; los que taparían la cara se saltan solos. Para mitos y noticias.
- **Dentro del móvil** (`"movil": [{"frase", "dur", "titulo", "acento", "pie", "escala": 0.62, "y": 250}]`): el vídeo entra en un móvil con la interfaz de Reels (dibujos propios, tu foto y tu @); los subtítulos bajan debajo. Para citar un DM o un comentario, o reforzar «Comenta PALABRA».
- **Zoom de cámara** (`"camara": [{"frase", "dur", "zoom": 1.25, "info", "tc_inicio"}]`): visor con esquinas, REC que parpadea, código de tiempo, cuadro de enfoque que busca la cara y zoom lento hacia ella. Para el «grabado en directo».
- **Tarjetas flotantes** (`"flotantes": [{"frase", "hasta_frase" | "dur", "zona": "arriba" | "abajo" | "cerrado", "items": [{"frase", "texto", "sub", "icono", "sitio"?}]}]`): tarjeta oscura con borde de color e icono que entra girando en 3D al decir su frase, flota y se balancea, y sale volando al final. Las zonas son las mitades de la pantalla partida del reencuadre o el primer plano; se colocan a los lados de la cara. Iconos: codigo, grado, reloj, lupa, salud, herramienta, tecnologia, barco, bici, pausa, dinero, escudo, datos, instagram.
- Descartados: plató/croma. No encajan: chat a pantalla completa, vídeo encima. Decorativos: cristal líquido, cristal roto, órbita, portal.

**Pegatina congelada** (hecha en casa y gratis):
- Receta: `"pegatina": [{"frase": "la toma de huellas", "nombre": "LA CITA", "rol": "toma de huellas", "dur": 2.5}]`. `nombre` como mucho 24 caracteres; `rol` es opcional; `y` (1245 por defecto, bajo los subtítulos).
- Qué pasa: destello y obturador; el plano se congela oscurecido, desenfocado y con puntos de color. La persona se despega con borde blanco y sombra (rebote `back.out` y un balanceo lento). La etiqueta entra girando con un pop. A los 2,5 s todo vuelve en seco con un whoosh. **La voz y los subtítulos siguen.**
- La silueta sale de Vision **solo sobre ese fotograma**, sin necesidad de `silueta.webm`, y se limpia con OpenCV para quitar objetos blancos del fondo. Se guarda en `assets/pegatina/`.
- Una por idea nueva, separadas al menos 5 s (avisa si no). Si coincide con la caja «Comenta», la etiqueta sube encima de la cabeza. No se combina en el mismo momento con `impactos`, `zoom_lento` ni la pizarra.
- En la página de revisión sale como pieza «Pegatina congelada».

**Barrido, niveles y comparar:**
- **Barrido de color** (`"barrido": {"frase", "dur": 1.1, "etiquetas": true, "antes": "ANTES", "despues": "DESPUÉS", "intensidad": 1, "hasta_frase" | "seg"}`).
  - Una raya de color con brillo cruza de izquierda a derecha y deja el vídeo con más contraste, tonos cálidos, sombras verdosas y viñeta. Mientras cruza salen las pastillas «ANTES» y «DESPUÉS». Suenan subida y whoosh.
  - Se queda hasta el final, salvo que se diga otra cosa. Las pegatinas congeladas de después se tiñen igual.
  - No se usa con la pizarra, ni con un titular detrás después del barrido (la silueta saldría sin teñir).
- **Ranking por niveles** (`"niveles": {"tema", "filas": ["SÍ", "NO"], "items": [{"nombre", "fila", "frase", "emoji" | "logo" | "imagen"}], "mantener": 2}`).
  - La tabla va arriba, centrada. Tú bajas a la franja de abajo con raya de color, como en la pizarra, y los subtítulos suben a y=880.
  - Las filas entran escalonadas. Cada elemento cae en su fila con rebote y un pop al decir su frase. La pastilla pasa de «CLASIFICANDO» a «CLASIFICADO».
  - Límites: hasta 6 filas, 4 por fila, 12 en total y nombres de hasta 14 caracteres.
  - Iconos: banderas con `emoji` y logos de Simple Icons 16.34.0 con `logo` (se bajan una vez a `marca/logos/simple/`). Las filas son las que dices tú, nunca inventadas.
  - No se usa con la pizarra.
- **Antes y después a tu espalda** (`"detras": [{"tipo": "comparar", "valor_antes", "valor_despues", "txt_antes", "txt_despues", "frase", "dur", "fuente"}]`). Necesita `silueta.webm`.
  - Una tarjeta de cristal oscuro con filo de color sube por detrás de los hombros, con la cabeza delante.
  - A la izquierda va el «antes», que se tacha en rojo; a la derecha sale el «después» grande en tu color de acento, con impacto.
  - Los valores son de hasta 16 caracteres. Cada cifra es un dato: lleva fuente.

**Cierres que rotan** (`scripts/cierre.py`). La receta lleva `"cierre"` en vez de la caja «Comenta» fija:
- **Con palabra** (una por cada palabra de `marca/marca.json`, en minúsculas y sin tildes: `"cierre": "guia"`): la caja «Comenta» de siempre, o la notificación con `"estilo": "notificacion"`. Una palabra puede llevar su propio texto (`"dicho"`, `"aviso"`) en `marca.json`.
- **Sin palabra** (`conversacion`, `info`): caja «pregunta». Arriba, «TU TURNO»; en medio, la pregunta en una caja blanca con filo de color y las palabras entrando escalonadas; debajo, «TE LEO EN LOS COMENTARIOS 👇» (o «¿QUIERES INFO? DÍMELO AHÍ 📩»). Si la dices (`"frase"`), va en el sitio de los subtítulos, que se ocultan mientras está. Si no la dices (vídeos ya grabados), va abajo, más pequeña y sin «TU TURNO», justo antes de «Sígueme», y los subtítulos siguen. Dura 6 s. La pregunta, como mucho 70 caracteres.
- Reglas: nunca el mismo dos seguidos y como mucho 2 de embudo (con palabra) cada 7 (`python3 scripts/cierre.py sugerir`). Al grabar: `python3 scripts/cierre.py guia`.
- Una palabra que no esté montada en tu herramienta de mensajes automáticos (p. ej. ManyChat) no se usa: nadie respondería.
- Recetas sin `"cierre"`: sacan la caja «Comenta» con su palabra (o la de por defecto), o nada con `"comenta": false`.

Pieza común: `scripts/recorte.py`. Vision saca la máscara a unos 23 fotogramas por segundo, unos 2 minutos para 80 s, y la guarda como VP9 con transparencia. HyperFrames la respeta. Capas, de abajo arriba: vídeo, sombra, efecto detrás, persona recortada (solo mientras dura el efecto) y subtítulos. No se combina con `impactos`, `zoom_lento` ni pizarra, porque mueven el vídeo y no la silueta. (Vision es de Mac: en Windows o Linux estos efectos no funcionan.)

**Gancho de frase cortada** (el arranque que mejor funciona; se propone en todos los vídeos nuevos): `montaje.py` con dos tramos del corte. Primero la frase más impactante del vídeo (cifra, promesa falsa, contradicción), **cortada en seco** justo al acabar la idea; después `"entrada": "impacto"` (subida de aire, destello, golpe de zoom, boom) y el vídeo desde el principio. Con `"entrada": "glitch"` sale la versión suave. Luego `preparar.py <NOMBRE> --sin-silencios`. Si una frase se dice dos veces, `golpes` y `chips` admiten `"despues_de"`.

**Cuando la cara queda alta en el plano** (grabado de pie con la cámara alta): tres ajustes de receta para que nada tape una cara. Sin ellos, todo sale como siempre.
- `"gancho": {"baja": 450}`: baja el antetítulo y el titular esos píxeles (al pecho, por encima de los subtítulos).
- `"chips": [{"items": […], "y": 650}]`: un grupo de pastillas a su propia altura (por defecto, `chips_y` o 200).
- `"logos": [{…, "x": 70}]` (y `"y"`): el logo deja de ir centrado; con dos personas, arriba a la izquierda sobre la cabeza de quien está a ese lado.
- Ojo también con la cuenta atrás del cámara («3, 2») al principio de la toma: suena bajita y `preparar.py` no la quita. Mídela y empieza el tramo donde arranca la voz.

**Movimiento de las piezas** (para que no parezca un PowerPoint). Toda tarjeta, rótulo, pizarra o carrusel animado:
- entra con curva y rebote al final (`back.out`), nunca lineal;
- si es una lista o un grupo, sus elementos entran escalonados (`stagger`), no todos a la vez;
- con capas, fondo, medio y frente se mueven a velocidades distintas (parallax);
- si la pantalla se queda quieta, lleva un micromovimiento constante (zoom lento o vaivén suave).

## Fuera del editor

| Qué | Decisión |
|---|---|
| Responder «Comenta PALABRA» por DM | Tu herramienta de mensajes automáticos (p. ej. ManyChat). La configura el creador; el editor no la monta. |
| Lo que se promete en la llamada (una guía, una checklist) | Tiene que existir antes de publicar. |
| Copiar un vídeo ajeno en plantilla | Descartado: es lo que ya hace este editor con sus recetas, y exigiría clonar código de terceros. |

## Piezas técnicas (`scripts/`)

- `gancho.py`: gancho, `datos` (número/`decimales`/`estrellas`/`destello`, `lista`, `cuentas`), `impactos`, `logos` (salen solos al decir la `frase` o un `alias`, 2,6 s arriba), `tarjetas` (`{"tipo": "youtube", "frase": "mi canal de YouTube"}`: tarjeta de suscripción con los datos de `marca/canal.json`; los suscriptores se escriben como YouTube, 12.345 → «12,3 mil»).
- `efectos.py`: `golpes` (`bn`, `tachado`, `alarma`, `magia`), `chips`, sellos «N/10», `conversacion`, `comentarios`, la caja «Comenta», la caja «pregunta» y la tarjeta «Sígueme».
- `ranking.py`: columna 1-10, icono que vuela, `sello`, `zoom_ritmo`, `cta` (`cta_x`, `cta_y`, `cta_w`).
  - `"aspecto": "completa"`: números grandes a toda la altura que no se borran; el elemento sale grande en el centro y se queda como miniatura junto a su número. Se ajusta con `grande`, `grande_x` y `grande_y`, y con `subtitulos.izq` ≈ 330 para no pisar la columna.
  - `"orden": "numero_primero"`: para cuando se dice «Diez. …» antes de describirlo.
  - Cada elemento admite `"imagen": "<archivo en assets/>"` (foto recortada) en vez de `icono`.
- `variantes.py`: genera y renderiza las variantes de `recetas/variantes.json` (claves de receta: `video_filtro`, `video_zoom`, `subtitulos.fuente`).
- `sfx.py`: whoosh, pop, tic, impacto, caja, subida, boom, glitch, error, magia; mezcla en una sola pista a −14 LUFS. Cada `assets/sfx/` guarda su banco en `BANCO`: el de los proyectos nuevos es **«variado»** (los WAV de `marca/sfx/earshot/` para whoosh, pop, tic e impacto; el mismo sonido no se repite a menos de 0,2 s y cada aparición cambia un poco de tono, ±3 %, y de volumen). «mezcla» y «ffmpeg» siguen sonando igual en los proyectos que ya los tenían.
- Receta: `subtitulos` (`izq`, `top`) para mover los subtítulos; `centro_cara` (de YuNet) para zoom y líneas.
- `zoom_lento: {"de": 1.0, "a": 1.12}`: acercamiento suave hacia `centro_cara` durante todo el vídeo. Admite `"tramos"` anclados a frases: se pausa donde la pizarra o la pantalla partida mueven el vídeo, y así no salta. No se combina con `impactos`.
- En una tarjeta `lista`, cada ítem admite `"icono": "x"` (aspa roja en vez de visto) y `"tachado": true` (texto tachado en rojo). Ejemplo: el mantra «✗ no es rápido · ✗ no es fácil · ✓ pero es posible».
- `"outro": "marca/outros/<archivo>.mp4"` (con `"seguir": false`): `entregar.py` pega el outro al final con destello blanco de 0,4 s, subida de aire y boom, y reajusta el total a −14 LUFS. Para shorts sacados de un vídeo largo.
- `comenta` (automática en vídeos de más de 12 s si la receta no lleva `"cierre"`): caja «COMENTA PALABRA · 📩 Revisa tus mensajes» abajo (y≈1232), bajo los subtítulos, 5,5 s. Aparece al decir «comenta» o, si no lo dice, justo antes de «Sígueme» o del outro. La palabra por defecto es la de `marca/marca.json`; se cambia con `{"palabra": "OTRA"}` y se quita con `false`. Solo palabras montadas.
  - `"estilo": "notificacion"`: en vez de la caja, una notificación de iPhone arriba (y=150) con tu foto de perfil, «tucuenta · ahora» y «Comenta PALABRA y revisa tus mensajes 📩». Mismo momento que la caja. Espera a que acaben un logo o una tarjeta de datos; si coincide con «Sígueme», la tarjeta baja; si arriba no queda hueco, sale la caja. Sirve para probarla contra la caja en variantes (A con caja, B con notificación) y comparar cuántos comentan. Sin logos de WhatsApp ni de Instagram. Texto propio con `"texto": "… {palabra} …"`.
- **Tarjeta «Sígueme»**: en todos los vídeos, «SÍGUEME EN @tucuenta» + los iconos de tus redes (`marca/redes/`). Sale al decir «sígueme» o, si no lo dice, en los últimos 3,5 s; se queda hasta el final si faltan menos de 12 s. Baja sola a la zona inferior (y≈1226, más pequeña) si arriba hay un logo, unas pastillas (`chips`) o una tarjeta de datos; en el ranking la caja «Comenta» le cede el sitio. Se quita con `"seguir": false`.
- `terminados.py`: nombre y carpeta de cada entrega (`"tema"`, `"variante"`, `"letra"` en la receta) y registro en `proyectos/_entregas.md`.
- `recorte.py` + `detras.py`: silueta con Vision y efectos detrás de la persona (`"detras"`).
- `captura.py`: foto de una web oficial y posición de cada texto buscado, para la escena `captura` (usa el Chrome y el puppeteer-core de HyperFrames 0.8.78).
- `pizarra.py`: modelo M11 (`"pizarra"`). Cada escena puede llevar su `"cara"` (`circulo` o `franja`). La cara viaja de un sitio a otro con transición, y con `respiros` y `final_completo` vuelve a pantalla completa (la «pizarra mixta», que es la Pizarra viajera).
- `prensa.py`: fotos con licencia y titulares reales con su fuente (`"prensa"`, E-64).
- `comentario.py` (python con OpenCV): captura → PNG con la foto de perfil difuminada (búsqueda automática o `--avatar`), `--recorte` y `--tapar` para quitar los botones. Lo llama `efectos.py` (pieza `"comentarios"`), que se niega con un DM.
- `guiones.py`: `publicar` (guion → PDF en «0 Guiones» de tu carpeta de trabajo), `pendientes` y `recoger` («0 Comentarios» → `guiones/<carpeta>/captura-N.jpg`).
- `revision.py` + `revision_pagina.html`: página de revisión de una muestra (opcional, como página privada de claude.ai). Piezas sacadas de los `.clip` de la composición y de la receta; marcas del creador en la base de datos de la página (`marcas`, `notas`, `envios`, `ajustes`). La pieza p00 es el caption y la portada 9:16 de `proyectos/<VIDEO>/caption.md`.
- `ajustes.py`: aplica a la receta los cambios hechos desde la página de revisión (`campos`, `aplicar`, `cambiadas`, `notas`, `heredar`, `probar`).
- `textos.py`: el `.txt` que acompaña a cada vídeo entregado. `--borrador` crea `caption.md` desde `plantillas/caption.md` (huecos `__ASI__`, como las recetas) y `--comprobar` revisa huecos, primera línea, palabra montada y portada 9:16.
- `efectos_indice.py`: índice de la biblioteca de efectos (`comprobar`, `usos`, `lista`, `receta`, `columna`, `elegidos`).
- `galeria.py`: clips de cada efecto y la página de la biblioteca (opcional).

Si analizas un reel de referencia, deja su análisis en `referencias/<nombre>/` (fuera de git) y, si sale una receta o un efecto nuevo, añádelo a este catálogo.
