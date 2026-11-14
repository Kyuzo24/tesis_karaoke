from pathlib import Path
from urllib.parse import quote
from xml.sax.saxutils import escape


OUT = Path(__file__).resolve().parent

COLORS = {
    "ink": "#1F2937",
    "muted": "#5B6472",
    "line": "#46515F",
    "blue": "#DCEAF7",
    "blue_stroke": "#4779A8",
    "green": "#E5F2EA",
    "green_stroke": "#4D8064",
    "amber": "#FFF3D6",
    "amber_stroke": "#A87822",
    "red": "#FBE8E8",
    "red_stroke": "#A84B4B",
    "gray": "#F3F4F6",
    "gray_stroke": "#6B7280",
    "white": "#FFFFFF",
}

ICONS = {
    "voice": '<path d="M4 12h3l2-5 4 10 2-5h5"/>',
    "process": '<rect x="3" y="5" width="6" height="6" rx="1"/><rect x="15" y="5" width="6" height="6" rx="1"/><rect x="9" y="15" width="6" height="6" rx="1"/><path d="M9 8h6M18 11v2l-6 2M6 11v2l6 2"/>',
    "features": '<path d="M4 16l4-5 4 3 5-7 3 3"/><path d="M4 20h16"/>',
    "score": '<path d="M5 19V9M12 19V5M19 19v-7"/><path d="M3 19h18"/>',
    "user": '<circle cx="12" cy="8" r="4"/><path d="M4 21c1-5 15-5 16 0"/>',
    "audio": '<path d="M4 12h3l2-4 3 8 3-8 2 4h3"/>',
    "numbers": '<path d="M5 19V9M12 19V5M19 19v-7"/><path d="M3 19h18"/>',
    "warning": '<path d="M12 3L2.5 20h19L12 3z"/><path d="M12 9v5M12 17h.01"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7h.01"/>',
    "music": '<path d="M9 18V6l10-2v12"/><circle cx="6" cy="18" r="3"/><circle cx="16" cy="16" r="3"/>',
    "split": '<path d="M5 5v4c0 4 3 4 7 4h7"/><path d="M15 9l4 4-4 4"/><path d="M5 19v-4c0-4 3-4 7-4h7"/>',
    "pitch": '<path d="M3 17l4-5 4 3 5-8 5 3"/><path d="M3 21h18"/>',
    "play": '<circle cx="12" cy="12" r="9"/><path d="M10 8l6 4-6 4V8z"/>',
    "mic": '<rect x="9" y="3" width="6" height="12" rx="3"/><path d="M5 11a7 7 0 0014 0M12 18v3M8 21h8"/>',
    "blocks": '<rect x="3" y="6" width="5" height="12" rx="1"/><rect x="10" y="3" width="5" height="18" rx="1"/><rect x="17" y="8" width="4" height="8" rx="1"/>',
    "stabilize": '<path d="M3 13h3l2-5 3 9 3-7 2 3h5"/><path d="M4 20h16"/>',
    "display": '<rect x="3" y="4" width="18" height="13" rx="2"/><path d="M8 21h8M12 17v4"/>',
    "record": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4"/>',
    "align": '<path d="M4 6h5c3 0 3 6 6 6h5"/><path d="M4 18h5c3 0 3-6 6-6"/><path d="M17 9l3 3-3 3"/>',
    "metrics": '<path d="M4 20V10h4v10M10 20V5h4v15M16 20v-7h4v7"/><path d="M2 20h20"/>',
    "segments": '<path d="M3 7h5v10H3zM10 7h5v10h-5zM17 7h4v10h-4z"/><path d="M3 20h18"/>',
    "feedback": '<path d="M4 4h16v12H9l-5 4V4z"/><path d="M8 8h8M8 12h5"/>',
    "results": '<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M9 3v3h6V3M8 12l3 3 5-6"/>',
    "storage": '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 2 16 2 16 0V5M4 12c0 2 16 2 16 0"/>',
    "history": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l4 2M5 5L3 9l4-1"/>',
    "trend": '<path d="M3 18l5-6 4 3 7-9"/><path d="M15 6h4v4M3 21h18"/>',
}


def icon_markup(name, x, y, size=28, color=None):
    color = color or COLORS["ink"]
    scale = size / 24
    return (
        f'<g transform="translate({x} {y}) scale({scale})" fill="none" '
        f'stroke="{color}" stroke-width="1.8" stroke-linecap="round" '
        f'stroke-linejoin="round">{ICONS[name]}</g>'
    )


def icon_data_uri(name):
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        f'fill="none" stroke="{COLORS["ink"]}" stroke-width="1.8" '
        f'stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</svg>'
    )
    return "data:image/svg+xml," + quote(svg, safe="")


def svg_text(x, y, lines, size=21, weight="normal", color=None):
    color = color or COLORS["ink"]
    line_height = size * 1.24
    start = y - (len(lines) - 1) * line_height / 2
    spans = []
    for index, line in enumerate(lines):
        dy = 0 if index == 0 else line_height
        spans.append(
            f'<tspan x="{x}" dy="{dy}">{escape(line)}</tspan>'
        )
    return (
        f'<text x="{x}" y="{start}" text-anchor="middle" '
        f'font-family="Arial, sans-serif" font-size="{size}" '
        f'font-weight="{weight}" fill="{color}">{"".join(spans)}</text>'
    )


def svg_box(node):
    x, y, w, h = node["x"], node["y"], node["w"], node["h"]
    fill = node.get("fill", COLORS["white"])
    stroke = node.get("stroke", COLORS["line"])
    radius = node.get("radius", 8)
    label = node["label"]
    if isinstance(label, str):
        label = [label]
    icon = node.get("icon")
    icon_size = node.get("icon_size", 27)
    content = [
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="2"/>',
    ]
    text_x = x + w / 2
    if icon:
        content.append(icon_markup(icon, x + 14, y + (h - icon_size) / 2, icon_size))
        text_x += min(16, w * 0.06)
    content.append(
            svg_text(
                text_x,
                y + h / 2 + node.get("text_dy", 7),
                label,
                node.get("font_size", 21),
                node.get("weight", "normal"),
            )
    )
    return "\n".join(content)


def svg_path(points, dashed=False, color=None, width=2.4):
    color = color or COLORS["line"]
    coords = " ".join(f"{x},{y}" for x, y in points)
    dash = ' stroke-dasharray="8 7"' if dashed else ""
    return (
        f'<polyline points="{coords}" fill="none" stroke="{color}" '
        f'stroke-width="{width}" stroke-linejoin="round" '
        f'stroke-linecap="round" marker-end="url(#arrow)"{dash}/>'
    )


def write_svg(filename, width, height, nodes, paths, bands=None, notes=None):
    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        "<defs>",
        '<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerWidth="8" markerHeight="8" orient="auto-start-reverse">',
        f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{COLORS["line"]}"/>',
        "</marker>",
        "</defs>",
        f'<rect width="{width}" height="{height}" fill="{COLORS["white"]}"/>',
    ]
    for band in bands or []:
        elements.append(
            f'<rect x="{band["x"]}" y="{band["y"]}" width="{band["w"]}" '
            f'height="{band["h"]}" rx="10" fill="{band["fill"]}" '
            f'stroke="{band["stroke"]}" stroke-width="1.5"/>'
        )
        elements.append(
            svg_text(
                band["x"] + 22,
                band["y"] + 32,
                [band["title"]],
                22,
                "bold",
                COLORS["ink"],
            ).replace('text-anchor="middle"', 'text-anchor="start"')
        )
    elements.extend(svg_path(**path) for path in paths)
    elements.extend(svg_box(node) for node in nodes)
    for note in notes or []:
        elements.append(
            svg_text(
                note["x"], note["y"], note["lines"], note.get("size", 18),
                note.get("weight", "normal"), note.get("color", COLORS["muted"])
            )
        )
    elements.append("</svg>")
    (OUT / filename).write_text("\n".join(elements), encoding="utf-8")


def drawio_value(label):
    if isinstance(label, str):
        label = [label]
    return "&lt;div&gt;" + "&lt;br&gt;".join(escape(line) for line in label) + "&lt;/div&gt;"


def write_drawio(filename, page_name, width, height, nodes, edges, bands=None, notes=None):
    cells = [
        '<mxCell id="0"/>',
        '<mxCell id="1" parent="0"/>',
    ]
    for index, band in enumerate(bands or [], 1):
        cells.append(
            f'<mxCell id="band{index}" value="{escape(band["title"])}" '
            f'style="swimlane;html=1;rounded=1;startSize=42;fontStyle=1;fontSize=18;'
            f'fillColor={band["fill"]};strokeColor={band["stroke"]};horizontal=1;" '
            f'vertex="1" parent="1"><mxGeometry x="{band["x"]}" y="{band["y"]}" '
            f'width="{band["w"]}" height="{band["h"]}" as="geometry"/></mxCell>'
        )
    for node in nodes:
        icon_style = ""
        if node.get("icon"):
            icon_style = (
                f'shape=label;image={icon_data_uri(node["icon"])};imageWidth=26;imageHeight=26;'
                'imageAlign=left;imageVerticalAlign=middle;spacingLeft=38;'
            )
        cells.append(
            f'<mxCell id="{node["id"]}" value="{drawio_value(node["label"])}" '
            f'style="rounded=1;whiteSpace=wrap;html=1;fontFamily=Arial;fontSize={node.get("font_size", 18)};{icon_style}'
            f'fillColor={node.get("fill", COLORS["white"])};strokeColor={node.get("stroke", COLORS["line"])};'
            f'strokeWidth=2;align=center;verticalAlign=middle;" vertex="1" parent="1">'
            f'<mxGeometry x="{node["x"]}" y="{node["y"]}" width="{node["w"]}" '
            f'height="{node["h"]}" as="geometry"/></mxCell>'
        )
    for index, edge in enumerate(edges, 1):
        dashed = "dashed=1;" if edge.get("dashed") else ""
        cells.append(
            f'<mxCell id="edge{index}" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;'
            f'jettySize=auto;html=1;endArrow=block;endFill=1;strokeWidth=2;strokeColor={COLORS["line"]};{dashed}" '
            f'edge="1" parent="1" source="{edge["source"]}" target="{edge["target"]}">'
            '<mxGeometry relative="1" as="geometry"/></mxCell>'
        )
    for index, note in enumerate(notes or [], 1):
        value = "&lt;br&gt;".join(escape(line) for line in note["lines"])
        cells.append(
            f'<mxCell id="note{index}" value="{value}" '
            f'style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;'
            f'whiteSpace=wrap;fontFamily=Arial;fontSize={note.get("size", 16)};fontColor={note.get("color", COLORS["muted"])};" '
            f'vertex="1" parent="1"><mxGeometry x="{note["x"] - 130}" y="{note["y"] - 28}" '
            f'width="260" height="56" as="geometry"/></mxCell>'
        )
    xml = (
        '<mxfile host="app.diagrams.net" modified="2026-06-20T00:00:00.000Z" agent="Codex" version="24.7.17">'
        f'<diagram id="{page_name.lower().replace(" ", "-")}" name="{escape(page_name)}">'
        f'<mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" '
        f'connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="{width}" pageHeight="{height}" '
        'math="0" shadow="0"><root>' + "".join(cells) + "</root></mxGraphModel></diagram></mxfile>"
    )
    (OUT / filename).write_text(xml, encoding="utf-8")


def figure_11():
    nodes = []
    labels = [
        ["Interpretación", "vocal"],
        ["Captura y", "procesamiento"],
        ["Extracción de", "características"],
        ["Nota, curva o", "puntuación"],
        ["Interpretación", "del usuario"],
    ]
    fills = ["blue", "gray", "green", "amber", "red"]
    strokes = ["blue_stroke", "gray_stroke", "green_stroke", "amber_stroke", "red_stroke"]
    icons = ["voice", "process", "features", "score", "user"]
    for i, label in enumerate(labels):
        nodes.append({
            "id": f"n{i+1}", "x": 50 + i * 305, "y": 120, "w": 240, "h": 110,
            "label": label, "fill": COLORS[fills[i]], "stroke": COLORS[strokes[i]],
            "icon": icons[i],
        })
    paths = [
        {"points": [(290 + i * 305, 175), (355 + i * 305, 175)]}
        for i in range(4)
    ]
    edges = [{"source": f"n{i}", "target": f"n{i+1}"} for i in range(1, 5)]
    notes = [{"x": 800, "y": 295, "lines": ["El resultado requiere interpretación por parte del usuario."], "size": 18}]
    write_svg("figura_1_1_herramientas_apoyo_vocal.svg", 1600, 350, nodes, paths, notes=notes)
    write_drawio("figura_1_1_herramientas_apoyo_vocal.drawio", "Figura 1.1", 1600, 350, nodes, edges, notes=notes)


def figure_12():
    nodes = [
        {"id": "n1", "x": 280, "y": 60, "w": 440, "h": 90, "label": ["Interpretación vocal"], "fill": COLORS["blue"], "stroke": COLORS["blue_stroke"], "icon": "voice"},
        {"id": "n2", "x": 280, "y": 205, "w": 440, "h": 110, "label": ["Datos acústicos", "Frecuencia fundamental y pitch"], "fill": COLORS["gray"], "stroke": COLORS["gray_stroke"], "icon": "audio"},
        {"id": "n3", "x": 280, "y": 370, "w": 440, "h": 110, "label": ["Indicadores cuantitativos", "Notas, cents, curvas y puntuaciones"], "fill": COLORS["amber"], "stroke": COLORS["amber_stroke"], "font_size": 20, "icon": "numbers"},
        {"id": "gap", "x": 230, "y": 535, "w": 540, "h": 90, "label": ["BRECHA DE INTERPRETACIÓN"], "fill": COLORS["red"], "stroke": COLORS["red_stroke"], "weight": "bold", "icon": "warning"},
        {"id": "n4", "x": 280, "y": 680, "w": 440, "h": 125, "label": ["Información útil para el usuario", "Qué ocurrió, dónde ocurrió, si se repitió", "y cómo ha evolucionado"], "fill": COLORS["green"], "stroke": COLORS["green_stroke"], "font_size": 18, "icon": "info"},
    ]
    paths = [
        {"points": [(500, 150), (500, 205)]},
        {"points": [(500, 315), (500, 370)]},
        {"points": [(500, 480), (500, 535)]},
        {"points": [(500, 625), (500, 680)]},
    ]
    edges = [
        {"source": "n1", "target": "n2"},
        {"source": "n2", "target": "n3"},
        {"source": "n3", "target": "gap"},
        {"source": "gap", "target": "n4"},
    ]
    write_svg("figura_1_2_brecha_interpretacion.svg", 1000, 865, nodes, paths)
    write_drawio("figura_1_2_brecha_interpretacion.drawio", "Figura 1.2", 1000, 865, nodes, edges)


def figure_13():
    bands = [
        {"x": 25, "y": 25, "w": 1750, "h": 245, "title": "1. Preparación de la canción", "fill": "#F7FAFC", "stroke": "#AAB4C0"},
        {"x": 25, "y": 300, "w": 1750, "h": 245, "title": "2. Sesión en tiempo real", "fill": "#F7FAFC", "stroke": "#AAB4C0"},
        {"x": 25, "y": 575, "w": 1750, "h": 500, "title": "3. Análisis posterior y seguimiento", "fill": "#F7FAFC", "stroke": "#AAB4C0"},
    ]
    nodes = [
        {"id": "song", "x": 90, "y": 105, "w": 220, "h": 90, "label": ["Canción de", "referencia"], "fill": COLORS["blue"], "stroke": COLORS["blue_stroke"], "icon": "music"},
        {"id": "separate", "x": 390, "y": 105, "w": 240, "h": 90, "label": ["Separación de", "fuentes"], "fill": COLORS["gray"], "stroke": COLORS["gray_stroke"], "icon": "split"},
        {"id": "voice", "x": 730, "y": 75, "w": 220, "h": 80, "label": ["Voz de", "referencia"], "fill": COLORS["green"], "stroke": COLORS["green_stroke"], "icon": "voice"},
        {"id": "instrumental", "x": 730, "y": 170, "w": 220, "h": 80, "label": ["Pista", "instrumental"], "fill": COLORS["amber"], "stroke": COLORS["amber_stroke"], "icon": "music"},
        {"id": "refpitch", "x": 1050, "y": 75, "w": 260, "h": 80, "label": ["Extracción del pitch", "de referencia"], "fill": COLORS["green"], "stroke": COLORS["green_stroke"], "font_size": 19, "icon": "pitch"},

        {"id": "playback", "x": 1320, "y": 330, "w": 250, "h": 70, "label": ["Reproducción del", "acompañamiento"], "fill": COLORS["amber"], "stroke": COLORS["amber_stroke"], "font_size": 18, "icon": "play"},
        {"id": "mic", "x": 90, "y": 435, "w": 190, "h": 80, "label": ["Micrófono"], "fill": COLORS["blue"], "stroke": COLORS["blue_stroke"], "icon": "mic"},
        {"id": "capture", "x": 355, "y": 435, "w": 220, "h": 80, "label": ["Captura por", "bloques"], "fill": COLORS["gray"], "stroke": COLORS["gray_stroke"], "icon": "blocks"},
        {"id": "livepitch", "x": 650, "y": 435, "w": 235, "h": 80, "label": ["Detección y", "estabilización"], "fill": COLORS["green"], "stroke": COLORS["green_stroke"], "icon": "stabilize"},
        {"id": "display", "x": 970, "y": 435, "w": 230, "h": 80, "label": ["Visualización de", "la nota actual"], "fill": COLORS["amber"], "stroke": COLORS["amber_stroke"], "font_size": 19, "icon": "display"},
        {"id": "recording", "x": 1320, "y": 435, "w": 250, "h": 80, "label": ["Grabación de la", "interpretación"], "fill": COLORS["blue"], "stroke": COLORS["blue_stroke"], "icon": "record"},

        {"id": "inputref", "x": 90, "y": 640, "w": 230, "h": 75, "label": ["Pitch de referencia", "preparado"], "fill": COLORS["green"], "stroke": COLORS["green_stroke"], "font_size": 18, "icon": "pitch"},
        {"id": "inputrec", "x": 90, "y": 770, "w": 230, "h": 75, "label": ["Interpretación", "grabada"], "fill": COLORS["blue"], "stroke": COLORS["blue_stroke"], "font_size": 18, "icon": "record"},
        {"id": "align", "x": 400, "y": 705, "w": 240, "h": 90, "label": ["Alineación y", "comparación"], "fill": COLORS["gray"], "stroke": COLORS["gray_stroke"], "icon": "align"},
        {"id": "metrics", "x": 710, "y": 705, "w": 210, "h": 90, "label": ["Cálculo de", "métricas"], "fill": COLORS["blue"], "stroke": COLORS["blue_stroke"], "icon": "metrics"},
        {"id": "segments", "x": 970, "y": 705, "w": 280, "h": 90, "label": ["Detección y caracterización", "de segmentos"], "fill": COLORS["green"], "stroke": COLORS["green_stroke"], "font_size": 16, "icon": "segments"},
        {"id": "feedback", "x": 1300, "y": 705, "w": 260, "h": 90, "label": ["Retroalimentación en", "lenguaje natural"], "fill": COLORS["amber"], "stroke": COLORS["amber_stroke"], "font_size": 18, "icon": "feedback"},
        {"id": "results", "x": 1620, "y": 705, "w": 140, "h": 90, "label": ["Resultados"], "fill": COLORS["red"], "stroke": COLORS["red_stroke"], "font_size": 16, "icon": "results", "icon_size": 22},
        {"id": "storage", "x": 720, "y": 875, "w": 250, "h": 85, "label": ["Almacenamiento", "de la sesión"], "fill": COLORS["blue"], "stroke": COLORS["blue_stroke"], "font_size": 18, "icon": "storage"},
        {"id": "historical", "x": 1060, "y": 875, "w": 260, "h": 85, "label": ["Comparación", "histórica"], "fill": COLORS["gray"], "stroke": COLORS["gray_stroke"], "font_size": 18, "icon": "history"},
        {"id": "evolution", "x": 1410, "y": 875, "w": 270, "h": 85, "label": ["Visualización de", "la evolución"], "fill": COLORS["green"], "stroke": COLORS["green_stroke"], "font_size": 18, "icon": "trend"},
    ]
    paths = [
        {"points": [(310, 150), (390, 150)]},
        {"points": [(630, 150), (680, 150), (680, 115), (730, 115)]},
        {"points": [(630, 150), (680, 150), (680, 210), (730, 210)]},
        {"points": [(950, 115), (1050, 115)]},
        {"points": [(840, 250), (840, 285), (1445, 285), (1445, 330)]},
        {"points": [(280, 475), (355, 475)]},
        {"points": [(575, 475), (650, 475)]},
        {"points": [(885, 475), (970, 475)]},
        {"points": [(575, 475), (610, 475), (610, 525), (1270, 525), (1270, 475), (1320, 475)]},
        {"points": [(320, 677), (360, 677), (360, 735), (400, 735)]},
        {"points": [(320, 807), (360, 807), (360, 765), (400, 765)]},
        {"points": [(640, 750), (710, 750)]},
        {"points": [(920, 750), (970, 750)]},
        {"points": [(1250, 750), (1300, 750)]},
        {"points": [(1560, 750), (1620, 750)]},
        {"points": [(1690, 795), (1690, 835), (845, 835), (845, 875)]},
        {"points": [(970, 917), (1060, 917)]},
        {"points": [(1320, 917), (1410, 917)]},
    ]
    edges = [
        {"source": "song", "target": "separate"},
        {"source": "separate", "target": "voice"},
        {"source": "separate", "target": "instrumental"},
        {"source": "voice", "target": "refpitch"},
        {"source": "instrumental", "target": "playback"},
        {"source": "mic", "target": "capture"},
        {"source": "capture", "target": "livepitch"},
        {"source": "livepitch", "target": "display"},
        {"source": "capture", "target": "recording"},
        {"source": "inputref", "target": "align"},
        {"source": "inputrec", "target": "align"},
        {"source": "align", "target": "metrics"},
        {"source": "metrics", "target": "segments"},
        {"source": "segments", "target": "feedback"},
        {"source": "feedback", "target": "results"},
        {"source": "results", "target": "storage"},
        {"source": "storage", "target": "historical"},
        {"source": "historical", "target": "evolution"},
    ]
    notes = [
        {"x": 800, "y": 375, "lines": ["Procesamiento continuo de baja latencia"], "size": 17},
        {"x": 900, "y": 1025, "lines": ["La comparación utiliza sesiones realizadas sobre una misma canción y referencia."], "size": 17},
    ]
    write_svg("figura_1_3_flujo_solucion.svg", 1800, 1100, nodes, paths, bands=bands, notes=notes)
    write_drawio("figura_1_3_flujo_solucion.drawio", "Figura 1.3", 1800, 1100, nodes, edges, bands=bands, notes=notes)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    figure_11()
    figure_12()
    figure_13()
    print(f"Figuras creadas en: {OUT}")
