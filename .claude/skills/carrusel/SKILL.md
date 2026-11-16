---
name: carrusel
description: Hace un carrusel animado de Instagram con la marca del creador (la de marca/marca.json), con portada fija y piezas de 7 s en bucle en 1080×1440, hecho con scripts/carrusel.py. Propone los puntos y los datos, los verifica con su fuente, escribe carruseles/<nombre>/carrusel.json, renderiza, revisa las hojas, enseña la muestra y entrega con el visto bueno. Úsala cuando el creador diga «/carrusel», «hazme un carrusel de…», «un carrusel urgente de esta noticia», «otro carrusel con lo nuevo» o mande una referencia de carrusel. No la uses para vídeos grabados (eso es /editor) ni para guiones (eso es /guion).
---

# carrusel

Carrusel animado: una **portada fija** (PNG) con el título y el índice, y una **pieza de 7 s por punto**, en bucle y sin voz. La ficha está en el catálogo (`subtitulos/recetas/README.md`, «Carrusel animado») y el motor es `scripts/carrusel.py`. Esta skill fija el **camino** y las trampas.

## Antes de nada
- Lee `CLAUDE.md` (regla de datos, cierres), `marca/marca.json` (su @, su color de acento, sus palabras de «Comenta») y `marca/voz.md` (si no existe, se crea en la primera sesión: `INSTALAR.md`, apartado «Su marca», con la plantilla `marca/voz.ejemplo.md`).
- Trabaja en la carpeta del repo, **no en un worktree**: la entrega escribe en su carpeta de entregas y en `proyectos/_entregas.md`.
- `HYPERFRAMES_SKIP_SKILLS=1` delante de todo comando que renderice.

## Las dos clases de carrusel
| | **De servicio** | **De posición** |
|---|---|---|
| Para qué | Explicar pasos, trámites, papeles u opciones | Opinión, luto o indignación ante una noticia |
| Ejemplos de tema | «5 trámites al llegar», «qué hacer si te pasa X» | «Hoy estamos de luto» tras una tragedia |
| Cierre | El que toque en la rotación: pieza «Comenta PALABRA» (`cta`) o pieza «Tu turno» (`cierre` sin palabra) | Sin llamada: `"cta": false` |
| Logo y foto | Su logo (o el de la marca con la que colabora) y su foto | En tragedias, `"logo": false` y `"foto": false` |
| Fuentes | Solo oficiales o primarias | Oficiales y medios, **cada uno con su nombre** |

## El camino (siempre este orden)

### 1. Proponer antes de animar
- Puntos del carrusel y los datos de cada uno, con su fuente. Espera el sí del creador antes de renderizar.
- **Estructura:**
  - **De 6 a 10 diapositivas, contando la portada y el cierre.** `carrusel.py` no deja pasar de 10.
  - **Portada:** promete un resultado con algo de tensión, en 6 palabras o menos.
  - **Antetítulo de la portada:** para quién es («Si acabas de empezar», «Si tienes cita la semana que viene»).
  - **La pieza 01 es una segunda portada.** Instagram vuelve a enseñar el carrusel desde la segunda diapositiva a quien no lo deslizó, así que la 01 tiene que entenderse sola: nada de introducciones.
  - **Una idea por pieza.**
  - **De servicio:** propón, antes del cierre, una pieza de resumen. Es la que se guarda en captura y se manda por mensaje.
- **Ganchos de portada que encajan** (con datos solo si están verificados en fuentes oficiales):
  - «Lo que nadie te dijo de [trámite o tema]»
  - «Haz esto antes de [empezar / pedir la cita]»
  - «[A] o [B]: la diferencia que nadie te explica»
  - «Si hoy empezara de cero, haría esto primero»
  - «Deja de [X]. Empieza a [Y]», para desmontar un mito con la voz de `marca/voz.md`
  - Fuera, los de cuentas de marketing: «crecer en 2026», «sin anuncios», «lo que aprendí tras N publicaciones» (salvo que su tema sea justo ese).
- **De posición (luto, tragedias):** nada de ganchos con tensión ni trucos de alcance. La portada dice lo que hay.
- **El cierre rota:** antes de proponerlo, `python3 scripts/cierre.py sugerir`. Los carruseles cuentan en la rotación, igual que los vídeos (nunca el mismo dos seguidos; como mucho 2 de embudo cada 7).
  - **Sin palabra** (info o conversación): `"cierre": {"tipo": "info", "pregunta": "¿…?"}`. Sale la pieza «Tu turno»: la pregunta, y con info alguien escribe «Quiero información» y el creador le responde.
  - **Con palabra** (una de `marca/marca.json`): `"cta": {"palabra": "…"}`, la pieza «Comenta» de siempre.
- Si es **noticia de última hora**:
  - **cifras de víctimas o afectados:** solo con quién las da y a qué hora («el presidente regional, 19:14»), y con el aviso «Cifra aún provisional»;
  - **la causa:** si no está confirmada, cada versión va atribuida (Gobierno, empresa, sindicatos) y marcada «Versión no confirmada»;
  - **la indignación pide respuestas, no señala a nadie** mientras no haya una causa oficial;
  - un luto oficial, solo si está en el boletín oficial (en España, el sumario del día del BOE está en `boe.es/boe/dias/AAAA/MM/DD/`);
  - en el pie: primero las personas, luego los datos. Nada de bulos («espera a la información oficial»).
- Las webs oficiales que cargan con JavaScript no se leen con curl ni con WebFetch: usa un navegador y `document.body.textContent`.

### 2. Escribir `carruseles/<nombre>/carrusel.json`
- **Copia la forma de un carrusel anterior** si el creador ya tiene alguno; si no, sigue esta lista y la cabecera de `scripts/carrusel.py`.
- **Arriba:** `tema` (el mismo que el de la entrega anterior si es otra variante: cae en la misma carpeta), `letra`, `paleta` (`"marca"`, su color de acento y negro, o `"logo"`, los colores del logo), y `logo`, `foto` y `cta` o `cierre` cuando haga falta.
- **`_nota` y `_fuentes`:** de dónde sale cada cifra, con la hora. Así se puede comprobar después.
- **`portada`:** `antetitulo` (para quién es), `titulo` y `fondo`. En el título de la portada `**así**` pinta en su color de acento.
- **`diapositivas`**, cada una con:
  - `antetitulo`, `titulo`, `pastilla` y `fondo` (`negro`, `crema` o `amarillo`, que sale en su color de acento);
  - `panel`: los bloques;
  - `texto`, con `**acentos**`;
  - `fuente` y `aviso`.
- **Bloques del panel:**
  - `campo` (etiqueta y valor que se escribe);
  - `checks` (lista que se marca);
  - `contador` (número que sube);
  - `precio`, `documento` (con `sello`), `tarjeta`, `calendario`, `huella` y `estado`;
  - `foto` (E-65): foto de apoyo que llena el panel por detrás, con su crédito. Ponla la primera del panel y, encima, como mucho un `contador` y un `campo`, que salen compactos abajo.
    - Fotos de Wikimedia Commons solo con licencia libre (CC0, dominio público, CC BY, CC BY-SA; nunca NC ni ND). La API de Commons frena si se busca muy seguido: deja unos segundos entre búsquedas.
    - Guárdalas en `carruseles/<nombre>/fotos/` (fuera de git) y anota título, página, autor, licencia y fecha en `fotos/fuentes.json` (en git). El autor va en el `credito` y en el pie.
    - Si lo importante de la foto queda tapado por las cifras, súbelo con `"foco": [x, y]` y, si hace falta, `"zoom": 1.5`. Míralo en la hoja.
- **El pie** es el caption:
  - con cierre de palabra, la llamada va en la primera línea, con «revisa tus mensajes»;
  - con cierre sin palabra, el gancho va en la primera línea y la pregunta al final, antes de los hashtags. Esa línea sale de `cierre.linea_caption` en `scripts/cierre.py`;
  - 5 hashtags como mucho.

### 3. Renderizar y revisar
```bash
HYPERFRAMES_SKIP_SKILLS=1 python3 scripts/carrusel.py <nombre> --hoja
```
- Sale en `out/carrusel_<nombre>/`: `00_portada.png`, `01.mp4`… y una `NN_hoja.png` por pieza.
- **Mira la portada y todas las hojas.** Para rehacer una sola pieza: `--solo 02`. Para probar la otra paleta en una pieza: `--paleta logo --solo 02`.
- Comprueba el movimiento: los bloques entran con rebote y escalonados, nunca todos a la vez.

### 4. Muestra y entrega
- Envíale la portada, las piezas y `pie.txt` para que lo vea en el móvil. No entregues nada sin su visto bueno.
- Con su sí:
  ```bash
  ENTREGA_APROBADA=1 HYPERFRAMES_SKIP_SKILLS=1 python3 scripts/carrusel.py <nombre> --entregar
  ```
  Copia a su carpeta de entregas, «<fecha tema>/<fecha tema> - <letra> carrusel - 00 portada.png, 01.mp4…, pie.txt», y apunta la fila en `proyectos/_entregas.md`.
- **Historias:** si las pide, `HYPERFRAMES_SKIP_SKILLS=1 python3 scripts/carrusel.py <nombre> --historias --hoja` → `out/carrusel_<nombre>_historias/` (9:16). Con su sí, `ENTREGA_APROBADA=1 HYPERFRAMES_SKIP_SKILLS=1 python3 scripts/carrusel.py <nombre> --historias --entregar`: letra siguiente, en la carpeta «<fecha tema> - historias». Solo con cierre sin palabra o `"cta": false` (en historias no hay comentarios).
- Para cambiar solo el pie de algo ya entregado: edítalo en el JSON y en `out/…/pie.txt`, y cópialo a mano a la carpeta de la entrega, con su permiso.
- Git, solo si lo pide: rama y pull request (`carruseles/<nombre>/`).

## Trampas conocidas
- **Los `**asteriscos**` solo funcionan en el título de la portada y en `texto`.** En el `titulo` de una pieza salen tal cual.
- **Con 7 a 9 piezas, el índice de la portada se apoya encima del @ y encoge la letra.** Si aun así el título de la portada no cabe, `carrusel.py` lo encoge solo hasta dejar 30 px de aire. Mejor en tres líneas como mucho.
- **Títulos largos de pieza:** `tam_titulo` ya los encoge, pero un título de más de unos 30 caracteres queda pequeño. Mejor corto.
- **`checks` pone marcas de verificación de color:** no lo uses para cifras de víctimas. Usa `contador` o `campo`.
- **En `cta`** solo van palabras de `marca/marca.json` (las que tiene montadas en su herramienta de mensajes automáticos). INFO no va en `cta`: es el cierre `"info"`, con la pieza «Tu turno».
