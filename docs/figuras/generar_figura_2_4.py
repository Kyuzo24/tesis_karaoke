from pathlib import Path


OUT = Path(__file__).resolve().parent
INK = "#1F2937"
LINE = "#46515F"


def text(x, y, value, size=20, weight="normal", color=INK):
    return (
        f'<text x="{x}" y="{y}" text-anchor="middle" font-family="Arial, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{color}">{value}</text>'
    )


def card(x, y, w, h, first, second, fill, stroke):
    return "\n".join(
        [
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="2"/>',
            text(x + w / 2, y + h / 2 - 5, first, 20, "bold"),
            text(x + w / 2, y + h / 2 + 27, second, 17, "normal", "#5B6472"),
        ]
    )


def write_svg():
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="560" viewBox="0 0 1500 560">',
        '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto">',
        f'<path d="M0 0L10 5L0 10z" fill="{LINE}"/></marker></defs>',
        '<rect width="1500" height="560" fill="#FFFFFF"/>',
        card(55, 205, 260, 135, "Canción original", "mezcla musical", "#DCEAF7", "#4779A8"),
        card(410, 205, 260, 135, "Modelo preentrenado", "Demucs / HT Demucs", "#F3F4F6", "#6B7280"),
        card(785, 55, 230, 105, "Voz", "vocals", "#E5F2EA", "#4D8064"),
        card(785, 180, 230, 105, "Batería", "drums", "#FFF3D6", "#A87822"),
        card(785, 305, 230, 105, "Bajo", "bass", "#DCEAF7", "#4779A8"),
        card(785, 430, 230, 105, "Otros", "other", "#FBE8E8", "#A84B4B"),
        card(1165, 130, 280, 120, "Referencia vocal", "extracción de pitch", "#E5F2EA", "#4D8064"),
        card(1165, 330, 280, 120, "Acompañamiento", "batería + bajo + otros", "#FFF3D6", "#A87822"),
        f'<line x1="315" y1="272" x2="410" y2="272" stroke="{LINE}" stroke-width="2.5" marker-end="url(#arrow)"/>',
    ]
    for y in (107, 232, 357, 482):
        parts.append(f'<path d="M670 272H725V{y}H785" fill="none" stroke="{LINE}" stroke-width="2" marker-end="url(#arrow)"/>')
    parts.append(f'<path d="M1015 107H1090V190H1165" fill="none" stroke="{LINE}" stroke-width="2" marker-end="url(#arrow)"/>')
    for y in (232, 357, 482):
        parts.append(f'<path d="M1015 {y}H1090V390H1165" fill="none" stroke="{LINE}" stroke-width="2"/>')
    parts.append(f'<path d="M1090 390H1165" fill="none" stroke="{LINE}" stroke-width="2" marker-end="url(#arrow)"/>')
    parts.append('</svg>')
    (OUT / "figura_2_4_separacion_fuentes.svg").write_text("\n".join(parts), encoding="utf-8")


def write_drawio():
    cells = ['<mxCell id="0"/>', '<mxCell id="1" parent="0"/>']
    nodes = [
        ("song",55,205,260,135,"Canción original&lt;br&gt;mezcla musical","#DCEAF7","#4779A8"),
        ("model",410,205,260,135,"Modelo preentrenado&lt;br&gt;Demucs / HT Demucs","#F3F4F6","#6B7280"),
        ("vocals",785,55,230,105,"Voz&lt;br&gt;vocals","#E5F2EA","#4D8064"),
        ("drums",785,180,230,105,"Batería&lt;br&gt;drums","#FFF3D6","#A87822"),
        ("bass",785,305,230,105,"Bajo&lt;br&gt;bass","#DCEAF7","#4779A8"),
        ("other",785,430,230,105,"Otros&lt;br&gt;other","#FBE8E8","#A84B4B"),
        ("reference",1165,130,280,120,"Referencia vocal&lt;br&gt;extracción de pitch","#E5F2EA","#4D8064"),
        ("instrumental",1165,330,280,120,"Acompañamiento&lt;br&gt;batería + bajo + otros","#FFF3D6","#A87822"),
    ]
    for node_id,x,y,w,h,value,fill,stroke in nodes:
        cells.append(
            f'<mxCell id="{node_id}" value="{value}" style="rounded=1;whiteSpace=wrap;html=1;fontFamily=Arial;'
            f'fontSize=18;fillColor={fill};strokeColor={stroke};strokeWidth=2;" vertex="1" parent="1">'
            f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>'
        )
    edges = [('song','model'),('model','vocals'),('model','drums'),('model','bass'),('model','other'),('vocals','reference'),('drums','instrumental'),('bass','instrumental'),('other','instrumental')]
    for index,(source,target) in enumerate(edges,1):
        cells.append(
            f'<mxCell id="e{index}" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;endFill=1;'
            f'strokeWidth=2;strokeColor={LINE};" edge="1" parent="1" source="{source}" target="{target}">'
            '<mxGeometry relative="1" as="geometry"/></mxCell>'
        )
    xml = (
        '<mxfile host="app.diagrams.net" modified="2026-06-22T00:00:00.000Z" agent="Codex" version="24.7.17">'
        '<diagram id="figura-2-4" name="Figura 2.4"><mxGraphModel dx="1200" dy="700" grid="1" gridSize="10" '
        'guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1500" '
        'pageHeight="560" math="0" shadow="0"><root>' + "".join(cells) + '</root></mxGraphModel></diagram></mxfile>'
    )
    (OUT / "figura_2_4_separacion_fuentes.drawio").write_text(xml, encoding="utf-8")


if __name__ == "__main__":
    write_svg()
    write_drawio()
    print(OUT)
