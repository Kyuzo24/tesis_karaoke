from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt


ROOT = Path(__file__).resolve().parents[1]


FONT = "Times New Roman"


def set_run(run, size=12, bold=False, italic=False, all_caps=False):
    run.font.name = FONT
    run._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    if all_caps:
        run.text = run.text.upper()


def set_paragraph(paragraph, size=12, bold=False, align=None, space_after=0):
    if align is not None:
        paragraph.alignment = align
    paragraph.paragraph_format.space_after = Pt(space_after)
    paragraph.paragraph_format.line_spacing = 1.15
    for run in paragraph.runs:
        set_run(run, size=size, bold=bold)


def set_cell_text(cell, text, size=12, bold=False, align=None):
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = align or WD_ALIGN_PARAGRAPH.LEFT
    run = p.add_run(text)
    set_run(run, size=size, bold=bold)
    p.paragraph_format.space_after = Pt(0)


def clear_table_borders(table):
    tbl = table._tbl
    tbl_pr = tbl.tblPr
    borders = tbl_pr.first_child_found_in("w:tblBorders")
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        tbl_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = "w:{}".format(edge)
        element = borders.find(qn(tag))
        if element is None:
            element = OxmlElement(tag)
            borders.append(element)
        element.set(qn("w:val"), "nil")


def configure_document(doc):
    section = doc.sections[0]
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin = Cm(3)
    section.right_margin = Cm(2.5)
    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = FONT
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    normal.font.size = Pt(12)


def add_index_entry(doc, number, title, level=0):
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.left_indent = Cm(0.6 * level)
    paragraph.paragraph_format.first_line_indent = Cm(-0.1 if level else 0)
    paragraph.paragraph_format.space_after = Pt(1)
    run = paragraph.add_run(f"{number} {title}" if number else title)
    set_run(run, size=12, bold=(level == 0 and bool(number)))


def build_index():
    doc = Document()
    configure_document(doc)

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("TABLA DE CONTENIDOS")
    set_run(run, size=14, bold=True)
    title.paragraph_format.space_after = Pt(18)

    entries = [
        ("", "Resumen", 0),
        ("", "Índice de figuras", 0),
        ("", "Índice de tablas", 0),
        ("1.", "Introducción", 0),
        ("1.1.", "Contexto", 1),
        ("1.2.", "Definición del problema", 1),
        ("1.3.", "Propuesta de solución", 1),
        ("1.4.", "Objetivos", 1),
        ("1.4.1.", "Objetivo general", 2),
        ("1.4.2.", "Objetivos específicos", 2),
        ("1.5.", "Alcances y limitaciones", 1),
        ("1.6.", "Plan de trabajo", 1),
        ("1.6.1.", "Descripción de las etapas del proyecto", 2),
        ("1.6.2.", "Relación entre objetivos y etapas", 2),
        ("1.7.", "Estado actual del proyecto", 1),
        ("2.", "Marco teórico y trabajo relacionado", 0),
        ("2.1.", "Fundamentos musicales y vocales", 1),
        ("2.1.1.", "Frecuencia y altura tonal", 2),
        ("2.1.2.", "Notas musicales y octavas", 2),
        ("2.1.3.", "Afinación y estabilidad tonal", 2),
        ("2.2.", "Procesamiento digital de audio", 1),
        ("2.2.1.", "Digitalización de una señal", 2),
        ("2.2.2.", "Frecuencia de muestreo", 2),
        ("2.2.3.", "Ventanas y bloques de audio", 2),
        ("2.2.4.", "Ruido, silencios y filtrado", 2),
        ("2.3.", "Estimación de frecuencia fundamental", 1),
        ("2.3.1.", "Sonoridad y periodicidad", 2),
        ("2.3.2.", "Estimación mediante pYIN", 2),
        ("2.3.3.", "WORLD y Pyworld", 2),
        ("2.3.4.", "Errores frecuentes de estimación", 2),
        ("2.3.5.", "Criterios para el proyecto", 2),
        ("2.4.", "Separación de fuentes musicales", 1),
        ("2.4.1.", "Separación mediante modelos preentrenados", 2),
        ("2.4.2.", "Spleeter", 2),
        ("2.4.3.", "Demucs y Hybrid Transformer Demucs", 2),
        ("2.4.4.", "Artefactos y limitaciones", 2),
        ("2.4.5.", "Criterios para el proyecto", 2),
        ("2.5.", "Alineación temporal mediante Dynamic Time Warping", 1),
        ("2.5.1.", "Matriz de costos", 2),
        ("2.5.2.", "Trayectoria de alineación", 2),
        ("2.5.3.", "Aplicación a curvas de pitch", 2),
        ("2.5.4.", "Limitaciones de la alineación", 2),
        ("2.5.5.", "Criterios para el proyecto", 2),
        ("2.6.", "Detección y caracterización de segmentos problemáticos", 1),
        ("2.6.1.", "Evidencias locales de la interpretación", 2),
        ("2.6.2.", "Formación dinámica de segmentos", 2),
        ("2.6.3.", "Caracterización de problemáticas", 2),
        ("2.6.4.", "Severidad y priorización", 2),
        ("2.6.5.", "Criterios para el proyecto", 2),
        ("2.7.", "Generación de retroalimentación en lenguaje natural", 1),
        ("2.7.1.", "Representación estructurada de hallazgos", 2),
        ("2.7.2.", "Generación mediante plantillas", 2),
        ("2.7.3.", "Generación mediante un modelo de lenguaje", 2),
        ("2.7.4.", "Riesgos y validación", 2),
        ("2.7.5.", "Criterios para el proyecto", 2),
        ("2.8.", "Seguimiento y comparación de la evolución", 1),
        ("2.8.1.", "Persistencia de sesiones", 2),
        ("2.8.2.", "Comparabilidad entre sesiones", 2),
        ("2.8.3.", "Resumen de cambios", 2),
        ("2.8.4.", "Criterios para el proyecto", 2),
        ("2.9.", "Tecnologías consideradas", 1),
        ("2.9.1.", "Lenguaje y procesamiento de audio", 2),
        ("2.9.2.", "Interfaz gráfica", 2),
        ("2.9.3.", "Almacenamiento", 2),
        ("2.9.4.", "Distribución y dependencias", 2),
        ("2.9.5.", "Criterios para el proyecto", 2),
        ("2.10.", "Trabajo relacionado", 1),
        ("2.10.1.", "Diferenciación de la propuesta", 2),
        ("2.11.", "Síntesis del capítulo", 1),
        ("3.", "Metodología", 0),
        ("3.1.", "Estrategia metodológica", 1),
        ("3.1.1.", "Adaptación de PXP al proyecto", 2),
        ("3.1.2.", "Evidencia de aceptación por capacidad", 2),
        ("3.1.3.", "Dependencias entre iteraciones", 2),
        ("3.1.4.", "Tratamiento de decisiones abiertas", 2),
        ("3.2.", "Diseño de evaluación", 1),
        ("3.2.1.", "Conjunto de pruebas", 2),
        ("3.2.2.", "Experimento de estimación y filtrado de pitch", 2),
        ("3.2.3.", "Experimento de detección en tiempo real", 2),
        ("3.2.4.", "Experimento de alineación y segmentación", 2),
        ("3.2.5.", "Evaluación de retroalimentación e historial", 2),
        ("3.2.6.", "Pruebas funcionales y regresión", 2),
        ("3.2.7.", "Reproducibilidad y registro", 2),
        ("3.3.", "Estado metodológico actual", 1),
        ("3.4.", "Amenazas a la validez", 1),
        ("3.5.", "Síntesis del capítulo", 1),
        ("4.", "Desarrollo", 0),
        ("4.1.", "Arquitectura derivada del entorno de ejecución", 1),
        ("4.1.1.", "Despliegue físico", 2),
        ("4.1.2.", "Arquitectura lógica actual", 2),
        ("4.1.3.", "Flujos de ejecución", 2),
        ("4.1.4.", "Modelo de datos", 2),
        ("4.2.", "Implementación y decisiones actuales", 1),
        ("4.2.1.", "Identidad y ciclo de una canción", 2),
        ("4.2.2.", "Separación y construcción del acompañamiento", 2),
        ("4.2.3.", "Estimación y filtrado de frecuencia fundamental", 2),
        ("4.2.4.", "Captura, concurrencia y estado", 2),
        ("4.2.5.", "Alineación y métricas", 2),
        ("4.2.6.", "Visualización y persistencia", 2),
        ("4.3.", "Evolución arquitectónica necesaria", 1),
        ("4.3.1.", "Canal de tiempo real", 2),
        ("4.3.2.", "Trayectoria y segmentos", 2),
        ("4.3.3.", "Versionado para comparación histórica", 2),
        ("4.3.4.", "Adaptadores de retroalimentación y presentación", 2),
        ("4.4.", "Evidencia producida por el prototipo", 1),
        ("4.5.", "Riesgos técnicos concretos", 1),
        ("4.6.", "Síntesis del capítulo", 1),
        ("", "Referencias", 0),
        ("", "Anexos", 0),
        ("A.", "Especificación de requisitos", 1),
        ("B.", "Historias de usuario", 1),
        ("C.", "Carta Gantt", 1),
        ("D.", "Modelo de datos", 1),
        ("E.", "Diagramas complementarios", 1),
        ("F.", "Evidencia de pruebas", 1),
    ]

    for number, title_text, level in entries:
        add_index_entry(doc, number, title_text, level)

    note = doc.add_paragraph()
    note.paragraph_format.space_before = Pt(12)
    note.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    run = note.add_run(
        "Nota: este índice corresponde al estado actual del documento. La numeración de páginas "
        "debe actualizarse cuando los capítulos se integren en un único archivo."
    )
    set_run(run, size=10, italic=True)

    path = ROOT / "Indice_estado_actual_memoria.docx"
    doc.save(path)
    return path


def add_spacer(doc, height_pt):
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(height_pt)


def build_cover():
    doc = Document()
    configure_document(doc)
    section = doc.sections[0]
    section.top_margin = Cm(2.3)
    section.bottom_margin = Cm(2.3)
    section.left_margin = Cm(3)
    section.right_margin = Cm(3)

    header_lines = [
        "UNIVERSIDAD DE TALCA",
        "FACULTAD DE INGENIERÍA",
        "ESCUELA DE INGENIERÍA CIVIL EN COMPUTACIÓN",
    ]
    for line in header_lines:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(line)
        set_run(run, size=12, bold=True)
        p.paragraph_format.space_after = Pt(2)

    add_spacer(doc, 72)

    title = (
        "Sistema de análisis vocal, detección de patrones de error y "
        "retroalimentación basado en procesamiento digital de señales"
    )
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(36)
    run = p.add_run(title)
    set_run(run, size=18, bold=True)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(24)
    run = p.add_run("DIEGO ALFONSO TAPIA VÁSQUEZ")
    set_run(run, size=13, bold=True)

    table = doc.add_table(rows=3, cols=1)
    clear_table_borders(table)
    table.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_cell_text(table.cell(0, 0), "Profesor Guía: RICARDO PÉREZ", size=12, align=WD_ALIGN_PARAGRAPH.CENTER)
    set_cell_text(
        table.cell(1, 0),
        "Memoria para optar al título de",
        size=12,
        align=WD_ALIGN_PARAGRAPH.CENTER,
    )
    set_cell_text(
        table.cell(2, 0),
        "Ingeniero Civil en Computación",
        size=12,
        align=WD_ALIGN_PARAGRAPH.CENTER,
    )

    for row in table.rows:
        row.height = Cm(0.6)

    add_spacer(doc, 140)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("Curicó - Chile")
    set_run(run, size=12)
    p.paragraph_format.space_after = Pt(4)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("junio, 2026")
    set_run(run, size=12)

    path = ROOT / "Portada_memoria.docx"
    doc.save(path)
    return path


if __name__ == "__main__":
    index_path = build_index()
    cover_path = build_cover()
    print(index_path)
    print(cover_path)
