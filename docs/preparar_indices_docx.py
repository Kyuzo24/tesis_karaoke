from copy import deepcopy
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt


ROOT = Path(r"C:\Users\Diego Tapia\Desktop\Pene\U\13avo semestre")
FORM = next(ROOT.glob("Formulaci*"))
DOC_PATH = FORM / "Informe final" / "Documento" / "Documento final.docx"
BACKUP_PATH = DOC_PATH.with_name("Documento final_backup_antes_indices.docx")


def clean(text: str) -> str:
    return text.replace("\r", "").replace("\x07", "").strip()


def set_font(paragraph, size=12, bold=False, align=None):
    if align is not None:
        paragraph.alignment = align
    paragraph.paragraph_format.space_after = Pt(0)
    for run in paragraph.runs:
        run.font.name = "Times New Roman"
        run._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
        run.font.size = Pt(size)
        run.bold = bold


def add_complex_field(paragraph, instruction: str, placeholder: str = ""):
    run = paragraph.add_run()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    run._r.append(fld_begin)

    run = paragraph.add_run()
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = instruction
    run._r.append(instr)

    run = paragraph.add_run()
    fld_separate = OxmlElement("w:fldChar")
    fld_separate.set(qn("w:fldCharType"), "separate")
    run._r.append(fld_separate)

    if placeholder:
        run = paragraph.add_run(placeholder)
        run.font.name = "Times New Roman"
        run.font.size = Pt(11)

    run = paragraph.add_run()
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_end)


def add_tc_field(paragraph, text: str, table_id: str):
    safe = text.replace('"', "'")
    run = paragraph.add_run()
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), f'TC "{safe}" \\f {table_id}')
    run._r.append(fld)


def add_update_fields_on_open(document):
    settings = document.settings.element
    for child in settings.findall(qn("w:updateFields")):
        settings.remove(child)
    update = OxmlElement("w:updateFields")
    update.set(qn("w:val"), "true")
    settings.append(update)


def insert_paragraph_at(document, body_index: int, text: str = "", style=None):
    paragraph = document.add_paragraph(text)
    if style:
        paragraph.style = style
    p = paragraph._p
    document.element.body.remove(p)
    document.element.body.insert(body_index, p)
    return paragraph


def find_manual_index_bounds(document):
    start_para = None
    content_para = None
    intro_count = 0
    for paragraph in document.paragraphs:
        text = clean(paragraph.text)
        if start_para is None and text == "TABLA DE CONTENIDOS":
            start_para = paragraph
        if text == "1. Introducción":
            intro_count += 1
            if intro_count == 2:
                content_para = paragraph
                break
    if start_para is None or content_para is None:
        raise RuntimeError("No se pudo ubicar el índice manual o el inicio real del capítulo 1.")

    body = document.element.body
    return body.index(start_para._p), body.index(content_para._p)


def remove_body_range(document, start_idx, end_idx):
    body = document.element.body
    for idx in range(end_idx - 1, start_idx - 1, -1):
        body.remove(body[idx])


def style_content_headings(document):
    content_started = False
    for paragraph in document.paragraphs:
        text = clean(paragraph.text)
        if text == "1. Introducción":
            content_started = True
        if not content_started:
            continue

        if text in {
            "1. Introducción",
            "2. Marco teórico y trabajo relacionado",
            "3. Metodología",
            "4. Desarrollo",
            "Referencias",
            "Anexos",
        }:
            paragraph.style = "Heading 1"
        elif any(text.startswith(f"{chapter}.") for chapter in ["1", "2", "3", "4"]) and text.count(".") >= 2:
            if text.split(" ", 1)[0].count(".") == 2:
                paragraph.style = "Heading 2"
            elif text.split(" ", 1)[0].count(".") == 3:
                paragraph.style = "Heading 3"


def has_real_anexos(document):
    content_started = False
    for paragraph in document.paragraphs:
        text = clean(paragraph.text)
        if text == "1. Introducción":
            content_started = True
        if content_started and text == "Anexos":
            return True
    return False


def ensure_anexos_section(document):
    if has_real_anexos(document):
        return
    document.add_page_break()
    heading = document.add_paragraph("Anexos", style="Heading 1")
    set_font(heading, size=14, bold=True)
    paragraphs = [
        "Los anexos de esta entrega se presentan como documentos complementarios al documento principal. Estos artefactos respaldan la especificación, planificación y modelado del sistema desarrollado durante el primer semestre.",
        "Anexo A: Especificación de requisitos. Archivo: Especificacion de Requisitos.docx.",
        "Anexo B: Historias de usuario. Archivo: Historias de Usuario.docx.",
        "Anexo C: Carta Gantt. Archivo: Carta Gantt.xlsx.",
        "Anexo D: Modelo de datos. Archivo: Modelo de datos.png.",
    ]
    for text in paragraphs:
        paragraph = document.add_paragraph(text)
        set_font(paragraph, size=12)


def add_caption_tc_fields(document):
    for paragraph in document.paragraphs:
        text = clean(paragraph.text)
        if text.startswith("Figura "):
            label = text.split(". Fuente:", 1)[0]
            add_tc_field(paragraph, label, "F")
        elif text.startswith("Cuadro "):
            label = text.split(". Fuente:", 1)[0]
            add_tc_field(paragraph, label, "T")


def insert_front_indices(document, insert_idx):
    body_index = insert_idx

    title = insert_paragraph_at(document, body_index, "TABLA DE CONTENIDOS")
    set_font(title, size=14, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    body_index += 1

    toc = insert_paragraph_at(document, body_index)
    add_complex_field(toc, 'TOC \\o "1-3" \\h \\z \\u', "Actualizar tabla de contenidos")
    set_font(toc, size=12)
    body_index += 1

    br = insert_paragraph_at(document, body_index)
    br.add_run().add_break(WD_BREAK.PAGE)
    body_index += 1

    fig_title = insert_paragraph_at(document, body_index, "ÍNDICE DE FIGURAS")
    set_font(fig_title, size=14, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    body_index += 1

    fig_index = insert_paragraph_at(document, body_index)
    add_complex_field(fig_index, "TOC \\f F \\h \\z", "Actualizar índice de figuras")
    set_font(fig_index, size=12)
    body_index += 1

    br = insert_paragraph_at(document, body_index)
    br.add_run().add_break(WD_BREAK.PAGE)
    body_index += 1

    table_title = insert_paragraph_at(document, body_index, "ÍNDICE DE TABLAS")
    set_font(table_title, size=14, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    body_index += 1

    table_index = insert_paragraph_at(document, body_index)
    add_complex_field(table_index, "TOC \\f T \\h \\z", "Actualizar índice de tablas")
    set_font(table_index, size=12)
    body_index += 1

    br = insert_paragraph_at(document, body_index)
    br.add_run().add_break(WD_BREAK.PAGE)


def main():
    if not BACKUP_PATH.exists():
        BACKUP_PATH.write_bytes(DOC_PATH.read_bytes())

    document = Document(str(DOC_PATH))
    ensure_anexos_section(document)
    style_content_headings(document)
    add_caption_tc_fields(document)
    add_update_fields_on_open(document)

    start_idx, end_idx = find_manual_index_bounds(document)
    remove_body_range(document, start_idx, end_idx)
    insert_front_indices(document, start_idx)

    document.save(str(DOC_PATH))
    print(DOC_PATH)
    print(BACKUP_PATH)


if __name__ == "__main__":
    main()
