from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml.ns import qn
from docx.shared import Cm, Pt


ROOT = Path(r"C:\Users\Diego Tapia\Desktop\Pene\U\13avo semestre")
FORM = next(ROOT.glob("Formulaci*"))
DOC_PATH = FORM / "Informe final" / "Documento" / "Documento final.docx"


def clean(text: str) -> str:
    return text.replace("\r", "").replace("\x07", "").strip()


def set_font(paragraph, size=12, bold=False, align=None):
    if align is not None:
        paragraph.alignment = align
    paragraph.paragraph_format.space_after = Pt(0)
    paragraph.paragraph_format.line_spacing = 1.0
    for run in paragraph.runs:
        run.font.name = "Times New Roman"
        run._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
        run.font.size = Pt(size)
        run.bold = bold


def remove_tc_fields(document):
    for paragraph in document.paragraphs:
        for fld in list(paragraph._p.xpath(".//w:fldSimple")):
            parent = fld.getparent()
            parent.remove(fld)


def remove_update_fields_on_open(document):
    settings = document.settings.element
    for child in list(settings.findall(qn("w:updateFields"))):
        settings.remove(child)


def find_front_bounds(document):
    start = None
    content = None
    for paragraph in document.paragraphs:
        text = clean(paragraph.text)
        if start is None and text == "TABLA DE CONTENIDOS":
            start = paragraph
        elif start is not None and text == "1. Introducción":
            content = paragraph
            break
    if start is None or content is None:
        raise RuntimeError("No se pudo ubicar el índice frontal o el inicio del capítulo 1.")
    body = document.element.body
    return body.index(start._p), body.index(content._p)


def remove_body_range(document, start_idx, end_idx):
    body = document.element.body
    for idx in range(end_idx - 1, start_idx - 1, -1):
        body.remove(body[idx])


def insert_paragraph_at(document, body_index, text="", style=None):
    paragraph = document.add_paragraph(text)
    if style:
        paragraph.style = style
    p = paragraph._p
    document.element.body.remove(p)
    document.element.body.insert(body_index, p)
    return paragraph


def iter_content_paragraphs(document):
    started = False
    for paragraph in document.paragraphs:
        text = clean(paragraph.text)
        if text == "1. Introducción":
            started = True
        if started:
            yield paragraph


def heading_level(text):
    if text in {
        "1. Introducción",
        "2. Marco teórico y trabajo relacionado",
        "3. Metodología",
        "4. Desarrollo",
        "Referencias",
        "Anexos",
    }:
        return 0
    token = text.split(" ", 1)[0]
    if token.startswith(("1.", "2.", "3.", "4.")):
        dot_count = token.count(".")
        if dot_count == 2:
            return 1
        if dot_count == 3:
            return 2
    return None


def style_headings(document):
    for paragraph in iter_content_paragraphs(document):
        text = clean(paragraph.text)
        level = heading_level(text)
        if level == 0:
            paragraph.style = "Heading 1"
        elif level == 1:
            paragraph.style = "Heading 2"
        elif level == 2:
            paragraph.style = "Heading 3"


def collect_items(document):
    toc_items = []
    fig_items = []
    table_items = []
    for paragraph in iter_content_paragraphs(document):
        text = clean(paragraph.text)
        level = heading_level(text)
        if level is not None:
            toc_items.append((text, level))
        elif text.startswith("Figura "):
            fig_items.append(text.split(". Fuente:", 1)[0])
        elif text.startswith("Cuadro "):
            table_items.append(text.split(". Fuente:", 1)[0])
    return toc_items, fig_items, table_items


def ensure_anexos(document):
    if any(clean(p.text) == "Anexos" for p in iter_content_paragraphs(document)):
        return
    document.add_page_break()
    heading = document.add_paragraph("Anexos", style="Heading 1")
    set_font(heading, size=14, bold=True)
    texts = [
        "Los anexos de esta entrega se presentan como documentos complementarios al documento principal. Estos artefactos respaldan la especificación, planificación y modelado del sistema desarrollado durante el primer semestre.",
        "Anexo A: Especificación de requisitos. Archivo: Especificacion de Requisitos.docx.",
        "Anexo B: Historias de usuario. Archivo: Historias de Usuario.docx.",
        "Anexo C: Carta Gantt. Archivo: Carta Gantt.xlsx.",
        "Anexo D: Modelo de datos. Archivo: Modelo de datos.png.",
    ]
    for text in texts:
        paragraph = document.add_paragraph(text)
        set_font(paragraph)


def add_title(document, idx, text):
    paragraph = insert_paragraph_at(document, idx, text)
    set_font(paragraph, size=14, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    return idx + 1


def add_entry(document, idx, text, page, level=0):
    paragraph = insert_paragraph_at(document, idx, f"{text}\t{page}")
    set_font(paragraph, size=12)
    paragraph.paragraph_format.left_indent = Cm(0.55 * level)
    paragraph.paragraph_format.tab_stops.clear_all()
    paragraph.paragraph_format.tab_stops.add_tab_stop(
        Cm(15.5), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS
    )
    return idx + 1


def add_page_break(document, idx):
    paragraph = insert_paragraph_at(document, idx)
    paragraph.add_run().add_break(WD_BREAK.PAGE)
    return idx + 1


def build_front(document, insert_idx, toc_items, fig_items, table_items, pages=None):
    pages = pages or {}
    idx = insert_idx
    idx = add_title(document, idx, "TABLA DE CONTENIDOS")
    for text, level in toc_items:
        idx = add_entry(document, idx, text, pages.get(("toc", text), "0"), level)
    idx = add_page_break(document, idx)

    idx = add_title(document, idx, "ÍNDICE DE FIGURAS")
    for text in fig_items:
        idx = add_entry(document, idx, text, pages.get(("fig", text), "0"), 0)
    idx = add_page_break(document, idx)

    idx = add_title(document, idx, "ÍNDICE DE TABLAS")
    for text in table_items:
        idx = add_entry(document, idx, text, pages.get(("tab", text), "0"), 0)
    idx = add_page_break(document, idx)


def main():
    document = Document(str(DOC_PATH))
    remove_update_fields_on_open(document)
    remove_tc_fields(document)
    ensure_anexos(document)
    style_headings(document)
    toc_items, fig_items, table_items = collect_items(document)
    start_idx, end_idx = find_front_bounds(document)
    remove_body_range(document, start_idx, end_idx)
    build_front(document, start_idx, toc_items, fig_items, table_items)
    document.save(str(DOC_PATH))
    print(DOC_PATH)
    print(len(toc_items), len(fig_items), len(table_items))


if __name__ == "__main__":
    main()
