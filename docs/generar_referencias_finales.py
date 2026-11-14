import re
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
SOURCES = [
    ROOT / "Capitulo_2_Marco_teorico_actualizado.docx",
    ROOT / "Capitulo_3_Metodologia_version_especifica.docx",
    ROOT / "Capitulo_4_Desarrollo_version_especifica.docx",
]
OUTPUT = ROOT / "Referencias_documento_final.docx"
REFERENCE_RE = re.compile(r"^\[(\d+)\]\s+(.+)$")
URL_RE = re.compile(r"https?://\S+")


def format_run(run, size=12, bold=False):
    run.font.name = "Times New Roman"
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "Times New Roman")
    run.font.size = Pt(size)
    run.bold = bold


def add_hyperlink(paragraph, text, url):
    relation_id = paragraph.part.relate_to(
        url,
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
        is_external=True,
    )
    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), relation_id)
    run = OxmlElement("w:r")
    properties = OxmlElement("w:rPr")
    color = OxmlElement("w:color")
    color.set(qn("w:val"), "0563C1")
    underline = OxmlElement("w:u")
    underline.set(qn("w:val"), "single")
    fonts = OxmlElement("w:rFonts")
    fonts.set(qn("w:ascii"), "Times New Roman")
    fonts.set(qn("w:hAnsi"), "Times New Roman")
    size = OxmlElement("w:sz")
    size.set(qn("w:val"), "24")
    properties.extend([fonts, color, underline, size])
    run.append(properties)
    node = OxmlElement("w:t")
    node.text = text
    run.append(node)
    hyperlink.append(run)
    paragraph._p.append(hyperlink)


def collect_references():
    references = {}
    for source in SOURCES:
        document = Document(source)
        for paragraph in document.paragraphs:
            match = REFERENCE_RE.match(paragraph.text.strip())
            if not match:
                continue
            number = int(match.group(1))
            value = match.group(2).strip()
            if number not in references or len(value) > len(references[number]):
                references[number] = value
    return references


def add_reference(document, number, value):
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    paragraph.paragraph_format.left_indent = Cm(0.9)
    paragraph.paragraph_format.first_line_indent = Cm(-0.9)
    paragraph.paragraph_format.line_spacing = 1.15
    paragraph.paragraph_format.space_after = Pt(7)
    prefix = paragraph.add_run(f"[{number}] ")
    format_run(prefix)

    cursor = 0
    for match in URL_RE.finditer(value):
        before = value[cursor : match.start()]
        if before:
            run = paragraph.add_run(before)
            format_run(run)
        raw_url = match.group(0)
        url = raw_url.rstrip(".,;)")
        suffix = raw_url[len(url) :]
        add_hyperlink(paragraph, url, url)
        if suffix:
            run = paragraph.add_run(suffix)
            format_run(run)
        cursor = match.end()
    if cursor < len(value):
        run = paragraph.add_run(value[cursor:])
        format_run(run)


def main():
    references = collect_references()
    document = Document()
    section = document.sections[0]
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.5)

    title = document.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.space_after = Pt(18)
    format_run(title.add_run("Referencias bibliográficas consolidadas"), 16, True)

    introduction = document.add_paragraph()
    introduction.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    introduction.paragraph_format.line_spacing = 1.5
    introduction.paragraph_format.space_after = Pt(12)
    format_run(
        introduction.add_run(
            "Referencias citadas en las versiones finales actuales de los capítulos 2, 3 y 4. "
            "Se conserva la numeración utilizada en el texto y se eliminan las repeticiones entre capítulos."
        )
    )

    for number in sorted(references):
        add_reference(document, number, references[number])

    document.save(OUTPUT)
    print(OUTPUT)
    print(f"Referencias incluidas: {len(references)}")


if __name__ == "__main__":
    main()
