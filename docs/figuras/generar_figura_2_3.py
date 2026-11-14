from pathlib import Path


OUT = Path(__file__).resolve().parent
INK = "#1F2937"
LINE = "#46515F"


def text(x, y, value, size=20, weight="normal", color=INK):
    return (
        f'<text x="{x}" y="{y}" text-anchor="middle" font-family="Arial, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{color}">{value}</text>'
    )


def box(x, label1, label2, fill, stroke):
    return "\n".join(
        [
            f'<rect x="{x}" y="120" width="245" height="125" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="2"/>',
            text(x + 122.5, 170, label1, 20, "bold"),
            text(x + 122.5, 205, label2, 18),
        ]
    )


def write_svg():
    nodes = [
        (45, "Bloque de", "audio vocal", "#DCEAF7", "#4779A8"),
        (330, "Análisis de", "periodicidad", "#F3F4F6", "#6B7280"),
        (615, "Decisión de", "sonoridad", "#FFF3D6", "#A87822"),
        (900, "Estimación y", "refinamiento de F0", "#E5F2EA", "#4D8064"),
        (1185, "Trayectoria", "temporal de F0", "#FBE8E8", "#A84B4B"),
    ]
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1480" height="430" viewBox="0 0 1480 430">',
        '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto">',
        f'<path d="M0 0L10 5L0 10z" fill="{LINE}"/></marker></defs>',
        '<rect width="1480" height="430" fill="#FFFFFF"/>',
    ]
    for node in nodes:
        parts.append(box(*node))
    for x in (290, 575, 860, 1145):
        parts.append(f'<line x1="{x}" y1="182" x2="{x + 40}" y2="182" stroke="{LINE}" stroke-width="2.5" marker-end="url(#arrow)"/>')

    parts.extend(
        [
            text(737, 76, "¿Existe una componente periódica confiable?", 19, "bold"),
            f'<path d="M737 95V120" fill="none" stroke="{LINE}" stroke-width="1.8" marker-end="url(#arrow)"/>',
            f'<path d="M737 245V295H590" fill="none" stroke="{LINE}" stroke-width="2" marker-end="url(#arrow)"/>',
            '<rect x="335" y="295" width="255" height="75" rx="8" fill="#F3F4F6" stroke="#6B7280" stroke-width="1.5"/>',
            text(462, 326, "Sin F0 válida", 19, "bold"),
            text(462, 352, "silencio o tramo no sonoro", 16, "normal", "#5B6472"),
            '<rect x="760" y="295" width="500" height="75" rx="8" fill="#E5F2EA" stroke="#4D8064" stroke-width="1.5"/>',
            text(1010, 326, "Filtrado temporal", 19, "bold"),
            text(1010, 352, "continuidad, confianza y eliminación de saltos aislados", 16, "normal", "#5B6472"),
            f'<path d="M1022 245V295" fill="none" stroke="{LINE}" stroke-width="2" marker-end="url(#arrow)"/>',
            '</svg>',
        ]
    )
    (OUT / "figura_2_3_estimacion_f0.svg").write_text("\n".join(parts), encoding="utf-8")


def write_drawio():
    nodes = [
        ("audio", 45, "Bloque de&lt;br&gt;audio vocal", "#DCEAF7", "#4779A8"),
        ("period", 330, "Análisis de&lt;br&gt;periodicidad", "#F3F4F6", "#6B7280"),
        ("voicing", 615, "Decisión de&lt;br&gt;sonoridad", "#FFF3D6", "#A87822"),
        ("estimate", 900, "Estimación y&lt;br&gt;refinamiento de F0", "#E5F2EA", "#4D8064"),
        ("track", 1185, "Trayectoria&lt;br&gt;temporal de F0", "#FBE8E8", "#A84B4B"),
    ]
    cells = ['<mxCell id="0"/>', '<mxCell id="1" parent="0"/>']
    for node_id, x, value, fill, stroke in nodes:
        cells.append(
            f'<mxCell id="{node_id}" value="{value}" style="rounded=1;whiteSpace=wrap;html=1;'
            f'fontFamily=Arial;fontSize=19;fillColor={fill};strokeColor={stroke};strokeWidth=2;" vertex="1" parent="1">'
            f'<mxGeometry x="{x}" y="120" width="245" height="125" as="geometry"/></mxCell>'
        )
    for index, (source, target) in enumerate((('audio','period'),('period','voicing'),('voicing','estimate'),('estimate','track')), 1):
        cells.append(
            f'<mxCell id="e{index}" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;'
            f'endFill=1;strokeWidth=2;strokeColor={LINE};" edge="1" parent="1" source="{source}" target="{target}">'
            '<mxGeometry relative="1" as="geometry"/></mxCell>'
        )
    cells.extend(
        [
            '<mxCell id="invalid" value="Sin F0 válida&lt;br&gt;silencio o tramo no sonoro" style="rounded=1;whiteSpace=wrap;html=1;'
            'fontFamily=Arial;fontSize=17;fillColor=#F3F4F6;strokeColor=#6B7280;" vertex="1" parent="1">'
            '<mxGeometry x="335" y="295" width="255" height="75" as="geometry"/></mxCell>',
            '<mxCell id="filter" value="Filtrado temporal&lt;br&gt;continuidad, confianza y eliminación de saltos aislados" '
            'style="rounded=1;whiteSpace=wrap;html=1;fontFamily=Arial;fontSize=17;fillColor=#E5F2EA;strokeColor=#4D8064;" '
            'vertex="1" parent="1"><mxGeometry x="760" y="295" width="500" height="75" as="geometry"/></mxCell>',
            f'<mxCell id="e5" style="edgeStyle=orthogonalEdgeStyle;html=1;endArrow=block;strokeWidth=2;strokeColor={LINE};" '
            'edge="1" parent="1" source="voicing" target="invalid"><mxGeometry relative="1" as="geometry"/></mxCell>',
            f'<mxCell id="e6" style="edgeStyle=orthogonalEdgeStyle;html=1;endArrow=block;strokeWidth=2;strokeColor={LINE};" '
            'edge="1" parent="1" source="estimate" target="filter"><mxGeometry relative="1" as="geometry"/></mxCell>',
        ]
    )
    xml = (
        '<mxfile host="app.diagrams.net" modified="2026-06-22T00:00:00.000Z" agent="Codex" version="24.7.17">'
        '<diagram id="figura-2-3" name="Figura 2.3"><mxGraphModel dx="1200" dy="700" grid="1" gridSize="10" '
        'guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1480" '
        'pageHeight="430" math="0" shadow="0"><root>' + "".join(cells) + '</root></mxGraphModel></diagram></mxfile>'
    )
    (OUT / "figura_2_3_estimacion_f0.drawio").write_text(xml, encoding="utf-8")


if __name__ == "__main__":
    write_svg()
    write_drawio()
    print(OUT)
