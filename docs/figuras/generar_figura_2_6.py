from pathlib import Path


OUT = Path(__file__).resolve().parent
INK = "#1F2937"
LINE = "#46515F"


def label(x, y, value, size=18, weight="normal", color=INK):
    return f'<text x="{x}" y="{y}" text-anchor="middle" font-family="Arial" font-size="{size}" font-weight="{weight}" fill="{color}">{value}</text>'


def card(x, y, w, h, title, lines, fill, stroke):
    parts = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="2"/>', label(x + w / 2, y + 36, title, 19, "bold")]
    for index, line in enumerate(lines):
        parts.append(label(x + w / 2, y + 70 + index * 27, line, 16, "normal", "#5B6472"))
    return "".join(parts)


def write_svg():
    stages = [
        (40, "Diferencias locales", ["error en cents", "voz ausente", "inestabilidad"], "#DCEAF7", "#4779A8"),
        (330, "Detección", ["criterios de magnitud", "duración y confianza"], "#F3F4F6", "#6B7280"),
        (620, "Agrupación temporal", ["instantes contiguos", "inicio y término"], "#E5F2EA", "#4D8064"),
        (910, "Caracterización", ["tipo de problema", "evidencia y contexto"], "#FFF3D6", "#A87822"),
        (1200, "Priorización", ["severidad", "persistencia", "relevancia"], "#FBE8E8", "#A84B4B"),
    ]
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="520" viewBox="0 0 1500 520">',
        '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M0 0L10 5L0 10z" fill="#46515F"/></marker></defs>',
        '<rect width="1500" height="520" fill="#FFFFFF"/>',
        label(750, 55, "Formación de segmentos problemáticos a partir de evidencias temporales", 23, "bold"),
    ]
    for x, title, lines, fill, stroke in stages:
        parts.append(card(x, 150, 250, 155, title, lines, fill, stroke))
    for x in (290, 580, 870, 1160):
        parts.append(f'<line x1="{x}" y1="228" x2="{x + 40}" y2="228" stroke="{LINE}" stroke-width="2.5" marker-end="url(#arrow)"/>')
    parts.extend([
        '<line x1="70" y1="390" x2="1430" y2="390" stroke="#CBD5E1" stroke-width="10" stroke-linecap="round"/>',
        '<line x1="285" y1="390" x2="520" y2="390" stroke="#C16B32" stroke-width="16" stroke-linecap="round"/>',
        '<line x1="785" y1="390" x2="1110" y2="390" stroke="#A84B4B" stroke-width="16" stroke-linecap="round"/>',
        label(402, 435, "Segmento 1", 16, "bold", "#8A4B24"),
        label(947, 435, "Segmento 2", 16, "bold", "#873D3D"),
        label(750, 485, "Línea temporal de la interpretación", 17, "normal", "#5B6472"),
        '</svg>',
    ])
    (OUT / "figura_2_6_segmentos_problematicos.svg").write_text("\n".join(parts), encoding="utf-8")


def write_drawio():
    cells = ['<mxCell id="0"/>', '<mxCell id="1" parent="0"/>']
    nodes = [
        ("local", 40, "Diferencias locales&lt;br&gt;error, ausencia e inestabilidad", "#DCEAF7", "#4779A8"),
        ("detect", 330, "Detección&lt;br&gt;magnitud, duración y confianza", "#F3F4F6", "#6B7280"),
        ("group", 620, "Agrupación temporal&lt;br&gt;instantes contiguos", "#E5F2EA", "#4D8064"),
        ("describe", 910, "Caracterización&lt;br&gt;tipo, evidencia y contexto", "#FFF3D6", "#A87822"),
        ("rank", 1200, "Priorización&lt;br&gt;severidad y persistencia", "#FBE8E8", "#A84B4B"),
    ]
    for node_id, x, value, fill, stroke in nodes:
        cells.append(f'<mxCell id="{node_id}" value="{value}" style="rounded=1;whiteSpace=wrap;html=1;fontFamily=Arial;fontSize=17;fillColor={fill};strokeColor={stroke};strokeWidth=2;" vertex="1" parent="1"><mxGeometry x="{x}" y="170" width="250" height="140" as="geometry"/></mxCell>')
    for index, (source, target) in enumerate(zip([x[0] for x in nodes[:-1]], [x[0] for x in nodes[1:]]), 1):
        cells.append(f'<mxCell id="e{index}" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;endFill=1;strokeWidth=2;strokeColor=#46515F;" edge="1" parent="1" source="{source}" target="{target}"><mxGeometry relative="1" as="geometry"/></mxCell>')
    xml = '<mxfile host="app.diagrams.net" agent="Codex"><diagram name="Figura 2.6"><mxGraphModel pageWidth="1500" pageHeight="520"><root>' + ''.join(cells) + '</root></mxGraphModel></diagram></mxfile>'
    (OUT / "figura_2_6_segmentos_problematicos.drawio").write_text(xml, encoding="utf-8")


if __name__ == "__main__":
    write_svg()
    write_drawio()
    print(OUT)
