from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "Puntos_1.6_y_1.7.docx"


def set_font(run, size=12, bold=False, italic=False):
    run.font.name = "Times New Roman"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic


def set_cell_shading(cell, fill):
    properties = cell._tc.get_or_add_tcPr()
    shading = properties.find(qn("w:shd"))
    if shading is None:
        shading = OxmlElement("w:shd")
        properties.append(shading)
    shading.set(qn("w:fill"), fill)


def set_cell_border(cell, size=8, color="000000"):
    properties = cell._tc.get_or_add_tcPr()
    borders = properties.first_child_found_in("w:tcBorders")
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        properties.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = "w:" + edge
        node = borders.find(qn(tag))
        if node is None:
            node = OxmlElement(tag)
            borders.append(node)
        node.set(qn("w:val"), "single")
        node.set(qn("w:sz"), str(size))
        node.set(qn("w:color"), color)


def add_heading(document, text, level):
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_before = Pt(12 if level == 1 else 8)
    paragraph.paragraph_format.space_after = Pt(6)
    paragraph.paragraph_format.keep_with_next = True
    run = paragraph.add_run(text)
    set_font(run, size=14 if level == 1 else 12, bold=True)
    return paragraph


def add_body(document, text):
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    paragraph.paragraph_format.line_spacing = 1.5
    paragraph.paragraph_format.space_after = Pt(6)
    run = paragraph.add_run(text)
    set_font(run)
    return paragraph


def add_numbered_stage(document, number, title, description):
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    paragraph.paragraph_format.left_indent = Cm(0.5)
    paragraph.paragraph_format.first_line_indent = Cm(-0.5)
    paragraph.paragraph_format.line_spacing = 1.5
    paragraph.paragraph_format.space_after = Pt(5)
    run = paragraph.add_run(f"{number}. {title}: ")
    set_font(run, bold=True)
    run = paragraph.add_run(description)
    set_font(run)


def style_table(table, header=True):
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    for row_index, row in enumerate(table.rows):
        for cell in row.cells:
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            set_cell_border(cell)
            if header and row_index == 0:
                set_cell_shading(cell, "D9E2F3")
            for paragraph in cell.paragraphs:
                paragraph.paragraph_format.space_before = Pt(2)
                paragraph.paragraph_format.space_after = Pt(2)
                paragraph.paragraph_format.line_spacing = 1.0
                for run in paragraph.runs:
                    set_font(run, size=10, bold=(header and row_index == 0))


def add_caption(document, text):
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_before = Pt(5)
    paragraph.paragraph_format.space_after = Pt(8)
    run = paragraph.add_run(text)
    set_font(run, size=10)


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

add_heading(document, "1.6. Plan de trabajo", 1)

add_body(
    document,
    "El desarrollo del proyecto se organiza de manera incremental, distribuyendo las actividades desde la definición inicial hasta la evaluación del sistema. La planificación considera la construcción progresiva de los componentes, permitiendo validar cada módulo antes de integrarlo con los restantes.",
)
add_body(
    document,
    "La distribución temporal, duración y estado de las actividades se presentan detalladamente en la Carta Gantt adjunta a esta entrega.",
)

add_heading(document, "1.6.1. Descripción de las etapas del proyecto", 2)
add_body(document, "El plan de trabajo se divide en las siguientes etapas:")

stages = [
    ("Planificación y diseño", "comprende la definición del problema, los objetivos, el alcance, la metodología, los requisitos, las historias de usuario y la arquitectura inicial del sistema."),
    ("Base del sistema", "considera la gestión local de canciones, la separación de voz y acompañamiento, la extracción del pitch de referencia, la reproducción de la pista instrumental y la captura del micrófono."),
    ("Comparación y métricas", "incluye la alineación entre la interpretación del usuario y la referencia, el cálculo de métricas de afinación, la visualización de resultados y su almacenamiento inicial."),
    ("Interfaz prototipo", "corresponde al desarrollo de una primera interfaz que permita integrar el catálogo, la preparación de canciones, las sesiones de canto y la presentación de resultados."),
    ("Detección de notas en tiempo real", "contempla la captura continua mediante bloques de audio, la estimación y estabilización de la frecuencia fundamental, la conversión a notas musicales y la evaluación de la latencia."),
    ("Análisis avanzado", "considera el refinamiento de la alineación y las métricas temporales, junto con la detección, caracterización y priorización de segmentos problemáticos."),
    ("Generación de retroalimentación", "comprende la transformación de los hallazgos estructurados en observaciones en lenguaje natural y la validación de su coherencia y explicabilidad."),
    ("Persistencia, evolución e interfaz final", "incluye el almacenamiento estructurado de las sesiones, la comparación histórica de interpretaciones, la visualización de la evolución y la integración de la interfaz definitiva."),
    ("Evaluación y cierre", "contempla las pruebas funcionales, la evaluación técnica y de usabilidad, las correcciones finales y la documentación del proyecto."),
]
for index, (title, description) in enumerate(stages, 1):
    add_numbered_stage(document, index, title, description)

add_heading(document, "1.6.2. Relación entre objetivos y etapas", 2)
add_body(
    document,
    "Las actividades fueron definidas para responder a los objetivos específicos del proyecto. El Cuadro 1.1 presenta la relación principal entre ambos elementos.",
)

objective_rows = [
    ("Analizar y seleccionar técnicas de procesamiento de audio", "Planificación y diseño"),
    ("Preparar canciones y obtener una referencia tonal", "Base del sistema"),
    ("Detectar notas musicales en tiempo real", "Detección de notas en tiempo real"),
    ("Transformar el pitch en representaciones musicales", "Base del sistema y detección en tiempo real"),
    ("Alinear y comparar interpretaciones", "Comparación y métricas; análisis avanzado"),
    ("Definir métricas cuantitativas", "Comparación y métricas; análisis avanzado"),
    ("Detectar y priorizar segmentos problemáticos", "Análisis avanzado"),
    ("Generar retroalimentación en lenguaje natural", "Generación de retroalimentación"),
    ("Comparar sesiones y representar la evolución", "Persistencia, evolución e interfaz final"),
    ("Implementar una interfaz interactiva", "Interfaz prototipo e interfaz final"),
    ("Evaluar el sistema", "Evaluación y cierre"),
]
table = document.add_table(rows=1, cols=2)
table.rows[0].cells[0].text = "Objetivo específico"
table.rows[0].cells[1].text = "Etapas asociadas"
for objective, stage in objective_rows:
    cells = table.add_row().cells
    cells[0].text = objective
    cells[1].text = stage
for row in table.rows:
    row.cells[0].width = Cm(9.4)
    row.cells[1].width = Cm(6.6)
style_table(table)
add_caption(document, "Cuadro 1.1: Relación entre los objetivos específicos y las etapas del proyecto. Fuente: elaboración propia.")

add_heading(document, "1.7. Estado actual del proyecto", 1)

paragraphs = [
    "Hasta el momento se ha desarrollado la base funcional del sistema. El prototipo permite gestionar un catálogo local de canciones, separar la voz del acompañamiento, generar una pista instrumental y extraer una representación de pitch desde la voz original. La extracción incluye filtros de rango, energía, duración y estabilidad destinados a reducir detecciones no representativas.",
    "También se encuentra implementado el flujo inicial de una sesión de canto. El sistema puede reproducir el acompañamiento mientras captura el micrófono, detener la sesión y almacenar la interpretación como un archivo de audio. Posteriormente, extrae el pitch del usuario y realiza una alineación inicial con la referencia mediante DTW.",
    "A partir de la alineación se calculan métricas globales, como el error promedio en cents, la desviación, la tendencia general y el porcentaje de puntos dentro de distintos márgenes de afinación. Los resultados pueden visualizarse mediante curvas de notas y se almacenan localmente en archivos estructurados.",
    "Las funcionalidades existentes se encuentran integradas en una interfaz prototipo desarrollada con Tkinter. Esta permite agregar y eliminar canciones, reprocesar referencias, iniciar y detener sesiones, consultar métricas, visualizar gráficos y ejecutar un diagnóstico técnico del filtrado de pitch.",
    "Algunos componentes se encuentran parcialmente desarrollados. La alineación y las métricas requieren validación y refinamiento, mientras que el manejo de errores y las pruebas del sistema todavía no poseen una cobertura completa. La interfaz actual cumple una función de integración y experimentación, pero no corresponde necesariamente a la tecnología gráfica definitiva.",
    "Las funcionalidades relacionadas con la contribución principal del proyecto permanecen pendientes. Entre ellas se encuentran la detección de notas en tiempo real, el análisis dinámico de segmentos, la caracterización y priorización de problemas, la generación de retroalimentación en lenguaje natural y el seguimiento de la evolución entre sesiones.",
    "Para estimar el avance se revisó el cumplimiento de los requisitos definidos. La clasificación obtenida se presenta en el Cuadro 1.2.",
]
for text in paragraphs:
    add_body(document, text)

status_rows = [
    ("Completados", "16"),
    ("Parciales", "14"),
    ("Pendientes", "15"),
    ("Total", "45"),
]
table = document.add_table(rows=1, cols=2)
table.rows[0].cells[0].text = "Estado"
table.rows[0].cells[1].text = "Cantidad"
for status, count in status_rows:
    cells = table.add_row().cells
    cells[0].text = status
    cells[1].text = count
for row in table.rows:
    row.cells[0].width = Cm(10)
    row.cells[1].width = Cm(4)
    row.cells[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
style_table(table)
for run in table.rows[-1].cells[0].paragraphs[0].runs + table.rows[-1].cells[1].paragraphs[0].runs:
    run.bold = True
add_caption(document, "Cuadro 1.2: Estado actual de los requisitos del sistema. Fuente: elaboración propia.")

add_body(
    document,
    "Considerando únicamente los requisitos completamente implementados, el proyecto presenta un avance del 35,6 %. Los requisitos parciales no fueron contabilizados como completados, con el propósito de mantener una estimación conservadora. Este resultado refleja que la base técnica y el flujo inicial se encuentran disponibles, mientras que el análisis avanzado, la retroalimentación y el seguimiento histórico concentran el trabajo restante.",
)

document.save(OUTPUT)
print(OUTPUT)
