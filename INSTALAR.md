# Instalar el editor (guía para Claude)

> **Claude:** esta guía es para ti. La persona que te la pasa es creadora de contenido y probablemente no programa.
> Léela entera antes de empezar. Ve paso a paso, explica cada paso en una frase sencilla, ejecuta tú los comandos y
> comprueba cada uno antes de pasar al siguiente. **Nada global sin preguntar:** no toques `~/.claude/settings.json`,
> ni skills globales, ni tareas programadas del sistema sin su sí.

## 0. Qué se instala

| Pieza | Para qué |
|---|---|
| **FFmpeg** | Cortar, unir, pasar a vertical y dejar el volumen a −14 LUFS |
| **whisper.cpp** (`whisper-cli`) | Transcribir palabra a palabra, en local y gratis |
| **Node.js** | Lo necesita HyperFrames |
| **HyperFrames 0.8.78** | Dibuja subtítulos, tarjetas y efectos (HTML + GSAP) y los renderiza con un Chrome sin ventana |
| **Python 3 + OpenCV, Pillow, numpy** | Encontrar la cara (YuNet), recortes y fotogramas |
| **yt-dlp** (opcional) | Bajar reels de referencia |
| Modelos (~550 MB) | Whisper large-v3-turbo y el detector de caras YuNet |

Coste: 0 €. Todo corre en el ordenador, sin suscripciones.

## 1. ¿Qué sistema tiene?

Pregúntalo o compruébalo (`uname -a`):

| Sistema | Estado |
|---|---|
| **Mac con chip Apple (M1 o posterior)** | **Verificado.** Todo funciona y usa el chip para el vídeo (VideoToolbox) |
| **Windows 11** | **Verificado con WSL2 y Ubuntu 26.04** (17-nov-2026): sigue los pasos de Linux. Camino de software (libx264 y zscale) |
| **Linux** (Ubuntu 22.04 o posterior) | Los mismos pasos que en WSL; en un Linux sin Windows aún no se ha probado |
| Mac con Intel | Sin probar; debería ir por el camino de software (`EDITOR_SIN_VT=1`) |

### Windows: antes de nada
1. **WSL2 con Ubuntu.** En PowerShell como administrador: `wsl --install -d Ubuntu` y reinicia.
   - Si dice `ERROR_ALREADY_EXISTS` aunque `wsl --status` diga que no está instalado, Ubuntu ya quedó registrado: sigue al punto 2.
2. **Abre «Ubuntu» desde el menú Inicio una vez** y deja que la persona cree su usuario y contraseña.
   Hasta entonces, cualquier `wsl -d Ubuntu -- …` se queda colgado en «Esperando a que se complete el comando OOBE»
   (si pasa: `wsl --terminate Ubuntu` y abre Ubuntu a mano).
3. **Trabaja siempre dentro de WSL:** el repo en `~/editor-videos-kit`, no en `/mnt/c/` (es mucho más lento).
4. **Si usas la app de Claude Code de Windows**, lanza cada comando con una shell de login:
   `wsl.exe -d Ubuntu -- bash -lc 'cd ~/editor-videos-kit && …'`. Con `bash -s` o sin `-l`, `~/.local/bin` no entra en el PATH.
   Las comillas anidadas de PowerShell → `wsl` → `bash` fallan: mejor desde Git Bash o con Claude Code instalado dentro de Ubuntu
   (las dos formas funcionan).

## 2. Programas

### Mac
Si no tiene Homebrew, instálalo desde https://brew.sh (pide su contraseña: que la escriba la persona).
```bash
brew install ffmpeg whisper-cpp yt-dlp node python
```
Para recortar la foto de las portadas (`scripts/portada.py`, solo Mac) también hace falta Swift:
```bash
xcode-select --install
```

### Linux / WSL2 (Ubuntu)
```bash
sudo apt update && sudo apt install -y ffmpeg python3 python3-venv git cmake build-essential curl unzip \
  libnss3 libnspr4 libasound2t64 libgbm1 fonts-liberation
```
(`unzip` y las librerías de la segunda línea los necesita el Chrome sin ventana de HyperFrames: sin ellos no baja o no arranca.)

Node 22 o posterior. Comprueba qué versión trae apt con `apt-cache policy nodejs`: en Ubuntu 24.04 o posterior suele valer
(`sudo apt install -y nodejs npm`). Si es más vieja:
```bash
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash - && sudo apt install -y nodejs
```
whisper.cpp se compila (unos minutos):
```bash
git clone --depth 1 https://github.com/ggml-org/whisper.cpp ~/whisper.cpp && cd ~/whisper.cpp && cmake -B build && cmake --build build -j --config Release
```
```bash
mkdir -p ~/.local/bin && ln -sf ~/whisper.cpp/build/bin/whisper-cli ~/.local/bin/whisper-cli
```
(Si `which whisper-cli` no lo encuentra, no pasa nada: los scripts lo buscan también en `~/.local/bin`.)

yt-dlp (opcional): `python3 -m pip install --user yt-dlp`.

HyperFrames usa un Chrome sin ventana. Si aun así el primer render falla diciendo que falta una `.so`
(`ldd` sobre el ejecutable que nombra el error dice cuál), instala el resto: `sudo apt install -y libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libasound2t64 libpango-1.0-0 libcairo2`.

### Versiones con las que está verificado
- Mac: FFmpeg 9.0.1 · whisper.cpp 1.9.5 · Node 26.5 · Python 3.9 a 3.15 · HyperFrames 0.8.78.
- Windows (WSL2, Ubuntu 26.04): FFmpeg 8.0.1 · whisper.cpp compilado · Node 22.22 · Python 3.14 · HyperFrames 0.8.78.

## 3. HyperFrames: no se instala, y tiene una trampa

Se usa siempre con `npx` y con una variable delante de **todos** sus comandos:
```bash
HYPERFRAMES_SKIP_SKILLS=1 npx --yes hyperframes@0.8.78 --version
```
**Sin `HYPERFRAMES_SKIP_SKILLS=1`, HyperFrames copia 19 skills de terceros a la carpeta global de Claude.**
Los scripts ya la ponen; tú ponla siempre que lo llames a mano. La primera vez tarda (baja Chrome).
HyperFrames avisará de que hay una versión más nueva y propondrá `upgrade`: **ignóralo**. El kit está probado con 0.8.78.

## 4. El repo, Python y los modelos

Dentro de la carpeta del repo:
```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```
```bash
mkdir -p models && curl -L -o models/ggml-large-v3-turbo-q5_0.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo-q5_0.bin
```
```bash
curl -L -o models/face_detection_yunet_2023mar.onnx https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx
```

## 5. Sus ajustes y su carpeta de trabajo

```bash
cp editor.ejemplo.json editor.json
```
Pregúntale dónde quiere la carpeta de trabajo (por defecto `~/Editor`). Si graba con el móvil, lo cómodo es una carpeta
que se sincronice con el móvil (iCloud Drive en iPhone + Mac, Google Drive o Dropbox en los demás): así deja ahí los
vídeos desde el teléfono. Escribe la ruta en `editor.json` → `carpeta_editor` y créala:
```bash
python3 scripts/kit.py carpetas
```

| Carpeta | Qué hay |
|---|---|
| `0 Referencias` | Reels que le gustan, para estudiar qué hacen |
| `0 Comentarios` | Capturas de comentarios de seguidores que se convierten en guiones (`/guion`) |
| `0 Guiones` | Guiones listos para leer en el móvil |
| `1 Para editar` | Vídeos en bruto |
| `2 Terminados` | La versión para publicar, una carpeta por vídeo con sus variantes A, B, C… |
| `3 Originales usados` | Los brutos ya procesados |
| `4 Publicados` | Lo que ya subió (lo mueve la persona) |
| `Recursos` | Tomas de apoyo, outros, música |

**Trampa de iCloud en Mac:** con «Optimizar almacenamiento» un vídeo puede ser solo un marcador sin descargar.
Antes de procesarlo: `brctl download <archivo>` y esperar a que tenga su tamaño real.

**Google Drive (u otra unidad) en Windows con WSL:** WSL no ve la unidad `G:` por sí solo.
```bash
sudo mkdir -p /mnt/g && sudo mount -t drvfs G: /mnt/g
```
```bash
echo 'G: /mnt/g drvfs defaults,nofail 0 0' | sudo tee -a /etc/fstab
```
- La carpeta de trabajo queda en `/mnt/g/Mi unidad/Editor` (ponla así en `editor.json`).
- Google Drive tiene que estar **abierto en Windows antes de arrancar Ubuntu**. Si no, la carpeta no aparece:
  ábrelo, `wsl --shutdown` en PowerShell y vuelve a abrir Ubuntu.
- Con Drive en modo «streaming», marca la carpeta `Editor` como «Disponible sin conexión».
- Los scripts copian sin fechas ni permisos, que Drive visto desde WSL no deja cambiar.

## 6. Su marca (la primera conversación)

Hazle estas preguntas, una a una, y rellena `marca/marca.json`:

1. **Usuario en redes** (sin @) y **nombre** con el que firma.
2. **Color de acento**: el color de la palabra que se está diciendo en los subtítulos y de los números de las
   tarjetas. Si tiene portadas, pídele dos o tres capturas y saca el color dominante de sus textos. Por defecto, amarillo `#FFC800`.
3. **Fuente de los subtítulos**: condensada y gruesa, en mayúsculas. Vienen Anton (por defecto), Bebas Neue, Barlow Condensed y Oswald
   en `marca/fuentes/`; en `marca.json` → `"fuente"` va su nombre tal cual. Los rótulos, tarjetas y carruseles siguen en Anton.
4. **Redes** donde está (para la tarjeta «Sígueme»): instagram, tiktok, youtube, facebook.
5. **Palabras de «Comenta X»** (y `palabra_por_defecto`, una de ellas): solo las que ya tenga montadas en una herramienta de mensajes automáticos
   (ManyChat u otra) que responde al comentario y manda un DM. **Si una palabra no está montada, nadie responde**: no la
   pongas. Si no tiene ninguna, deja `"palabras": {}` y borra `palabra_por_defecto`: usará los cierres sin palabra (pregunta + «te leo en los comentarios»).
6. **Su voz**: crea `marca/voz.md` con cómo habla (tuteo o usted, frases que repite, temas, lo que nunca diría, a quién
   le habla). Pídele 2-3 transcripciones de vídeos suyos que funcionaron y sácalo de ahí. Los guiones se escriben con esa voz.
7. Opcional: su foto para la tarjeta de YouTube en `marca/tarjetas/avatar-youtube.jpg` y los datos del canal en
   `marca/canal.json`; logos de marcas que nombre en `marca/logos/`; fotos suyas recortables en `marca/fotos/`.

Comprueba:
```bash
python3 scripts/kit.py
```
Tiene que decir su usuario, su acento, sus palabras, la carpeta de trabajo y «FFmpeg: listo».

## 7. Primer vídeo

1. Que grabe 30-60 s hablando a cámara (vertical, como siempre) y lo deje en `1 Para editar`.
2. Escríbele `/editor` y sigue la skill: prepara, busca tomas repetidas, propone el gancho de frase cortada y una
   receta del catálogo (`subtitulos/recetas/README.md`), saca la muestra y **no entrega nada sin su visto bueno**.

## 8. Lo que NO hay que hacer

- No quitar `HYPERFRAMES_SKIP_SKILLS=1` de ningún comando.
- No subir a git vídeos, audio, renders, modelos ni fotos de terceros (el `.gitignore` ya los deja fuera).
- No usar palabras de «Comenta» que no estén montadas.
- No tocar la configuración global de Claude sin preguntar.

## 9. Qué está probado

Probado en el kit, en un Mac, desde un clon limpio: instalación, preparar (cortar silencios y transcribir), receta
«Golpe y cuentas» con una marca distinta (otro usuario, otro color, sin palabras de «Comenta») y muestra final.
Las demás recetas (pizarras, ranking, top, titular detrás, sketch), el carrusel, la ruta y el reencuadre de entrevistas
salen de un editor que los usa a diario y sus composiciones son idénticas a las originales, pero dentro del kit todavía
no se han renderizado de principio a fin.

En Windows 11 con WSL2 (17-nov-2026) se instaló desde cero y se entregaron 2 vídeos de verdad con «Pizarra»
(también se renderizó una muestra de «Gancho titular»), con la carpeta de trabajo en Google Drive.

| Pieza | Mac | Windows (WSL2) |
|---|---|---|
| Instalar, preparar y transcribir | ✓ probado | ✓ probado |
| «Golpe y cuentas» | ✓ probado | sin probar |
| «Pizarra» y «Gancho titular», con entrega | sin probar en el kit | ✓ probado |
| Paso de HDR del iPhone a SDR | ✓ (VideoToolbox) | pendiente (zscale + tonemap) |
| Resto de recetas, carrusel, ruta, reencuadre | sin probar en el kit | sin probar |
| Recortar la foto de la portada (`portada.py`, Vision) | ✓ | no (solo Mac) |

Si algo falla, apúntalo en un issue del repo con el comando y el error.
