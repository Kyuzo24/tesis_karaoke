# Letras sincronizadas

La interfaz principal (`iniciar_live.bat`) muestra la letra encima del gráfico. En **Configurar letra** puedes buscar en LRCLIB por título y artista, elegir una versión comparando su álbum y duración, o importar un archivo UTF-8 `.lrc`.

Se guarda `canciones/<id>/letra.json` con el LRC original, las líneas interpretadas, la fuente y el ajuste temporal. Cantar no hace solicitudes de red. La consulta explícita a LRCLIB usa `/api/search`, sin cuenta ni clave, con un límite de espera de 12 segundos. Si no hay resultados sincronizados, se ofrece la importación; no se inventan tiempos para letras sin marcas.

Formato de ejemplo (texto de prueba):

```text
[00:05.00]Primera frase de prueba
[00:08.50]Segunda frase de prueba
[00:12.00]
```

Una línea vacía con marca temporal indica una pausa. Se admiten varias marcas en una línea, fracciones de uno a tres dígitos, metadatos y `[offset:...]` (convención LRC: un offset positivo adelanta los tiempos). El ajuste de la interfaz tiene su propio significado explícito: positivo retrasa la letra y negativo la adelanta.

La letra usa el tiempo de la canción durante la grabación y el tiempo compensado de la toma durante su revisión. El ajuste de letra no modifica audio, notas ni métricas. Se muestra la línea actual y la próxima; no hay resaltado por palabra. Si no se marca el final, la última línea permanece visible. Una grabación recortada o de otra versión puede necesitar editar el LRC; un desfase constante no corrige cambios de estructura.

La interfaz clásica Tk fue retirada el 27 de octubre de 2026. El parser y almacenamiento están en el backend compartido (`audio/letras.py`).

Validación: pruebas del parser y persistencia, prueba de interfaz con texto sintético (inicio, avance, pausa, retroceso, signo del ajuste), consulta real a LRCLIB y revisión visual del panel.
