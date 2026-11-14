from pathlib import Path

from docx import Document

from generar_capitulos_3_4 import (
    add_body,
    add_caption,
    add_figure,
    add_heading,
    add_placeholder,
    add_reference,
    add_table,
    add_title,
    configure,
)


ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / "docs" / "figuras"
OUTPUT_3 = ROOT / "Capitulo_3_Metodologia_version_especifica.docx"
OUTPUT_4 = ROOT / "Capitulo_4_Desarrollo_version_especifica.docx"


def build_chapter_3():
    document = Document()
    configure(document)
    add_title(document, "3. Metodología")
    add_body(document, "La metodología del proyecto debe responder a una dificultad concreta: no basta con implementar una secuencia de pantallas, porque el valor del sistema depende de que varias decisiones acústicas produzcan resultados defendibles. La separación de una canción puede dejar artefactos; un estimador de frecuencia fundamental puede perder bloques o saltar de octava; DTW puede alinear regiones incorrectas; y una redacción fluida puede ser incoherente con las métricas. Por esta razón, el trabajo se organiza en incrementos cuyo cierre exige evidencia técnica, además de funcionamiento visible.")
    add_body(document, "El capítulo describe una adaptación de Personal Extreme Programming (PXP) al desarrollo individual de software experimental de audio. La adaptación integra requisitos, historias de usuario, hipótesis técnicas, artefactos reproducibles y criterios de aceptación. También define cómo se evaluarán la estimación de pitch, la latencia, la alineación, los segmentos y la fidelidad de la retroalimentación.")

    add_heading(document, "3.1. Estrategia metodológica", 1)
    add_heading(document, "3.1.1. Adaptación de PXP al proyecto", 2)
    add_body(document, "PXP fue seleccionado porque permite que una sola persona mantenga planificación, registro de esfuerzo, iteraciones breves, pruebas y refactorización. Su flexibilidad resulta pertinente cuando una prueba técnica puede invalidar una decisión previa. Por ejemplo, una biblioteca puede extraer pitch con buena cobertura fuera de línea, pero no cumplir la latencia requerida durante la captura. En ese caso, la iteración no se cierra por haber integrado la biblioteca; se reabre la hipótesis y se prueba otra configuración o estrategia [30].")
    add_body(document, "La unidad de avance no será solamente una historia de usuario terminada. Cada incremento deberá vincular: a) un requisito o riesgo; b) una hipótesis técnica; c) una modificación identificable del sistema; d) audios o datos de prueba; e) una medición; y f) una decisión de aceptación o ajuste. Esta regla busca evitar que una función aparezca completa en la interfaz mientras su comportamiento acústico continúa sin validar.")
    add_figure(document, FIGURES / "figura_3_1_iteracion_evidencia_v2.png", "Figura 3.1: Iteración orientada por evidencia técnica. Fuente: elaboración propia.")

    add_heading(document, "3.1.2. Evidencia de aceptación por capacidad", 2)
    add_body(document, "Los 45 requisitos se mantienen en sus fichas individuales, pero dentro de la metodología se agrupan por capacidad y por evidencia necesaria. Esta integración evita repetir las especificaciones y permite observar qué impide realmente cerrar cada grupo. El Cuadro 3.1 diferencia la evidencia disponible al finalizar el primer semestre de la evidencia que aún falta producir.")
    add_table(document,
        ["Capacidad", "Requisitos", "Evidencia actual", "Condición para cerrar"],
        [
            ("Preparación de canciones", "RF01–RF06", "metadata.json, stems de Demucs, instrumental.wav y ref_pitch.csv.", "Probar reutilización, reprocesamiento y error de separación con audios distintos."),
            ("Sesión de canto", "RF07–RF15", "Reproducción y grabación mono a 44,1 kHz; WAV fechado; cursor de referencia.", "Sustituir análisis posterior por captura de bloques y demostrar latencia inferior a 150 ms."),
            ("Comparación", "RF16–RF17", "DTW inicial y JSON con error, dispersión, tendencia y tolerancias.", "Validar la trayectoria, medir en escala tonal y conservar correspondencias temporales."),
            ("Segmentos", "RF18–RF20", "Modelo conceptual y métricas locales definidas.", "Comparar segmentos detectados con intervalos anotados y justificar categorías."),
            ("Retroalimentación", "RF21–RF23", "Contrato conceptual de hallazgos estructurados.", "Verificar que cada afirmación corresponda con tiempos, categoría y evidencia guardada."),
            ("Evolución", "RF27–RF29", "Dos grabaciones y resultados asociados con una misma canción.", "Versionar referencia y configuración antes de comparar mejoras o persistencias."),
        ], [3.4, 2.4, 5.5, 5.3], 8)
    add_caption(document, "Cuadro 3.1: Evidencia requerida para aceptar las capacidades principales. Fuente: elaboración propia.")
    add_body(document, "Los requisitos transversales se comprueban en los mismos incrementos. RNF05 fija una latencia objetivo inferior a 150 ms; RNF10 exige mantener grabaciones locales salvo autorización; RNF11 y RNF12 obligan a conservar la relación entre mensajes y evidencia; y RNF14 exige detectar fallas de Demucs o de un posible LLM. Por tanto, estos requisitos no se validarán en una etapa separada al final, sino como condiciones de aceptación de las funciones relacionadas.")

    add_heading(document, "3.1.3. Dependencias entre iteraciones", 2)
    add_body(document, "La secuencia de iteraciones responde a dependencias de información. No es posible detectar segmentos antes de conservar una alineación temporal; no es posible generar retroalimentación explicable antes de estructurar esos segmentos; y no es válido comparar la evolución si dos sesiones fueron procesadas con referencias o configuraciones incompatibles. La planificación prioriza estas dependencias por sobre una distribución uniforme de funciones.")
    add_table(document,
        ["Iteración", "Pregunta que debe responder", "Incremento", "Puerta de salida"],
        [
            ("1. Preparación", "¿Puede una canción convertirse en referencia y acompañamiento reutilizables?", "Catálogo, Demucs, instrumental y pitch filtrado.", "Artefactos persistentes y reprocesables."),
            ("2. Captura", "¿Puede registrarse una interpretación sincronizada sin bloquear la aplicación?", "playrec, WAV, cursor y comparación posterior.", "Flujo completo estable; tiempo real queda como deuda explícita."),
            ("3A. Tiempo real", "¿Puede estimarse una nota dentro de 150 ms durante toda la canción?", "InputStream, bloques, confianza y estabilización.", "Distribución de latencia y tasa de bloques válidos."),
            ("3B. Análisis", "¿La comparación conserva correspondencias suficientemente confiables?", "DTW en cents, trayectoria, métricas locales y segmentos.", "Acuerdo con intervalos revisados manualmente."),
            ("4. Comunicación", "¿Los hallazgos pueden explicarse y compararse sin inventar información?", "Plantillas/LLM, persistencia versionada e historial.", "Trazabilidad completa y aceptación de usuarios."),
        ], [2.4, 5.4, 5.0, 4.0], 8)
    add_caption(document, "Cuadro 3.2: Dependencias y puertas de salida de las iteraciones. Fuente: elaboración propia.")

    add_heading(document, "3.1.4. Tratamiento de decisiones abiertas", 2)
    add_body(document, "La interfaz gráfica, SQLite, el ejecutable y el LLM no se tratarán como un único paquete de decisiones. Cada alternativa responde a un problema diferente y tendrá un experimento acotado. La interfaz se decidirá según esfuerzo de migración y capacidad de presentar gráficos y segmentos; SQLite se evaluará según complejidad de consultas históricas; PyInstaller según tamaño y reproducibilidad; y el LLM según fidelidad, recursos y privacidad.")
    add_table(document,
        ["Decisión", "Alternativas", "Criterios", "Momento de resolución"],
        [
            ("Interfaz", "Mantener Tkinter o migrar a Qt for Python.", "Reutilización de lógica, gráficos, esfuerzo y distribución.", "Después de estabilizar contratos del análisis."),
            ("Persistencia", "Archivos estructurados o SQLite + archivos de audio.", "Versionado, consultas, integridad y migración.", "Antes de implementar historial."),
            ("Retroalimentación", "Plantillas, LLM local o servicio remoto.", "Fidelidad, latencia, memoria, privacidad y licencia.", "Después de validar segmentos."),
            ("Distribución", "Proyecto Python o paquete PyInstaller.", "Tamaño, dependencias nativas, modelos y repetibilidad.", "Cuando la tecnología final esté cerrada."),
            ("Diagnóstico", "Herramienta visible o función interna.", "Utilidad para explicar filtrado y costo de mantenimiento.", "Después de las pruebas de pitch."),
        ], [3.0, 5.0, 5.2, 3.6], 8)
    add_caption(document, "Cuadro 3.3: Decisiones abiertas y criterios de resolución. Fuente: elaboración propia.")

    add_heading(document, "3.2. Diseño de evaluación", 1)
    add_heading(document, "3.2.1. Conjunto de pruebas", 2)
    add_body(document, "Un único tipo de audio no permite atribuir correctamente los errores. Se utilizarán cuatro estratos de prueba. Las señales controladas permiten conocer la nota y el tiempo esperados; las voces aisladas permiten evaluar el estimador sin acompañamiento; las interpretaciones reales permiten observar variaciones naturales; y las condiciones degradadas permiten comprobar que el sistema prefiera informar datos insuficientes antes que entregar resultados engañosos.")
    add_table(document,
        ["Estrato", "Contenido", "Uso", "Variable controlada"],
        [
            ("A. Sintético", "Tonos, escalas, silencios y cambios de nota generados.", "Precisión de F0, saltos de octava y latencia.", "Frecuencia, inicio, duración y amplitud."),
            ("B. Voz limpia", "Fragmentos vocales o stems sin acompañamiento.", "Cobertura y estabilidad del estimador.", "Ruido y filtración instrumental reducidos."),
            ("C. Canto real", "Repeticiones de una misma canción por sesión.", "DTW, segmentos, retroalimentación e historial.", "Canción y referencia compartidas."),
            ("D. Condición degradada", "Ruido moderado, silencios, baja energía y filtración.", "Robustez y manejo de datos insuficientes.", "Nivel y tipo de degradación."),
        ], [2.7, 5.1, 5.0, 4.0], 8)
    add_caption(document, "Cuadro 3.4: Estratos del conjunto de pruebas. Fuente: elaboración propia.")

    add_heading(document, "3.2.2. Experimento de estimación y filtrado de pitch", 2)
    add_body(document, "La evaluación separará el estimador crudo del filtrado posterior. Para cada archivo se registrará la cantidad de puntos crudos, puntos conservados, error en cents respecto de la referencia conocida y regiones donde se perdieron notas. La conservación por sí sola no implica calidad: mantener muchos puntos ruidosos puede empeorar el análisis, mientras que un filtro demasiado agresivo puede eliminar ataques y notas breves.")
    add_body(document, "Los parámetros actuales —rango A1–C7, umbral RMS, relleno de huecos de hasta cinco marcos, duración mínima de dos marcos, mediana de siete marcos y rechazo de saltos superiores a nueve semitonos— se tratarán como una configuración inicial. Se compararán configuraciones sin modificar varias variables simultáneamente y se almacenará la versión utilizada. También deberá unificarse el rango del filtro con el fallback pYIN, que actualmente comienza en C2.")

    add_heading(document, "3.2.3. Experimento de detección en tiempo real", 2)
    add_body(document, "El prototipo actual utiliza sounddevice.playrec y analiza el WAV al finalizar; por tanto, no constituye evidencia de RF10–RF12. La prueba de tiempo real requiere una captura basada en callback o InputStream. Cada bloque conservará el instante de entrada, el instante en que se obtiene F0 y el instante en que la nota queda disponible para la presentación.")
    add_body(document, "La latencia se calculará desde la disponibilidad del bloque hasta la salida estabilizada. Se informarán mediana, percentil 95 y máximo, además de la proporción de bloques que cumplen 150 ms. También se medirá continuidad durante una canción completa y se observará si la cola de procesamiento crece. El requisito se aceptará únicamente si la nota permanece disponible sin interrupciones perceptibles y la distribución respalda RNF05 y RNF07.")

    add_heading(document, "3.2.4. Experimento de alineación y segmentación", 2)
    add_body(document, "La implementación actual ejecuta DTW directamente sobre frecuencias en Hz y utiliza la trayectoria solo para calcular errores. El experimento comparará este comportamiento con una distancia calculada en cents o MIDI, debido a que una diferencia en Hz no representa el mismo intervalo en registros distintos. Para un subconjunto de canciones se marcarán manualmente inicios de frases o notas, y se revisará si la trayectoria relaciona regiones equivalentes.")
    add_body(document, "Una vez validada la trayectoria, se anotarán intervalos con desviación sostenida, ausencia de voz o inestabilidad. Los segmentos automáticos se compararán mediante solapamiento temporal, precisión, exhaustividad y error en sus límites. Los umbrales de magnitud y duración se fijarán después de una prueba piloto; no se establecerán solo para obtener una cantidad conveniente de hallazgos.")

    add_heading(document, "3.2.5. Evaluación de retroalimentación e historial", 2)
    add_body(document, "Cada mensaje se evaluará contra el registro estructurado que lo originó. Los tiempos, magnitudes y categorías mencionados deberán coincidir; una recomendación no podrá atribuir causas respiratorias, fisiológicas o clínicas. Para un eventual LLM se repetirá la misma entrada varias veces con el fin de detectar variabilidad y se comparará su salida con una plantilla determinista.")
    add_body(document, "La evaluación con usuarios distinguirá comprensión de corrección. Primero se preguntará si el usuario puede localizar el segmento y explicar qué observó el sistema; después, una revisión experta podrá valorar si la categoría acústica es razonable. La comparación histórica se probará solo con sesiones que compartan identificador y versión de referencia, configuración de análisis y canción.")

    add_heading(document, "3.2.6. Pruebas funcionales y regresión", 2)
    add_body(document, "Las pruebas funcionales se derivarán de las fichas de requisitos y se conservarán como regresión. Un flujo exitoso no será suficiente: deben incluirse canciones duplicadas, archivos incompatibles, stems ausentes, micrófono no disponible, grabaciones sin pitch, DTW sin puntos comparables, resultados antiguos y fallas de componentes externos.")
    add_table(document,
        ["Caso crítico", "Riesgo", "Comportamiento exigido"],
        [
            ("Demucs falla o no está instalado.", "Canción marcada falsamente como preparada.", "No activar preparada; conservar error y permitir reintento."),
            ("El micrófono no entrega datos.", "WAV vacío o bloqueo de interfaz.", "Detener la sesión, informar y volver a estado estable."),
            ("No existe pitch suficiente.", "Métricas aparentemente precisas sin evidencia.", "Resultado 'sin datos' y cero puntos comparados."),
            ("Se reprocesa la referencia.", "Historial incompatible silenciosamente.", "Crear nueva versión o marcar sesiones no comparables."),
            ("El generador textual falla.", "Pérdida de resultados acústicos.", "Conservar hallazgos y usar plantilla o mensaje controlado."),
        ], [4.0, 5.5, 6.5], 9)
    add_caption(document, "Cuadro 3.5: Casos funcionales críticos y comportamiento esperado. Fuente: elaboración propia.")

    add_heading(document, "3.2.7. Reproducibilidad y registro", 2)
    add_body(document, "Cada ejecución experimental deberá registrar archivo de entrada, canción, fecha, versión de referencia, estimador utilizado, parámetros del filtro, versión del algoritmo de alineación y código del experimento. Los audios originales no se sobrescribirán. Los resultados derivados podrán regenerarse, pero deberán conservar un identificador de configuración para evitar comparaciones entre procesos distintos.")

    add_heading(document, "3.3. Estado metodológico actual", 1)
    add_body(document, "La primera mitad del proyecto demuestra el flujo de preparación y una comparación completa posterior a la sesión. También ofrece una herramienta que cuantifica cuántos puntos de pitch sobreviven al filtrado. Sin embargo, estos artefactos constituyen evidencia de integración, no una validación de precisión general. La siguiente puerta metodológica es demostrar captura por bloques y decidir una representación de alineación que pueda sostener segmentos temporales.")
    add_body(document, "El avance de 35,6 % se conserva como medida administrativa basada en requisitos completados. Para las iteraciones siguientes se complementará con evidencia por capacidad, porque dos requisitos pueden demandar esfuerzos y riesgos muy diferentes.")

    add_heading(document, "3.4. Amenazas a la validez", 1)
    add_body(document, "Las principales amenazas son la cantidad limitada de voces, el sesgo introducido por la separación de la canción original, la variación entre micrófonos y habitaciones, y la ausencia inicial de anotaciones expertas. También existe riesgo de ajustar umbrales a pocas grabaciones del desarrollador. Para reducirlo, se separarán datos de ajuste y prueba, se documentarán condiciones acústicas y se evitará presentar una métrica global como diagnóstico completo de calidad vocal.")

    add_heading(document, "3.5. Síntesis del capítulo", 1)
    add_body(document, "La versión metodológica propuesta convierte PXP en un ciclo de hipótesis, incremento, prueba y decisión. Los requisitos se integran mediante evidencia concreta y puertas de salida, mientras las decisiones abiertas se resuelven después de estabilizar sus dependencias. El diseño de evaluación separa estimación, tiempo real, alineación, segmentación, redacción e historial para que los errores puedan atribuirse al componente correspondiente.")

    add_heading(document, "Referencia incorporada", 1)
    add_reference(document, 30, "S. A. Asri, I. G. M. A. Sunaya, P. M. Prihatini y W. Setiawan, “Comparing Traditional and Agile Software Development Approaches: Case of Personal Extreme Programming,” Proceedings of ICST 2018, 2018. Disponible en: https://www.atlantis-press.com/article/55910901.pdf.")
    document.save(OUTPUT_3)


def build_chapter_4():
    document = Document()
    configure(document)
    add_title(document, "4. Desarrollo")
    add_body(document, "El desarrollo actual no corresponde todavía a la arquitectura objetivo completa. Existe un flujo local capaz de preparar una canción, grabar una interpretación, extraer pitch, alinear secuencias y guardar métricas; sin embargo, la nota se calcula después de grabar, la trayectoria DTW no se conserva y las sesiones no registran versiones de referencia. Este capítulo describe el sistema a partir de esa realidad, separando lo implementado de las extensiones necesarias.")

    add_heading(document, "4.1. Arquitectura derivada del entorno de ejecución", 1)
    add_heading(document, "4.1.1. Despliegue físico", 2)
    add_body(document, "El prototipo se ejecuta en Windows como un proceso Python iniciado desde app.py. Tkinter atiende eventos y utiliza hilos daemon para que la separación, el reprocesamiento y la grabación no bloqueen el ciclo gráfico. La captura y reproducción se realizan en el mismo equipo mediante sounddevice; la pista instrumental se remuestrea a 44,1 kHz y el micrófono se registra en un canal float32.")
    add_body(document, "Demucs se ejecuta como subproceso. Cuando existe el entorno incluido en el proyecto, el comando utiliza py -3.10 -m demucs y añade sus site-packages al PYTHONPATH; en otro caso emplea el intérprete activo. Esta diferencia explica por qué empaquetar la aplicación no consiste únicamente en convertir app.py a ejecutable: el proceso externo, los modelos, PyTorch y las bibliotecas nativas de audio también deben resolverse.")
    add_figure(document, FIGURES / "ilustracion_arquitectura_fisica_drawio.png", "Figura 4.1: Arquitectura física de ejecución local. Fuente: elaboración propia.")

    add_heading(document, "4.1.2. Arquitectura lógica actual", 2)
    add_body(document, "La arquitectura existente está organizada en módulos Python, aunque app.py todavía conoce directamente numerosas operaciones. catalogo.py controla el ciclo de vida de una canción; separacion.py prepara stems; pitch.py estima y filtra F0; karaoke.py coordina reproducción, captura y análisis posterior; comparacion.py ejecuta DTW; metricas.py resume errores; guardar.py escribe la referencia; y visualizacion.py transforma frecuencias a notas MIDI para los gráficos.")
    add_body(document, "La Figura 4.2 representa dos líneas. La línea continua muestra los módulos existentes o parciales. La discontinua muestra las extensiones que deben incorporarse: captura por bloques, conservación de una trayectoria tonal, segmentos verificables, retroalimentación controlada e historial versionado. Esta distinción evita que la arquitectura objetivo sea interpretada como implementación terminada.")
    add_figure(document, FIGURES / "ilustracion_arquitectura_logica_drawio.png", "Figura 4.2: Arquitectura lógica actual y extensiones pendientes. Fuente: elaboración propia.")

    add_heading(document, "4.1.3. Flujos de ejecución", 2)
    add_body(document, "El sistema posee dos flujos principales. El primero prepara una canción: se genera un identificador a partir del título y un sufijo UUID, se copia el audio al catálogo, se crea metadata.json, se ejecuta HT Demucs, se suman drums, bass y other para producir instrumental.wav, se extrae pitch desde vocals.wav y se escribe ref_pitch.csv. Si los stems existen y no se fuerza el reprocesamiento, se reutilizan.")
    add_body(document, "El segundo flujo comienza al cantar. karaoke.py carga el instrumental a 44,1 kHz, ejecuta playrec y consulta cada 100 ms si terminó la pista o se solicitó detener. El WAV se recorta a la duración registrada. Después se extrae el pitch del usuario, se limita la referencia a esa duración, se ejecuta DTW y se guarda un JSON junto al WAV. El cursor que avanza durante la canción representa tiempo de reproducción; no es todavía una nota detectada en tiempo real.")
    add_table(document,
        ["Flujo", "Entrada", "Procesamiento", "Artefactos"],
        [
            ("Preparación", "Archivo WAV, MP3, FLAC, OGG o M4A; título y artista.", "Catálogo → Demucs → mezcla instrumental → F0 → filtrado.", "metadata.json, vocals.wav, instrumental.wav y ref_pitch.csv."),
            ("Sesión", "Canción preparada, micrófono y señal de detención.", "playrec → WAV → F0 → DTW → métricas → gráfico.", "usuario_<fecha>.wav y usuario_<fecha>_resultado.json."),
            ("Diagnóstico", "Voz separada y grabación reciente opcional.", "F0 crudo → filtro → comparación de cobertura.", "Conteo, porcentaje y curvas crudo/filtrado en memoria."),
        ], [2.7, 4.7, 5.4, 4.2], 8)
    add_caption(document, "Cuadro 4.1: Flujos y artefactos producidos por el prototipo. Fuente: elaboración propia.")

    add_heading(document, "4.1.4. Modelo de datos", 2)
    add_body(document, "El modelo definitivo deberá distinguir datos de origen, datos derivados y versiones de procesamiento. Canción representa la identidad estable; Referencia representa una preparación concreta de esa canción; Sesión utiliza una versión de referencia; Resultado utiliza una versión de análisis; y Segmento conserva evidencia y límites temporales. Esta distinción es necesaria porque regenerar ref_pitch.csv modifica actualmente la referencia en el mismo archivo y podría volver incomparables resultados antiguos sin dejar registro.")
    add_body(document, "El diagrama elaborado por el autor deberá considerar al menos Canción, Referencia, Sesión, Resultado, Métrica, Segmento y Retroalimentación, además de los identificadores de configuración. Los audios pueden mantenerse fuera de SQLite y relacionarse mediante rutas. Se reserva el siguiente espacio para incorporar ese modelo.")
    add_placeholder(document)

    add_heading(document, "4.2. Implementación y decisiones actuales", 1)
    add_heading(document, "4.2.1. Identidad y ciclo de una canción", 2)
    add_body(document, "catalogo.py crea identificadores con un slug del título y ocho caracteres de UUID. Esta decisión permite repetir títulos sin colisionar dentro de canciones/. metadata.json conserva id, título, artista, rutas de original, vocals, instrumental y pitch de referencia, fecha de creación y estado preparada. Eliminar una canción también elimina sus grabaciones y la salida asociada de Demucs.")
    add_body(document, "Las rutas son relativas al directorio de ejecución. Esto simplifica el prototipo, pero el ejecutable deberá resolver un directorio de datos estable y con permisos de escritura. También deberá decidirse si eliminar una canción borra definitivamente las sesiones o si existe una papelera, ya que el comportamiento actual no es reversible.")

    add_heading(document, "4.2.2. Separación y construcción del acompañamiento", 2)
    add_body(document, "separacion.py espera cuatro stems de HT Demucs [13]. vocals se utiliza como referencia; drums, bass y other se cargan con librosa y se suman para producir instrumental.wav. La primera tasa de muestreo encontrada se utiliza como objetivo para los stems siguientes. Si ya existen vocals.wav e instrumental.wav se evita repetir el modelo.")
    add_body(document, "La suma directa conserva el contenido instrumental, pero actualmente no normaliza picos ni registra si se produjo clipping. Esta condición deberá comprobarse porque un acompañamiento saturado afecta la experiencia y puede aumentar la filtración hacia el micrófono. También conviene registrar el modelo de Demucs empleado, ya que cambiarlo modifica la referencia.")

    add_heading(document, "4.2.3. Estimación y filtrado de frecuencia fundamental", 2)
    add_body(document, "pitch.py utiliza DIO y StoneMask cuando Pyworld está disponible [11]. Si la dependencia no existe, utiliza pYIN. El resultado pasa por FILTRO_SUAVE, cuya configuración actual se resume en el Cuadro 4.2. Estos parámetros se diseñaron para reducir ruido y detecciones aisladas, pero aún no constituyen valores validados para todas las voces.")
    add_table(document,
        ["Parámetro", "Valor actual", "Efecto", "Aspecto por validar"],
        [
            ("Rango", "A1–C7", "Descarta frecuencias fuera del rango.", "pYIN comienza en C2; debe unificarse."),
            ("Energía", "máx(P25 RMS × 1,25; máximo RMS × 0,012)", "Elimina bloques de baja energía.", "Sensibilidad a canciones con dinámica desigual."),
            ("Huecos", "Hasta 5 marcos", "Interpola pérdidas breves.", "Puede unir regiones que deberían permanecer separadas."),
            ("Duración mínima", "2 marcos", "Elimina detecciones aisladas.", "Depende del periodo de marco del estimador."),
            ("Mediana", "7 marcos", "Obtiene una tendencia local robusta.", "Retardo y pérdida de transiciones rápidas."),
            ("Salto máximo", "9 semitonos", "Descarta candidatos alejados de la mediana.", "Puede eliminar saltos melódicos reales."),
        ], [3.3, 4.3, 4.5, 5.3], 8)
    add_caption(document, "Cuadro 4.2: Configuración actual del filtrado de pitch. Fuente: elaboración propia.")
    add_body(document, "El RMS se calcula con ventanas de 2048 muestras y salto de 512. Los huecos breves se interpolan antes de eliminar segmentos cortos; luego la frecuencia se convierte a MIDI, se compara con una mediana móvil y se descartan saltos. El diagnóstico conserva simultáneamente la trayectoria cruda y filtrada para observar cuánto material se eliminó.")

    add_heading(document, "4.2.4. Captura, concurrencia y estado", 2)
    add_body(document, "karaoke.py utiliza sounddevice.playrec con reproducción no bloqueante y mantiene un bucle de supervisión cada 100 ms. app.py ejecuta este flujo en un hilo daemon y utiliza after para actualizar Tkinter desde el hilo principal. El mismo patrón se aplica a Demucs, reprocesamiento y diagnóstico, evitando que las operaciones largas congelen la ventana.")
    add_body(document, "Este diseño es suficiente para grabar y actualizar el cursor, pero playrec entrega la matriz completa como una operación que se consume al final. RF10 y RF11 requieren acceso progresivo a bloques. La extensión deberá utilizar InputStream o Stream con callback, una cola acotada y una política para descartar o agrupar bloques cuando el estimador no alcance el ritmo de captura.")

    add_heading(document, "4.2.5. Alineación y métricas", 2)
    add_body(document, "comparacion.py utiliza dtw-python sobre los arreglos de frecuencia. Después recorre index1 e index2, transforma cada par a cents y elimina errores iguales o superiores a 1000 cents en valor absoluto. metricas.py calcula error absoluto promedio, desviación, media firmada, tendencia y porcentajes dentro de 50 y 100 cents. La tendencia se considera estable cuando la media firmada se encuentra entre −10 y 10 cents.")
    add_body(document, "El diseño tiene tres limitaciones relevantes. Primero, el costo de DTW se calcula en Hz, por lo que una misma diferencia interválica tiene mayor costo en registros altos. Segundo, se pierde la trayectoria después de calcular las métricas, impidiendo relacionar errores con tiempos. Tercero, el límite de 1000 cents funciona como protección, pero todavía no está justificado experimentalmente. La siguiente versión deberá alinear una representación logarítmica, conservar pares temporales y clasificar correspondencias de baja confianza [16].")

    add_heading(document, "4.2.6. Visualización y persistencia", 2)
    add_body(document, "visualizacion.py convierte frecuencia a MIDI y corta las curvas cuando existen huecos superiores a 0,25 segundos. La referencia se muestra en una ventana móvil de 40 segundos y el cursor se mantiene aproximadamente a un cuarto del ancho. Después de la sesión se grafican las curvas Esperado y Obtenido.")
    add_body(document, "El JSON de resultado repite las curvas completas de referencia y usuario junto con las métricas. Esta decisión facilita reconstruir el gráfico, pero duplica información y puede aumentar el tamaño de cada sesión. Para el historial conviene separar la identidad de la referencia, los datos de pitch, la trayectoria de alineación y el resumen de métricas.")
    add_table(document,
        ["Contrato", "Campos actuales", "Campos requeridos para la versión objetivo"],
        [
            ("metadata.json", "id, título, artista, rutas, creada_en y preparada.", "reference_id, modelo de separación y versión activa."),
            ("ref_pitch.csv", "tiempo, frecuencia y nota.", "Mantener datos; asociar versión y configuración externa."),
            ("resultado.json", "métricas y cuatro arreglos para el gráfico.", "session_id, reference_id, analysis_version, trayectoria y confianza."),
            ("Segmento", "No implementado.", "inicio, fin, categoría, severidad, confianza, evidencia y prioridad."),
            ("Retroalimentación", "No implementada.", "texto, segmentos utilizados, generador, versión y validación."),
        ], [3.2, 6.0, 8.3], 8)
    add_caption(document, "Cuadro 4.3: Evolución prevista de los contratos persistidos. Fuente: elaboración propia.")

    add_heading(document, "4.3. Evolución arquitectónica necesaria", 1)
    add_heading(document, "4.3.1. Canal de tiempo real", 2)
    add_body(document, "Se incorporará un componente independiente de captura continua. Su salida no será una nota directa, sino un bloque con muestras, tiempo inicial, tiempo final y estado. El estimador producirá frecuencia, confianza y sonoridad; un estabilizador decidirá la nota visible. La grabación completa deberá continuar en paralelo para que el análisis posterior no dependa de los valores simplificados mostrados durante el canto.")

    add_heading(document, "4.3.2. Trayectoria y segmentos", 2)
    add_body(document, "La comparación deberá producir una colección de pares alineados con tiempo de referencia, tiempo de usuario, diferencia en cents y confianza. Sobre esta serie se agruparán observaciones contiguas, permitiendo huecos breves controlados. La caracterización se basará en reglas explícitas antes de experimentar con modelos más complejos. Esta representación será la única entrada aceptada por el generador de retroalimentación.")

    add_heading(document, "4.3.3. Versionado para comparación histórica", 2)
    add_body(document, "Regenerar la referencia no deberá sobrescribir la identidad utilizada por sesiones anteriores. Cada preparación recibirá reference_id y conservará modelo, fecha y configuración de pitch. Del mismo modo, cada resultado almacenará analysis_version. Dos sesiones serán comparables cuando compartan canción y referencia, y cuando sus configuraciones sean equivalentes o exista un proceso explícito de recalcular ambas.")

    add_heading(document, "4.3.4. Adaptadores de retroalimentación y presentación", 2)
    add_body(document, "El generador de texto se definirá mediante una interfaz que reciba hallazgos estructurados y devuelva texto más un registro de validación. Una implementación por plantillas permitirá completar y probar el flujo sin LLM. Si se añade un modelo local o remoto, este no accederá directamente al audio ni decidirá los segmentos.")
    add_body(document, "La interfaz gráfica definitiva consumirá servicios de aplicación y objetos de resultado; no importará Demucs, Pyworld ni DTW directamente. Esta frontera hace viable reemplazar Tkinter sin diseñar todavía pantallas ni mockups y reduce el riesgo de que la migración visual altere cálculos ya validados.")

    add_heading(document, "4.4. Evidencia producida por el prototipo", 1)
    add_body(document, "El repositorio contiene canciones preparadas, stems, referencias y dos sesiones asociadas con una misma canción. Como ejemplo de ejecución, el archivo usuario_20260604_131542_resultado.json registra 3077 pares comparados, error absoluto promedio de 66,94 cents, desviación de 109,00 cents, media firmada de 19,94 cents y 59,64 % de pares dentro de 50 cents. Estos valores demuestran que el flujo produce y persiste resultados; no deben interpretarse como validación del estimador ni como diagnóstico de la persona que cantó.")
    add_body(document, "La separación entre evidencia de integración y evidencia de precisión es importante. Un JSON bien formado prueba que los módulos se conectaron, pero solo los experimentos del capítulo 3 podrán establecer si la referencia, alineación y métricas representan adecuadamente la interpretación.")

    add_heading(document, "4.5. Riesgos técnicos concretos", 1)
    add_table(document,
        ["Riesgo", "Origen en el diseño actual", "Tratamiento previsto"],
        [
            ("Latencia acumulada", "Estimador fuera de línea y mediana temporal.", "Cola acotada, medición por bloque y configuración específica para tiempo real."),
            ("Referencia cambiante", "ref_pitch.csv se sobrescribe al reprocesar.", "Versiones inmutables y relación explícita con sesiones."),
            ("DTW engañoso", "Costo en Hz, sin restricciones ni confianza persistida.", "Escala logarítmica, límites de deformación y revisión de anclas."),
            ("Resultados sobredimensionados", "Curvas completas duplicadas en cada JSON.", "Separar series, relaciones y resúmenes."),
            ("Fallo de dependencias", "Demucs como subproceso y bibliotecas nativas.", "Comprobación al iniciar, mensajes específicos y estrategia de instalación."),
            ("Texto no fundamentado", "Un LLM puede agregar causas no observadas.", "Entrada cerrada, validador, registro y fallback por plantillas."),
        ], [4.0, 6.0, 6.5], 8)
    add_caption(document, "Cuadro 4.4: Riesgos derivados de la implementación actual. Fuente: elaboración propia.")

    add_heading(document, "4.6. Síntesis del capítulo", 1)
    add_body(document, "La versión específica del desarrollo muestra que el prototipo ya conecta preparación, captura, pitch, DTW, métricas y persistencia, pero también identifica las modificaciones necesarias para sostener la contribución de la tesis. El trabajo pendiente no consiste únicamente en agregar pantallas: requiere captura continua, una representación alineada trazable, segmentos con evidencia, versionado de referencias y un generador textual subordinado al análisis.")

    add_heading(document, "Referencias técnicas citadas", 1)
    add_reference(document, 11, "M. Morise, F. Yokomori y K. Ozawa, “WORLD: A Vocoder-Based High-Quality Speech Synthesis System for Real-Time Applications,” IEICE Transactions on Information and Systems, 2016. Disponible en: https://www.jstage.jst.go.jp/article/transinf/E99.D/7/E99.D_2015EDP7457/_pdf.")
    add_reference(document, 13, "S. Rouard, F. Massa y A. Défossez, “Hybrid Transformers for Music Source Separation,” Proceedings of ICASSP 2023, 2023. Disponible en: https://arxiv.org/pdf/2211.08553.")
    add_reference(document, 16, "librosa development team, “librosa.sequence.dtw: Dynamic Time Warping,” documentación oficial. Disponible en: https://librosa.org/doc/latest/generated/librosa.sequence.dtw.html.")
    document.save(OUTPUT_4)


if __name__ == "__main__":
    build_chapter_3()
    build_chapter_4()
    print(OUTPUT_3)
    print(OUTPUT_4)
