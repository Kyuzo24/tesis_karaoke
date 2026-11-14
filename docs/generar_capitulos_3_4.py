from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_ROW_HEIGHT_RULE, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / "docs" / "figuras"
OUTPUT_3 = ROOT / "Capitulo_3_Metodologia.docx"
OUTPUT_4 = ROOT / "Capitulo_4_Desarrollo.docx"


def format_run(run, size=12, bold=False, italic=False, color=None):
    run.font.name = "Times New Roman"
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "Times New Roman")
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    if color:
        run.font.color.rgb = RGBColor.from_string(color)


def configure(document):
    section = document.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.5)
    styles = document.styles
    styles["Normal"].font.name = "Times New Roman"
    styles["Normal"]._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    styles["Normal"].font.size = Pt(12)


def add_title(document, value):
    p = document.add_paragraph()
    p.paragraph_format.space_after = Pt(14)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(value)
    format_run(r, 16, True)


def add_heading(document, value, level=1):
    p = document.add_paragraph()
    p.paragraph_format.space_before = Pt(13 if level == 1 else 9)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(value)
    format_run(r, 14 if level == 1 else 12, True)
    return p


def add_body(document, value):
    p = document.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.space_after = Pt(6)
    format_run(p.add_run(value))
    return p


def set_cell_margins(cell, top=80, start=90, bottom=80, end=90):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for margin, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{margin}"))
        if node is None:
            node = OxmlElement(f"w:{margin}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def shade(cell, color):
    node = OxmlElement("w:shd")
    node.set(qn("w:fill"), color)
    cell._tc.get_or_add_tcPr().append(node)


def add_table(document, headers, rows, widths, font_size=9):
    table = document.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.style = "Table Grid"
    for i, (header, width) in enumerate(zip(headers, widths)):
        cell = table.rows[0].cells[i]
        cell.width = Cm(width)
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        shade(cell, "DCEAF7")
        set_cell_margins(cell)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        format_run(p.add_run(header), font_size, True)
    for row_values in rows:
        cells = table.add_row().cells
        for i, (value, width) in enumerate(zip(row_values, widths)):
            cells[i].width = Cm(width)
            cells[i].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            set_cell_margins(cells[i])
            p = cells[i].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_after = Pt(0)
            format_run(p.add_run(value), font_size)
    document.add_paragraph().paragraph_format.space_after = Pt(1)
    return table


def add_caption(document, value):
    p = document.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(8)
    format_run(p.add_run(value), 10)


def add_figure(document, path, caption, width=16):
    p = document.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(3)
    p.add_run().add_picture(str(path), width=Cm(width))
    add_caption(document, caption)


def add_placeholder(document):
    table = document.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    cell = table.cell(0, 0)
    cell.width = Cm(16)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    shade(cell, "F8FAFC")
    row = table.rows[0]
    row.height = Cm(10.5)
    row.height_rule = WD_ROW_HEIGHT_RULE.EXACTLY
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    format_run(p.add_run("ESPACIO RESERVADO PARA EL MODELO DE DATOS"), 12, True, color="5B6472")
    p2 = cell.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    format_run(p2.add_run("Sustituir este recuadro por el diagrama elaborado por el autor."), 10, italic=True, color="5B6472")
    add_caption(document, "Figura 4.3: Modelo de datos del sistema. Fuente: elaboración propia.")


def add_reference(document, number, value):
    p = document.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.left_indent = Cm(0.75)
    p.paragraph_format.first_line_indent = Cm(-0.75)
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(5)
    format_run(p.add_run(f"[{number}] {value}"), 10)


def build_chapter_3():
    document = Document()
    configure(document)
    add_title(document, "3. Metodología")
    add_body(document, "Este capítulo describe la metodología utilizada para organizar el desarrollo individual del sistema, la forma en que los requisitos se integran con las historias de usuario y las iteraciones, y los procedimientos previstos para evaluar los resultados. Debido a que el proyecto se encuentra al cierre del primer semestre y presenta una implementación parcial, se distingue entre actividades ejecutadas, componentes en desarrollo y etapas planificadas para el segundo semestre.")

    add_heading(document, "3.1. Metodología de desarrollo", 1)
    add_body(document, "Se adoptó Personal Extreme Programming (PXP), una adaptación de los principios de Extreme Programming para proyectos desarrollados principalmente por una persona. PXP conserva un trabajo iterativo, la priorización de requisitos, la estimación de tareas, la implementación incremental y la revisión frecuente de los resultados. Estudios comparativos describen esta metodología como una alternativa flexible para detectar errores y ajustar la planificación durante el desarrollo [30].")
    add_body(document, "La metodología resulta apropiada para este proyecto porque sus componentes poseen incertidumbres técnicas distintas. La separación de fuentes, la estimación de pitch, el procesamiento en tiempo real, la alineación y la generación de retroalimentación requieren pruebas antes de cerrar parámetros o decisiones tecnológicas. Una planificación estrictamente secuencial dificultaría incorporar los resultados de estas pruebas en las etapas posteriores.")
    add_body(document, "La adaptación utilizada organiza el trabajo en cinco momentos: revisión de requisitos, planificación, iteración técnica, revisión del resultado y registro del avance. Cada iteración produce un incremento verificable y actualiza las estimaciones de la siguiente, como se muestra en la Figura 3.1.")
    add_figure(document, FIGURES / "figura_3_1_ciclo_pxp.png", "Figura 3.1: Ciclo PXP adaptado al desarrollo del proyecto. Fuente: elaboración propia.")

    add_heading(document, "3.1.1. Integración de requisitos e historias de usuario", 2)
    add_body(document, "La especificación contiene 29 requisitos funcionales y 16 requisitos no funcionales. Para evitar que el capítulo se convierta en una repetición de las 45 fichas individuales, los requisitos se presentan agrupados por capacidad del sistema. Las especificaciones completas se mantienen en el documento complementario de requisitos, mientras que las historias de usuario expresan el valor esperado y permiten asignar cada capacidad a una iteración.")
    add_body(document, "El Cuadro 3.1 relaciona las capacidades principales con sus requisitos, historias e iteraciones. El estado corresponde al cierre del primer semestre y utiliza las categorías implementado, parcial y pendiente.")
    add_table(document,
        ["Capacidad", "Requisitos", "Historias", "Iteración", "Estado"],
        [
            ("Catálogo y preparación de canciones", "RF01–RF06", "HU01–HU03", "1", "Implementado"),
            ("Sesión de canto y visualización", "RF07–RF15", "HU04–HU07", "2", "Parcial; falta nota en tiempo real"),
            ("Comparación y análisis segmentado", "RF16–RF20", "HU08–HU10", "3", "Parcial; existe alineación y métricas base"),
            ("Retroalimentación y consulta", "RF21–RF23", "HU11–HU12", "4", "Pendiente"),
            ("Evolución entre sesiones", "RF27–RF29", "HU13", "4", "Pendiente"),
            ("Operación y decisiones abiertas", "RF24–RF26", "HU14 y tareas transversales", "Transversal", "Mixto; diagnóstico técnico disponible"),
        ], [4.2, 3.0, 3.2, 2.0, 4.0], 8)
    add_caption(document, "Cuadro 3.1: Integración de capacidades, requisitos e historias de usuario. Fuente: elaboración propia.")
    add_body(document, "Los requisitos no funcionales se aplican de manera transversal y condicionan la aceptación de los requisitos funcionales. Por ejemplo, detectar una nota no se considera suficiente si la latencia impide utilizarla durante el canto; del mismo modo, una retroalimentación redactada correctamente debe conservar trazabilidad con los segmentos y métricas que la originaron.")
    add_table(document,
        ["Área transversal", "Requisitos no funcionales", "Aplicación principal"],
        [
            ("Interacción y tiempo real", "RNF01, RNF02, RNF04–RNF07", "Usabilidad, claridad, evolución gráfica, latencia y continuidad."),
            ("Calidad del análisis", "RNF08, RNF11, RNF12", "Robustez acústica, trazabilidad y explicabilidad."),
            ("Arquitectura y mantenimiento", "RNF03, RNF13", "Separación modular y facilidad de modificación."),
            ("Datos, privacidad y distribución", "RNF09, RNF10, RNF14–RNF16", "Persistencia local, dependencias, ejecutable y trabajo sin conexión."),
        ], [4.0, 4.1, 8.3], 9)
    add_caption(document, "Cuadro 3.2: Aplicación transversal de los requisitos no funcionales. Fuente: elaboración propia.")

    add_heading(document, "3.1.2. Planificación de iteraciones", 2)
    add_body(document, "Las historias se distribuyeron en cuatro iteraciones funcionales y una etapa de cierre. La asignación mantiene primero la preparación de canciones y la captura, luego la comparación, y finalmente las funciones que dependen de resultados estructurados. La Carta Gantt adjunta contiene el detalle semanal de las tareas durante los dos semestres.")
    add_table(document,
        ["Etapa", "Semanas", "Objetivo", "Entregable", "Estado"],
        [
            ("Iteración 1", "1–6", "Preparar canciones y referencias.", "Catálogo, stems, instrumental y pitch de referencia.", "Completada"),
            ("Iteración 2", "7–15", "Integrar la sesión de canto.", "Reproducción, captura, guardado e interfaz prototipo.", "Parcial"),
            ("Iteración 3", "16–22", "Completar análisis temporal.", "Nota en tiempo real, DTW refinado, métricas y segmentos.", "Planificada"),
            ("Iteración 4", "23–28", "Comunicar resultados y evolución.", "Retroalimentación, persistencia y comparación histórica.", "Planificada"),
            ("Cierre", "29–30", "Evaluar y documentar.", "Pruebas, ajustes y memoria final.", "Planificada"),
        ], [2.4, 1.7, 4.0, 5.8, 2.5], 8)
    add_caption(document, "Cuadro 3.3: Distribución general de iteraciones. Fuente: elaboración propia.")

    add_heading(document, "3.1.3. Procedimiento de una iteración", 2)
    add_body(document, "Al comienzo de cada iteración se seleccionan las historias y requisitos que pueden producir un incremento verificable. Estos elementos se dividen en tareas técnicas y se estiman considerando dependencias, pruebas necesarias y riesgos. Cuando existe incertidumbre sobre una biblioteca o algoritmo, se realiza primero una prueba de concepto acotada.")
    add_body(document, "Durante la implementación se mantienen separadas las responsabilidades de catálogo, separación, captura, extracción de pitch, comparación, métricas, visualización y persistencia. Cada incremento se verifica con entradas normales, casos sin pitch suficiente y errores operacionales. Las incidencias encontradas se registran para corregir el código o modificar los parámetros antes de continuar.")
    add_body(document, "La revisión final compara el incremento con los criterios de los requisitos asignados. Un requisito se clasifica como implementado solo cuando su flujo principal se encuentra disponible; los elementos que poseen una parte funcional pero requieren validación o integración permanecen parciales.")

    add_heading(document, "3.1.4. Estado al cierre del primer semestre", 2)
    add_body(document, "La revisión conservadora de los 45 requisitos identifica 16 implementados, 14 parciales y 15 pendientes. Considerando únicamente los requisitos completados, el avance funcional corresponde al 35,6 %. Este porcentaje supera el mínimo esperado para la entrega, pero no representa el porcentaje de escritura de la memoria ni una validación definitiva del sistema.")
    add_table(document, ["Estado", "Cantidad", "Proporción"], [
        ("Implementados", "16", "35,6 %"),
        ("Parciales", "14", "31,1 %"),
        ("Pendientes", "15", "33,3 %"),
        ("Total", "45", "100 %"),
    ], [6.0, 4.0, 4.0], 10)
    add_caption(document, "Cuadro 3.4: Estado de requisitos al cierre del primer semestre. Fuente: elaboración propia.")

    add_heading(document, "3.2. Metodología de evaluación", 1)
    add_body(document, "La evaluación combinará mediciones técnicas, pruebas funcionales y una revisión cualitativa de utilidad. Estas evaluaciones se aplicarán progresivamente: durante el desarrollo para comparar configuraciones y, al final, sobre un conjunto estable de funciones y datos.")

    add_heading(document, "3.2.1. Evaluación cuantitativa", 2)
    add_body(document, "La evaluación cuantitativa medirá el comportamiento de los módulos acústicos mediante audios y referencias conocidas. Siempre que sea posible se utilizarán señales con notas o trayectorias controladas, complementadas con grabaciones representativas de las condiciones de uso. Los resultados se conservarán junto con la configuración utilizada para permitir su repetición.")
    add_table(document,
        ["Indicador", "Cálculo o unidad", "Propósito"],
        [
            ("Detecciones válidas de F0", "Porcentaje de bloques con estimación confiable.", "Revisar cobertura del estimador."),
            ("Error tonal", "Diferencia absoluta y firmada en cents.", "Medir precisión y tendencia de afinación."),
            ("Estabilidad", "Dispersión de cents en regiones sostenidas.", "Examinar fluctuaciones temporales."),
            ("Latencia", "Milisegundos entre captura y nota mostrada.", "Validar la detección en tiempo real."),
            ("Alineación", "Costo DTW y correspondencias revisadas.", "Detectar deformaciones incorrectas."),
            ("Segmentación", "Coincidencia con intervalos anotados.", "Evaluar límites, categorías y omisiones."),
        ], [4.0, 6.0, 6.0], 9)
    add_caption(document, "Cuadro 3.5: Indicadores cuantitativos previstos. Fuente: elaboración propia.")

    add_heading(document, "3.2.2. Pruebas funcionales", 2)
    add_body(document, "Las pruebas funcionales se diseñarán a partir de los requisitos y tratarán cada módulo como una caja negra. Para cada caso se registrarán precondiciones, entrada, procedimiento, salida esperada, salida obtenida y estado. Se incluirán tanto recorridos correctos como entradas incompletas, archivos inexistentes, silencios y fallas de dependencias.")
    add_table(document,
        ["Grupo de prueba", "Ejemplos", "Resultado esperado"],
        [
            ("Preparación", "Audio válido, archivo incompatible, separación fallida.", "Canción preparada o error comprensible sin pérdida del catálogo."),
            ("Sesión", "Inicio, detención manual, fin de pista, micrófono no disponible.", "Captura sincronizada y retorno a un estado consistente."),
            ("Análisis", "Pitch suficiente, silencios extensos, secuencias desiguales.", "Métricas trazables o indicación de datos insuficientes."),
            ("Resultados", "Segmentos múltiples, ausencia de hallazgos, sesiones comparables.", "Mensajes coherentes y datos persistentes."),
        ], [3.5, 6.4, 6.1], 9)
    add_caption(document, "Cuadro 3.6: Grupos de pruebas funcionales previstos. Fuente: elaboración propia.")

    add_heading(document, "3.2.3. Evaluación cualitativa", 2)
    add_body(document, "Cuando el flujo final esté disponible se realizarán pruebas de aceptación con usuarios. La evaluación buscará determinar si la información entregada es comprensible, si los segmentos pueden localizarse en la grabación y si las observaciones resultan útiles para repetir la práctica. También se registrarán dificultades de interacción, aunque el diseño gráfico definitivo aún no se encuentra establecido.")
    add_body(document, "Las respuestas combinarán preguntas cerradas y comentarios abiertos. La evaluación no solicitará a los usuarios validar diagnósticos clínicos ni técnica vocal especializada; se concentrará en claridad, coherencia, utilidad percibida y correspondencia entre audio, gráfico y texto.")

    add_heading(document, "3.2.4. Validación de la retroalimentación", 2)
    add_body(document, "La retroalimentación se validará en dos niveles. Primero se comprobará automáticamente que los tiempos, categorías y valores mencionados existan en los hallazgos estructurados. Luego se revisará cualitativamente que el mensaje no agregue causas no observadas, no contradiga las métricas y utilice un lenguaje comprensible. Este procedimiento será común para plantillas y para un eventual modelo de lenguaje.")

    add_heading(document, "3.3. Resultados esperados y evidencia actual", 1)
    add_body(document, "Al finalizar el proyecto se espera disponer de una aplicación local capaz de preparar canciones, mostrar la nota detectada durante el canto, comparar una grabación con su referencia, localizar segmentos problemáticos, explicar los principales hallazgos y comparar sesiones realizadas sobre una misma canción.")
    add_body(document, "La evidencia actual cubre la gestión del catálogo, separación de fuentes, generación del acompañamiento, extracción y filtrado de pitch, reproducción y captura, almacenamiento de la interpretación, alineación DTW inicial, métricas globales y visualización mediante una interfaz prototipo. Permanecen pendientes la detección de nota en tiempo real, el análisis dinámico de segmentos, la retroalimentación en lenguaje natural, la comparación histórica y la validación integral.")

    add_heading(document, "3.4. Síntesis del capítulo", 1)
    add_body(document, "El capítulo definió un proceso PXP adaptado al desarrollo individual y relacionó requisitos, historias e iteraciones sin duplicar las fichas de especificación. También estableció una estrategia de evaluación cuantitativa, funcional y cualitativa. Esta metodología permite continuar desde la base implementada hacia los componentes de análisis avanzado manteniendo trazabilidad y una medición conservadora del avance.")

    add_heading(document, "Referencia incorporada", 1)
    add_reference(document, 30, "S. A. Asri, I. G. M. A. Sunaya, P. M. Prihatini y W. Setiawan, “Comparing Traditional and Agile Software Development Approaches: Case of Personal Extreme Programming,” Proceedings of ICST 2018, 2018. Disponible en: https://www.atlantis-press.com/article/55910901.pdf.")
    document.save(OUTPUT_3)


def build_chapter_4():
    document = Document()
    configure(document)
    add_title(document, "4. Desarrollo")
    add_body(document, "Este capítulo presenta el diseño técnico del sistema y el estado de la implementación alcanzado al cierre del primer semestre. La descripción se concentra en los componentes existentes y en las decisiones necesarias para completar el proyecto. Las funcionalidades futuras se identifican como pendientes y no se presentan como resultados implementados.")

    add_heading(document, "4.1. Diseño de software", 1)
    add_body(document, "El diseño busca aislar la interacción gráfica de los procesos acústicos y de análisis. Esta separación permite sustituir la interfaz Tkinter utilizada por el prototipo sin reescribir los módulos de catálogo, separación, captura, pitch o comparación. También permite evaluar de manera independiente el almacenamiento mediante archivos o SQLite y la generación de texto mediante plantillas o un modelo de lenguaje.")
    add_body(document, "No se incluye un apartado de diseño de interfaz ni mockups en esta versión, debido a que la tecnología gráfica definitiva y la organización visual continúan pendientes. Esta omisión no afecta la descripción de los contratos entre la capa de presentación y los módulos internos, que sí forman parte de la arquitectura.")

    add_heading(document, "4.1.1. Arquitectura física", 2)
    add_body(document, "El sistema se ejecuta principalmente en un computador local con Windows. El usuario utiliza un micrófono para la captura y audífonos o parlantes para escuchar el acompañamiento. En el mismo equipo se ejecutan la aplicación de escritorio, las bibliotecas de audio, los modelos preentrenados y el almacenamiento de canciones, grabaciones y resultados.")
    add_body(document, "La operación principal no requiere un servidor. De manera opcional puede existir conexión para descargar modelos o utilizar un servicio de lenguaje remoto, si esa alternativa fuera seleccionada. Estos componentes no deben considerarse obligatorios mientras la estrategia de distribución y la integración del LLM permanezcan en evaluación.")
    add_figure(document, FIGURES / "figura_4_1_arquitectura_fisica.png", "Figura 4.1: Arquitectura física de ejecución local. Fuente: elaboración propia con recurso visual generado mediante IA.")

    add_heading(document, "4.1.2. Arquitectura lógica", 2)
    add_body(document, "La arquitectura lógica se organiza en presentación, coordinación, procesamiento de audio, análisis posterior y persistencia. La presentación recibe comandos y muestra información, pero no realiza cálculos acústicos. La coordinación administra el catálogo y el ciclo de una sesión, invocando módulos especializados según corresponda.")
    add_body(document, "El procesamiento de audio reúne la separación de fuentes, reproducción, captura y estimación de pitch. Parte de este trabajo ocurre antes de cantar, otra parte durante la sesión y otra después de detener la grabación. El análisis posterior alinea las trayectorias, calcula métricas y, en la versión prevista, detectará segmentos, generará retroalimentación y comparará sesiones.")
    add_body(document, "La persistencia conserva archivos musicales y datos derivados. Las dependencias apuntan hacia módulos internos, de modo que los algoritmos no dependan de una interfaz específica. La Figura 4.2 presenta esta organización e incorpora una representación conceptual del flujo completo.")
    add_figure(document, FIGURES / "figura_4_2_arquitectura_logica.png", "Figura 4.2: Arquitectura lógica del sistema. Fuente: elaboración propia con recurso visual generado mediante IA.")

    add_table(document,
        ["Componente", "Responsabilidad", "Implementación actual", "Estado"],
        [
            ("Presentación", "Comandos, estado y visualización.", "app.py y visualización Tkinter.", "Prototipo; reemplazable"),
            ("Catálogo", "Registrar, seleccionar y eliminar canciones.", "audio/catalogo.py", "Implementado"),
            ("Separación", "Obtener voz, instrumental y stems.", "audio/separacion.py y Demucs.", "Implementado"),
            ("Pitch", "Extraer, filtrar y convertir F0.", "audio/pitch.py con Pyworld/librosa.", "Implementado fuera del ciclo en tiempo real"),
            ("Sesión", "Reproducir, capturar y detener.", "audio/karaoke.py", "Implementado"),
            ("Comparación", "Alinear y calcular métricas.", "audio/comparacion.py y audio/metricas.py", "Parcial; requiere validación"),
            ("Segmentos", "Detectar, caracterizar y priorizar.", "Contrato definido.", "Pendiente"),
            ("Retroalimentación", "Redactar hallazgos verificables.", "Alternativas definidas.", "Pendiente"),
            ("Historial", "Comparar sesiones y evolución.", "Requisitos y datos definidos.", "Pendiente"),
            ("Persistencia", "Guardar audios y resultados.", "audio/guardar.py, CSV y JSON.", "Parcial; SQLite por evaluar"),
        ], [3.0, 5.0, 5.2, 3.0], 8)
    add_caption(document, "Cuadro 4.1: Responsabilidades y estado de los componentes lógicos. Fuente: elaboración propia.")

    add_heading(document, "4.1.3. Modelo de datos", 2)
    add_body(document, "El modelo de datos deberá representar al menos las entidades Canción, Referencia, Sesión, Grabación, Métrica, Segmento y Retroalimentación. Una canción puede poseer una referencia preparada y múltiples sesiones; cada sesión conserva su grabación, resultados derivados y configuración de análisis. Los segmentos se relacionan con intervalos temporales de una sesión y pueden utilizarse posteriormente para comparar dificultades entre fechas.")
    add_body(document, "Actualmente estas relaciones se materializan mediante carpetas, archivos WAV, CSV, JSON y metadatos. Si se adopta SQLite [28], los archivos de audio pueden permanecer en el sistema de archivos y la base de datos almacenar sus rutas y relaciones. El siguiente espacio queda reservado para incorporar el diagrama definitivo elaborado por el autor.")
    add_placeholder(document)

    add_heading(document, "4.2. Implementación actual", 1)
    add_heading(document, "4.2.1. Gestión y preparación de canciones", 2)
    add_body(document, "El catálogo copia cada canción a una carpeta identificable y conserva metadatos básicos. La preparación ejecuta HT Demucs [13] para separar vocals, drums, bass y other. Los componentes instrumentales se combinan para obtener el acompañamiento y la pista vocals se utiliza para calcular la referencia tonal. Los resultados se reutilizan en sesiones posteriores para evitar repetir un procesamiento costoso.")
    add_body(document, "La referencia se almacena como una secuencia temporal con frecuencia y nota aproximada. Su estimación utiliza Pyworld, que proporciona acceso a procedimientos de WORLD [11], y pYIN como alternativa. Antes de guardar los datos se aplican filtros de rango, energía, duración y estabilidad. El sistema permite reprocesar la referencia cuando se modifican los parámetros o cuando el resultado inicial contiene pocos puntos válidos.")

    add_heading(document, "4.2.2. Sesión de canto", 2)
    add_body(document, "Durante una sesión, el módulo de karaoke reproduce el acompañamiento y captura simultáneamente el micrófono. El usuario puede detener manualmente o esperar el final de la pista. La grabación se guarda dentro de la carpeta asociada con la canción y se entrega al flujo de comparación.")
    add_body(document, "La interfaz prototipo mantiene el estado de los controles durante los procesos largos y ejecuta preparación o comparación sin bloquear el flujo principal. La visualización de la nota detectada en bloques de baja latencia todavía no se encuentra integrada; por ello, la estimación actual del usuario se realiza después de finalizar la grabación.")

    add_heading(document, "4.2.3. Comparación y métricas", 2)
    add_body(document, "El pitch de la grabación se procesa mediante los mismos criterios generales de validez utilizados para la referencia. Las secuencias resultantes se alinean mediante DTW [16] y se transforman a cents para calcular error absoluto, tendencia firmada, dispersión y proporción de puntos dentro de tolerancias de 50 y 100 cents.")
    add_body(document, "Los resultados se muestran mediante curvas temporales y valores resumidos. Este análisis constituye una base funcional, pero aún requiere validar la alineación, revisar el comportamiento frente a silencios y conservar las correspondencias necesarias para delimitar segmentos problemáticos.")

    add_heading(document, "4.2.4. Persistencia y diagnóstico técnico", 2)
    add_body(document, "Las canciones, stems, referencias, grabaciones y resultados se conservan localmente. Los resultados de una sesión utilizan un archivo estructurado que incluye métricas y datos suficientes para reconstruir la visualización. El prototipo también dispone de un diagnóstico de filtros que compara la cantidad de puntos de pitch antes y después de la limpieza.")
    add_body(document, "Este diagnóstico apoya el desarrollo y no constituye una evaluación de la calidad vocal del usuario. Su permanencia en la versión final dependerá de su utilidad para validar configuraciones y explicar casos donde no exista información suficiente.")

    add_heading(document, "4.3. Desarrollo pendiente", 1)
    add_body(document, "El segundo semestre concentrará la contribución principal del proyecto. Primero se incorporará la estimación de nota en tiempo real mediante bloques, con medición de latencia y estabilización. Después se refinará la alineación y se implementará la formación dinámica de segmentos, su caracterización y priorización.")
    add_body(document, "Sobre los hallazgos estructurados se construirá la retroalimentación mediante plantillas y se evaluará si un modelo de lenguaje aporta claridad suficiente para justificar su integración. Finalmente se implementará la persistencia histórica, la comparación entre sesiones y el resumen de evolución.")
    add_body(document, "Las decisiones sobre interfaz definitiva, SQLite, empaquetado ejecutable, distribución de Demucs y ejecución local o remota del LLM se resolverán mediante pruebas de tamaño, rendimiento y esfuerzo de integración. Para el empaquetado se considerará PyInstaller [29], sin asumir que todos los modelos deban quedar contenidos en un único archivo. Ninguna de estas decisiones modifica el contrato central entre captura, análisis, segmentos y retroalimentación.")
    add_table(document,
        ["Línea pendiente", "Dependencias", "Resultado verificable"],
        [
            ("Nota en tiempo real", "Captura por bloques y estimador de F0.", "Nota estable con latencia medida."),
            ("Segmentos problemáticos", "DTW refinado, métricas locales y confianza.", "Intervalos con tipo, evidencia y prioridad."),
            ("Retroalimentación", "Hallazgos estructurados y validador.", "Texto coherente sin afirmaciones inventadas."),
            ("Evolución", "Persistencia de sesiones comparables.", "Cambios mejorados, persistentes o empeorados."),
            ("Distribución final", "Interfaz, dependencias y modelos seleccionados.", "Instalación reproducible en Windows."),
        ], [4.2, 5.7, 6.1], 9)
    add_caption(document, "Cuadro 4.2: Líneas de desarrollo pendientes y resultados verificables. Fuente: elaboración propia.")

    add_heading(document, "4.4. Limitaciones del diseño actual", 1)
    add_body(document, "La referencia depende de la calidad de la separación vocal y puede contener filtraciones instrumentales. La captura del micrófono puede incorporar ruido, latencia o acompañamiento reproducido por parlantes. DTW puede generar correspondencias incorrectas cuando la interpretación se aleja demasiado de la canción y las métricas globales pueden ocultar regiones breves.")
    add_body(document, "El diseño reduce estos riesgos mediante confianza, filtros, trazabilidad y separación entre análisis y redacción, pero no los elimina. La evaluación deberá determinar bajo qué condiciones el sistema produce resultados suficientemente confiables y cuándo corresponde informar que no existen datos adecuados para analizar.")

    add_heading(document, "4.5. Síntesis del capítulo", 1)
    add_body(document, "El capítulo describió una arquitectura local y modular que separa presentación, coordinación, procesamiento, análisis y persistencia. Se documentaron los componentes implementados durante el primer semestre y las funciones que permanecen pendientes. La interfaz definitiva se excluyó deliberadamente y el espacio para el modelo de datos quedó preparado para incorporar el diagrama elaborado por el autor.")

    add_heading(document, "Referencias técnicas citadas", 1)
    add_reference(document, 11, "M. Morise, F. Yokomori y K. Ozawa, “WORLD: A Vocoder-Based High-Quality Speech Synthesis System for Real-Time Applications,” IEICE Transactions on Information and Systems, 2016. Disponible en: https://www.jstage.jst.go.jp/article/transinf/E99.D/7/E99.D_2015EDP7457/_pdf.")
    add_reference(document, 13, "S. Rouard, F. Massa y A. Défossez, “Hybrid Transformers for Music Source Separation,” Proceedings of ICASSP 2023, 2023. Disponible en: https://arxiv.org/pdf/2211.08553.")
    add_reference(document, 16, "librosa development team, “librosa.sequence.dtw: Dynamic Time Warping,” documentación oficial. Disponible en: https://librosa.org/doc/latest/generated/librosa.sequence.dtw.html.")
    add_reference(document, 28, "SQLite Consortium, “About SQLite.” Disponible en: https://www.sqlite.org/about.html.")
    add_reference(document, 29, "PyInstaller Development Team, “PyInstaller Documentation.” Disponible en: https://pyinstaller.org/en/stable/.")
    document.save(OUTPUT_4)


if __name__ == "__main__":
    build_chapter_3()
    build_chapter_4()
    print(OUTPUT_3)
    print(OUTPUT_4)
