from pathlib import Path
from copy import deepcopy

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml.ns import qn
from docx.shared import Pt, Cm


ROOT = Path(r"C:\Users\Diego Tapia\Desktop\Pene\U\13avo semestre")
FORM = next(ROOT.glob("Formulaci*"))
FOLDER = FORM / "Informe final" / "Documento"
TARGET = FOLDER / "Documento final.docx"
CURRENT_WITH_PAGES = FOLDER / "Documento final_con_indices.docx"
BACKUP = FOLDER / "Documento final_backup_antes_indices.docx"


def clean(text: str) -> str:
    return text.replace("\r", "").replace("\x07", "").strip()


def extract_index_pages(path: Path):
    doc = Document(str(path))
    sections = {"toc": [], "fig": [], "tab": []}
    current = None
    for para in doc.paragraphs:
        text = clean(para.text)
        if not text:
            continue
        if text == "TABLA DE CONTENIDOS":
            current = "toc"
            continue
        if text == "ÍNDICE DE FIGURAS":
            current = "fig"
            continue
        if text == "ÍNDICE DE TABLAS":
            current = "tab"
            continue
        if current and "\t" in text:
            label, page = text.rsplit("\t", 1)
            if page.strip().isdigit():
                sections[current].append((label.strip(), page.strip()))
                continue
        if current == "tab" and text == "1. Introducción":
            break
    return sections


def find_front_bounds(doc: Document):
    start = None
    end = None
    intro_count = 0
    for para in doc.paragraphs:
        text = clean(para.text)
        if start is None and text == "TABLA DE CONTENIDOS":
            start = para
        if text == "1. Introducción":
            intro_count += 1
            if intro_count == 2:
                end = para
                break
    if start is None or end is None:
        raise RuntimeError("No se encontró el índice manual o el inicio real del capítulo 1.")
    body = doc.element.body
    return body.index(start._p), body.index(end._p)


def remove_body_range(doc: Document, start_idx: int, end_idx: int):
    body = doc.element.body
    for idx in range(end_idx - 1, start_idx - 1, -1):
        body.remove(body[idx])


def insert_paragraph_at(doc: Document, body_idx: int, text: str = ""):
    para = doc.add_paragraph(text)
    p = para._p
    doc.element.body.remove(p)
    doc.element.body.insert(body_idx, p)
    return para


def set_normal(para, size=12, bold=False, align=None, left_cm=0):
    para.style = "Normal"
    if align is not None:
        para.alignment = align
    para.paragraph_format.space_after = Pt(0)
    para.paragraph_format.line_spacing = 1.0
    para.paragraph_format.left_indent = Cm(left_cm)
    for run in para.runs:
        run.font.name = "Times New Roman"
        run._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
        run.font.size = Pt(size)
        run.bold = bold


def level_for(label: str) -> int:
    if label in {"Referencias", "Anexos"}:
        return 0
    number = label.split(" ", 1)[0]
    if number.count(".") >= 3:
        return 2
    if number.count(".") == 2:
        return 1
    return 0


def add_title(doc, idx, text):
    para = insert_paragraph_at(doc, idx, text)
    set_normal(para, size=14, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    return idx + 1


def add_entry(doc, idx, label, page, level=0):
    para = insert_paragraph_at(doc, idx, f"{label.strip()}\t{page}")
    set_normal(para, size=12, bold=False, left_cm=0.55 * level)
    para.paragraph_format.tab_stops.clear_all()
    para.paragraph_format.tab_stops.add_tab_stop(
        Cm(15.5), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS
    )
    return idx + 1


def add_break(doc, idx):
    para = insert_paragraph_at(doc, idx)
    para.add_run().add_break(WD_BREAK.PAGE)
    set_normal(para)
    return idx + 1


def insert_indices(doc: Document, idx: int, pages):
    idx = add_title(doc, idx, "TABLA DE CONTENIDOS")
    for label, page in pages["toc"]:
        idx = add_entry(doc, idx, label, page, level_for(label))
    idx = add_break(doc, idx)

    idx = add_title(doc, idx, "ÍNDICE DE FIGURAS")
    for label, page in pages["fig"]:
        idx = add_entry(doc, idx, label, page, 0)
    idx = add_break(doc, idx)

    idx = add_title(doc, idx, "ÍNDICE DE TABLAS")
    for label, page in pages["tab"]:
        idx = add_entry(doc, idx, label, page, 0)
    idx = add_break(doc, idx)


def has_real_anexos(doc: Document):
    intro_count = 0
    started = False
    for para in doc.paragraphs:
        text = clean(para.text)
        if text == "1. Introducción":
            intro_count += 1
            if intro_count >= 2:
                started = True
        if started and text == "Anexos":
            return True
    return False


def add_anexos(doc: Document):
    if has_real_anexos(doc):
        return
    doc.add_page_break()
    h = doc.add_paragraph("Anexos")
    set_normal(h, size=14, bold=True)
    texts = [
        "Los anexos de esta entrega se presentan como documentos complementarios al documento principal. Estos artefactos respaldan la especificación, planificación y modelado del sistema desarrollado durante el primer semestre.",
        "Anexo A: Especificación de requisitos. Archivo: Especificacion de Requisitos.docx.",
        "Anexo B: Historias de usuario. Archivo: Historias de Usuario.docx.",
        "Anexo C: Carta Gantt. Archivo: Carta Gantt.xlsx.",
        "Anexo D: Modelo de datos. Archivo: Modelo de datos.png.",
    ]
    for text in texts:
        para = doc.add_paragraph(text)
        set_normal(para, size=12)


def main():
    pages = extract_index_pages(CURRENT_WITH_PAGES)
    if not pages["toc"] or not pages["fig"] or not pages["tab"]:
        raise RuntimeError("No se pudieron extraer los índices paginados.")

    doc = Document(str(BACKUP))
    start, end = find_front_bounds(doc)
    remove_body_range(doc, start, end)
    insert_indices(doc, start, pages)
    add_anexos(doc)
    doc.save(str(TARGET))
    print(TARGET)
    print(len(pages["toc"]), len(pages["fig"]), len(pages["tab"]))


if __name__ == "__main__":
    main()
