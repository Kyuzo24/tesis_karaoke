# Retroalimentación local y compensación temporal

Versión de análisis 3.0.0; reglas de redacción 2.0.0 y análisis de notas 1.0.0. 11 de octubre de 2026.

## Uso

Reiniciar con `iniciar_live.bat`. Resultado e Historial muestran las métricas, la explicación y los fragmentos. La interfaz actual utiliza el backend compartido. La interfaz clásica fue retirada el 27 de octubre de 2026. No hay llamadas a Ollama, OpenAI u otros servicios, ni configuración de claves o modelos. Los lanzadores ya no arrancan servidores de IA. Las variables antiguas de proveedor no reactivan servicios.

La compensación se calcula y aplica antes del análisis de cada grabación nueva. Al consultar una toma antigua se recalcula a partir del pitch guardado y la referencia del catálogo, sin extraer nuevamente pitch ni modificar el WAV o su resultado histórico. Se guardan únicamente archivos derivados de ajuste y explicaciones. Las versiones anteriores 1 y 2 se adaptan al contrato 3.

## Sincronización

Se busca un desplazamiento global entre −2 y +2 segundos: exploración cada 20 ms, refinamiento cada 5 ms. La resolución de búsqueda no equivale a precisión de medida. El objetivo utiliza cercanía de pitch (contribución lineal hasta 300 cents), un soporte temporal fijo y el mismo denominador de referencia detectada para todos los candidatos. La falta de coincidencia no desaparece del denominador. No se usa DTW ni se desplaza cada fragmento por separado.

Criterios heurísticos iniciales:

- Al menos 5 s de referencia y 5 s comparables en el mejor candidato.
- Al menos seis cambios de 80 cents o más, observados cada aproximadamente 100 ms.
- Al menos dos ventanas no superpuestas, cada una con 2 s de referencia y tres cambios. Hasta nueve ventanas repartidas por la toma.
- Mejora de al menos 0,03 sobre el objetivo sin ajuste.
- Margen sobre alternativas separadas al menos 120 ms: el mayor entre 0,015 y el 10 % de la mejora obtenida.
- Al menos dos tercios de las ventanas respaldan el desplazamiento dentro de 60 ms.
- Se rechazan candidatos a partir de ±1960 ms, cerca del extremo de búsqueda.

Cuando pasa todos los criterios se aplica automáticamente. En otro caso se conserva cero y se explica el motivo: evidencia insuficiente, ambigüedad, inconsistencia, límite o mejora insuficiente. No se presenta una probabilidad de confianza. El ajuste puede incluir tanto retraso técnico como retraso global al cantar.

**Modificar** permite aplicar un valor manual, desactivar o volver al automático. Positivo adelanta la voz grabada; negativo la atrasa. Un valor manual, incluido cero, prevalece sobre cualquier estimación futura. Se conservan los ajustes manuales anteriores. Volver al automático invalida la estimación guardada y vuelve a calcularla.

`*_alineacion.json` conserva modo, desplazamiento, versión, diagnóstico y huella de las curvas. Una nueva referencia o pitch invalida la estimación automática; la manual se conserva. El análisis expone `compensacion_temporal_s` y `alineacion`; `latencia_estimada_s` queda nulo, ya que no se mide latencia del dispositivo. Los extremos no capturados se excluyen de la evaluación y se contabilizan explícitamente. El audio y sus timestamps originales no se reescriben.

La escucha de un fragmento utiliza los límites de referencia más el desfase para localizar la voz original. En la interfaz web, la mezcla instrumental usa durante esa escucha la compensación del análisis; fuera de ese modo conserva el ajuste independiente del mezclador. El gráfico de tomas guardadas utiliza la misma compensación del análisis, sin un ajuste visual adicional.

## Comparación por notas y coherencia visual

`audio.notas_musicales` es la fuente común del resumen, los fragmentos, las explicaciones y los colores de las tomas guardadas en ambas interfaces. Las curvas originales no se reescriben. La comparación instantánea sigue en `metricas` como detalle técnico; los indicadores principales proceden de `musical.metricas`. Los históricos con DTW quedan desplegables en la interfaz web y ya no califican la toma en las tarjetas ni en el historial.

La extracción se realiza dentro de cada fragmento de referencia, después de compensar el desfase global:

- Rejilla de 10 ms y observación más cercana hasta 25 ms. No se atraviesan huecos de detección.
- Mediana de 50 ms; un cambio de al menos 0,8 semitonos debe persistir 100 ms para iniciar otra nota.
- Duración mínima de 120 ms. Se recortan hasta 40 ms en cada borde (como máximo aproximadamente un quinto de la nota) y se exige un núcleo de al menos 60 ms.
- La altura representativa es la mediana del núcleo sin redondearla a un semitono. Se omiten núcleos cuya dispersión entre percentiles 10 y 90 supera 150 cents.

Son parámetros iniciales, no una transcripción musical validada. Las transiciones y tramos inestables no reciben puntuación. Las repeticiones de una misma altura sin pausa detectable pueden quedar unidas. Los límites de fragmento también delimitan las notas detectadas.

El emparejamiento conserva el orden y utiliza cada nota del usuario como máximo una vez. Exige entradas separadas como máximo 250 ms y solapamiento de al menos 25 % de la duración de la nota más corta. Optimiza únicamente la proximidad temporal y el solapamiento: **no selecciona la pareja por lo bien que afine**. Las diferencias de octava y otras desviaciones grandes permanecen como diferencias. No hay estiramiento de tiempo ni corrección local de desfases. Los fragmentos excepcionalmente largos se procesan en lotes de 100 notas de referencia, preservando el orden entre lotes; esa aproximación puede perder una pareja en el límite de lote.

El porcentaje principal cuenta notas comparadas, no fotogramas ni segundos. Cada nota comparada pesa una vez. Se muestran dos márgenes: ±50 cents y ±100 cents. El resumen agrega las mismas notas que los fragmentos, sin promediar sus porcentajes. La cobertura es notas comparadas / notas estables de referencia; las no emparejadas no se cuentan como aciertos ni como errores. No representa la cobertura de todas las notas reales de la canción.

Las diferencias de inicio y duración se conservan separadamente en cada pareja; la mediana de diferencias de inicio se muestra como dato temporal, sin convertirla en calificación de ritmo.

En la web, los bloques de referencia usan las alturas medianas del backend y los colores del usuario usan exactamente la clasificación de las parejas: verde hasta 50 cents, amarillo hasta 100, rojo por encima, gris sin pareja. La línea blanca muestra la curva detectada; no es otra puntuación. El ajuste visual independiente queda desactivado para las tomas guardadas: se modifica la compensación en Sincronización y se recalculan todas las vistas. Durante la grabación en vivo sigue existiendo una visualización provisional.

## Reglas y plantillas

`audio.retro_notas` redacta exclusivamente a partir de las notas y sus parejas. Comunica conteos, cobertura, márgenes y limitaciones. Con menos de tres notas comparadas o cobertura menor al 40 %, no presenta una valoración representativa; mantiene observaciones locales. Entre 40 y 80 % indica cobertura parcial.

Selecciona como máximo un acierto, dos observaciones de direcciones distintas y una práctica. Cada observación cita una nota concreta y la diferencia de su altura mediana. Las discrepancias de 600 cents o más priorizan comprobar correspondencia y detección. No inventa fortalezas ni atribuye causas fisiológicas, salud, técnica o progreso entre tomas. El porcentaje no es una calificación global de interpretación.

Las reglas temporales anteriores se conservan para contextos técnicos sin análisis musical; no se usan en la redacción principal del flujo normal de las tomas.

## Persistencia y trazabilidad

`*_explicaciones.json` contiene versión de reglas y entradas identificadas por hash de contexto y versión. Cada entrada guarda contenido y trazabilidad: regla, plantilla, versión, valores utilizados, IDs de evidencia y acción sugerida. Un ajuste temporal cambia el contexto e invalida la entrada anterior. Nunca se reutilizan textos de antiguos proveedores de IA. Las escrituras son atómicas; si no puede guardarse una explicación, sigue disponible en pantalla.

El nombre heredado `preparar_contexto_modelo` se mantiene por compatibilidad, pero es un contrato de datos local y no llama a un modelo. `audio.explicaciones` valida que cada observación y práctica cite evidencia existente y acciones respaldadas.

## Métricas históricas

El indicador anterior utiliza DTW sobre frecuencias y excluye diferencias ≥1000 cents. La comparación por fragmentos utiliza tiempo compartido y conserva discrepancias grandes. No son porcentajes equivalentes. Aplicar un ajuste modifica la correspondencia de la evaluación, no demuestra que el usuario haya mejorado su interpretación.

## Verificación

`python -m unittest discover -s tests` cubre desfases conocidos positivos y negativos, notas sostenidas, repeticiones ambiguas, desfases variables, límites de búsqueda, caché, prioridad manual, extremos capturados, evidencia insuficiente y ausencia de red.

`scripts/verificar_reglas_alineacion.py` valida el contrato JSON y las explicaciones sobre las tomas existentes, sin reescribirlas. Guarda `output/verificacion_reglas_alineacion.json`. La validación inicial examinó 22 tomas: nueve ajustes aceptados y trece sin ajuste; no es una medición de exactitud con anotaciones humanas.

`scripts/verificar_interfaz.cjs` verifica la interfaz web real con un puente simulado: fragmentos, cambios de toma, modos automático/manual/desactivado, barra de preparación y ausencia de controles de IA. El tiempo de esta comprobación no representa el procesamiento completo de una grabación ni la separación de voces.

## Resultado de la toma revisada

En `usuario_20261010_182938` (Chasin You), con compensación de 255 ms, se comparan 43 de 68 notas estables: 60,5 % dentro de ±50 cents y 83,7 % dentro de ±100 cents, con cobertura de notas del 63,2 %. Las 25 sin pareja se informan explícitamente. El 42,1 % temporal y el 82,5 % histórico DTW miden otras cosas; el cambio no demuestra una mejora de la interpretación grabada ni una exactitud validada contra anotaciones humanas.
