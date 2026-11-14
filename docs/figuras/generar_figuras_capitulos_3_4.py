import base64
from pathlib import Path


OUT = Path(__file__).resolve().parent
RESOURCES = OUT / "recursos"
INK = "#1F2937"
MUTED = "#5B6472"
LINE = "#46515F"


def data_url(path):
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def text(x, y, value, size=18, weight="normal", color=INK, anchor="middle"):
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="Arial" font-size="{size}" font-weight="{weight}" fill="{color}">{value}</text>'


def multiline(x, y, lines, size=18, weight="normal", color=INK, gap=25):
    spans = "".join(f'<tspan x="{x}" dy="{0 if i == 0 else gap}">{line}</tspan>' for i, line in enumerate(lines))
    return f'<text x="{x}" y="{y}" text-anchor="middle" font-family="Arial" font-size="{size}" font-weight="{weight}" fill="{color}">{spans}</text>'


def card(x, y, w, h, title, details, fill, stroke, title_size=19):
    result = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="2"/>', text(x + w / 2, y + 36, title, title_size, "bold")]
    for i, detail in enumerate(details):
        result.append(text(x + w / 2, y + 70 + i * 26, detail, 16, "normal", MUTED))
    return "".join(result)


def defs():
    return f'''<defs>
<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M0 0L10 5L0 10z" fill="{LINE}"/></marker>
<clipPath id="rounded"><rect x="35" y="105" width="780" height="430" rx="12"/></clipPath>
<clipPath id="concept"><rect x="80" y="85" width="1440" height="430" rx="12"/></clipPath>
</defs>'''


def arrow(x1, y1, x2, y2, dashed=False):
    dash = ' stroke-dasharray="8 7"' if dashed else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{LINE}" stroke-width="2.5"{dash} marker-end="url(#arrow)"/>'


def generate_pxp():
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="650" viewBox="0 0 1400 650">', defs(),
        '<rect width="1400" height="650" fill="#FFFFFF"/>',
        text(700, 55, "Ciclo de trabajo PXP adaptado al proyecto", 23, "bold"),
        card(65, 235, 215, 135, "Requisitos", ["historias", "prioridades"], "#DCEAF7", "#4779A8"),
        card(345, 235, 215, 135, "Planificación", ["tareas", "estimaciones"], "#F3F4F6", "#6B7280"),
        card(625, 185, 260, 235, "Iteración", ["diseño acotado", "implementación", "pruebas", "refactorización"], "#E5F2EA", "#4D8064"),
        card(950, 235, 190, 135, "Revisión", ["resultado", "incidencias"], "#FFF3D6", "#A87822"),
        card(1205, 235, 150, 135, "Registro", ["avance", "ajustes"], "#FBE8E8", "#A84B4B", 18),
        arrow(280, 302, 345, 302), arrow(560, 302, 625, 302), arrow(885, 302, 950, 302), arrow(1140, 302, 1205, 302),
        f'<path d="M1280 370V530H452V370" fill="none" stroke="{LINE}" stroke-width="2.5" stroke-dasharray="8 7" marker-end="url(#arrow)"/>',
        text(850, 570, "Los resultados de cada iteración actualizan la planificación siguiente", 17, "normal", MUTED),
        '</svg>',
    ]
    (OUT / "figura_3_1_ciclo_pxp.svg").write_text("".join(parts), encoding="utf-8")


def generate_physical():
    image = data_url(RESOURCES / "entorno_fisico_karaoke.png")
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900" viewBox="0 0 1600 900">', defs(),
        '<rect width="1600" height="900" fill="#FFFFFF"/>',
        text(800, 55, "Arquitectura física de ejecución local", 24, "bold"),
        f'<image href="{image}" x="35" y="105" width="780" height="430" preserveAspectRatio="xMidYMid slice" clip-path="url(#rounded)"/>',
        '<rect x="35" y="105" width="780" height="430" rx="12" fill="none" stroke="#CBD5E1" stroke-width="2"/>',
        text(425, 575, "Entorno de uso: cantante, micrófono, audífonos y computador", 17, "normal", MUTED),
        card(900, 105, 630, 125, "Equipo local Windows", ["aplicación de escritorio en Python", "procesamiento sin servidor obligatorio"], "#DCEAF7", "#4779A8", 21),
        card(900, 280, 290, 135, "Recursos de análisis", ["Demucs / WORLD", "bibliotecas y modelos"], "#E5F2EA", "#4D8064"),
        card(1240, 280, 290, 135, "Persistencia local", ["canciones y audios", "CSV / JSON o SQLite"], "#FFF3D6", "#A87822"),
        card(900, 465, 290, 135, "Entrada y salida", ["micrófono", "audio y visualización"], "#F3F4F6", "#6B7280"),
        card(1240, 465, 290, 135, "Componentes opcionales", ["descarga de modelos", "servicio LLM remoto"], "#FBE8E8", "#A84B4B"),
        arrow(1215, 230, 1045, 280), arrow(1215, 230, 1385, 280), arrow(1045, 415, 1045, 465), arrow(1385, 415, 1385, 465, True),
        card(225, 700, 300, 110, "Captura", ["audio del usuario"], "#DCEAF7", "#4779A8"),
        card(650, 700, 300, 110, "Procesamiento local", ["tiempo real y posterior"], "#E5F2EA", "#4D8064"),
        card(1075, 700, 300, 110, "Resultados", ["métricas y sesiones"], "#FFF3D6", "#A87822"),
        arrow(525, 755, 650, 755), arrow(950, 755, 1075, 755),
        '</svg>',
    ]
    (OUT / "figura_4_1_arquitectura_fisica.svg").write_text("".join(parts), encoding="utf-8")


def generate_logical():
    image = data_url(RESOURCES / "flujo_conceptual_audio.png")
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1120" viewBox="0 0 1600 1120">', defs(),
        '<rect width="1600" height="1120" fill="#FFFFFF"/>',
        text(800, 50, "Arquitectura lógica del sistema", 24, "bold"),
        f'<image href="{image}" x="80" y="85" width="1440" height="430" preserveAspectRatio="xMidYMid meet" clip-path="url(#concept)"/>',
        '<rect x="80" y="85" width="1440" height="430" rx="12" fill="none" stroke="#CBD5E1" stroke-width="2"/>',
        text(800, 545, "Representación conceptual: audio, extracción, análisis, retroalimentación y evolución", 17, "normal", MUTED),
        card(80, 610, 250, 130, "Presentación", ["interfaz sustituible", "vistas y comandos"], "#FBE8E8", "#A84B4B"),
        card(390, 610, 300, 130, "Coordinación", ["catálogo", "sesión de canto"], "#FFF3D6", "#A87822"),
        card(750, 610, 350, 130, "Procesamiento de audio", ["separación y captura", "pitch y nota en tiempo real"], "#DCEAF7", "#4779A8"),
        card(1160, 610, 350, 130, "Análisis posterior", ["DTW, métricas y segmentos", "retroalimentación e historial"], "#E5F2EA", "#4D8064"),
        arrow(330, 675, 390, 675), arrow(690, 675, 750, 675), arrow(1100, 675, 1160, 675),
        card(135, 850, 300, 130, "Archivos musicales", ["original y stems", "grabaciones"], "#F3F4F6", "#6B7280"),
        card(650, 850, 300, 130, "Datos derivados", ["pitch y métricas", "segmentos"], "#F3F4F6", "#6B7280"),
        card(1165, 850, 300, 130, "Persistencia", ["archivos estructurados", "SQLite por evaluar"], "#F3F4F6", "#6B7280"),
        arrow(540, 740, 285, 850), arrow(925, 740, 800, 850), arrow(1335, 740, 1315, 850),
        text(800, 1055, "Las dependencias fluyen hacia módulos internos; la presentación no contiene lógica acústica", 17, "normal", MUTED),
        '</svg>',
    ]
    (OUT / "figura_4_2_arquitectura_logica.svg").write_text("".join(parts), encoding="utf-8")


def mx_image_style(data):
    return f"shape=image;verticalLabelPosition=bottom;verticalAlign=top;imageAspect=1;aspect=fixed;image={data};"


def drawio(name, diagram_name, width, height, image_nodes, nodes, edges):
    cells = ['<mxCell id="0"/>', '<mxCell id="1" parent="0"/>']
    for node_id, x, y, w, h, data in image_nodes:
        cells.append(f'<mxCell id="{node_id}" value="" style="{mx_image_style(data)}" vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
    for node_id, x, y, w, h, value, fill, stroke in nodes:
        cells.append(f'<mxCell id="{node_id}" value="{value}" style="rounded=1;whiteSpace=wrap;html=1;fontFamily=Arial;fontSize=17;fillColor={fill};strokeColor={stroke};strokeWidth=2;" vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
    for index, (source, target, dashed) in enumerate(edges, 1):
        cells.append(f'<mxCell id="e{index}" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;endFill=1;strokeWidth=2;strokeColor=#46515F;dashed={1 if dashed else 0};" edge="1" parent="1" source="{source}" target="{target}"><mxGeometry relative="1" as="geometry"/></mxCell>')
    xml = f'<mxfile host="app.diagrams.net" agent="Codex"><diagram name="{diagram_name}"><mxGraphModel pageWidth="{width}" pageHeight="{height}"><root>{"".join(cells)}</root></mxGraphModel></diagram></mxfile>'
    (OUT / name).write_text(xml, encoding="utf-8")


def generate_drawio():
    drawio("figura_3_1_ciclo_pxp.drawio", "Figura 3.1", 1400, 650, [], [
        ("req", 65, 235, 215, 135, "Requisitos&lt;br&gt;historias y prioridades", "#DCEAF7", "#4779A8"),
        ("plan", 345, 235, 215, 135, "Planificación&lt;br&gt;tareas y estimaciones", "#F3F4F6", "#6B7280"),
        ("iteration", 625, 185, 260, 235, "Iteración&lt;br&gt;diseño, implementación,&lt;br&gt;pruebas y refactorización", "#E5F2EA", "#4D8064"),
        ("review", 950, 235, 190, 135, "Revisión&lt;br&gt;resultados e incidencias", "#FFF3D6", "#A87822"),
        ("log", 1205, 235, 150, 135, "Registro&lt;br&gt;avance y ajustes", "#FBE8E8", "#A84B4B"),
    ], [("req", "plan", False), ("plan", "iteration", False), ("iteration", "review", False), ("review", "log", False), ("log", "plan", True)])

    physical_img = data_url(RESOURCES / "entorno_fisico_karaoke.png")
    drawio("figura_4_1_arquitectura_fisica.drawio", "Figura 4.1", 1600, 900, [("photo", 35, 105, 780, 430, physical_img)], [
        ("pc", 900, 105, 630, 125, "Equipo local Windows&lt;br&gt;aplicación de escritorio en Python", "#DCEAF7", "#4779A8"),
        ("models", 900, 280, 290, 135, "Recursos de análisis&lt;br&gt;Demucs / WORLD", "#E5F2EA", "#4D8064"),
        ("storage", 1240, 280, 290, 135, "Persistencia local&lt;br&gt;archivos o SQLite", "#FFF3D6", "#A87822"),
        ("io", 900, 465, 290, 135, "Entrada y salida&lt;br&gt;micrófono, audio y visualización", "#F3F4F6", "#6B7280"),
        ("optional", 1240, 465, 290, 135, "Componentes opcionales&lt;br&gt;descargas o LLM remoto", "#FBE8E8", "#A84B4B"),
    ], [("pc", "models", False), ("pc", "storage", False), ("models", "io", False), ("storage", "optional", True)])

    logical_img = data_url(RESOURCES / "flujo_conceptual_audio.png")
    drawio("figura_4_2_arquitectura_logica.drawio", "Figura 4.2", 1600, 1120, [("concept", 80, 85, 1440, 430, logical_img)], [
        ("ui", 80, 610, 250, 130, "Presentación&lt;br&gt;interfaz sustituible", "#FBE8E8", "#A84B4B"),
        ("coord", 390, 610, 300, 130, "Coordinación&lt;br&gt;catálogo y sesión", "#FFF3D6", "#A87822"),
        ("audio", 750, 610, 350, 130, "Procesamiento de audio&lt;br&gt;separación, captura y pitch", "#DCEAF7", "#4779A8"),
        ("analysis", 1160, 610, 350, 130, "Análisis posterior&lt;br&gt;DTW, segmentos y evolución", "#E5F2EA", "#4D8064"),
        ("files", 135, 850, 300, 130, "Archivos musicales&lt;br&gt;original, stems y grabaciones", "#F3F4F6", "#6B7280"),
        ("derived", 650, 850, 300, 130, "Datos derivados&lt;br&gt;pitch, métricas y segmentos", "#F3F4F6", "#6B7280"),
        ("persist", 1165, 850, 300, 130, "Persistencia&lt;br&gt;archivos o SQLite", "#F3F4F6", "#6B7280"),
    ], [("ui", "coord", False), ("coord", "audio", False), ("audio", "analysis", False), ("coord", "files", False), ("audio", "derived", False), ("analysis", "persist", False)])


if __name__ == "__main__":
    generate_pxp()
    generate_physical()
    generate_logical()
    generate_drawio()
    print(OUT)
