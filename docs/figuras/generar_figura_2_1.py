from pathlib import Path
from urllib.parse import quote


OUT = Path(__file__).resolve().parent

INK = "#1F2937"
LINE = "#46515F"
BLUE = "#DCEAF7"
BLUE_STROKE = "#4779A8"
GREEN = "#E5F2EA"
GREEN_STROKE = "#4D8064"
AMBER = "#FFF3D6"
AMBER_STROKE = "#A87822"

MUSIC_ICON = '<path d="M9 18V6l10-2v12"/><circle cx="6" cy="18" r="3"/><circle cx="16" cy="16" r="3"/>'


def text(x, y, value, size=22, weight="normal", color=INK):
    return (
        f'<text x="{x}" y="{y}" text-anchor="middle" font-family="Arial, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{color}">{value}</text>'
    )


def icon(x, y, size=31):
    scale = size / 24
    return (
        f'<g transform="translate({x} {y}) scale({scale})" fill="none" stroke="{INK}" '
        f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{MUSIC_ICON}</g>'
    )


def card(x, note, frequency, fill, stroke):
    return "\n".join(
        [
            f'<rect x="{x}" y="85" width="260" height="145" rx="8" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="2"/>',
            icon(x + 22, 106),
            text(x + 145, 132, note, 28, "bold"),
            text(x + 145, 184, frequency, 25),
        ]
    )


def write_svg():
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="410" viewBox="0 0 1400 410">',
        '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">',
        f'<path d="M0 0L10 5L0 10z" fill="{LINE}"/></marker></defs>',
        '<rect width="1400" height="410" fill="#FFFFFF"/>',
        card(80, "La3", "220 Hz", BLUE, BLUE_STROKE),
        card(570, "La4", "440 Hz", GREEN, GREEN_STROKE),
        card(1060, "La5", "880 Hz", AMBER, AMBER_STROKE),
        f'<line x1="340" y1="158" x2="570" y2="158" stroke="{LINE}" stroke-width="2.5" marker-end="url(#arrow)"/>',
        f'<line x1="830" y1="158" x2="1060" y2="158" stroke="{LINE}" stroke-width="2.5" marker-end="url(#arrow)"/>',
        text(455, 118, "1 octava", 19, "bold"),
        text(455, 206, "frecuencia ×2", 18, "normal", "#5B6472"),
        text(945, 118, "1 octava", 19, "bold"),
        text(945, 206, "frecuencia ×2", 18, "normal", "#5B6472"),
        f'<rect x="350" y="290" width="700" height="70" rx="8" fill="#F3F4F6" stroke="#6B7280" stroke-width="1.5"/>',
        text(700, 334, "Una octava = 12 semitonos = 1200 cents", 22, "bold"),
        '</svg>',
    ]
    (OUT / "figura_2_1_frecuencia_octavas.svg").write_text("\n".join(parts), encoding="utf-8")


def icon_uri():
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
        f'stroke="{INK}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
        f'{MUSIC_ICON}</svg>'
    )
    return "data:image/svg+xml," + quote(svg, safe="")


def write_drawio():
    nodes = [
        ("a3", 80, "La3&lt;br&gt;220 Hz", BLUE, BLUE_STROKE),
        ("a4", 570, "La4&lt;br&gt;440 Hz", GREEN, GREEN_STROKE),
        ("a5", 1060, "La5&lt;br&gt;880 Hz", AMBER, AMBER_STROKE),
    ]
    cells = ['<mxCell id="0"/>', '<mxCell id="1" parent="0"/>']
    image = icon_uri()
    for node_id, x, value, fill, stroke in nodes:
        cells.append(
            f'<mxCell id="{node_id}" value="{value}" style="shape=label;rounded=1;whiteSpace=wrap;html=1;'
            f'fontFamily=Arial;fontSize=22;fontStyle=1;fillColor={fill};strokeColor={stroke};strokeWidth=2;'
            f'image={image};imageWidth=30;imageHeight=30;imageAlign=left;imageVerticalAlign=middle;spacingLeft=42;" '
            f'vertex="1" parent="1"><mxGeometry x="{x}" y="85" width="260" height="145" as="geometry"/></mxCell>'
        )
    for edge_id, source, target in (("e1", "a3", "a4"), ("e2", "a4", "a5")):
        cells.append(
            f'<mxCell id="{edge_id}" value="1 octava&lt;br&gt;frecuencia ×2" '
            f'style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;endFill=1;strokeWidth=2;'
            f'strokeColor={LINE};fontFamily=Arial;fontSize=16;labelBackgroundColor=#FFFFFF;" edge="1" '
            f'parent="1" source="{source}" target="{target}"><mxGeometry relative="1" as="geometry"/></mxCell>'
        )
    cells.append(
        '<mxCell id="note" value="Una octava = 12 semitonos = 1200 cents" '
        'style="rounded=1;whiteSpace=wrap;html=1;fontFamily=Arial;fontSize=20;fontStyle=1;'
        'fillColor=#F3F4F6;strokeColor=#6B7280;strokeWidth=1.5;" vertex="1" parent="1">'
        '<mxGeometry x="350" y="290" width="700" height="70" as="geometry"/></mxCell>'
    )
    xml = (
        '<mxfile host="app.diagrams.net" modified="2026-06-22T00:00:00.000Z" agent="Codex" version="24.7.17">'
        '<diagram id="figura-2-1" name="Figura 2.1"><mxGraphModel dx="1200" dy="700" grid="1" gridSize="10" '
        'guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" '
        'pageWidth="1400" pageHeight="410" math="0" shadow="0"><root>'
        + "".join(cells)
        + '</root></mxGraphModel></diagram></mxfile>'
    )
    (OUT / "figura_2_1_frecuencia_octavas.drawio").write_text(xml, encoding="utf-8")


if __name__ == "__main__":
    write_svg()
    write_drawio()
    print(OUT)
