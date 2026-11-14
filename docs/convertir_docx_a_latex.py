from __future__ import annotations

import re
import shutil
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn


ROOT_13 = Path(r"C:\Users\Diego Tapia\Desktop\Pene\U\13avo semestre")
FORMULACION = next(ROOT_13.glob("Formulaci*"))
DOC_DIR = FORMULACION / "Informe final" / "Documento"
DOCX_PATH = DOC_DIR / "Documento final.docx"
OUT_DIR = DOC_DIR / "Documento_final_LaTeX"
FIG_DIR = OUT_DIR / "figuras"


CHAPTERS = {
    "1. introducción": "Introducción",
    "2. marco teórico y trabajo relacionado": "Marco teórico y trabajo relacionado",
    "3. metodología": "Metodología",
    "4. desarrollo": "Desarrollo",
}


LATEX_SPECIALS = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def tex(text: str) -> str:
    text = clean_text(text)
    return "".join(LATEX_SPECIALS.get(ch, ch) for ch in text)


def image_rids_from_element(element) -> list[str]:
    rids: list[str] = []
    for node in element.iter():
        if node.tag.endswith("}blip"):
            rid = node.get(qn("r:embed")) or node.get(qn("r:link"))
            if rid and rid not in rids:
                rids.append(rid)
    return rids


def parse_caption(text: str, kind: str) -> tuple[str, str] | None:
    label_name = "Figura" if kind == "figure" else "Cuadro"
    match = re.match(
        rf"^{label_name}\s+([0-9]+(?:\.[0-9]+)*)\s*:\s*(.+)$",
        clean_text(text),
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    number = match.group(1)
    body = match.group(2)
    return number, body


def label_from_number(prefix: str, number: str) -> str:
    return f"{prefix}:{number.replace('.', '-')}"


def body_elements(document: Document):
    paragraphs = iter(document.paragraphs)
    tables = iter(document.tables)
    for child in document.element.body.iterchildren():
        if child.tag == qn("w:p"):
            yield "p", next(paragraphs)
        elif child.tag == qn("w:tbl"):
            yield "t", next(tables)


class LatexConverter:
    def __init__(self, document: Document) -> None:
        self.document = document
        self.image_files: dict[str, str] = {}
        self.figure_count = 0
        self.table_count = 0

    def write_image(self, rid: str) -> str:
        if rid in self.image_files:
            return self.image_files[rid]

        image_part = self.document.part.related_parts[rid]
        source_name = Path(str(image_part.partname)).name
        safe_name = re.sub(r"[^A-Za-z0-9_.-]", "_", source_name)
        target = FIG_DIR / safe_name

        duplicate = 1
        while target.exists() and target.read_bytes() != image_part.blob:
            stem = Path(safe_name).stem
            suffix = Path(safe_name).suffix
            target = FIG_DIR / f"{stem}_{duplicate}{suffix}"
            duplicate += 1

        target.write_bytes(image_part.blob)
        self.image_files[rid] = target.name
        return target.name

    def figure_block(
        self,
        rids: list[str],
        caption: tuple[str, str] | None,
    ) -> list[str]:
        if not rids:
            return []

        self.figure_count += 1
        lines = [r"\begin{figure}[H]", r"\centering"]
        for rid in rids:
            name = self.write_image(rid)
            lines.append(
                rf"\includegraphics[width=\textwidth,height=0.72\textheight,keepaspectratio]{{figuras/{name}}}"
            )
        if caption:
            number, body = caption
            lines.append(rf"\caption{{{tex(body)}}}")
            lines.append(rf"\label{{{label_from_number('fig', number)}}}")
        lines.append(r"\end{figure}")
        lines.append("")
        return lines

    def table_block(
        self,
        table,
        caption: tuple[str, str] | None,
    ) -> list[str]:
        rows = table.rows
        if not rows:
            return []

        column_count = max(len(row.cells) for row in rows)
        if column_count == 0:
            return []

        self.table_count += 1
        spec = "|" + "|".join(
            [r">{\raggedright\arraybackslash}X" for _ in range(column_count)]
        ) + "|"
        lines = [r"\begin{table}[H]", r"\centering", r"\small"]
        if caption:
            number, body = caption
            lines.append(rf"\caption{{{tex(body)}}}")
            lines.append(rf"\label{{{label_from_number('tab', number)}}}")
        lines.append(rf"\begin{{tabularx}}{{\textwidth}}{{{spec}}}")
        lines.append(r"\hline")
        for row in rows:
            values = []
            for idx in range(column_count):
                value = ""
                if idx < len(row.cells):
                    value = row.cells[idx].text
                value = tex(value).replace("\n", r"\newline ")
                values.append(value)
            lines.append(" & ".join(values) + r" \\")
            lines.append(r"\hline")
        lines.append(r"\end{tabularx}")
        lines.append(r"\end{table}")
        lines.append("")
        return lines


def heading_block(text_value: str) -> list[str] | None:
    lowered = clean_text(text_value).lower()
    if lowered in CHAPTERS:
        return [rf"\chapter{{{tex(CHAPTERS[lowered])}}}", ""]

    subsection = re.match(r"^\d+\.\d+\.\d+\.?\s+(.+)$", clean_text(text_value))
    if subsection:
        return [rf"\subsection{{{tex(subsection.group(1))}}}", ""]

    section = re.match(r"^\d+\.\d+\.?\s+(.+)$", clean_text(text_value))
    if section:
        return [rf"\section{{{tex(section.group(1))}}}", ""]

    return None


def find_next_caption(
    elements: list[tuple[str, object]],
    index: int,
    kind: str,
) -> tuple[tuple[str, str] | None, int | None]:
    cursor = index + 1
    while cursor < len(elements):
        next_kind, next_item = elements[cursor]
        if next_kind != "p":
            return None, None
        next_text = clean_text(next_item.text)
        if not next_text:
            cursor += 1
            continue
        caption = parse_caption(next_text, kind)
        if caption:
            return caption, cursor
        return None, None
    return None, None


def preamble(logo_name: str | None) -> list[str]:
    lines = [
        r"\documentclass[12pt,letterpaper]{report}",
        r"\usepackage[left=3cm,right=2.5cm,top=2.5cm,bottom=2.5cm]{geometry}",
        r"\usepackage{fontspec}",
        r"\IfFontExistsTF{Times New Roman}{\setmainfont{Times New Roman}}{\setmainfont{TeX Gyre Termes}}",
        r"\usepackage{polyglossia}",
        r"\setdefaultlanguage{spanish}",
        r"\usepackage{graphicx}",
        r"\usepackage{float}",
        r"\usepackage{caption}",
        r"\usepackage{array}",
        r"\usepackage{tabularx}",
        r"\usepackage{booktabs}",
        r"\usepackage{enumitem}",
        r"\usepackage{xurl}",
        r"\usepackage[hidelinks]{hyperref}",
        r"\usepackage{titlesec}",
        r"\titleformat{\chapter}[hang]{\normalfont\bfseries\Large}{\thechapter.}{0.6em}{}",
        r"\titleformat{name=\chapter,numberless}[hang]{\normalfont\bfseries\Large}{}{0pt}{}",
        r"\titlespacing*{\chapter}{0pt}{-0.5cm}{0.8cm}",
        r"\renewcommand{\contentsname}{TABLA DE CONTENIDOS}",
        r"\renewcommand{\listfigurename}{ÍNDICE DE FIGURAS}",
        r"\renewcommand{\listtablename}{ÍNDICE DE TABLAS}",
        r"\renewcommand{\tablename}{Cuadro}",
        r"\captionsetup{font=small,labelfont=bf}",
        r"\setlength{\parindent}{1.25cm}",
        r"\setlength{\parskip}{0.35em}",
        r"\sloppy",
        "",
        r"\begin{document}",
        "",
        r"\begin{titlepage}",
        r"\centering",
    ]
    if logo_name:
        lines.append(rf"\includegraphics[width=0.24\textwidth]{{figuras/{logo_name}}}\\[0.8cm]")
    lines.extend(
        [
            r"{\bfseries UNIVERSIDAD DE TALCA\par}",
            r"{\bfseries FACULTAD DE INGENIERÍA\par}",
            r"{\bfseries ESCUELA DE INGENIERÍA CIVIL EN COMPUTACIÓN\par}",
            r"\vfill",
            r"{\Large\bfseries Sistema de análisis vocal, detección de patrones de error y retroalimentación basado en procesamiento digital de señales\par}",
            r"\vspace{2.5cm}",
            r"{\bfseries DIEGO ALFONSO TAPIA VÁSQUEZ\par}",
            r"\vfill",
            r"{Curicó - Chile\par}",
            r"{Junio, 2026\par}",
            r"\end{titlepage}",
            "",
            r"\pagenumbering{roman}",
            r"\tableofcontents",
            r"\listoffigures",
            r"\listoftables",
            r"\clearpage",
            r"\pagenumbering{arabic}",
            "",
        ]
    )
    return lines


def find_logo(document: Document, converter: LatexConverter) -> str | None:
    for paragraph in document.paragraphs[:20]:
        rids = image_rids_from_element(paragraph._p)
        if rids:
            return converter.write_image(rids[0])
    return None


def convert() -> None:
    if not DOCX_PATH.exists():
        raise FileNotFoundError(DOCX_PATH)

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    document = Document(DOCX_PATH)
    converter = LatexConverter(document)
    logo_name = find_logo(document, converter)

    elements = list(body_elements(document))
    lines = preamble(logo_name)

    started = False
    in_references = False
    references_open = False
    i = 0
    while i < len(elements):
        kind, item = elements[i]

        if kind == "p":
            paragraph = item
            text_value = clean_text(paragraph.text)
            rids = image_rids_from_element(paragraph._p)

            if not started:
                if text_value == "1. Introducción":
                    started = True
                else:
                    i += 1
                    continue

            if rids:
                caption = parse_caption(text_value, "figure")
                consume_to = None
                if caption is None:
                    caption, consume_to = find_next_caption(elements, i, "figure")
                lines.extend(converter.figure_block(rids, caption))
                i = (consume_to + 1) if consume_to is not None else i + 1
                continue

            if not text_value:
                i += 1
                continue

            if text_value == "Referencias":
                if references_open:
                    lines.extend([r"\end{enumerate}", ""])
                    references_open = False
                lines.extend(
                    [
                        r"\chapter*{Referencias}",
                        r"\addcontentsline{toc}{chapter}{Referencias}",
                        "",
                    ]
                )
                in_references = True
                i += 1
                continue

            if text_value == "Anexos":
                if references_open:
                    lines.extend([r"\end{enumerate}", ""])
                    references_open = False
                in_references = False
                lines.extend(
                    [
                        r"\chapter*{Anexos}",
                        r"\addcontentsline{toc}{chapter}{Anexos}",
                        "",
                    ]
                )
                i += 1
                continue

            if in_references:
                ref_match = re.match(r"^\[(\d+)\]\s*(.+)$", text_value)
                if ref_match:
                    if not references_open:
                        lines.extend(
                            [
                                r"\begin{enumerate}[label={[\arabic*]},leftmargin=*]",
                                "",
                            ]
                        )
                        references_open = True
                    lines.append(rf"\item {tex(ref_match.group(2))}")
                    lines.append("")
                else:
                    if references_open:
                        lines.extend([r"\end{enumerate}", ""])
                        references_open = False
                    lines.extend([tex(text_value), ""])
                i += 1
                continue

            if parse_caption(text_value, "figure") or parse_caption(text_value, "table"):
                i += 1
                continue

            heading = heading_block(text_value)
            if heading:
                lines.extend(heading)
            else:
                lines.extend([tex(text_value), ""])
            i += 1
            continue

        table = item
        if not started:
            i += 1
            continue

        table_rids = image_rids_from_element(table._tbl)
        if table_rids:
            caption = None
            consume_to = None
            caption, consume_to = find_next_caption(elements, i, "figure")
            lines.extend(converter.figure_block(table_rids, caption))
            i = (consume_to + 1) if consume_to is not None else i + 1
            continue

        caption = None
        consume_to = None
        caption, consume_to = find_next_caption(elements, i, "table")
        lines.extend(converter.table_block(table, caption))
        i = (consume_to + 1) if consume_to is not None else i + 1

    if references_open:
        lines.extend([r"\end{enumerate}", ""])

    lines.extend([r"\end{document}", ""])
    (OUT_DIR / "main.tex").write_text("\n".join(lines), encoding="utf-8")
    (OUT_DIR / "README.txt").write_text(
        "Documento convertido desde Documento final.docx.\n"
        "Compilación recomendada: xelatex main.tex, ejecutar dos veces para actualizar índices.\n"
        "La carpeta figuras contiene las imágenes extraídas desde el documento Word.\n",
        encoding="utf-8",
    )

    print(f"DOCX: {DOCX_PATH}")
    print(f"Salida: {OUT_DIR}")
    print(f"Imagenes extraidas: {len(converter.image_files)}")
    print(f"Figuras generadas: {converter.figure_count}")
    print(f"Tablas generadas: {converter.table_count}")


if __name__ == "__main__":
    convert()
