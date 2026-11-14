from pathlib import Path
from math import sin, pi


OUT = Path(__file__).resolve().parent
INK = "#1F2937"
LINE = "#46515F"
BLUE = "#4779A8"
GREEN = "#4D8064"
AMBER = "#A87822"


def label(x, y, value, size=21, weight="normal", color=INK):
    return (
        f'<text x="{x}" y="{y}" text-anchor="middle" font-family="Arial, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{color}">{value}</text>'
    )


def waveform_points(x0, x1, center_y, amplitude, cycles=2.2, samples=100):
    points = []
    for index in range(samples + 1):
        ratio = index / samples
        x = x0 + (x1 - x0) * ratio
        y = center_y - amplitude * sin(2 * pi * cycles * ratio)
        points.append(f"{x:.1f},{y:.1f}")
    return " ".join(points)


def write_svg():
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="500" viewBox="0 0 1500 500">',
        '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto">',
        f'<path d="M0 0L10 5L0 10z" fill="{LINE}"/></marker></defs>',
        '<rect width="1500" height="500" fill="#FFFFFF"/>',
    ]

    panels = [
        (50, "Señal continua", "#F3F4F6", "#6B7280"),
        (540, "Muestreo digital", "#DCEAF7", "#4779A8"),
        (1030, "Procesamiento por bloques", "#E5F2EA", "#4D8064"),
    ]
    for x, title, fill, stroke in panels:
        parts.append(f'<rect x="{x}" y="70" width="420" height="260" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
        parts.append(label(x + 210, 110, title, 22, "bold"))

    continuous = waveform_points(85, 435, 215, 62)
    parts.append(f'<polyline points="{continuous}" fill="none" stroke="{BLUE}" stroke-width="3"/>')
    parts.append(f'<line x1="85" y1="285" x2="435" y2="285" stroke="{LINE}" stroke-width="1.5"/>')
    parts.append(label(260, 312, "tiempo", 16, "normal", "#5B6472"))

    sampled = waveform_points(575, 925, 215, 62)
    parts.append(f'<polyline points="{sampled}" fill="none" stroke="#9CA3AF" stroke-width="2" opacity="0.55"/>')
    for index in range(13):
        ratio = index / 12
        x = 575 + 350 * ratio
        y = 215 - 62 * sin(2 * pi * 2.2 * ratio)
        parts.append(f'<line x1="{x:.1f}" y1="285" x2="{x:.1f}" y2="{y:.1f}" stroke="{BLUE}" stroke-width="1.5" opacity="0.65"/>')
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{BLUE}"/>')
    parts.append(f'<line x1="575" y1="285" x2="925" y2="285" stroke="{LINE}" stroke-width="1.5"/>')
    parts.append(label(750, 312, "muestras discretas", 16, "normal", "#5B6472"))

    block_wave = waveform_points(1065, 1415, 215, 52)
    parts.append(f'<polyline points="{block_wave}" fill="none" stroke="{GREEN}" stroke-width="2.5"/>')
    block_specs = [(1065, 180, "#DCEAF7", BLUE), (1165, 180, "#FFF3D6", AMBER), (1265, 150, "#FBE8E8", "#A84B4B")]
    for x, width, fill, stroke in block_specs:
        parts.append(f'<rect x="{x}" y="140" width="{width}" height="150" rx="4" fill="{fill}" fill-opacity="0.35" stroke="{stroke}" stroke-width="2"/>')
    parts.append(label(1240, 312, "bloques parcialmente superpuestos", 16, "normal", "#5B6472"))

    parts.append(f'<line x1="470" y1="200" x2="540" y2="200" stroke="{LINE}" stroke-width="2.5" marker-end="url(#arrow)"/>')
    parts.append(f'<line x1="960" y1="200" x2="1030" y2="200" stroke="{LINE}" stroke-width="2.5" marker-end="url(#arrow)"/>')

    parts.append('<rect x="280" y="390" width="940" height="70" rx="8" fill="#FFF3D6" stroke="#A87822" stroke-width="1.5"/>')
    parts.append(label(750, 432, "El tamaño y desplazamiento de los bloques influyen en la latencia y estabilidad del análisis.", 20, "bold"))
    parts.append('</svg>')
    (OUT / "figura_2_2_muestreo_bloques.svg").write_text("\n".join(parts), encoding="utf-8")


def write_drawio():
    cells = ['<mxCell id="0"/>', '<mxCell id="1" parent="0"/>']
    panels = [
        ("p1", 50, "Señal continua", "#F3F4F6", "#6B7280"),
        ("p2", 540, "Muestreo digital", "#DCEAF7", "#4779A8"),
        ("p3", 1030, "Procesamiento por bloques", "#E5F2EA", "#4D8064"),
    ]
    descriptions = {
        "p1": "Variación continua de presión&lt;br&gt;a lo largo del tiempo",
        "p2": "Valores discretos obtenidos&lt;br&gt;a intervalos regulares",
        "p3": "Ventanas parcialmente superpuestas&lt;br&gt;para el análisis temporal",
    }
    for node_id, x, title, fill, stroke in panels:
        value = f"&lt;b&gt;{title}&lt;/b&gt;&lt;br&gt;&lt;br&gt;{descriptions[node_id]}"
        cells.append(
            f'<mxCell id="{node_id}" value="{value}" style="rounded=1;whiteSpace=wrap;html=1;'
            f'fontFamily=Arial;fontSize=20;fillColor={fill};strokeColor={stroke};strokeWidth=2;" vertex="1" parent="1">'
            f'<mxGeometry x="{x}" y="70" width="420" height="260" as="geometry"/></mxCell>'
        )
    for edge_id, source, target in (("e1", "p1", "p2"), ("e2", "p2", "p3")):
        cells.append(
            f'<mxCell id="{edge_id}" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;'
            f'endFill=1;strokeWidth=2;strokeColor={LINE};" edge="1" parent="1" source="{source}" target="{target}">'
            '<mxGeometry relative="1" as="geometry"/></mxCell>'
        )
    cells.append(
        '<mxCell id="note" value="El tamaño y desplazamiento de los bloques influyen en la latencia y estabilidad del análisis." '
        'style="rounded=1;whiteSpace=wrap;html=1;fontFamily=Arial;fontSize=18;fontStyle=1;fillColor=#FFF3D6;'
        'strokeColor=#A87822;strokeWidth=1.5;" vertex="1" parent="1"><mxGeometry x="280" y="390" '
        'width="940" height="70" as="geometry"/></mxCell>'
    )
    xml = (
        '<mxfile host="app.diagrams.net" modified="2026-06-22T00:00:00.000Z" agent="Codex" version="24.7.17">'
        '<diagram id="figura-2-2" name="Figura 2.2"><mxGraphModel dx="1200" dy="700" grid="1" gridSize="10" '
        'guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1500" '
        'pageHeight="500" math="0" shadow="0"><root>' + "".join(cells) + '</root></mxGraphModel></diagram></mxfile>'
    )
    (OUT / "figura_2_2_muestreo_bloques.drawio").write_text(xml, encoding="utf-8")


if __name__ == "__main__":
    write_svg()
    write_drawio()
    print(OUT)
