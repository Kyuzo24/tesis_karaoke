from pathlib import Path


OUT = Path(__file__).resolve().parent
INK = "#1F2937"
MUTED = "#5B6472"
GRID = "#CBD5E1"


def write_svg():
    cells = []
    for row in range(7):
        for col in range(9):
            x = 925 + col * 45
            y = 115 + row * 45
            fill = "#F8FAFC"
            if (col, row) in {(0, 0), (1, 0), (2, 1), (3, 2), (4, 2), (5, 3), (6, 4), (7, 5), (8, 6)}:
                fill = "#DCEAF7"
            cells.append(f'<rect x="{x}" y="{y}" width="45" height="45" fill="{fill}" stroke="{GRID}"/>')

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="560" viewBox="0 0 1500 560">
<rect width="1500" height="560" fill="#FFFFFF"/>
<text x="345" y="55" text-anchor="middle" font-family="Arial" font-size="22" font-weight="bold" fill="{INK}">Curvas de pitch con distinta duración</text>
<text x="1125" y="55" text-anchor="middle" font-family="Arial" font-size="22" font-weight="bold" fill="{INK}">Matriz de costos y trayectoria DTW</text>
<line x1="90" y1="445" x2="745" y2="445" stroke="{INK}" stroke-width="2"/>
<line x1="90" y1="105" x2="90" y2="445" stroke="{INK}" stroke-width="2"/>
<text x="420" y="490" text-anchor="middle" font-family="Arial" font-size="17" fill="{MUTED}">Tiempo</text>
<text x="35" y="280" text-anchor="middle" transform="rotate(-90 35 280)" font-family="Arial" font-size="17" fill="{MUTED}">Altura tonal</text>
<polyline points="110,380 180,380 230,295 315,295 365,205 455,205 510,285 590,285 640,170 720,170" fill="none" stroke="#4779A8" stroke-width="7" stroke-linejoin="round"/>
<polyline points="110,405 155,405 205,325 280,325 330,235 405,235 455,315 535,315 585,195 720,195" fill="none" stroke="#C16B32" stroke-width="7" stroke-linejoin="round"/>
<line x1="120" y1="80" x2="165" y2="80" stroke="#4779A8" stroke-width="6"/><text x="180" y="87" font-family="Arial" font-size="17" fill="{INK}">Referencia</text>
<line x1="315" y1="80" x2="360" y2="80" stroke="#C16B32" stroke-width="6"/><text x="375" y="87" font-family="Arial" font-size="17" fill="{INK}">Interpretación</text>
{''.join(cells)}
<polyline points="947,137 992,137 1037,182 1082,227 1127,227 1172,272 1217,317 1262,362 1307,407" fill="none" stroke="#4779A8" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>
<text x="1125" y="472" text-anchor="middle" font-family="Arial" font-size="17" fill="{MUTED}">Tiempo de la interpretación</text>
<text x="865" y="272" text-anchor="middle" transform="rotate(-90 865 272)" font-family="Arial" font-size="17" fill="{MUTED}">Tiempo de la referencia</text>
<text x="1125" y="520" text-anchor="middle" font-family="Arial" font-size="17" fill="{INK}">La trayectoria vincula instantes equivalentes</text>
</svg>'''
    (OUT / "figura_2_5_alineacion_dtw.svg").write_text(svg, encoding="utf-8")


def write_drawio():
    style = "rounded=1;whiteSpace=wrap;html=1;fontFamily=Arial;fontSize=18;strokeWidth=2;"
    cells = [
        '<mxCell id="0"/>', '<mxCell id="1" parent="0"/>',
        f'<mxCell id="a" value="Curva de pitch de referencia" style="{style}fillColor=#DCEAF7;strokeColor=#4779A8;" vertex="1" parent="1"><mxGeometry x="80" y="150" width="310" height="100" as="geometry"/></mxCell>',
        f'<mxCell id="b" value="Curva de pitch interpretada" style="{style}fillColor=#FCE8DA;strokeColor=#C16B32;" vertex="1" parent="1"><mxGeometry x="80" y="315" width="310" height="100" as="geometry"/></mxCell>',
        f'<mxCell id="c" value="Matriz de costos&lt;br&gt;distancia entre instantes" style="{style}fillColor=#F3F4F6;strokeColor=#6B7280;" vertex="1" parent="1"><mxGeometry x="560" y="230" width="320" height="115" as="geometry"/></mxCell>',
        f'<mxCell id="d" value="Trayectoria de alineación DTW&lt;br&gt;correspondencias temporales" style="{style}fillColor=#E5F2EA;strokeColor=#4D8064;" vertex="1" parent="1"><mxGeometry x="1060" y="230" width="350" height="115" as="geometry"/></mxCell>',
    ]
    for i, (source, target) in enumerate((("a", "c"), ("b", "c"), ("c", "d")), 1):
        cells.append(f'<mxCell id="e{i}" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;endFill=1;strokeWidth=2;strokeColor=#46515F;" edge="1" parent="1" source="{source}" target="{target}"><mxGeometry relative="1" as="geometry"/></mxCell>')
    xml = '<mxfile host="app.diagrams.net" agent="Codex"><diagram name="Figura 2.5"><mxGraphModel pageWidth="1500" pageHeight="560"><root>' + ''.join(cells) + '</root></mxGraphModel></diagram></mxfile>'
    (OUT / "figura_2_5_alineacion_dtw.drawio").write_text(xml, encoding="utf-8")


if __name__ == "__main__":
    write_svg()
    write_drawio()
    print(OUT)
