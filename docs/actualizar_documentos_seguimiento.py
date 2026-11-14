from copy import deepcopy
from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt


ROOT = Path(__file__).resolve().parents[1]
REQ_PATH = ROOT / "Especificacion_de_Requisitos.docx"
HU_PATH = ROOT / "Historias_de_Usuario.docx"
UPDATE_DATE = "20-06-2026"


def border(cell, size=8):
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
        node.set(qn("w:space"), "0")
        node.set(qn("w:color"), "000000")


def margins(cell, top=100, start=130, bottom=100, end=130):
    properties = cell._tc.get_or_add_tcPr()
    cell_margins = properties.first_child_found_in("w:tcMar")
    if cell_margins is None:
        cell_margins = OxmlElement("w:tcMar")
        properties.append(cell_margins)
    for name, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = cell_margins.find(qn("w:" + name))
        if node is None:
            node = OxmlElement("w:" + name)
            cell_margins.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def row_height(row, cm):
    properties = row._tr.get_or_add_trPr()
    height = OxmlElement("w:trHeight")
    height.set(qn("w:val"), str(int(Cm(cm).twips)))
    height.set(qn("w:hRule"), "atLeast")
    properties.append(height)
    properties.append(OxmlElement("w:cantSplit"))


def configure_document(document):
    section = document.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(1.5)
    section.bottom_margin = Cm(1.5)
    section.left_margin = Cm(1.5)
    section.right_margin = Cm(1.5)
    style = document.styles["Normal"]
    style.font.name = "Times New Roman"
    style._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    style.font.size = Pt(11)


def write_cell(cell, text, size=11, bold=False, align=WD_ALIGN_PARAGRAPH.LEFT):
    cell.text = ""
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    paragraph = cell.paragraphs[0]
    paragraph.alignment = align
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.space_after = Pt(0)
    run = paragraph.add_run(text)
    run.bold = bold
    run.font.name = "Times New Roman"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    run.font.size = Pt(size)
    border(cell)
    margins(cell)


def read_requirements():
    source = Document(REQ_PATH)
    records = []
    for table in source.tables:
        records.append({
            "code": table.cell(0, 0).text.strip(),
            "name": table.cell(0, 1).text.strip(),
            "description": table.cell(1, 1).text.strip(),
            "source": table.cell(2, 1).text.strip(),
            "priority": table.cell(3, 1).text.strip(),
            "stability": table.cell(4, 1).text.strip(),
            "date": UPDATE_DATE,
            "type": table.cell(6, 1).text.strip(),
        })
    return records


def update_requirements(records):
    records = [record for record in records if record["code"] not in {"RF27", "RF28", "RF29"}]
    for record in records:
        if record["code"] == "RF23":
            record["description"] = (
                "El sistema deberá almacenar para cada sesión la canción y referencia utilizadas, "
                "la fecha, la grabación, las métricas, los segmentos detectados y la retroalimentación generada."
            )
            record["priority"] = "Alta"
            record["stability"] = "No transable"
        elif record["code"] == "RNF09":
            record["description"] = (
                "El sistema deberá conservar localmente y de forma estructurada las canciones, sesiones, métricas, "
                "segmentos y retroalimentaciones necesarias para realizar comparaciones históricas. La tecnología "
                "de almacenamiento podrá basarse en archivos o en una base de datos SQLite."
            )
            record["priority"] = "Alta"
            record["stability"] = "No transable"

    new_requirements = [
        {
            "code": "RF27",
            "name": "Comparar sesiones",
            "description": (
                "El sistema deberá permitir seleccionar y comparar sesiones realizadas sobre una misma canción "
                "y referencia, utilizando las métricas y los segmentos problemáticos almacenados."
            ),
            "source": "Cantante",
            "priority": "Alta",
            "stability": "No transable",
            "date": UPDATE_DATE,
            "type": "Funcional",
        },
        {
            "code": "RF28",
            "name": "Visualizar evolución",
            "description": (
                "El sistema deberá representar la evolución temporal del usuario mediante la comparación de "
                "métricas y problemáticas obtenidas en sesiones realizadas sobre una misma canción."
            ),
            "source": "Cantante",
            "priority": "Alta",
            "stability": "No transable",
            "date": UPDATE_DATE,
            "type": "Funcional",
        },
        {
            "code": "RF29",
            "name": "Resumir cambios entre sesiones",
            "description": (
                "El sistema deberá generar un resumen que indique qué aspectos del desempeño mejoraron, "
                "persistieron o empeoraron entre las sesiones comparadas."
            ),
            "source": "Cantante",
            "priority": "Media",
            "stability": "No transable",
            "date": UPDATE_DATE,
            "type": "Funcional",
        },
    ]
    functional_end = next(i for i, record in enumerate(records) if record["code"].startswith("RNF"))
    return records[:functional_end] + new_requirements + records[functional_end:]


def write_requirements(records):
    document = Document()
    configure_document(document)
    for index, record in enumerate(records, 1):
        table = document.add_table(rows=7, cols=2)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False
        table.allow_autofit = False
        for row in table.rows:
            row.cells[0].width = Cm(5.6)
            row.cells[1].width = Cm(12.4)
            for cell in row.cells:
                border(cell)
                margins(cell)

        write_cell(table.cell(0, 0), record["code"], 12)
        write_cell(table.cell(0, 1), record["name"], 12)
        write_cell(table.cell(1, 0), "Descripción")
        write_cell(table.cell(1, 1), record["description"])
        write_cell(table.cell(2, 0), "Fuente")
        write_cell(table.cell(2, 1), record["source"])
        write_cell(table.cell(3, 0), "Prioridad")
        write_cell(table.cell(3, 1), record["priority"])
        write_cell(table.cell(4, 0), "Estabilidad")
        write_cell(table.cell(4, 1), record["stability"])
        write_cell(table.cell(5, 0), "Fecha Actualización")
        write_cell(table.cell(5, 1), record["date"])
        write_cell(table.cell(6, 0), "Tipo")
        write_cell(table.cell(6, 1), record["type"])
        for row, height in zip(table.rows, [0.9, 3.0, 0.9, 0.9, 0.9, 0.9, 0.9]):
            row_height(row, height)

        caption = document.add_paragraph()
        caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
        caption.paragraph_format.space_before = Pt(10)
        caption.paragraph_format.space_after = Pt(0)
        run = caption.add_run(f"Cuadro {index}: Especificación del Requisito {record['code']}")
        run.font.name = "Times New Roman"
        run._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
        run.font.size = Pt(12)
        if index < len(records):
            document.add_page_break()
    document.save(REQ_PATH)


def after_prefix(value, prefix):
    if not value.startswith(prefix):
        raise ValueError(f"Se esperaba el prefijo {prefix!r} en {value!r}")
    return value[len(prefix):].strip()


def read_stories():
    source = Document(HU_PATH)
    stories = []
    for table in source.tables:
        stories.append({
            "number": after_prefix(table.cell(1, 0).text, "Número:"),
            "user": after_prefix(table.cell(1, 1).text, "Usuario:"),
            "name": after_prefix(table.cell(2, 0).text, "Nombre historia:"),
            "priority": after_prefix(table.cell(3, 0).text, "Prioridad en negocio:"),
            "risk": after_prefix(table.cell(3, 1).text, "Riesgo en desarrollo:"),
            "iteration": after_prefix(table.cell(4, 0).text, "Iteración asignada:"),
            "programmer": after_prefix(table.cell(4, 1).text, "Programador responsable:"),
            "description": after_prefix(table.cell(5, 0).text, "Descripción:"),
            "observations": after_prefix(table.cell(6, 0).text, "Observaciones:"),
        })
    return stories


def update_stories(stories):
    story = next(item for item in stories if item["number"] == "HU13")
    story.update({
        "user": "Cantante",
        "name": "Consultar y comparar evolución",
        "priority": "Alta",
        "risk": "Medio",
        "iteration": "4",
        "description": (
            "Como cantante, quiero consultar y comparar sesiones realizadas sobre una misma canción, "
            "para observar los cambios de mi desempeño y mis dificultades a lo largo del tiempo."
        ),
        "observations": (
            "La comparación utilizará la misma canción y referencia. Deberá mostrar variaciones de métricas, "
            "problemáticas que mejoraron o persistieron y un resumen de los principales cambios."
        ),
    })
    return stories


def add_labeled_text(cell, label, value, font_size=11):
    paragraph = cell.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
    paragraph.paragraph_format.space_after = Pt(0)
    paragraph.paragraph_format.space_before = Pt(0)
    for text in (label, value):
        run = paragraph.add_run(text)
        run.font.name = "Times New Roman"
        run._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
        run.font.size = Pt(font_size)


def write_stories(stories):
    document = Document()
    configure_document(document)
    for index, story in enumerate(stories):
        table = document.add_table(rows=7, cols=2)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False
        table.allow_autofit = False
        for row in table.rows:
            row.cells[0].width = Cm(6.1)
            row.cells[1].width = Cm(11.9)
            for cell in row.cells:
                cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                border(cell)
                margins(cell, top=110, start=140, bottom=110, end=140)

        title_cell = table.cell(0, 0).merge(table.cell(0, 1))
        name_cell = table.cell(2, 0).merge(table.cell(2, 1))
        description_cell = table.cell(5, 0).merge(table.cell(5, 1))
        observations_cell = table.cell(6, 0).merge(table.cell(6, 1))
        for cell in (title_cell, name_cell, description_cell, observations_cell):
            border(cell)
            margins(cell, top=110, start=140, bottom=110, end=140)

        paragraph = title_cell.paragraphs[0]
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.paragraph_format.space_after = Pt(0)
        run = paragraph.add_run("Historia de Usuario")
        run.bold = True
        run.font.name = "Times New Roman"
        run._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
        run.font.size = Pt(16)

        add_labeled_text(table.cell(1, 0), "Número: ", story["number"])
        add_labeled_text(table.cell(1, 1), "Usuario: ", story["user"])
        add_labeled_text(name_cell, "Nombre historia: ", story["name"])
        add_labeled_text(table.cell(3, 0), "Prioridad en negocio: ", story["priority"])
        add_labeled_text(table.cell(3, 1), "Riesgo en desarrollo: ", story["risk"])
        add_labeled_text(table.cell(4, 0), "Iteración asignada: ", story["iteration"])
        add_labeled_text(table.cell(4, 1), "Programador responsable: ", story["programmer"])
        add_labeled_text(description_cell, "Descripción:\n", story["description"])
        add_labeled_text(observations_cell, "Observaciones:\n", story["observations"])
        for row, height in zip(table.rows, [0.9, 0.9, 1.55, 0.9, 0.9, 3.2, 2.0]):
            row_height(row, height)
        if index < len(stories) - 1:
            document.add_page_break()
    document.save(HU_PATH)


if __name__ == "__main__":
    requirements = update_requirements(read_requirements())
    stories = update_stories(read_stories())
    write_requirements(requirements)
    write_stories(stories)
    print(f"Requisitos actualizados: {len(requirements)}")
    print(f"Historias actualizadas: {len(stories)}")
