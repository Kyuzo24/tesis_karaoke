# Limpieza realizada — 27 de octubre de 2026

Tras autorización del usuario, se retiraron:

- Interfaz clásica: app.py, ui_feedback.py e iniciar_app.bat.
- Prototipos de mockups/ (cinco archivos).
- Entradas experimentales main.py y test.py.
- Cuatro funciones JavaScript antiguas de resumen.
- Botones generales ocultos de Biblioteca y sus referencias/eventos; las acciones por canción se conservan.
- Método antiguo LiveBackend.add_song, sustituido por add_song_from_file.
- extraer_pitch_desde_audio, sin consumidores; se conservan los extractores activos y usados por pruebas.
- Reglas CSS sobreescritas que ocultaban completamente el menú lateral.

El punto de entrada vigente es iniciar_live.bat (desktop_live.py y ui_live/).
Diagnóstico, compatibilidad con tomas antiguas, herramientas de evaluación, datos y documentos se conservan. Los generadores históricos de capítulos todavía describen versiones anteriores; no se reescribieron documentos académicos como parte de esta limpieza.

La revisión original se conserva debajo como antecedente, no como inventario vigente.

---

# Revisión de código residual — 27 de octubre de 2026

Revisión estática de los lanzadores, interfaces, backend, referencias desde pruebas y scripts. No se modificó código de ejecución. Diagnóstico queda expresamente fuera de los candidatos a retirar. No se clasifican audios, resultados, datasets ni documentos como código eliminable.

## Hallazgos confirmados en la interfaz actual

- `ui_live/app.js`: `tuningSummary`, `marginSummary`, `trendSummary` y `usefulVoiceSummary` solo tienen su definición; no hay llamadas en los JavaScript ni en el HTML. Construyen los antiguos textos de evaluación. Candidatas a retirar juntas; no afectan al cálculo actual.
- `ui_live/index.html`: los botones `editButton`, `reprocessButton` y `deleteButton` siguen en la cabecera que `review.css` oculta. `app.js` aún los registra, actualiza su estado y conecta sus eventos. Las acciones vigentes están en cada tarjeta. Retirar conjuntamente HTML, referencias `els`, cambios de estado y listeners; conservar las funciones de editar/reprocesar/eliminar.
- `ui_live/review.css`: reglas antiguas de ocultación completa de la barra lateral (`display:none`, columna de cero píxeles, desplazamiento -100%) están sobreescritas por las reglas posteriores de la barra de iconos. Consolidar las reglas finales, comprobando escritorio, ventana estrecha y movimiento reducido; no eliminar bloques de medios completos porque contienen propiedades todavía activas.

## Candidatos desconectados de los lanzadores actuales

- `desktop_live.py`, método `add_song`: flujo antiguo que abre el selector desde el backend. La interfaz actual usa `select_audio_file` y `add_song_from_file`. No se encontró consumidor dentro de las interfaces revisadas. Al ser un método público del puente, conviene conservar una nota de migración si se elimina.
- `main.py`: ejecución experimental con rutas fijas `data/referencia.wav` y `data/usuario.wav`; no aparece en los lanzadores. Ejecuta análisis al importarse, sin guardia `__main__`. Archivar como ejemplo o convertirlo en CLI explícita; no tratarlo como punto de entrada actual.
- `test.py`: importa dependencias y muestra un mensaje; no prueba comportamiento ni forma parte de `tests/`. Candidato a mover a herramientas de comprobación de instalación.
- `mockups/`: prototipos HTML separados; los lanzadores usan `app.py` o `desktop_live.py`, y la interfaz principal carga `ui_live/`. Material histórico, no ventanas activas. Archivar si ya no se necesita como referencia visual.
- `audio/pitch.py`, `extraer_pitch_desde_audio`: sin referencias encontradas en el código de aplicación, pruebas o scripts revisados. Revisar su utilidad como API experimental antes de eliminarla; no confundirla con las variantes ligera y detallada activas.

## Elementos que deben conservarse

- Diagnóstico, su navegación y sus funciones de referencia: excluidos por petición del usuario.
- `app.py` y `ui_feedback.py`: interfaz clásica con lanzador `iniciar_app.bat`. Que sea anterior no la convierte en código muerto.
- `desktop_live.py` y `ui_live/`: interfaz principal con lanzador `iniciar_live.bat`.
- `leer_ajuste`, `configurar` y `extraer_pitch_crudo`: tienen consumidores en pruebas; `configurar` documenta además compatibilidad y rechazo de proveedores externos. No se consideran muertos por falta de llamadas desde la interfaz.
- Scripts de datasets y evaluaciones: herramientas independientes; su ausencia en la navegación no indica desuso.
- Métricas históricas y lectura de resultados antiguos: compatibilidad existente, distinta de las cuatro funciones de presentación sin llamadas.

## Orden sugerido de limpieza

1. Retirar las cuatro funciones JavaScript y los controles ocultos, conservando las acciones por tarjeta.
2. Consolidar CSS de la barra lateral y verificar ambas anchuras.
3. Archivar prototipos y puntos de entrada experimentales, conservando su propósito documentado.
4. Evaluar APIs de compatibilidad por separado.

Esta revisión no demuestra ausencia de consumidores externos ni cubre código de dependencias. No se ejecutaron benchmarks ni se afirma una mejora de rendimiento: el beneficio esperado de la limpieza es reducir confusión y mantenimiento.
