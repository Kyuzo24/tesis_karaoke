# Karaoke Studio — tesis

Aplicación de escritorio para practicar canto, grabar interpretaciones y analizar la afinación frente a una referencia vocal. El proyecto incluye el código Python, la interfaz, pruebas, herramientas de evaluación y documentos de la tesis.

## Recuperar el trabajo en otro PC

**Estado del traslado:** el código y la documentación están en GitHub. Los ZIP de canciones, grabaciones, datasets y resultados se prepararon y verificaron localmente, pero su publicación en Releases falló por tiempos de espera de la conexión. Hasta confirmar esa publicación, el repositorio por sí solo no contiene esos datos. La copia local está en `.respaldo` en el PC de origen; conserva esa carpeta o cópiala a una unidad externa.

1. Inicia sesión en GitHub con la cuenta propietaria de este repositorio privado.
2. Descarga el código con **Code → Download ZIP**, o clona el repositorio con Git.
3. Abre [el respaldo de traslado](https://github.com/Kyuzo24/tesis_karaoke/releases/tag/respaldo-2026-11-14) y descarga todos sus archivos.
4. Extrae cada `proyecto-*.zip` en la raíz del código descargado. Cada ZIP es independiente; todos conservan las rutas originales. Esto restaura canciones, grabaciones, audios de entrada, datos de evaluación y resultados.
5. Extrae `perfil-aplicacion.zip` en `%LOCALAPPDATA%\Karaoke Studio` para recuperar los datos de la versión instalada y las preferencias.
6. Para usar la aplicación sin configurar Python, ejecuta `KaraokeStudio-1.0.2-Setup.exe`. Requiere Windows 10/11 de 64 bits. Si quieres usar las canciones y grabaciones del proyecto en la aplicación instalada, copia las carpetas `canciones`, `grabaciones` y `output` del proyecto a `%LOCALAPPDATA%\Karaoke Studio\Datos`, conservando las carpetas y archivos existentes. Algunas canciones conservan rutas hacia `output/htdemucs`.

El archivo `manifest-respaldo.json` registra tamaños y hashes SHA-256 de los archivos originales y de los ZIP. Conserva una copia de las descargas fuera del equipo antiguo antes de borrarlo o reinstalarlo.

## Continuar los chats de Codex

Lee [CONTEXTO_PARA_CODEX.md](CONTEXTO_PARA_CODEX.md) y [las instrucciones del historial](docs/contexto_codex/LEEME.md). Se exportaron los ocho chats de este proyecto, con transcripciones legibles y registros disponibles. Abre el repositorio en Codex en el nuevo PC y pide que los consulte para retomar el trabajo. Esta exportación no garantiza que aparezcan automáticamente los chats originales en la barra lateral.

## Trabajar en el código

El entorno de audio original utiliza Python 3.10. `requirements-entorno-original.txt` registra las versiones detectadas en el entorno de origen como referencia. Los entornos virtuales se deben recrear en el nuevo PC. Este inventario no es un archivo de bloqueo validado: el entorno original contiene dependencias con requisitos incompatibles declarados, como NumPy 1.26.4 y dtw-python 1.7.4, que declara NumPy >=2. Para recuperar una versión ejecutable con las dependencias empaquetadas, utiliza el instalador incluido en el respaldo.

```powershell
py -3.10 -m venv venv
```

Después de configurar las dependencias, el punto de entrada es `desktop_live.py` y el lanzador original es `iniciar_live.bat`.

Para la integración con YouTube, instala Python 3.11 o posterior y Node.js y ejecuta `instalar_youtube.bat`. Consulta [la documentación de la interfaz](ui_live/README.md).

## Contenido del respaldo

- Código, interfaz, pruebas, documentos y figuras: en Git.
- Canciones, grabaciones, audios de entrada, datasets, resultados, pistas separadas y perfil de la aplicación instalada: archivos ZIP en la descarga de respaldo.
- Instalador más reciente: descarga de respaldo.
- Entornos virtuales, cachés de Python, paquetes de compilación y versiones antiguas del instalador: se pueden regenerar y no se incluyen.

Los conjuntos de evaluación y resultados se restauran desde los ZIP; algunas herramientas de investigación pueden requerir dependencias adicionales registradas en el entorno original. Las rutas absolutas de informes antiguos pueden referirse al PC de origen.
