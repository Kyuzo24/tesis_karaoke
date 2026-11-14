# Contrato de retroalimentación del backend

Versión 3.0.0 — 11 de octubre de 2026.

## Uso

`audio.karaoke.comparar_grabacion(cancion, ruta_grabacion)` conserva las métricas y el gráfico existentes, y añade `resultado["retroalimentacion"]`. Ese objeto se guarda en el mismo archivo `*_resultado.json`; la compensación y las explicaciones se guardan también en archivos derivados, que se eliminan junto con la toma. Ambas interfaces pasan por esta función al finalizar la grabación.

Para preparar el contexto de una explicación local a partir de una comparación recién calculada:

```python
from audio.retroalimentacion import preparar_contexto_modelo

contexto = preparar_contexto_modelo(resultado["retroalimentacion"])
```

Para consultar una toma guardada:

```python
from audio.tomas import obtener_contexto_retroalimentacion

contexto = obtener_contexto_retroalimentacion(cancion, toma_id)
# Consulta individual, con eventos y hallazgo del fragmento:
contexto_fragmento = obtener_contexto_retroalimentacion(cancion, toma_id, fragmento_id='f0003')
```

Las tomas antiguas sin retroalimentación o con versiones 1.0.0 y 2.0.0 se adaptan usando el pitch del usuario guardado, el pitch de referencia del catálogo y la duración del WAV. Se lee la voz de referencia para calcular los cortes, pero no se vuelve a extraer pitch ni se reescriben los resultados originales al leerlos. Se persiste la compensación automática o manual en un archivo derivado. Sin evidencia se informa la insuficiencia correspondiente. Una versión desconocida provoca `ValueError`.

## Segmentación aprobada

`audio.segmentacion` calcula límites sobre la referencia completa antes de recortarlos a la duración de la toma. Así, las tomas de una canción usan los mismos cortes. Se exige energía ≤−15 dB relativos al percentil 95 del RMS y ausencia de pitch positivo a 25 ms o menos. La energía usa bloques de 20 ms.

Se separa por pausas de al menos 0,2 s. Solo los bloques mayores de 15 s se subdividen con pausas de al menos 0,05 s (60 ms efectivos), escogiendo pausas centrales sin crear hijos menores de 1 s. Se conservan fragmentos cortos preexistentes. Si no existe corte válido, el bloque largo permanece. No se fuerza un máximo. La referencia sin actividad produce cero fragmentos; si no se proporciona ruta de voz, se usa el respaldo explícito de ventanas de 5 s. Una ruta proporcionada pero ilegible produce un error, no un cambio silencioso de método.

Los resultados reproducen exactamente los cortes revisados: Destello 13, Reik 36 y Sombra 14. La carga duplicada de Reik se excluye de las pruebas; no se borró del catálogo.

Este módulo de análisis no llama a servicios externos. La capa `audio.explicaciones` consume el contexto y construye la redacción exclusivamente con reglas y plantillas locales; ambas interfaces permiten consultar resultados sin cuentas ni claves. La configuración, caché y sincronización se describen en [conexion_llm_interfaz.md](conexion_llm_interfaz.md). No hay lectura en voz alta.

## Datos producidos

El campo adicional `musical` contiene notas estables, correspondencias, cobertura y porcentajes por nota. Es la fuente principal de la interfaz y de las plantillas. Cada fragmento incluye su subconjunto `musical`; los campos temporales anteriores se conservan como detalle técnico. El método se documenta en [conexion_llm_interfaz.md](conexion_llm_interfaz.md).

- `version`: versión del contrato y de las reglas.
- `metodo`: comparación, fuente, unidades implícitas en las claves, denominadores, parámetros y latencia no estimada.
- `calidad`: suficiencia de evidencia, entradas descartadas/duplicadas y limitaciones.
- `resumen_metricas`: segundos observados y comparables, cobertura, errores en cents y porcentajes.
- `fragmentos`: intervalos de referencia con tiempos, métricas, suficiencia y eventos locales.
- `hallazgos`: tipo, categoría, ID de fragmento, evidencia numérica y acción sugerida.
- `seleccion`: hasta dos fortalezas, tres aspectos por mejorar y tres limitaciones para la explicación breve.

El contexto conserva método, calidad y resumen global, los hallazgos seleccionados y `analisis_fragmentos`. Por fragmento incluye métricas y hasta tres eventos de cada categoría (fortaleza, aspecto por revisar y limitación): selecciona los de mayor duración y los entrega en orden temporal. Indica cuántos eventos omitió. Se puede consultar un solo fragmento para limitar la cantidad de datos; el resumen global permanece identificado como global. No incluye curvas de frecuencia, rutas, audio ni textos libres del usuario. Los hallazgos globales se seleccionan por cercanía, magnitud del error y limitaciones, respectivamente.

Cada evento identifica una racha continua de al menos 0,3 s: cercanía dentro de ±50 cents, desviación aguda/grave, discrepancia ≥600 cents, falta de detección del usuario o falta de referencia. Incluye ID, inicio, fin, métricas y acción sugerida. No se unen rachas a través de huecos ni se interpretan las discrepancias grandes como fallos vocales. La duración mínima es una heurística para evitar comentarios sobre fluctuaciones instantáneas. Los eventos son evidencia local, incluso si el fragmento completo tiene cobertura insuficiente; no autorizan una valoración de las partes no observadas.

El contrato de contexto permite resumen y detalle por fragmento. La capa de redacción usa solicitudes separadas de resumen y fragmento, con campos `resumen`, `aciertos`, `aspectos_a_revisar`, `practica_sugerida` y `limitaciones`. Cada afirmación local cita IDs de evento o hallazgo y cada recomendación una acción respaldada. No se rellenan aciertos o dificultades inexistentes. La capa externa valida estructura y referencias; esto no garantiza por sí solo la fidelidad semántica del texto generado.

## Método y diferencias respecto del resumen histórico

La comparación histórica `audio.comparacion.comparar` usa DTW sobre frecuencias y excluye diferencias de 1.000 cents o más. Sus campos siguen intactos para compatibilidad. **No se deben utilizar esos campos en las plantillas como si fueran las métricas de este nuevo contexto.**

El nuevo resumen agrega únicamente los fragmentos conservados. `metodo.segmentacion` incluye duración total de grabación y tiempo fuera de fragmentos, para no confundir duración analizada con duración total. Las pausas excluidas no se evalúan. El último fragmento se recorta al final de la toma; no se penaliza lo que sucede después de detener la grabación.

El flujo compartido aplica una compensación global automática cuando hay evidencia consistente y conserva los ajustes manuales. Los estados distinguen ajuste automático, manual, desactivación y estimación no concluyente. Una llamada aislada a `generar_retroalimentacion` sigue marcando `no_verificada`; el flujo completo pasa por `analizar_alineado`. La compensación no mide latencia del dispositivo ni distingue retraso técnico de retraso global al cantar.

La retroalimentación usa las coordenadas de referencia y desplaza los tiempos de usuario con la compensación guardada, sin DTW ni estiramiento temporal. Divide el tiempo en celdas de 20 ms; cada centro toma la observación más cercana de cada curva solo si está a 25 ms o menos. No interpola huecos largos. Una observación aislada puede representar hasta 50 ms: cobertura significa soporte temporal estimado, no anotación exacta de actividad vocal.

Las celdas finales se recortan al final del fragmento o de la grabación. Los segundos y porcentajes se ponderan por esa duración para no inflar la cobertura por densidad de muestras. Se preservan ceros explícitos; se descartan tiempos/frecuencias no finitos, tiempos negativos o posteriores al final y frecuencias negativas. Los tiempos se ordenan; en duplicados se conserva la última observación. Las longitudes incompatibles o duraciones inválidas producen `ValueError`. Se limita el análisis a cuatro horas y dos millones de celdas.

El error firmado es `1200 * log2(f_usuario / f_referencia)`: positivo significa más agudo, negativo más grave. No se descartan desviaciones grandes. Cada porcentaje de afinación usa **solo tiempo con pitch en ambas curvas**; la cobertura usa tiempo con pitch en la referencia. Un 100% de cercanía con una cobertura del 5% no significa que la interpretación completa esté afinada.

La fuente es el pitch final de archivos de referencia y usuario. Ese pitch puede haber sido filtrado y corregido en octava, y las referencias antiguas no tienen versión de extractor registrada. No se reutilizan las métricas de entrenamiento de YIN para atribuir confianza a una toma real.

## Reglas temporales de respaldo (detalle técnico)

Estos umbrales son reglas iniciales de producto, no un clasificador entrenado ni una escala de calificación validada.

| Regla | Condición |
|---|---|
| Referencia insuficiente | Menos de 0,5 s con referencia detectada. |
| Detección insuficiente | Menos de 1 s comparable o menos del 40% de cobertura. |
| Evidencia parcial | Evidencia evaluable sin alcanzar simultáneamente 80% de cobertura y 2 s comparables; la redacción se limita a los intervalos observados. |
| Evidencia suficiente | Al menos 2 s comparables y cobertura de al menos 80%. No implica certeza del detector. |
| Discrepancia grande | Con datos comparables suficientes, al menos 30% del tiempo comparable difiere 600 cents o más. Se pide revisar correspondencia y detección, no se atribuye automáticamente al cantante. |
| Afinación cercana | Con evidencia suficiente, al menos 85% del tiempo comparable está dentro de ±50 cents. |
| Tendencia aguda/grave | Con evidencia suficiente, una dirección concentra al menos 70% del tiempo fuera del margen y un segundo comparable. |
| Desviaciones frecuentes | Con evidencia suficiente, menos de 70% está dentro de ±100 cents y no se cumple una regla anterior. |

Si no hay un hallazgo respaldado, no se fuerza una fortaleza ni una dificultad. Los tramos sin referencia no se califican como silencios verdaderos. Las notas ausentes del detector no se califican como notas que el usuario omitió. No se deducen respiración, ritmo, técnica vocal, causas fisiológicas ni progreso entre tomas.

## Comprobación y ejemplos

```powershell
python -m unittest discover -s tests -v
python scripts/ejemplo_retroalimentacion.py
python scripts/verificar_feedback_fragmentos.py
```

El script crea una demostración sintética identificada como tal en `output/retroalimentacion_demo`, valida el contrato JSON y puede comprobar resultados históricos en modo de solo lectura. El esquema `docs/retroalimentacion.schema.json` acepta el informe completo o el contexto compacto; los IDs enlazados, las sumas de duraciones y la coherencia de la evidencia también se comprueban en pruebas funcionales. `jsonschema` se utiliza solo para verificar el contrato, no es una dependencia adicional de ejecución de la aplicación.

La comprobación histórica inicial con fragmentos validó tres referencias y 28 tomas. El catálogo ha cambiado desde entonces; la verificación actual de reglas y alineación examinó 22 tomas y se registra en `output/verificacion_reglas_alineacion.json`. Guarda ejemplos reales separados en `output/retroalimentacion_fragmentos`, sin alterar resultados originales. Los tests cubren pausas, notas suaves detectadas, bloques largos sin cortes forzados, recorte de tomas, eventos interrumpidos por falta de detección e integración en la comparación compartida.
