from pathlib import Path


OUT = Path(__file__).resolve().parent
INK = "#1F2937"
LINE = "#46515F"


def text(x, y, value, size=18, weight="normal", color=INK):
    return f'<text x="{x}" y="{y}" text-anchor="middle" font-family="Arial" font-size="{size}" font-weight="{weight}" fill="{color}">{value}</text>'


def card(x, y, w, h, title, details, fill, stroke):
    result = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="2"/>', text(x + w / 2, y + 38, title, 19, "bold")]
    for index, detail in enumerate(details):
        result.append(text(x + w / 2, y + 72 + 27 * index, detail, 16, "normal", "#5B6472"))
    return "".join(result)


def arrow(x1, y1, x2, y2):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{LINE}" stroke-width="2.5" marker-end="url(#arrow)"/>'


def svg_shell(height, body):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="{height}" viewBox="0 0 1500 {height}">
<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M0 0L10 5L0 10z" fill="{LINE}"/></marker></defs>
<rect width="1500" height="{height}" fill="#FFFFFF"/>{body}</svg>'''


def write_feedback_svg():
    body = [
        text(750, 52, "Generación controlada de retroalimentación", 23, "bold"),
        card(45, 160, 260, 155, "Hallazgos estructurados", ["segmento y tiempo", "tipo y severidad", "evidencia numérica"], "#DCEAF7", "#4779A8"),
        card(390, 90, 275, 135, "Plantillas", ["reglas deterministas", "mensajes previsibles"], "#E5F2EA", "#4D8064"),
        card(390, 285, 275, 135, "Modelo de lenguaje", ["redacción contextual", "alternativa en evaluación"], "#FFF3D6", "#A87822"),
        card(760, 160, 275, 155, "Validación", ["coherencia con datos", "formato y límites", "sin causas inventadas"], "#F3F4F6", "#6B7280"),
        card(1130, 160, 320, 155, "Retroalimentación final", ["qué ocurrió", "dónde ocurrió", "orientación de práctica"], "#FBE8E8", "#A84B4B"),
        arrow(305, 237, 390, 158), arrow(305, 237, 390, 352),
        arrow(665, 158, 760, 220), arrow(665, 352, 760, 255), arrow(1035, 237, 1130, 237),
        text(750, 475, "El generador redacta los hallazgos; no determina los problemas acústicos", 17, "normal", "#5B6472"),
    ]
    (OUT / "figura_2_7_retroalimentacion.svg").write_text(svg_shell(520, "".join(body)), encoding="utf-8")


def write_history_svg():
    body = [text(750, 52, "Comparación de sesiones sobre una misma canción", 23, "bold")]
    sessions = [
        (90, "Sesión 1", "12-06-2026", "62 % dentro de ±50 cents", "inestabilidad recurrente", "#FBE8E8", "#A84B4B"),
        (510, "Sesión 2", "19-06-2026", "70 % dentro de ±50 cents", "inestabilidad reducida", "#FFF3D6", "#A87822"),
        (930, "Sesión 3", "26-06-2026", "78 % dentro de ±50 cents", "mejora sostenida", "#E5F2EA", "#4D8064"),
    ]
    for x, title, date, metric, issue, fill, stroke in sessions:
        body.append(card(x, 135, 330, 175, title, [date, metric, issue], fill, stroke))
    body.extend([arrow(420, 222, 510, 222), arrow(840, 222, 930, 222)])
    body.extend([
        '<line x1="135" y1="405" x2="1365" y2="405" stroke="#CBD5E1" stroke-width="8" stroke-linecap="round"/>',
        '<polyline points="180,420 610,370 1030,335 1320,300" fill="none" stroke="#4779A8" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>',
        '<circle cx="180" cy="420" r="9" fill="#4779A8"/><circle cx="610" cy="370" r="9" fill="#4779A8"/><circle cx="1030" cy="335" r="9" fill="#4779A8"/><circle cx="1320" cy="300" r="9" fill="#4779A8"/>',
        text(750, 485, "Evolución de una métrica comparable", 17, "normal", "#5B6472"),
    ])
    (OUT / "figura_2_8_evolucion_sesiones.svg").write_text(svg_shell(520, "".join(body)), encoding="utf-8")


def drawio_file(name, diagram_name, nodes, edges):
    cells = ['<mxCell id="0"/>', '<mxCell id="1" parent="0"/>']
    for node_id, x, y, w, h, value, fill, stroke in nodes:
        cells.append(f'<mxCell id="{node_id}" value="{value}" style="rounded=1;whiteSpace=wrap;html=1;fontFamily=Arial;fontSize=17;fillColor={fill};strokeColor={stroke};strokeWidth=2;" vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
    for index, (source, target) in enumerate(edges, 1):
        cells.append(f'<mxCell id="e{index}" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;endFill=1;strokeWidth=2;strokeColor=#46515F;" edge="1" parent="1" source="{source}" target="{target}"><mxGeometry relative="1" as="geometry"/></mxCell>')
    xml = f'<mxfile host="app.diagrams.net" agent="Codex"><diagram name="{diagram_name}"><mxGraphModel pageWidth="1500" pageHeight="520"><root>{"".join(cells)}</root></mxGraphModel></diagram></mxfile>'
    (OUT / name).write_text(xml, encoding="utf-8")


def write_drawio():
    drawio_file("figura_2_7_retroalimentacion.drawio", "Figura 2.7", [
        ("findings", 45, 180, 260, 145, "Hallazgos estructurados&lt;br&gt;tiempo, tipo, severidad y evidencia", "#DCEAF7", "#4779A8"),
        ("templates", 390, 95, 275, 125, "Plantillas&lt;br&gt;reglas deterministas", "#E5F2EA", "#4D8064"),
        ("llm", 390, 295, 275, 125, "Modelo de lenguaje&lt;br&gt;alternativa en evaluación", "#FFF3D6", "#A87822"),
        ("validation", 760, 180, 275, 145, "Validación&lt;br&gt;coherencia, formato y límites", "#F3F4F6", "#6B7280"),
        ("feedback", 1130, 180, 320, 145, "Retroalimentación final&lt;br&gt;qué, dónde y orientación", "#FBE8E8", "#A84B4B"),
    ], [("findings", "templates"), ("findings", "llm"), ("templates", "validation"), ("llm", "validation"), ("validation", "feedback")])
    drawio_file("figura_2_8_evolucion_sesiones.drawio", "Figura 2.8", [
        ("s1", 90, 170, 330, 160, "Sesión 1&lt;br&gt;métricas y segmentos", "#FBE8E8", "#A84B4B"),
        ("s2", 585, 170, 330, 160, "Sesión 2&lt;br&gt;cambios respecto de sesión 1", "#FFF3D6", "#A87822"),
        ("s3", 1080, 170, 330, 160, "Sesión 3&lt;br&gt;evolución consolidada", "#E5F2EA", "#4D8064"),
    ], [("s1", "s2"), ("s2", "s3")])


if __name__ == "__main__":
    write_feedback_svg()
    write_history_svg()
    write_drawio()
    print(OUT)
