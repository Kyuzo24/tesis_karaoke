from pathlib import Path


OUT = Path(__file__).resolve().parent
INK = "#111111"
GRAY = "#F2F2F2"
MID = "#D9D9D9"
MUTED = "#555555"


def text(x, y, value, size=18, weight="normal", anchor="middle", color=INK):
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="Arial" font-size="{size}" font-weight="{weight}" fill="{color}">{value}</text>'


def box(x, y, w, h, title, details=(), fill="#FFFFFF", dashed=False, radius=5):
    dash = ' stroke-dasharray="8 6"' if dashed else ""
    parts = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{INK}" stroke-width="2"{dash}/>', text(x + w / 2, y + 32, title, 18, "bold")]
    for i, line in enumerate(details):
        parts.append(text(x + w / 2, y + 62 + i * 24, line, 15, color=MUTED))
    return "".join(parts)


def arrow(x1, y1, x2, y2, dashed=False):
    dash = ' stroke-dasharray="8 6"' if dashed else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{INK}" stroke-width="2"{dash} marker-end="url(#arrow)"/>'


def path_arrow(path, dashed=False):
    dash = ' stroke-dasharray="8 6"' if dashed else ""
    return f'<path d="{path}" fill="none" stroke="{INK}" stroke-width="2"{dash} marker-end="url(#arrow)"/>'


def defs():
    return '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M0 0L10 5L0 10z" fill="#111111"/></marker></defs>'


def microphone(x, y, scale=1):
    return f'''<g transform="translate({x} {y}) scale({scale})" stroke="{INK}" fill="none" stroke-width="2">
<rect x="22" y="0" width="36" height="68" rx="18"/><path d="M12 38v10c0 25 56 25 56 0V38"/><line x1="40" y1="73" x2="40" y2="96"/><line x1="22" y1="96" x2="58" y2="96"/>
</g>'''


def laptop(x, y, scale=1):
    return f'''<g transform="translate({x} {y}) scale({scale})" stroke="{INK}" fill="#FFFFFF" stroke-width="2">
<rect x="0" y="0" width="150" height="95" rx="4"/><rect x="10" y="10" width="130" height="70" fill="{GRAY}"/><path d="M-12 98h174l-14 14H2z"/>
<polyline points="24,52 38,42 51,57 65,34 82,49 99,26 126,43" fill="none"/>
</g>'''


def folder_icon(x, y, scale=1):
    return f'''<g transform="translate({x} {y}) scale({scale})" stroke="{INK}" fill="#FFFFFF" stroke-width="2">
<path d="M0 18h34l9 10h67v62H0z"/><path d="M0 35h110"/>
</g>'''


def database_icon(x, y, scale=1):
    return f'''<g transform="translate({x} {y}) scale({scale})" stroke="{INK}" fill="#FFFFFF" stroke-width="2">
<ellipse cx="55" cy="15" rx="55" ry="15"/><path d="M0 15v62c0 20 110 20 110 0V15"/><path d="M0 46c0 20 110 20 110 0"/>
</g>'''


def document_icon(x, y, scale=1):
    return f'''<g transform="translate({x} {y}) scale({scale})" stroke="{INK}" fill="#FFFFFF" stroke-width="2">
<path d="M0 0h62l18 18v92H0z"/><path d="M62 0v18h18M15 45h50M15 62h50M15 79h34"/>
</g>'''


def generate_physical_svg():
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900" viewBox="0 0 1600 900">', defs(), '<rect width="1600" height="900" fill="#FFFFFF"/>',
        text(800, 45, "Arquitectura física de ejecución local", 24, "bold"),
        microphone(80, 205, 1.25), text(130, 355, "Micrófono", 17, "bold"), text(130, 380, "entrada mono", 14, color=MUTED),
        folder_icon(60, 535, 1.15), text(125, 670, "Canción original", 17, "bold"),
        '<rect x="285" y="85" width="970" height="700" rx="8" fill="#FFFFFF" stroke="#111111" stroke-width="2.5"/>',
        text(770, 120, "Computador local Windows", 21, "bold"),
        laptop(340, 165, 1.25), text(435, 330, "Aplicación de escritorio", 17, "bold"), text(435, 355, "app.py · Python", 14, color=MUTED),
        box(655, 165, 235, 120, "Captura de audio", ("sounddevice", "44,1 kHz"), GRAY),
        box(940, 165, 235, 120, "Coordinación", ("catálogo", "sesión"), "#FFFFFF"),
        box(350, 430, 235, 120, "Subproceso", ("HT Demucs", "Python 3.10"), GRAY),
        box(655, 430, 235, 120, "Análisis", ("Pyworld · librosa", "DTW · métricas"), "#FFFFFF"),
        database_icon(1000, 425, 1.15), text(1065, 565, "Almacenamiento local", 17, "bold"), text(1065, 590, "WAV · CSV · JSON", 14, color=MUTED),
        arrow(210, 280, 655, 225), arrow(185, 590, 350, 490), arrow(585, 490, 655, 490), arrow(890, 490, 1000, 490),
        path_arrow("M772 285V355H772V430"), path_arrow("M1058 285V355H772V430"),
        document_icon(1375, 180, 1.15), text(1420, 325, "Resultados", 17, "bold"), text(1420, 350, "métricas y gráfico", 14, color=MUTED),
        box(1325, 520, 215, 115, "Salida de audio", ("audífonos", "instrumental"), "#FFFFFF"),
        arrow(1255, 490, 1375, 250), arrow(1255, 540, 1325, 575),
        '<rect x="1310" y="695" width="245" height="115" rx="5" fill="#FFFFFF" stroke="#111111" stroke-width="2" stroke-dasharray="8 6"/>',
        text(1432, 730, "Conexión opcional", 17, "bold"), text(1432, 758, "descarga de modelos", 14, color=MUTED), text(1432, 782, "o LLM remoto", 14, color=MUTED),
        path_arrow("M1175 225H1280V752H1310", True),
        text(800, 855, "El flujo principal opera sin servidor y conserva los datos en el equipo", 16, color=MUTED),
        '</svg>',
    ]
    (OUT / "ilustracion_arquitectura_fisica_drawio.svg").write_text("".join(parts), encoding="utf-8")


def generate_logical_svg():
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1750" height="1050" viewBox="0 0 1750 1050">', defs(), '<rect width="1750" height="1050" fill="#FFFFFF"/>',
        text(875, 45, "Arquitectura lógica del sistema", 24, "bold"),
        '<rect x="45" y="85" width="1660" height="420" rx="8" fill="#FFFFFF" stroke="#111111" stroke-width="2"/>',
        text(875, 120, "Flujo implementado o parcial", 18, "bold"),
        box(75, 175, 220, 110, "app.py", ("eventos", "hilos"), GRAY),
        box(345, 175, 220, 110, "catalogo.py", ("identidad", "metadatos"), "#FFFFFF"),
        box(615, 175, 220, 110, "separacion.py", ("Demucs", "instrumental"), GRAY),
        box(885, 175, 220, 110, "pitch.py", ("F0", "filtrado"), "#FFFFFF"),
        box(1155, 175, 220, 110, "guardar.py", ("ref_pitch.csv",), GRAY),
        arrow(295, 230, 345, 230), arrow(565, 230, 615, 230), arrow(835, 230, 885, 230), arrow(1105, 230, 1155, 230),
        box(210, 350, 230, 110, "karaoke.py", ("reproducción", "grabación"), "#FFFFFF"),
        box(520, 350, 230, 110, "comparacion.py", ("DTW", "correspondencias"), GRAY),
        box(830, 350, 230, 110, "metricas.py", ("cents", "umbrales"), "#FFFFFF"),
        box(1140, 350, 230, 110, "visualizacion.py", ("nota", "tiempo"), GRAY),
        box(1450, 350, 210, 110, "Resultado JSON", ("métricas", "curvas"), "#FFFFFF"),
        arrow(440, 405, 520, 405), arrow(750, 405, 830, 405), arrow(1060, 405, 1140, 405), arrow(1370, 405, 1450, 405),
        path_arrow("M995 285V320H325V350"),
        '<rect x="45" y="565" width="1660" height="375" rx="8" fill="#FAFAFA" stroke="#111111" stroke-width="2" stroke-dasharray="9 7"/>',
        text(875, 605, "Extensión requerida", 18, "bold"),
        box(95, 680, 255, 125, "Captura por bloques", ("InputStream", "latencia < 150 ms"), "#FFFFFF", True),
        box(425, 680, 255, 125, "Nota estabilizada", ("F0 + confianza", "salida continua"), "#FFFFFF", True),
        box(755, 680, 255, 125, "Análisis temporal", ("DTW en cents", "segmentos"), "#FFFFFF", True),
        box(1085, 680, 255, 125, "Retroalimentación", ("hallazgos", "validación"), "#FFFFFF", True),
        box(1415, 680, 240, 125, "Historial", ("referencia versionada", "evolución"), "#FFFFFF", True),
        arrow(350, 742, 425, 742, True), arrow(680, 742, 755, 742, True), arrow(1010, 742, 1085, 742, True), arrow(1340, 742, 1415, 742, True),
        path_arrow("M325 460V525H222V680", True),
        text(875, 975, "Línea continua: disponible o parcial · Línea discontinua: pendiente", 16, color=MUTED),
        '</svg>',
    ]
    svg = "".join(parts).replace("latencia < 150 ms", "latencia &lt; 150 ms")
    (OUT / "ilustracion_arquitectura_logica_drawio.svg").write_text(svg, encoding="utf-8")


def drawio(name, diagram_name, width, height, nodes, edges, groups=()):
    cells = ['<mxCell id="0"/>', '<mxCell id="1" parent="0"/>']
    for group_id, x, y, w, h, label, dashed in groups:
        style = f'rounded=1;whiteSpace=wrap;html=1;verticalAlign=top;spacingTop=14;fontStyle=1;fontSize=18;fillColor=#FFFFFF;strokeColor=#111111;strokeWidth=2;dashed={1 if dashed else 0};'
        cells.append(f'<mxCell id="{group_id}" value="{label}" style="{style}" vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
    for node_id, x, y, w, h, value, fill, dashed, shape in nodes:
        shape_style = f'shape={shape};' if shape else ''
        style = f'{shape_style}rounded=1;whiteSpace=wrap;html=1;fontFamily=Arial;fontSize=16;fillColor={fill};strokeColor=#111111;strokeWidth=2;dashed={1 if dashed else 0};'
        cells.append(f'<mxCell id="{node_id}" value="{value}" style="{style}" vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
    for i, (source, target, dashed) in enumerate(edges, 1):
        cells.append(f'<mxCell id="e{i}" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;endFill=1;strokeWidth=2;strokeColor=#111111;dashed={1 if dashed else 0};" edge="1" parent="1" source="{source}" target="{target}"><mxGeometry relative="1" as="geometry"/></mxCell>')
    xml = f'<mxfile host="app.diagrams.net" agent="Codex"><diagram name="{diagram_name}"><mxGraphModel pageWidth="{width}" pageHeight="{height}"><root>{"".join(cells)}</root></mxGraphModel></diagram></mxfile>'
    (OUT / name).write_text(xml, encoding="utf-8")


def generate_drawio():
    drawio("ilustracion_arquitectura_fisica_drawio.drawio", "Arquitectura física", 1600, 900, [
        ("mic", 55, 220, 170, 95, "Micrófono&lt;br&gt;entrada mono", "#FFFFFF", False, "mxgraph.signs.tech.microphone"),
        ("song", 55, 535, 170, 95, "Canción original", "#FFFFFF", False, "folder"),
        ("app", 345, 165, 210, 105, "Aplicación&lt;br&gt;app.py · Python", "#F2F2F2", False, "process"),
        ("capture", 650, 165, 230, 110, "Captura de audio&lt;br&gt;sounddevice · 44,1 kHz", "#F2F2F2", False, "process"),
        ("coord", 940, 165, 230, 110, "Coordinación&lt;br&gt;catálogo · sesión", "#FFFFFF", False, "process"),
        ("demucs", 345, 430, 230, 110, "Subproceso&lt;br&gt;HT Demucs", "#F2F2F2", False, "process"),
        ("analysis", 650, 430, 230, 110, "Análisis&lt;br&gt;Pyworld · DTW", "#FFFFFF", False, "process"),
        ("storage", 970, 430, 230, 110, "Almacenamiento&lt;br&gt;WAV · CSV · JSON", "#F2F2F2", False, "cylinder"),
        ("results", 1350, 180, 180, 100, "Resultados&lt;br&gt;métricas y gráfico", "#FFFFFF", False, "document"),
        ("audioout", 1350, 515, 180, 100, "Salida de audio&lt;br&gt;audífonos", "#FFFFFF", False, "process"),
        ("optional", 1325, 700, 215, 110, "Conexión opcional&lt;br&gt;modelos o LLM", "#FFFFFF", True, "cloud"),
    ], [("mic", "capture", False), ("song", "demucs", False), ("app", "capture", False), ("app", "coord", False), ("demucs", "analysis", False), ("capture", "analysis", False), ("analysis", "storage", False), ("storage", "results", False), ("storage", "audioout", False), ("coord", "optional", True)], [("pc", 285, 85, 970, 700, "Computador local Windows", False)])

    current_nodes = [
        ("app", 75, 175, 220, 110, "app.py&lt;br&gt;eventos · hilos", "#F2F2F2", False, "process"),
        ("catalog", 345, 175, 220, 110, "catalogo.py&lt;br&gt;identidad · metadatos", "#FFFFFF", False, "process"),
        ("separation", 615, 175, 220, 110, "separacion.py&lt;br&gt;Demucs · instrumental", "#F2F2F2", False, "process"),
        ("pitch", 885, 175, 220, 110, "pitch.py&lt;br&gt;F0 · filtrado", "#FFFFFF", False, "process"),
        ("save", 1155, 175, 220, 110, "guardar.py&lt;br&gt;ref_pitch.csv", "#F2F2F2", False, "document"),
        ("karaoke", 210, 350, 230, 110, "karaoke.py&lt;br&gt;reproducción · grabación", "#FFFFFF", False, "process"),
        ("compare", 520, 350, 230, 110, "comparacion.py&lt;br&gt;DTW", "#F2F2F2", False, "process"),
        ("metrics", 830, 350, 230, 110, "metricas.py&lt;br&gt;cents · umbrales", "#FFFFFF", False, "process"),
        ("view", 1140, 350, 230, 110, "visualizacion.py&lt;br&gt;nota · tiempo", "#F2F2F2", False, "process"),
        ("json", 1450, 350, 210, 110, "Resultado JSON&lt;br&gt;métricas · curvas", "#FFFFFF", False, "document"),
        ("stream", 95, 680, 255, 125, "Captura por bloques&lt;br&gt;latencia &amp;lt; 150 ms", "#FFFFFF", True, "process"),
        ("stable", 425, 680, 255, 125, "Nota estabilizada&lt;br&gt;F0 + confianza", "#FFFFFF", True, "process"),
        ("temporal", 755, 680, 255, 125, "Análisis temporal&lt;br&gt;DTW en cents · segmentos", "#FFFFFF", True, "process"),
        ("feedback", 1085, 680, 255, 125, "Retroalimentación&lt;br&gt;hallazgos · validación", "#FFFFFF", True, "process"),
        ("history", 1415, 680, 240, 125, "Historial&lt;br&gt;referencia versionada", "#FFFFFF", True, "cylinder"),
    ]
    edges = [("app", "catalog", False), ("catalog", "separation", False), ("separation", "pitch", False), ("pitch", "save", False), ("karaoke", "compare", False), ("compare", "metrics", False), ("metrics", "view", False), ("view", "json", False), ("stream", "stable", True), ("stable", "temporal", True), ("temporal", "feedback", True), ("feedback", "history", True), ("karaoke", "stream", True)]
    drawio("ilustracion_arquitectura_logica_drawio.drawio", "Arquitectura lógica", 1750, 1050, current_nodes, edges, [("current", 45, 85, 1660, 420, "Flujo implementado o parcial", False), ("future", 45, 565, 1660, 375, "Extensión requerida", True)])


if __name__ == "__main__":
    generate_physical_svg()
    generate_logical_svg()
    generate_drawio()
    print(OUT)
