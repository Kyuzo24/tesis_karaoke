# Karaoke Studio UI

Interfaz de escritorio basada en el mockup `Live`, reorganizada en vistas de
trabajo para separar biblioteca, practica, resultados, historial y ajustes.

## Abrir

Usar el lanzador de escritorio:

```bat
iniciar_live.bat
```

No abrir `index.html` directamente para una sesion real. Si el archivo se abre en
un navegador normal, no tendra acceso al backend Python, al microfono ni a la
reproduccion con `sounddevice`.

## Estado actual

- organiza la aplicacion en vistas: Biblioteca, Practicar, Resultado, Historial y Ajustes
- carga canciones reales desde el catalogo Python
- busca canciones en YouTube Music y descarga su audio para prepararlas, o agrega un archivo local
- edita titulo y artista sin mover carpetas ni reprocesar audio
- elimina canciones del catalogo con confirmacion
- reprocesa la referencia vocal de la cancion seleccionada
- muestra la curva esperada antes de cantar
- muestra la referencia como bloques grisaceos y colorea el bloque del usuario segun precision
- agrupa los cuadros por nota estable para evitar bloques fantasma en transiciones
- permite ajustar la alineacion visual del usuario para diagnosticar desfases de latencia
- inicia la instrumental y la grabacion con `sounddevice.playrec`
- mide ruido ambiente antes de reproducir para filtrar sonidos de fondo
- recibe puntos de pitch del microfono mediante `pitch_callback`
- descarta saltos extremos en la curva en vivo
- corta el trazo visual cuando hay silencios entre notas
- permite detener y comparar solo el tramo grabado
- muestra el resultado final y el modo detalle
- refresca la curva del usuario cada 120 ms con ventanas de pitch de 0.32 s
- guarda cada grabacion como toma con audio, metricas y datos de grafico
- permite revisar tomas guardadas con previsualizacion de desempeno
- reproduce tomas con voz e instrumental sincronizadas, con mute y volumen por pista
- permite alternar la notacion de notas entre espanol e internacional

## Importar desde YouTube Music

En **Agregar canción**, busca por título y artista, selecciona un resultado y
confirma los datos. La aplicación descarga el audio, lo convierte a WAV y usa
la preparación habitual de voz, instrumental y notas de referencia. El progreso
aparece en el panel de preparación. También puedes elegir un archivo local.

Para instalar o actualizar el componente, ejecuta `instalar_youtube.bat` desde
la carpeta del proyecto. Requiere Python 3.11 o posterior y Node.js en PATH.
Se instala en `.youtube-env`, separado del entorno de audio Python 3.10.
FFmpeg se incluye mediante imageio-ffmpeg; no hace falta instalarlo globalmente.
La búsqueda usa [ytmusicapi](https://github.com/sigma67/ytmusicapi) sin iniciar sesión y filtra por canciones. Para descargar el audio utiliza [yt-dlp](https://github.com/yt-dlp/yt-dlp).

Se admiten videos de hasta 20 minutos y descargas de hasta 100 MB; no directos
ni contenido que exija iniciar sesión. Importa contenido propio o autorizado.
La disponibilidad depende de YouTube y puede requerir actualizar el componente.
No se utilizan cookies ni credenciales del navegador.

La biblioteca guarda la procedencia y evita duplicar el mismo video. Si falla
la preparación después de guardar el original, seleccionar otra vez ese video
reanuda la preparación sin descargarlo nuevamente. Mantén la aplicación abierta
durante la importación; la descarga no tiene un botón de cancelación.

## Pendiente

- permitir elegir manualmente dispositivos de entrada y salida
- afinar latencia/eco cuando la instrumental salga por parlantes
