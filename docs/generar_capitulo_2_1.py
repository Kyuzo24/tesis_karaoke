from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt


ROOT = Path(__file__).resolve().parents[1]
FIGURE = ROOT / "docs" / "figuras" / "figura_2_1_frecuencia_octavas.png"
FIGURE_2_2 = ROOT / "docs" / "figuras" / "figura_2_2_muestreo_bloques.png"
FIGURE_2_3 = ROOT / "docs" / "figuras" / "figura_2_3_estimacion_f0.png"
FIGURE_2_4 = ROOT / "docs" / "figuras" / "figura_2_4_separacion_fuentes.png"
FIGURE_2_5 = ROOT / "docs" / "figuras" / "figura_2_5_alineacion_dtw.png"
FIGURE_2_6 = ROOT / "docs" / "figuras" / "figura_2_6_segmentos_problematicos.png"
FIGURE_2_7 = ROOT / "docs" / "figuras" / "figura_2_7_retroalimentacion.png"
FIGURE_2_8 = ROOT / "docs" / "figuras" / "figura_2_8_evolucion_sesiones.png"
OUTPUT = ROOT / "Capitulo_2_Marco_teorico_actualizado.docx"


def format_run(run, size=12, bold=False, italic=False, font="Times New Roman"):
    run.font.name = font
    run._element.rPr.rFonts.set(qn("w:eastAsia"), font)
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic


def add_heading(document, text, level):
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_before = Pt(12 if level == 1 else 8)
    paragraph.paragraph_format.space_after = Pt(6)
    paragraph.paragraph_format.keep_with_next = True
    run = paragraph.add_run(text)
    format_run(run, size=14 if level == 1 else 12, bold=True)
    return paragraph


def add_body(document, text):
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    paragraph.paragraph_format.line_spacing = 1.5
    paragraph.paragraph_format.space_after = Pt(6)
    run = paragraph.add_run(text)
    format_run(run)
    return paragraph


def add_equation(document, equation):
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_before = Pt(5)
    paragraph.paragraph_format.space_after = Pt(7)
    run = paragraph.add_run(equation)
    format_run(run, size=12, italic=True, font="Cambria Math")


def add_reference(document, number, text):
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    paragraph.paragraph_format.left_indent = Cm(0.75)
    paragraph.paragraph_format.first_line_indent = Cm(-0.75)
    paragraph.paragraph_format.line_spacing = 1.15
    paragraph.paragraph_format.space_after = Pt(5)
    run = paragraph.add_run(f"[{number}] {text}")
    format_run(run, size=10)


def add_comparison_table(document, headers, rows, widths):
    table = document.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.style = "Table Grid"
    for index, (header, width) in enumerate(zip(headers, widths)):
        cell = table.rows[0].cells[index]
        cell.width = Cm(width)
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        shading = OxmlElement("w:shd")
        shading.set(qn("w:fill"), "DCEAF7")
        cell._tc.get_or_add_tcPr().append(shading)
        paragraph = cell.paragraphs[0]
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = paragraph.add_run(header)
        format_run(run, size=9, bold=True)
    for values in rows:
        cells = table.add_row().cells
        for index, (value, width) in enumerate(zip(values, widths)):
            cells[index].width = Cm(width)
            cells[index].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            paragraph = cells[index].paragraphs[0]
            paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
            paragraph.paragraph_format.space_after = Pt(0)
            run = paragraph.add_run(value)
            format_run(run, size=9)
    return table


document = Document()
section = document.sections[0]
section.page_width = Cm(21)
section.page_height = Cm(29.7)
section.top_margin = Cm(2.5)
section.bottom_margin = Cm(2.5)
section.left_margin = Cm(2.5)
section.right_margin = Cm(2.5)

normal = document.styles["Normal"]
normal.font.name = "Times New Roman"
normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
normal.font.size = Pt(12)

add_heading(document, "2. Marco teórico y trabajo relacionado", 1)

add_body(
    document,
    "Este capítulo presenta los fundamentos necesarios para comprender el funcionamiento del sistema propuesto. En primer lugar, se introducen conceptos musicales y acústicos relacionados con la altura tonal, la frecuencia fundamental y la afinación. Posteriormente, se abordan las técnicas de procesamiento digital de audio, separación de fuentes, estimación de pitch, alineación temporal y evaluación automática del canto.",
)
add_body(
    document,
    "Además, se revisan mecanismos para detectar comportamientos problemáticos dentro de una interpretación y generar retroalimentación comprensible. Finalmente, se presentan las tecnologías consideradas y los trabajos relacionados con la propuesta.",
)

add_heading(document, "2.1. Fundamentos musicales y vocales", 2)

add_heading(document, "2.1.1. Frecuencia y altura tonal", 2)
add_body(
    document,
    "El sonido corresponde a una variación de presión que se propaga a través de un medio. Cuando dicha variación presenta un comportamiento periódico, puede describirse mediante su frecuencia, expresada en hercios (Hz), que indica la cantidad de ciclos producidos durante un segundo.",
)
add_body(
    document,
    "La frecuencia es una propiedad física de la señal, mientras que la altura tonal corresponde a la percepción que permite ordenar los sonidos desde graves hasta agudos. Aunque ambos conceptos se encuentran relacionados, no son equivalentes. La percepción de altura también puede verse influida por la estructura armónica, la intensidad, la duración y las características del sistema auditivo [5].",
)
add_body(
    document,
    "La voz humana no produce una onda sinusoidal simple, sino una señal compleja formada por una frecuencia fundamental y múltiples componentes armónicos. La frecuencia fundamental, también denominada F0, se relaciona con la velocidad de vibración de los pliegues vocales y constituye la principal referencia utilizada para estimar la altura tonal de la voz.",
)
add_body(
    document,
    "En el contexto de este proyecto, la frecuencia fundamental permite representar la evolución tonal de una interpretación a lo largo del tiempo. Su estimación constituye la base para convertir la señal vocal en notas musicales, compararla con una referencia y detectar desviaciones de afinación.",
)

add_heading(document, "2.1.2. Notas musicales y octavas", 2)
add_body(
    document,
    "En el sistema musical occidental, una octava corresponde al intervalo existente entre dos sonidos cuyas frecuencias mantienen una relación de dos a uno. Por ejemplo, si una nota posee una frecuencia de 440 Hz, la nota equivalente ubicada una octava superior tendrá una frecuencia de 880 Hz, mientras que la ubicada una octava inferior tendrá una frecuencia de 220 Hz.",
)
add_body(
    document,
    "La afinación temperada divide cada octava en doce semitonos. La relación de frecuencia entre dos semitonos consecutivos corresponde a 2^(1/12). Tomando como referencia la nota La4, convencionalmente asociada con 440 Hz, la posición de una frecuencia dentro de la escala puede calcularse mediante:",
)
add_equation(document, "m = 69 + 12 log₂(f / 440)")
add_body(
    document,
    "donde f representa la frecuencia en hercios y m corresponde al número de nota en la escala MIDI. El valor 69 identifica la nota La4.",
)
add_body(
    document,
    "Esta representación permite asociar una frecuencia continua con una nota y su correspondiente octava. Sin embargo, durante una interpretación real la frecuencia producida no permanece necesariamente en el valor exacto de una nota. Por esta razón, el sistema debe conservar la frecuencia original y utilizar la nota musical principalmente como una representación comprensible para el usuario.",
)

figure_paragraph = document.add_paragraph()
figure_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
figure_paragraph.paragraph_format.space_before = Pt(8)
figure_paragraph.paragraph_format.space_after = Pt(4)
figure_paragraph.add_run().add_picture(str(FIGURE), width=Cm(16))

caption = document.add_paragraph()
caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
caption.paragraph_format.space_after = Pt(8)
run = caption.add_run("Figura 2.1: Relación de frecuencia entre una nota y sus octavas. Fuente: elaboración propia.")
format_run(run, size=10)

add_heading(document, "2.1.3. Afinación y estabilidad tonal", 2)
add_body(
    document,
    "La afinación puede analizarse comparando la frecuencia producida por el cantante con la frecuencia esperada. Debido a que la percepción musical funciona mediante relaciones de frecuencia, esta diferencia suele expresarse en cents en lugar de hercios.",
)
add_body(
    document,
    "Una octava contiene 1200 cents y cada semitono del sistema temperado contiene 100. La diferencia entre una frecuencia producida y una frecuencia de referencia puede calcularse mediante:",
)
add_equation(document, "c = 1200 log₂(fᵤ / fᵣ)")
add_body(
    document,
    "donde fᵤ representa la frecuencia producida por el usuario, fᵣ la frecuencia de referencia y c la diferencia expresada en cents. Un resultado positivo indica una interpretación más aguda que la referencia, mientras que un resultado negativo representa una interpretación más grave.",
)
add_body(
    document,
    "La precisión tonal no debe analizarse únicamente mediante valores aislados. Una interpretación puede presentar pequeñas variaciones naturales, transiciones entre notas y vibrato. Por esta razón, resulta necesario observar también la continuidad y duración de las desviaciones antes de clasificarlas como problemáticas.",
)
add_body(
    document,
    "La estabilidad tonal se relaciona con la capacidad de mantener una altura relativamente consistente durante una región donde se espera una nota sostenida. Una variabilidad elevada puede indicar inestabilidad, pero también puede corresponder a recursos expresivos. En consecuencia, la interpretación de esta métrica debe considerar el comportamiento de la referencia y el contexto temporal.",
)
add_body(
    document,
    "Estudios realizados con población general han mostrado que la precisión del canto puede presentar diferencias significativas entre personas y entre distintas tareas vocales [6]. Por este motivo, el sistema propuesto no pretende emitir diagnósticos sobre las capacidades del usuario, sino describir los comportamientos observados durante una interpretación específica.",
)

add_heading(document, "2.2. Procesamiento digital de audio", 2)
add_body(
    document,
    "El procesamiento digital de audio comprende el conjunto de métodos utilizados para representar, transformar y analizar señales sonoras mediante un sistema computacional. Para que una señal acústica pueda ser procesada, primero debe convertirse desde una variación continua de presión a una secuencia de valores discretos. A partir de esta representación es posible aplicar procedimientos de filtrado, extracción de características, comparación y visualización [7].",
)

add_heading(document, "2.2.1. Digitalización de una señal", 2)
add_body(
    document,
    "Una señal de audio capturada mediante un micrófono es inicialmente analógica, debido a que varía continuamente en el tiempo y en amplitud. La conversión analógica-digital mide esta señal en instantes determinados y asigna un valor numérico a cada medición. Como resultado se obtiene una secuencia que puede ser almacenada y procesada por un computador.",
)
add_body(
    document,
    "La digitalización considera principalmente el muestreo y la cuantización. El muestreo determina los instantes en que se observa la señal, mientras que la cuantización establece los valores disponibles para representar su amplitud. La cantidad de bits utilizada influye en la precisión de dicha representación y en el rango dinámico disponible [7].",
)
add_body(
    document,
    "En una aplicación de análisis vocal, la señal digital conserva la evolución temporal de la voz y permite calcular características como energía, frecuencia fundamental y estabilidad. La calidad de la captura influye directamente en los resultados, debido a que el ruido, la saturación o una amplitud insuficiente pueden dificultar la extracción de información tonal.",
)

add_heading(document, "2.2.2. Frecuencia de muestreo", 2)
add_body(
    document,
    "La frecuencia de muestreo indica la cantidad de muestras obtenidas durante un segundo y se expresa en hercios. Si una señal continua x(t) es capturada con una frecuencia de muestreo fs, su representación discreta puede expresarse como:",
)
add_equation(document, "x[n] = x(n / fₛ)")
add_body(
    document,
    "donde n corresponde al índice de la muestra. Una frecuencia de muestreo mayor permite representar componentes de frecuencia más elevadas, pero también aumenta la cantidad de datos que deben almacenarse y procesarse.",
)
add_body(
    document,
    "De acuerdo con el teorema de muestreo, la frecuencia utilizada debe ser superior al doble de la frecuencia máxima que se desea representar. Cuando esta condición no se cumple pueden aparecer componentes falsas, fenómeno conocido como aliasing. En aplicaciones de audio son habituales frecuencias como 44,1 kHz y 48 kHz, suficientes para representar el rango audible utilizado en grabaciones convencionales [7].",
)

add_heading(document, "2.2.3. Ventanas y bloques de audio", 2)
add_body(
    document,
    "Una señal vocal cambia constantemente, por lo que su análisis suele realizarse sobre fragmentos breves denominados ventanas o bloques. Cada bloque contiene una cantidad limitada de muestras y representa un intervalo local de la señal. Esto permite estimar características que varían con el tiempo sin esperar a que finalice la grabación completa [8].",
)
add_body(
    document,
    "Si un bloque contiene N muestras y la frecuencia de muestreo corresponde a fs, su duración puede calcularse mediante:",
)
add_equation(document, "T = N / fₛ")
add_body(
    document,
    "Los bloques pueden procesarse de manera consecutiva o parcialmente superpuesta. El desplazamiento entre el inicio de dos bloques se denomina salto o hop. El uso de superposición permite observar con mayor continuidad los cambios de la señal, aunque incrementa la cantidad de cálculos requeridos.",
)
add_body(
    document,
    "La selección del tamaño del bloque implica un compromiso. Un bloque pequeño reduce el tiempo necesario para producir un resultado y favorece una baja latencia, pero contiene menos información y puede generar estimaciones inestables. Un bloque de mayor duración puede mejorar la estabilidad del análisis, aunque retrasa la respuesta del sistema. Esta relación resulta especialmente importante para la detección de notas en tiempo real.",
)

figure_paragraph = document.add_paragraph()
figure_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
figure_paragraph.paragraph_format.space_before = Pt(8)
figure_paragraph.paragraph_format.space_after = Pt(4)
figure_paragraph.add_run().add_picture(str(FIGURE_2_2), width=Cm(16))

caption = document.add_paragraph()
caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
caption.paragraph_format.space_after = Pt(8)
run = caption.add_run("Figura 2.2: Digitalización y procesamiento de una señal mediante bloques. Fuente: elaboración propia.")
format_run(run, size=10)

add_heading(document, "2.2.4. Ruido, silencios y filtrado", 2)
add_body(
    document,
    "Las grabaciones vocales pueden contener ruido ambiental, filtración del acompañamiento, respiraciones, silencios y otros componentes que no representan una nota cantada. Si estos elementos se procesan como información tonal válida, pueden producir estimaciones erróneas y afectar la comparación con la referencia.",
)
add_body(
    document,
    "Para reducir este efecto pueden utilizarse criterios de energía, rangos de frecuencia permitidos, duración mínima y continuidad temporal. Los segmentos cuya energía se encuentre bajo un umbral pueden considerarse silencios, mientras que las frecuencias fuera del rango esperado pueden descartarse como detecciones no representativas.",
)
add_body(
    document,
    "También pueden aplicarse filtros temporales para reducir saltos aislados y estabilizar la trayectoria de la frecuencia fundamental. Sin embargo, un filtrado excesivo puede eliminar transiciones reales, vibrato o notas breves. Por esta razón, los parámetros deben equilibrar la eliminación de ruido con la conservación del comportamiento vocal relevante [7], [8].",
)
add_body(
    document,
    "En el sistema propuesto, estas operaciones se utilizarán tanto para preparar la melodía de referencia como para procesar la voz del usuario. Los parámetros y procedimientos concretos serán descritos posteriormente en el capítulo de diseño y desarrollo.",
)

add_heading(document, "2.3. Estimación de frecuencia fundamental", 2)
add_body(
    document,
    "La estimación de frecuencia fundamental busca determinar la periodicidad principal presente en una señal y representarla mediante una frecuencia expresada en hercios. En una señal vocal, este valor se utiliza como una aproximación de la altura tonal producida en cada instante. El resultado no corresponde a una única frecuencia para toda la grabación, sino a una trayectoria temporal de valores de F0.",
)
add_body(
    document,
    "Esta trayectoria constituye una entrada fundamental para el sistema propuesto, debido a que permite representar la melodía de referencia, visualizar la nota cantada, alinear interpretaciones y calcular diferencias de afinación. La calidad de las etapas posteriores depende de que la estimación mantenga continuidad y descarte los intervalos donde no existe evidencia tonal suficiente.",
)

add_heading(document, "2.3.1. Sonoridad y periodicidad", 2)
add_body(
    document,
    "No todos los fragmentos de una grabación vocal poseen una frecuencia fundamental definida. Las vocales y otros sonidos sonoros presentan una vibración relativamente periódica de los pliegues vocales, mientras que los silencios, consonantes no sonoras y ciertos ruidos carecen de una periodicidad estable. Por esta razón, los estimadores deben decidir primero si el bloque contiene información tonal válida.",
)
add_body(
    document,
    "Los métodos basados en periodicidad buscan repeticiones dentro de la forma de onda. El intervalo temporal entre dos repeticiones se denomina periodo y su inverso corresponde a la frecuencia fundamental. Este análisis puede realizarse mediante autocorrelación, funciones de diferencia o análisis espectral. En la práctica, suelen evaluarse varios candidatos antes de seleccionar el valor más probable.",
)
add_body(
    document,
    "Cuando la periodicidad o energía no alcanza un nivel de confianza suficiente, el bloque debe clasificarse como no sonoro y representarse sin un valor de F0. Esta decisión evita que silencios o ruidos sean convertidos incorrectamente en notas musicales.",
)

add_heading(document, "2.3.2. Estimación mediante pYIN", 2)
add_body(
    document,
    "pYIN es un método de estimación de frecuencia fundamental que extiende el enfoque YIN mediante un modelo probabilístico. En lugar de depender de un único umbral para seleccionar un periodo, considera múltiples candidatos y asigna probabilidades a las posibles estimaciones. Posteriormente, utiliza la continuidad temporal para obtener una trayectoria de F0 y determinar los intervalos sonoros y no sonoros [9].",
)
add_body(
    document,
    "Este enfoque resulta útil en señales musicales porque reduce cambios abruptos entre candidatos y proporciona información sobre la probabilidad de sonoridad. Su implementación se encuentra disponible en la biblioteca librosa, donde puede configurarse el rango de frecuencias esperado, el tamaño de los bloques y los parámetros relacionados con la transición entre valores [9].",
)
add_body(
    document,
    "A pesar de estas ventajas, la calidad del resultado continúa dependiendo del ruido, la intensidad de la voz, el rango configurado y la duración de los bloques. Además, un seguimiento temporal demasiado restrictivo puede suavizar transiciones reales entre notas.",
)

add_heading(document, "2.3.3. WORLD y Pyworld", 2)
add_body(
    document,
    "WORLD es un sistema de análisis y síntesis de voz que descompone la señal en frecuencia fundamental, envolvente espectral y características aperiódicas. Fue diseñado para producir análisis de alta calidad con un costo computacional adecuado para distintas aplicaciones de voz [11].",
)
add_body(
    document,
    "Dentro de este ecosistema existen diferentes estimadores de F0. Harvest utiliza información temporal y espectral para generar candidatos y seleccionar una trayectoria confiable, mostrando robustez en señales de voz con distintas condiciones [10]. Otro procedimiento utilizado en WORLD es DIO, cuya estimación inicial puede refinarse posteriormente mediante StoneMask.",
)
add_body(
    document,
    "Pyworld proporciona acceso a las funciones de WORLD desde Python. En el prototipo actual se utiliza DIO para producir una estimación inicial y StoneMask para refinarla. Cuando esta biblioteca no se encuentra disponible, pYIN puede emplearse como alternativa. La elección definitiva para el procesamiento en tiempo real deberá considerar no solo la precisión, sino también la latencia y el consumo de recursos.",
)

add_heading(document, "2.3.4. Errores frecuentes de estimación", 2)
add_body(
    document,
    "La estimación de F0 puede presentar errores incluso cuando existe una señal vocal clara. Entre ellos se encuentran los saltos de octava, donde el algoritmo selecciona el doble o la mitad de la frecuencia correcta; las detecciones aisladas durante silencios; la pérdida temporal de valores; y las fluctuaciones producidas por ruido o filtración del acompañamiento.",
)
add_body(
    document,
    "También pueden producirse dificultades durante ataques de notas, transiciones rápidas, vibrato intenso y regiones de baja energía. Estos comportamientos no deben corregirse únicamente mediante un suavizado general, ya que podrían representar características reales de la interpretación. Por ello, resulta necesario combinar la estimación acústica con criterios de confianza, continuidad y duración.",
)
add_body(
    document,
    "La Figura 2.3 resume el flujo general utilizado para obtener una trayectoria temporal de frecuencia fundamental a partir de bloques de audio vocal.",
)

figure_paragraph = document.add_paragraph()
figure_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
figure_paragraph.paragraph_format.space_before = Pt(8)
figure_paragraph.paragraph_format.space_after = Pt(4)
figure_paragraph.add_run().add_picture(str(FIGURE_2_3), width=Cm(16))

caption = document.add_paragraph()
caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
caption.paragraph_format.space_after = Pt(8)
run = caption.add_run("Figura 2.3: Flujo general de estimación de frecuencia fundamental. Fuente: elaboración propia.")
format_run(run, size=10)

add_heading(document, "2.3.5. Criterios para el proyecto", 2)
add_body(
    document,
    "El sistema requiere estimar F0 en dos situaciones diferentes. La preparación de la referencia se realiza antes de la sesión y permite utilizar un procesamiento más detallado, debido a que no posee restricciones estrictas de latencia. En cambio, la visualización de la nota durante el canto requiere producir resultados en intervalos breves y mantener la continuidad de la interfaz.",
)
add_body(
    document,
    "Por esta razón, los métodos deberán evaluarse considerando precisión, estabilidad, proporción de detecciones válidas, tiempo de procesamiento y comportamiento ante ruido moderado. El algoritmo utilizado para preparar la referencia no necesariamente deberá ser el mismo que se emplee durante la detección en tiempo real.",
)
add_body(
    document,
    "En ambos casos, la salida deberá conservar los tiempos y frecuencias estimadas antes de transformarlas en notas. Esto permite aplicar filtros, calcular diferencias en cents y mantener trazabilidad entre los resultados informados y los datos acústicos que los sustentan.",
)

add_heading(document, "2.4. Separación de fuentes musicales", 2)
add_body(
    document,
    "Una grabación musical corresponde generalmente a la mezcla de diferentes fuentes, como voz, batería, bajo y otros instrumentos. Aunque el usuario escucha estas fuentes de manera conjunta, el análisis vocal requiere disponer de una señal donde la voz principal se encuentre suficientemente aislada del acompañamiento.",
)
add_body(
    document,
    "La separación de fuentes musicales busca estimar las señales individuales que componen una mezcla. El resultado suele organizarse en stems, término utilizado para representar grupos de fuentes relacionados. En una configuración habitual se generan pistas independientes para voz, batería, bajo y otros componentes instrumentales.",
)

add_heading(document, "2.4.1. Separación mediante modelos preentrenados", 2)
add_body(
    document,
    "Los métodos actuales de separación suelen utilizar modelos de aprendizaje profundo entrenados con mezclas musicales y sus fuentes aisladas. Durante el entrenamiento, el modelo aprende a estimar cada componente a partir de la señal combinada. Posteriormente, el modelo preentrenado puede aplicarse a canciones que no formaron parte de sus datos de entrenamiento.",
)
add_body(
    document,
    "El uso de modelos preentrenados permite incorporar separación de fuentes sin construir un conjunto de datos propio ni realizar un proceso de entrenamiento. Sin embargo, el resultado depende de las características de la canción, la calidad de la mezcla y la similitud con el material utilizado durante el aprendizaje.",
)
add_body(
    document,
    "La separación puede realizarse sobre representaciones tiempo-frecuencia, sobre la forma de onda o mediante arquitecturas que combinan ambos dominios. Cada alternativa presenta diferencias en calidad, costo computacional y presencia de artefactos.",
)

add_heading(document, "2.4.2. Spleeter", 2)
add_body(
    document,
    "Spleeter es una herramienta de separación de fuentes desarrollada para ejecutar modelos preentrenados de manera eficiente. Permite generar configuraciones de dos, cuatro o cinco stems, incluyendo la separación entre voz y acompañamiento. Su diseño facilita la integración en flujos de procesamiento musical y reduce el tiempo necesario para preparar una canción [14].",
)
add_body(
    document,
    "Esta herramienta constituye una alternativa apropiada cuando la velocidad de procesamiento es prioritaria. No obstante, al igual que otros sistemas, puede conservar restos instrumentales en la pista vocal o eliminar componentes de la voz, lo que debe considerarse antes de utilizar el resultado como referencia tonal.",
)

add_heading(document, "2.4.3. Demucs y Hybrid Transformer Demucs", 2)
add_body(
    document,
    "Demucs aborda la separación musical mediante modelos que operan directamente sobre la forma de onda. Su arquitectura utiliza una estructura codificador-decodificador y conexiones internas destinadas a reconstruir las fuentes temporales a partir de la mezcla original [12].",
)
add_body(
    document,
    "Versiones posteriores incorporaron representaciones espectrales y mecanismos de atención. Hybrid Transformer Demucs combina ramas temporales y espectrales con transformadores capaces de intercambiar información entre ambas representaciones. De esta manera, el modelo utiliza simultáneamente características de la forma de onda y del dominio de frecuencia [13].",
)
add_body(
    document,
    "La implementación actual del proyecto utiliza el modelo HT Demucs para generar cuatro stems: vocals, drums, bass y other. La pista vocals se emplea para obtener el pitch de referencia, mientras que los tres componentes restantes se combinan para construir el acompañamiento instrumental.",
)

add_heading(document, "2.4.4. Artefactos y limitaciones", 2)
add_body(
    document,
    "La separación de fuentes no produce señales completamente independientes. Pueden permanecer instrumentos en la pista vocal, perderse componentes armónicos de la voz o generarse alteraciones temporales y espectrales. Estos artefactos pueden afectar la estimación de frecuencia fundamental y producir una referencia incompleta o inestable.",
)
add_body(
    document,
    "También existe un costo computacional relevante. Procesar una canción completa puede requerir varios minutos dependiendo del modelo y del hardware disponible. Por esta razón, la separación debe realizarse durante la preparación de la canción y no mientras el usuario se encuentra cantando.",
)
add_body(
    document,
    "La Figura 2.4 presenta el flujo utilizado para transformar una canción en una referencia vocal y una pista de acompañamiento.",
)

figure_paragraph = document.add_paragraph()
figure_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
figure_paragraph.paragraph_format.space_before = Pt(8)
figure_paragraph.paragraph_format.space_after = Pt(4)
figure_paragraph.add_run().add_picture(str(FIGURE_2_4), width=Cm(16))

caption = document.add_paragraph()
caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
caption.paragraph_format.space_after = Pt(8)
run = caption.add_run("Figura 2.4: Separación de una canción en fuentes vocales e instrumentales. Fuente: elaboración propia.")
format_run(run, size=10)

add_heading(document, "2.4.5. Criterios para el proyecto", 2)
add_body(
    document,
    "La herramienta seleccionada debe proporcionar una pista vocal adecuada para extraer la melodía y un acompañamiento que pueda reproducirse durante la sesión. Además, debe permitir reutilizar los resultados, evitando procesar nuevamente una canción cada vez que el usuario desee practicar.",
)
add_body(
    document,
    "La calidad de la separación deberá revisarse junto con la proporción de pitch válido obtenida desde la voz aislada. Si la pista presenta demasiados artefactos o no contiene suficiente información tonal, el sistema deberá informar que la canción no pudo prepararse de manera confiable.",
)
add_body(
    document,
    "Demucs fue seleccionado para el prototipo por ofrecer una separación organizada en stems y disponer de modelos preentrenados que pueden ejecutarse localmente. Esta decisión no implica que la herramienta forme parte obligatoriamente del ejecutable final, ya que su estrategia de distribución permanece sujeta a evaluación.",
)

add_heading(document, "2.5. Alineación temporal mediante Dynamic Time Warping", 2)
add_body(
    document,
    "Dos interpretaciones de una misma canción no presentan necesariamente la misma duración ni mantienen un tempo idéntico. El usuario puede adelantar o retrasar el inicio de una frase, prolongar una nota o modificar localmente la velocidad. Por esta razón, comparar las curvas de pitch únicamente mediante instantes coincidentes produciría diferencias que no corresponden a errores de afinación, sino a variaciones temporales.",
)
add_body(
    document,
    "Dynamic Time Warping (DTW) es un procedimiento que permite alinear dos secuencias temporales aunque sus elementos equivalentes aparezcan en instantes diferentes. Para ello, busca una correspondencia de costo mínimo entre ambas secuencias y admite repeticiones o avances desiguales a lo largo de sus ejes temporales [15].",
)

add_heading(document, "2.5.1. Matriz de costos", 2)
add_body(
    document,
    "El proceso comienza construyendo una matriz cuyos elementos representan la diferencia entre cada observación de la referencia y cada observación de la interpretación. En el contexto del proyecto, esta diferencia puede calcularse a partir de frecuencias, notas o valores expresados en cents. Los valores reducidos indican pares tonalmente similares, mientras que los valores elevados representan una mayor separación.",
)
add_body(
    document,
    "La selección de la medida de distancia influye directamente en el resultado. Trabajar con cents permite representar las diferencias de altura mediante una escala logarítmica y comparar de manera consistente notas pertenecientes a distintos registros. Los intervalos sin voz deben tratarse por separado para evitar que sean alineados como si contuvieran estimaciones tonales válidas.",
)

add_heading(document, "2.5.2. Trayectoria de alineación", 2)
add_body(
    document,
    "A partir de la matriz de costos, DTW determina una trayectoria que conecta el comienzo y el final de las secuencias. Cada punto de esta trayectoria vincula un instante de la referencia con uno de la interpretación. El costo acumulado se obtiene combinando la diferencia local con el mejor costo alcanzado desde las posiciones permitidas anteriormente [15].",
)
add_body(
    document,
    "Las restricciones de continuidad y monotonía impiden retroceder en el tiempo, pero permiten que un elemento de una secuencia se relacione con varios elementos de la otra. La biblioteca librosa proporciona una implementación configurable de DTW que admite matrices de características, matrices de costo previamente calculadas y restricciones sobre la trayectoria [16].",
)

add_heading(document, "2.5.3. Aplicación a curvas de pitch", 2)
add_body(
    document,
    "En el sistema propuesto, la alineación se aplicará entre la curva de pitch vocal obtenida desde la canción de referencia y la curva registrada durante la interpretación. Una vez establecidas las correspondencias temporales, será posible calcular diferencias de afinación sobre instantes comparables y localizar segmentos donde estas diferencias se mantienen durante un intervalo significativo.",
)
add_body(
    document,
    "La alineación temporal también ha sido utilizada en trabajos orientados a la corrección de canto, donde se busca relacionar una interpretación con una referencia antes de modificar su altura tonal [17]. En este proyecto no se pretende corregir el audio del usuario, sino utilizar la correspondencia como base para el análisis y la retroalimentación posterior.",
)
add_body(
    document,
    "La Figura 2.5 muestra de manera simplificada cómo dos curvas con duraciones distintas pueden vincularse mediante una matriz de costos y una trayectoria de alineación.",
)

figure_paragraph = document.add_paragraph()
figure_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
figure_paragraph.paragraph_format.space_before = Pt(8)
figure_paragraph.paragraph_format.space_after = Pt(4)
figure_paragraph.add_run().add_picture(str(FIGURE_2_5), width=Cm(16))

caption = document.add_paragraph()
caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
caption.paragraph_format.space_after = Pt(8)
run = caption.add_run("Figura 2.5: Alineación temporal de curvas de pitch mediante DTW. Fuente: elaboración propia.")
format_run(run, size=10)

add_heading(document, "2.5.4. Limitaciones de la alineación", 2)
add_body(
    document,
    "Una trayectoria demasiado flexible puede relacionar regiones que no corresponden musicalmente, ocultar omisiones o compensar desviaciones importantes. Por el contrario, restricciones excesivas pueden impedir la alineación de interpretaciones que contienen variaciones naturales de tempo. Además, los errores presentes en la estimación de pitch se trasladan a la matriz de costos y pueden desviar la trayectoria.",
)
add_body(
    document,
    "DTW tampoco determina por sí mismo si una diferencia constituye un problema vocal. Su resultado debe combinarse con criterios de duración, magnitud, continuidad y contexto musical. Las pausas extensas, frases omitidas y regiones con baja confianza requerirán reglas específicas antes de generar un diagnóstico.",
)

add_heading(document, "2.5.5. Criterios para el proyecto", 2)
add_body(
    document,
    "La implementación conservará tanto la trayectoria como el costo de alineación, de modo que los resultados puedan revisarse y asociarse con los segmentos originales. Se evaluará el uso de restricciones que limiten deformaciones temporales excesivas y se excluirán los bloques que no posean una estimación tonal confiable.",
)
add_body(
    document,
    "La alineación se realizará después de completar la grabación, ya que no es necesaria para mostrar la nota detectada en tiempo real. Esta separación permite mantener una respuesta inmediata durante el canto y reservar el análisis comparativo completo para la etapa posterior de procesamiento.",
)

add_heading(document, "2.6. Detección y caracterización de segmentos problemáticos", 2)
add_body(
    document,
    "Una métrica global resume el desempeño de una interpretación, pero no permite determinar dónde ocurrió una dificultad ni durante cuánto tiempo se mantuvo. Para entregar retroalimentación útil, el sistema debe conservar la dimensión temporal del análisis e identificar intervalos concretos donde las diferencias respecto de la referencia sean relevantes.",
)
add_body(
    document,
    "Los trabajos de evaluación automática del canto han utilizado información como la exactitud de los intervalos de pitch y las características del vibrato para describir aspectos de una interpretación [18]. Asimismo, interfaces como MiruSinger han mostrado la utilidad de presentar visualmente el pitch estimado junto con una referencia musical [19]. Estos antecedentes respaldan el uso de evidencia tonal localizada, aunque la propuesta de este proyecto busca además agruparla y expresarla mediante observaciones comprensibles.",
)

add_heading(document, "2.6.1. Evidencias locales de la interpretación", 2)
add_body(
    document,
    "Después de la alineación temporal, cada bloque válido puede asociarse con indicadores locales. Entre ellos se encuentran la diferencia de afinación en cents, el signo de la desviación, la ausencia de voz cuando existe una referencia tonal y la variabilidad observada dentro de una región sostenida. También debe conservarse la confianza de la estimación para distinguir una posible dificultad del usuario de un error del procesamiento acústico.",
)
add_body(
    document,
    "Una diferencia aislada no constituye necesariamente un problema. Los ataques de notas, el vibrato y las transiciones melódicas producen variaciones legítimas que podrían superar momentáneamente un umbral. Por ello, la detección debe considerar simultáneamente magnitud, duración, continuidad y contexto temporal.",
)

add_heading(document, "2.6.2. Formación dinámica de segmentos", 2)
add_body(
    document,
    "Los segmentos no se definirán mediante divisiones de duración fija. Se formarán agrupando observaciones consecutivas que presenten un comportamiento compatible, permitiendo pequeñas interrupciones cuando estas correspondan a estimaciones ausentes o transiciones breves. Cada segmento conservará su instante inicial, instante final y conjunto de evidencias asociadas.",
)
add_body(
    document,
    "Como alternativa para detectar cambios entre comportamientos temporales, existen métodos de detección de puntos de cambio que dividen una señal cuando sus propiedades estadísticas varían. La literatura distingue aproximaciones basadas en costos, búsqueda y penalizaciones, cuya selección depende de las características de la serie analizada [20]. En este proyecto estos métodos se consideran como una posibilidad de refinamiento, no como una decisión de implementación ya establecida.",
)

add_heading(document, "2.6.3. Caracterización de problemáticas", 2)
add_body(
    document,
    "Una vez delimitado un segmento, el sistema deberá caracterizar lo ocurrido mediante categorías sustentadas por los datos disponibles. Entre las problemáticas inicialmente consideradas se encuentran la afinación predominantemente baja o alta, la oscilación tonal excesiva, la pérdida de estabilidad en notas sostenidas, la entrada tardía o adelantada y la ausencia parcial de voz respecto de la referencia.",
)
add_body(
    document,
    "Estas categorías deberán validarse durante el desarrollo y podrán ajustarse si no existe evidencia suficiente para distinguirlas de manera confiable. En particular, el sistema no inferirá causas fisiológicas, técnicas vocales específicas ni condiciones clínicas a partir de una grabación. La salida describirá el comportamiento acústico observado y su relación con la referencia.",
)

add_heading(document, "2.6.4. Severidad y priorización", 2)
add_body(
    document,
    "La severidad de un segmento puede estimarse combinando la magnitud de la diferencia, su duración, persistencia y nivel de confianza. La prioridad, en cambio, también debe considerar la recurrencia del comportamiento y su relevancia dentro de la interpretación. De esta forma, una desviación breve pero extrema no necesariamente desplazará a una dificultad moderada que se repite durante varias frases.",
)
add_body(
    document,
    "La priorización permitirá seleccionar un número acotado de hallazgos para la retroalimentación. Con ello se evita presentar al usuario una lista extensa de pequeñas desviaciones y se concentra la atención en los segmentos que ofrecen mayor utilidad para una práctica posterior.",
)
add_body(
    document,
    "La Figura 2.6 resume el proceso que transforma las diferencias locales en segmentos caracterizados y priorizados.",
)

figure_paragraph = document.add_paragraph()
figure_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
figure_paragraph.paragraph_format.space_before = Pt(8)
figure_paragraph.paragraph_format.space_after = Pt(4)
figure_paragraph.add_run().add_picture(str(FIGURE_2_6), width=Cm(16))

caption = document.add_paragraph()
caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
caption.paragraph_format.space_after = Pt(8)
run = caption.add_run("Figura 2.6: Proceso de detección, caracterización y priorización de segmentos problemáticos. Fuente: elaboración propia.")
format_run(run, size=10)

add_heading(document, "2.6.5. Criterios para el proyecto", 2)
add_body(
    document,
    "Los umbrales y criterios iniciales deberán tratarse como parámetros ajustables y validarse con grabaciones de prueba. Cada segmento almacenará la evidencia numérica que justificó su clasificación, permitiendo revisar el resultado y modificar los criterios sin perder trazabilidad.",
)
add_body(
    document,
    "La detección producirá una representación estructurada independiente del mecanismo utilizado posteriormente para redactar la retroalimentación. Esta separación permitirá generar mensajes mediante plantillas o mediante un modelo de lenguaje sin delegar al generador textual la identificación de los problemas acústicos.",
)

add_heading(document, "2.7. Generación de retroalimentación en lenguaje natural", 2)
add_body(
    document,
    "La retroalimentación corresponde a la transformación de los resultados técnicos en observaciones que el usuario pueda comprender y relacionar con su interpretación. Su finalidad no es reemplazar la evaluación de un docente de canto, sino comunicar de manera clara los segmentos detectados, la evidencia disponible y los aspectos que podrían revisarse durante una nueva práctica.",
)
add_body(
    document,
    "La generación de lenguaje natural comprende tareas que convierten datos o representaciones internas en texto. Este proceso suele incluir la selección del contenido, su organización y su realización lingüística [21]. En el proyecto, estas etapas deben permanecer vinculadas con los hallazgos producidos por el análisis acústico.",
)

add_heading(document, "2.7.1. Representación estructurada de hallazgos", 2)
add_body(
    document,
    "Antes de redactar un mensaje, cada hallazgo deberá representarse mediante campos verificables: canción, intervalo temporal, categoría, severidad, confianza, métricas relevantes y relación con la referencia. Esta estructura constituye el contrato entre el módulo de análisis y el mecanismo de generación textual.",
)
add_body(
    document,
    "La separación impide que el componente de lenguaje modifique silenciosamente los resultados. También permite mostrar la misma evidencia mediante gráficos, tablas o mensajes y facilita comparar la salida producida por distintos generadores.",
)

add_heading(document, "2.7.2. Generación mediante plantillas", 2)
add_body(
    document,
    "Las plantillas combinan expresiones previamente definidas con valores obtenidos desde los segmentos. Su principal ventaja es la previsibilidad: para una misma entrada producen mensajes equivalentes y no agregan información que no se encuentre en las reglas. Además, pueden ejecutarse localmente con un costo reducido.",
)
add_body(
    document,
    "Como limitación, un conjunto de plantillas puede producir textos repetitivos y requiere anticipar las combinaciones posibles entre hallazgos. A medida que aumenta la cantidad de categorías, prioridades y relaciones entre sesiones, mantener mensajes naturales mediante reglas puede volverse más complejo.",
)

add_heading(document, "2.7.3. Generación mediante un modelo de lenguaje", 2)
add_body(
    document,
    "Un modelo de lenguaje puede recibir los hallazgos estructurados y redactar una explicación más contextual, agrupar observaciones relacionadas y adaptar el nivel de detalle. Existen familias de modelos con pesos disponibles que permiten estudiar su ejecución local [23], junto con herramientas como llama.cpp orientadas a realizar inferencia en equipos de uso general [24].",
)
add_body(
    document,
    "La ejecución local evitaría enviar grabaciones o resultados a un servicio externo, pero exige considerar tamaño del modelo, memoria, tiempo de respuesta, licencia y complejidad de distribución. Una alternativa remota simplificaría parte de la instalación, aunque introduciría conectividad, costos de uso y tratamiento de datos. La selección entre plantillas, modelo local o servicio remoto permanece sujeta a evaluación.",
)

add_heading(document, "2.7.4. Riesgos y validación", 2)
add_body(
    document,
    "Los modelos de lenguaje pueden producir afirmaciones plausibles que no se encuentran respaldadas por la entrada, comportamiento estudiado como alucinación en la generación de texto [22]. En este proyecto, una afirmación inventada podría atribuir al usuario una causa técnica o fisiológica que el análisis no puede demostrar.",
)
add_body(
    document,
    "Para reducir este riesgo, la entrada deberá limitarse a los hallazgos seleccionados, la salida utilizará un formato definido y se verificará que los tiempos, categorías y magnitudes mencionados correspondan con los datos originales. También se restringirán diagnósticos clínicos, juicios absolutos y recomendaciones que excedan el alcance del sistema.",
)
add_body(
    document,
    "La Figura 2.7 representa las dos alternativas de generación y la validación común que debe aplicarse antes de presentar el mensaje.",
)

figure_paragraph = document.add_paragraph()
figure_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
figure_paragraph.paragraph_format.space_before = Pt(8)
figure_paragraph.paragraph_format.space_after = Pt(4)
figure_paragraph.add_run().add_picture(str(FIGURE_2_7), width=Cm(16))

caption = document.add_paragraph()
caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
caption.paragraph_format.space_after = Pt(8)
run = caption.add_run("Figura 2.7: Generación y validación de retroalimentación en lenguaje natural. Fuente: elaboración propia.")
format_run(run, size=10)

add_heading(document, "2.7.5. Criterios para el proyecto", 2)
add_body(
    document,
    "La primera implementación podrá utilizar plantillas como mecanismo base y referencia de comportamiento. La incorporación de un modelo de lenguaje se considerará si mejora de manera comprobable la claridad sin reducir la fidelidad respecto de los datos. En ambos casos, el mensaje deberá indicar qué ocurrió, en qué segmento se observó y qué evidencia sustenta la observación.",
)
add_body(
    document,
    "La generación se ejecutará después del análisis de la grabación y no formará parte del flujo de detección de nota en tiempo real. El resultado estructurado se conservará junto con el texto, permitiendo regenerar la retroalimentación o auditarla posteriormente.",
)

add_heading(document, "2.8. Seguimiento y comparación de la evolución", 2)
add_body(
    document,
    "Una sesión aislada permite reconocer dificultades puntuales, pero no informa si estas disminuyen, persisten o cambian con la práctica. El seguimiento histórico utilizará los resultados almacenados para comparar interpretaciones realizadas en fechas diferentes y presentar su evolución.",
)

add_heading(document, "2.8.1. Persistencia de sesiones", 2)
add_body(
    document,
    "Cada sesión deberá mantener una relación con la canción y la referencia utilizadas, además de su fecha, grabación, métricas, segmentos y retroalimentación. Conservar estos elementos permite volver al audio original, verificar un hallazgo y aplicar en el futuro criterios de análisis actualizados.",
)
add_body(
    document,
    "Los datos derivados no sustituyen a la grabación. Una modificación del estimador de pitch, de la alineación o de los umbrales puede cambiar el resultado; por ello, el sistema deberá distinguir los archivos originales de los resultados calculados y registrar la versión o configuración relevante del procesamiento.",
)

add_heading(document, "2.8.2. Comparabilidad entre sesiones", 2)
add_body(
    document,
    "La comparación se limitará a sesiones correspondientes a una misma canción y referencia. Esta condición reduce diferencias originadas por melodías, rangos o duraciones distintas. Las métricas deberán calcularse mediante configuraciones equivalentes y se informará cuando una sesión no posea suficiente información tonal para ser comparable.",
)
add_body(
    document,
    "Además de observar la variación de métricas globales, se analizará la recurrencia de categorías y su ubicación aproximada dentro de la canción. Debido a que los límites de un segmento pueden variar entre interpretaciones, la comparación deberá apoyarse en la alineación temporal y no exigir coincidencias exactas de inicio y término.",
)

add_heading(document, "2.8.3. Resumen de cambios", 2)
add_body(
    document,
    "El resumen histórico distinguirá aspectos que mejoraron, persistieron o empeoraron. Una mejora puede reflejar una reducción de la magnitud o duración de un problema, mientras que la persistencia indica que una categoría continúa apareciendo en regiones comparables. Estas etiquetas se acompañarán con los valores que justifican el cambio.",
)
add_body(
    document,
    "La visualización deberá evitar presentar pequeñas fluctuaciones como progreso concluyente. Cuando las diferencias se encuentren dentro de un margen definido o la confianza sea insuficiente, el sistema las tratará como cambios no concluyentes.",
)
add_body(
    document,
    "La Figura 2.8 ilustra una secuencia de sesiones comparables y la evolución de una métrica a lo largo del tiempo.",
)

figure_paragraph = document.add_paragraph()
figure_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
figure_paragraph.paragraph_format.space_before = Pt(8)
figure_paragraph.paragraph_format.space_after = Pt(4)
figure_paragraph.add_run().add_picture(str(FIGURE_2_8), width=Cm(16))

caption = document.add_paragraph()
caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
caption.paragraph_format.space_after = Pt(8)
run = caption.add_run("Figura 2.8: Seguimiento de la evolución entre sesiones de una misma canción. Fuente: elaboración propia.")
format_run(run, size=10)

add_heading(document, "2.8.4. Criterios para el proyecto", 2)
add_body(
    document,
    "La comparación histórica constituirá una función posterior al análisis individual. Inicialmente se priorizará la selección de dos sesiones y, posteriormente, una vista cronológica que resuma varias interpretaciones. La implementación deberá permitir incorporar nuevas métricas sin invalidar las sesiones almacenadas.",
)

add_heading(document, "2.9. Tecnologías consideradas", 2)
add_body(
    document,
    "Las tecnologías del proyecto deben permitir procesamiento local de audio, interacción de escritorio y conservación de resultados. La selección definitiva de algunos componentes permanece abierta, por lo que esta sección distingue las herramientas utilizadas en el prototipo de las alternativas consideradas para la versión final.",
)

add_heading(document, "2.9.1. Lenguaje y procesamiento de audio", 2)
add_body(
    document,
    "El prototipo se encuentra desarrollado en Python, lenguaje que dispone de documentación y un ecosistema amplio de bibliotecas científicas [25]. librosa se utiliza para carga, transformación y análisis de audio; Pyworld proporciona acceso a procedimientos de WORLD; y Demucs realiza la separación de fuentes mediante modelos preentrenados. NumPy y SciPy apoyan las operaciones numéricas requeridas por estas etapas.",
)
add_body(
    document,
    "La detección durante el canto deberá ejecutarse sobre bloques breves y entregar únicamente la nota estimada a la interfaz. Los procesos de mayor costo, como separación, alineación completa, detección de segmentos y generación textual, se realizarán fuera de ese ciclo para evitar bloqueos y latencia perceptible.",
)

add_heading(document, "2.9.2. Interfaz gráfica", 2)
add_body(
    document,
    "La interfaz actual utiliza Tkinter, biblioteca incluida con Python y basada en Tcl/Tk [26]. Esta elección permitió implementar el flujo funcional del prototipo con pocas dependencias adicionales. Sin embargo, sus posibilidades de diseño y componentes pueden resultar limitadas para la presentación final esperada.",
)
add_body(
    document,
    "Qt for Python constituye una alternativa para desarrollar una interfaz de escritorio con componentes más flexibles y una apariencia visual más elaborada [27]. La migración deberá evaluarse considerando tiempo de desarrollo, facilidad de distribución y reutilización de la lógica existente. Debido a la separación modular del proyecto, el cambio de interfaz no debería modificar los módulos responsables del análisis de audio.",
)

add_heading(document, "2.9.3. Almacenamiento", 2)
add_body(
    document,
    "El prototipo conserva canciones, grabaciones, archivos CSV y resultados JSON en el sistema de archivos. Este mecanismo es suficiente para inspeccionar los datos y mantener trazabilidad durante el desarrollo. A medida que aumenten las sesiones, consultar relaciones entre canciones, fechas, métricas y segmentos mediante archivos individuales puede resultar menos conveniente.",
)
add_body(
    document,
    "SQLite ofrece una base de datos autocontenida que opera directamente sobre un archivo y no requiere un servidor independiente [28]. Puede utilizarse para indexar canciones, sesiones, métricas y segmentos, mientras los audios permanecen como archivos. La adopción de SQLite se mantiene como decisión pendiente y dependerá de la complejidad alcanzada por el seguimiento histórico.",
)

add_heading(document, "2.9.4. Distribución y dependencias", 2)
add_body(
    document,
    "Durante el desarrollo, la aplicación se ejecuta como código Python con sus dependencias instaladas. Herramientas como PyInstaller permiten empaquetar una aplicación y sus módulos para ejecutarla sin que el usuario instale Python por separado [29]. No obstante, el tamaño de bibliotecas científicas, modelos de separación y posibles modelos de lenguaje puede aumentar considerablemente el paquete.",
)
add_body(
    document,
    "La distribución final podrá utilizar un ejecutable principal acompañado por recursos o dependencias instalables, en lugar de incorporar todos los modelos dentro de un único archivo. Demucs y un eventual modelo de lenguaje podrían descargarse durante la instalación, mantenerse como componentes externos o excluirse de una versión reducida. La estrategia se definirá después de medir tamaño, compatibilidad y tiempos de ejecución en el entorno objetivo.",
)

add_heading(document, "2.9.5. Criterios para el proyecto", 2)
add_body(
    document,
    "Se conservará Python para el procesamiento mientras permita cumplir los requisitos de latencia y distribución. La interfaz, el almacenamiento, el mecanismo de generación textual y el empaquetado se evaluarán como decisiones independientes. Esta separación evita que una elección pendiente bloquee el desarrollo de la contribución principal, centrada en el análisis segmentado y la retroalimentación.",
)

add_heading(document, "2.10. Trabajo relacionado", 2)
add_body(
    document,
    "Los trabajos relacionados combinan evaluación automática, visualización, alineación y procesamiento de grabaciones musicales, aunque no todos persiguen el mismo propósito. El Cuadro 2.1 resume los antecedentes más próximos a los componentes centrales de la propuesta.",
)

add_comparison_table(
    document,
    ["Trabajo", "Enfoque", "Salida principal", "Relación con la propuesta"],
    [
        ("Nakano et al. (2006) [18]", "Exactitud de intervalos de pitch y características de vibrato.", "Evaluación automática de habilidad de canto.", "Fundamenta el uso de características tonales; la propuesta agrega segmentos y trazabilidad."),
        ("MiruSinger (2007) [19]", "Comparación visual con grabaciones musicales de referencia.", "Visualización de pitch y retroalimentación en tiempo real.", "Se relaciona con la nota en tiempo real; la propuesta añade análisis posterior e historial."),
        ("Luo et al. (2018) [17]", "Alineación temporal entre una interpretación y una referencia.", "Corrección de la voz cantada.", "Comparte la necesidad de alineación, pero la propuesta analiza y no modifica la voz."),
        ("Demucs y HT Demucs [12], [13]", "Separación de fuentes musicales mediante aprendizaje profundo.", "Pistas vocales e instrumentales separadas.", "Proporciona la referencia vocal y el acompañamiento utilizados por el sistema."),
    ],
    [3.1, 4.1, 3.8, 5.0],
)

caption = document.add_paragraph()
caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
caption.paragraph_format.space_before = Pt(5)
caption.paragraph_format.space_after = Pt(8)
run = caption.add_run("Cuadro 2.1: Comparación de trabajos relacionados con la propuesta. Fuente: elaboración propia.")
format_run(run, size=10)

add_heading(document, "2.10.1. Diferenciación de la propuesta", 2)
add_body(
    document,
    "Los antecedentes revisados muestran soluciones para medir características del canto, visualizar una trayectoria tonal, alinear interpretaciones o preparar las fuentes musicales. La propuesta integra estas capacidades dentro de un flujo orientado a la práctica individual: preparación de la canción, detección de nota durante el canto, análisis posterior, localización de problemas y conservación de sesiones.",
)
add_body(
    document,
    "Su principal diferenciación prevista es que la retroalimentación no dependerá únicamente de un puntaje o de la inspección manual de un gráfico. El sistema buscará identificar intervalos variables donde ocurre un comportamiento relevante, conservar la evidencia que lo sustenta y comunicarlo mediante lenguaje natural. Además, la comparación histórica permitirá observar si estos comportamientos cambian al repetir una misma canción.",
)
add_body(
    document,
    "Estas capacidades corresponden a objetivos de desarrollo y deberán validarse experimentalmente. La revisión de trabajos relacionados no permite asumir por sí sola que la retroalimentación será correcta o útil; dichas propiedades deberán evaluarse con datos y usuarios durante las etapas posteriores del proyecto.",
)

add_heading(document, "2.11. Síntesis del capítulo", 2)
add_body(
    document,
    "El capítulo presentó los conceptos necesarios para representar la altura tonal, procesar señales de audio, estimar frecuencia fundamental, separar fuentes musicales y alinear temporalmente una interpretación con su referencia. Sobre esta base se definió un enfoque para detectar segmentos problemáticos a partir de evidencias locales y transformarlos en retroalimentación trazable.",
)
add_body(
    document,
    "También se establecieron los criterios para comparar sesiones y observar la evolución del usuario. Finalmente, se revisaron las tecnologías utilizadas o consideradas y se relacionó la propuesta con antecedentes de evaluación, visualización, alineación y separación musical. Estos fundamentos orientan la especificación y el diseño que se desarrollarán en los capítulos siguientes.",
)

add_heading(document, "Referencias incorporadas en este capítulo", 2)
add_reference(
    document,
    5,
    "J. H. McDermott y A. J. Oxenham, “Music Perception, Pitch, and the Auditory System,” Current Opinion in Neurobiology, vol. 18, n.º 4, pp. 452–463, 2008. Versión de acceso abierto disponible en: https://pmc.ncbi.nlm.nih.gov/articles/PMC2629434/.",
)
add_reference(
    document,
    6,
    "S. Dalla Bella, J.-F. Giguère e I. Peretz, “Singing Proficiency in the General Population,” The Journal of the Acoustical Society of America, vol. 121, n.º 2, pp. 1182–1189, 2007. doi: 10.1121/1.2427111.",
)
add_reference(
    document,
    7,
    "S. W. Smith, The Scientist and Engineer's Guide to Digital Signal Processing. California Technical Publishing, 1997. Disponible en: https://www.dspguide.com/.",
)
add_reference(
    document,
    8,
    "J. O. Smith III, Spectral Audio Signal Processing. W3K Publishing, 2011. Disponible en: https://ccrma.stanford.edu/~jos/sasp/.",
)
add_reference(
    document,
    9,
    "librosa development team, “librosa.pyin: Fundamental Frequency Estimation Using Probabilistic YIN,” documentación oficial de librosa. Disponible en: https://librosa.org/doc/latest/generated/librosa.pyin.html.",
)
add_reference(
    document,
    10,
    "M. Morise, “Harvest: A High-Performance Fundamental Frequency Estimator from Speech Signals,” Proceedings of Interspeech 2017, pp. 2321–2325, 2017. Disponible en: https://www.isca-archive.org/interspeech_2017/morise17b_interspeech.pdf.",
)
add_reference(
    document,
    11,
    "M. Morise, F. Yokomori y K. Ozawa, “WORLD: A Vocoder-Based High-Quality Speech Synthesis System for Real-Time Applications,” IEICE Transactions on Information and Systems, vol. E99.D, n.º 7, pp. 1877–1884, 2016. Disponible en: https://www.jstage.jst.go.jp/article/transinf/E99.D/7/E99.D_2015EDP7457/_pdf.",
)
add_reference(
    document,
    12,
    "A. Défossez, N. Usunier, L. Bottou y F. Bach, “Music Source Separation in the Waveform Domain,” arXiv:1911.13254, 2019. Disponible en: https://arxiv.org/pdf/1911.13254.",
)
add_reference(
    document,
    13,
    "S. Rouard, F. Massa y A. Défossez, “Hybrid Transformers for Music Source Separation,” Proceedings of ICASSP 2023, pp. 1–5, 2023. Disponible en: https://arxiv.org/pdf/2211.08553.",
)
add_reference(
    document,
    14,
    "R. Hennequin, A. Khlif, F. Voituret y M. Moussallam, “Spleeter: A Fast and Efficient Music Source Separation Tool with Pre-Trained Models,” Journal of Open Source Software, vol. 5, n.º 50, p. 2154, 2020. Disponible en: https://joss.theoj.org/papers/10.21105/joss.02154.pdf.",
)
add_reference(
    document,
    15,
    "M. Müller, “Dynamic Time Warping,” Fundamentals of Music Processing: Audio, Analysis, Algorithms, Applications, recurso complementario en línea. Disponible en: https://www.audiolabs-erlangen.de/resources/MIR/FMP/C3/C3S2_DTWbasic.html.",
)
add_reference(
    document,
    16,
    "librosa development team, “librosa.sequence.dtw: Dynamic Time Warping,” documentación oficial de librosa. Disponible en: https://librosa.org/doc/latest/generated/librosa.sequence.dtw.html.",
)
add_reference(
    document,
    17,
    "Y.-J. Luo, M.-T. Chen, T.-S. Chi y L. Su, “Singing Voice Correction Using Canonical Time Warping,” Proceedings of ICASSP 2018, pp. 156–160, 2018. Disponible en: https://arxiv.org/pdf/1711.08600.",
)
add_reference(
    document,
    18,
    "T. Nakano, M. Goto y Y. Hiraga, “An Automatic Singing Skill Evaluation Method for Unknown Melodies Using Pitch Interval Accuracy and Vibrato Features,” Proceedings of Interspeech 2006, 2006. Disponible en: https://www.isca-archive.org/interspeech_2006/nakano06_interspeech.pdf.",
)
add_reference(
    document,
    19,
    "T. Nakano, M. Goto y Y. Hiraga, “MiruSinger: A Singing Skill Visualization Interface Using Real-Time Feedback and Music CD Recordings as Referential Data,” Proceedings of the IEEE International Symposium on Multimedia Workshops, pp. 75–76, 2007. Disponible en: https://staff.aist.go.jp/m.goto/PAPER/ISM2007nakano.pdf.",
)
add_reference(
    document,
    20,
    "C. Truong, L. Oudre y N. Vayatis, “Selective Review of Offline Change Point Detection Methods,” Signal Processing, vol. 167, art. 107299, 2020. Disponible en: https://arxiv.org/pdf/1801.00718.",
)
add_reference(
    document,
    21,
    "A. Gatt y E. Krahmer, “Survey of the State of the Art in Natural Language Generation: Core Tasks, Applications and Evaluation,” Journal of Artificial Intelligence Research, vol. 61, pp. 65–170, 2018. Disponible en: https://www.jair.org/index.php/jair/article/download/11173/26378.",
)
add_reference(
    document,
    22,
    "Z. Ji et al., “Survey of Hallucination in Natural Language Generation,” ACM Computing Surveys, vol. 55, n.º 12, art. 248, 2023. Disponible en: https://arxiv.org/pdf/2202.03629.",
)
add_reference(
    document,
    23,
    "H. Touvron et al., “LLaMA: Open and Efficient Foundation Language Models,” arXiv:2302.13971, 2023. Disponible en: https://arxiv.org/pdf/2302.13971.",
)
add_reference(
    document,
    24,
    "G. Gerganov y colaboradores, “llama.cpp: LLM Inference in C/C++,” repositorio de software. Disponible en: https://github.com/ggml-org/llama.cpp.",
)
add_reference(
    document,
    25,
    "Python Software Foundation, “Python 3 Documentation.” Disponible en: https://docs.python.org/3/.",
)
add_reference(
    document,
    26,
    "Python Software Foundation, “tkinter — Python Interface to Tcl/Tk.” Disponible en: https://docs.python.org/3/library/tkinter.html.",
)
add_reference(
    document,
    27,
    "The Qt Company, “Qt for Python Documentation.” Disponible en: https://doc.qt.io/qtforpython-6/.",
)
add_reference(
    document,
    28,
    "SQLite Consortium, “About SQLite.” Disponible en: https://www.sqlite.org/about.html.",
)
add_reference(
    document,
    29,
    "PyInstaller Development Team, “PyInstaller Documentation.” Disponible en: https://pyinstaller.org/en/stable/.",
)

document.save(OUTPUT)
print(OUTPUT)
