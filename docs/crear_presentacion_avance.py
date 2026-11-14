from __future__ import annotations

from pathlib import Path

import win32com.client


ROOT_13 = Path(r"C:\Users\Diego Tapia\Desktop\Pene\U\13avo semestre")
FORMULACION = next(ROOT_13.glob("Formulaci*"))
BASE_DIR = FORMULACION / "Informe final"
SOURCE = next(BASE_DIR.glob("*Presentaci*n*Avance*.pptx"))
OUTPUT = BASE_DIR / "Tapia_Diego_Presentación Avance_Estructura.pptx"


MsoTextOrientationHorizontal = 1
ppLayoutBlank = 12
msoShapeRoundedRectangle = 5
msoShapeRectangle = 1
msoConnectorStraight = 1
msoArrowheadTriangle = 2


def rgb(r: int, g: int, b: int) -> int:
    return r + (g << 8) + (b << 16)


NAVY = rgb(22, 45, 75)
BLUE = rgb(43, 102, 148)
TEAL = rgb(25, 135, 140)
GREEN = rgb(69, 145, 96)
AMBER = rgb(199, 138, 38)
RED = rgb(178, 76, 70)
LIGHT = rgb(242, 246, 249)
MID = rgb(225, 232, 238)
DARK = rgb(38, 38, 38)
WHITE = rgb(255, 255, 255)


def add_textbox(slide, text, left, top, width, height, size=18, bold=False, color=DARK):
    shape = slide.Shapes.AddTextbox(MsoTextOrientationHorizontal, left, top, width, height)
    shape.TextFrame.TextRange.Text = text
    shape.TextFrame.TextRange.Font.Name = "Aptos"
    shape.TextFrame.TextRange.Font.Size = size
    shape.TextFrame.TextRange.Font.Bold = -1 if bold else 0
    shape.TextFrame.TextRange.Font.Color.RGB = color
    shape.TextFrame.MarginLeft = 8
    shape.TextFrame.MarginRight = 8
    shape.TextFrame.MarginTop = 4
    shape.TextFrame.MarginBottom = 4
    return shape


def add_title(slide, title, subtitle=None):
    add_textbox(slide, title, 38, 26, 620, 42, size=30, bold=True, color=NAVY)
    bar = slide.Shapes.AddShape(msoShapeRectangle, 38, 73, 120, 4)
    bar.Fill.ForeColor.RGB = TEAL
    bar.Line.Visible = 0
    if subtitle:
        add_textbox(slide, subtitle, 38, 83, 630, 28, size=13, color=BLUE)


def add_footer(slide, index):
    add_textbox(slide, "Diego Tapia | Avance de Proyecto de Titulación", 38, 512, 520, 20, size=9, color=rgb(110, 110, 110))
    add_textbox(slide, str(index), 665, 512, 32, 20, size=9, color=rgb(110, 110, 110))


def add_bullets(slide, bullets, left, top, width, height, size=18):
    text = "\n".join(f"• {bullet}" for bullet in bullets)
    shape = add_textbox(slide, text, left, top, width, height, size=size, color=DARK)
    shape.TextFrame.TextRange.ParagraphFormat.SpaceAfter = 6
    return shape


def add_box(slide, text, left, top, width, height, fill=LIGHT, line=BLUE, size=15, bold=False):
    shape = slide.Shapes.AddShape(msoShapeRoundedRectangle, left, top, width, height)
    shape.Fill.ForeColor.RGB = fill
    shape.Line.ForeColor.RGB = line
    shape.Line.Weight = 1.2
    shape.TextFrame.TextRange.Text = text
    shape.TextFrame.TextRange.Font.Name = "Aptos"
    shape.TextFrame.TextRange.Font.Size = size
    shape.TextFrame.TextRange.Font.Bold = -1 if bold else 0
    shape.TextFrame.TextRange.Font.Color.RGB = DARK
    shape.TextFrame.TextRange.ParagraphFormat.Alignment = 2
    shape.TextFrame.VerticalAnchor = 3
    shape.TextFrame.MarginLeft = 8
    shape.TextFrame.MarginRight = 8
    return shape


def add_arrow(slide, x1, y1, x2, y2, color=BLUE):
    arrow = slide.Shapes.AddConnector(msoConnectorStraight, x1, y1, x2, y2)
    arrow.Line.ForeColor.RGB = color
    arrow.Line.Weight = 1.6
    arrow.Line.EndArrowheadStyle = msoArrowheadTriangle
    return arrow


def add_panel(slide, title, bullets, left, top, width, height, accent=BLUE):
    panel = slide.Shapes.AddShape(msoShapeRoundedRectangle, left, top, width, height)
    panel.Fill.ForeColor.RGB = LIGHT
    panel.Line.ForeColor.RGB = MID
    panel.Line.Weight = 1
    add_textbox(slide, title, left + 12, top + 10, width - 24, 24, size=16, bold=True, color=accent)
    add_bullets(slide, bullets, left + 12, top + 40, width - 24, height - 50, size=14)
    return panel


def slide_context(slide):
    add_title(slide, "Contexto y motivación")
    add_bullets(
        slide,
        [
            "La práctica vocal autónoma requiere reconocer cómo se comporta la voz durante una interpretación.",
            "Las herramientas digitales pueden mostrar pitch, notas o puntajes, pero no siempre orientan la práctica.",
            "Existe una oportunidad para transformar mediciones acústicas en retroalimentación clara y accionable.",
        ],
        48,
        120,
        385,
        230,
        size=18,
    )
    add_box(slide, "Voz del usuario", 460, 130, 165, 62, fill=WHITE, line=TEAL, bold=True)
    add_arrow(slide, 545, 192, 545, 225, TEAL)
    add_box(slide, "Análisis acústico", 460, 225, 165, 62, fill=WHITE, line=BLUE, bold=True)
    add_arrow(slide, 545, 287, 545, 320, BLUE)
    add_box(slide, "Orientación para practicar", 445, 320, 195, 70, fill=WHITE, line=GREEN, bold=True)
    add_footer(slide, 2)


def slide_problem(slide):
    add_title(slide, "Problema", "Brecha entre datos acústicos y retroalimentación comprensible")
    add_panel(
        slide,
        "Lo que entregan muchas herramientas",
        ["Frecuencia o nota detectada", "Curvas temporales de pitch", "Puntajes globales"],
        45,
        130,
        240,
        210,
        BLUE,
    )
    add_box(slide, "Brecha de interpretación", 315, 188, 150, 90, fill=rgb(255, 248, 232), line=AMBER, bold=True)
    add_arrow(slide, 285, 235, 315, 235, AMBER)
    add_arrow(slide, 465, 235, 495, 235, AMBER)
    add_panel(
        slide,
        "Lo que necesita el usuario",
        ["Dónde ocurrió el problema", "Qué patrón se observa", "Cómo cambia entre sesiones"],
        495,
        130,
        240,
        210,
        TEAL,
    )
    add_textbox(
        slide,
        "El desafío no es solo medir afinación, sino convertir evidencia temporal en información útil para la práctica.",
        70,
        380,
        610,
        55,
        size=19,
        bold=True,
        color=NAVY,
    )
    add_footer(slide, 3)


def slide_proposal(slide):
    add_title(slide, "Propuesta", "Sistema de análisis vocal con detección de segmentos y retroalimentación")
    steps = [
        ("Canción\nde referencia", TEAL),
        ("Captura de\ninterpretación", BLUE),
        ("Pitch y\nalineación", TEAL),
        ("Segmentos\nproblemáticos", AMBER),
        ("Feedback en\nlenguaje natural", GREEN),
    ]
    x = 42
    for idx, (label, color) in enumerate(steps):
        add_box(slide, label, x, 170, 118, 76, fill=WHITE, line=color, size=14, bold=True)
        if idx < len(steps) - 1:
            add_arrow(slide, x + 118, 208, x + 147, 208, color)
        x += 147
    add_bullets(
        slide,
        [
            "Se compara la interpretación del usuario con una referencia preparada.",
            "El análisis se organiza por segmentos, no solo por un puntaje global.",
            "La retroalimentación se genera desde evidencia estructurada para evitar afirmaciones no justificadas.",
        ],
        75,
        315,
        590,
        130,
        size=17,
    )
    add_footer(slide, 4)


def slide_objectives(slide):
    add_title(slide, "Objetivos y alcance")
    add_panel(
        slide,
        "Objetivo general",
        ["Desarrollar un sistema que apoye la práctica vocal mediante análisis de pitch, comparación con referencia y retroalimentación comprensible."],
        45,
        115,
        635,
        96,
        NAVY,
    )
    add_panel(
        slide,
        "Incluye",
        ["Preparación de canciones", "Captura de interpretaciones", "Comparación mediante pitch", "Persistencia de sesiones y resultados"],
        45,
        245,
        285,
        190,
        GREEN,
    )
    add_panel(
        slide,
        "Pendiente / por validar",
        ["Detección en tiempo real", "Segmentación dinámica", "Retroalimentación natural", "Interfaz final, LLM y distribución"],
        395,
        245,
        285,
        190,
        AMBER,
    )
    add_footer(slide, 5)


def slide_foundations(slide):
    add_title(slide, "Fundamentos técnicos")
    items = [
        ("Pitch / F0", "Representa la altura tonal de la voz en el tiempo.", TEAL),
        ("Separación de fuentes", "Permite obtener voz de referencia e instrumental.", BLUE),
        ("DTW", "Alinea temporalmente dos curvas de pitch comparables.", GREEN),
        ("Segmentación", "Agrupa evidencias locales en intervalos relevantes.", AMBER),
    ]
    positions = [(50, 130), (390, 130), (50, 315), (390, 315)]
    for (title, body, color), (x, y) in zip(items, positions):
        add_box(slide, title, x, y, 260, 52, fill=WHITE, line=color, size=18, bold=True)
        add_textbox(slide, body, x + 10, y + 65, 240, 70, size=15, color=DARK)
    add_footer(slide, 6)


def slide_architecture(slide):
    add_title(slide, "Arquitectura lógica")
    layers = [
        ("Interfaz de usuario", "canciones, reproducción, visualización", BLUE),
        ("Servicios de aplicación", "flujos de preparación, sesión y consulta", TEAL),
        ("Procesamiento de audio", "Demucs, pitch, captura y filtrado", BLUE),
        ("Análisis", "alineación, métricas, segmentos y comparación", AMBER),
        ("Persistencia", "canciones, referencias, sesiones y resultados", GREEN),
    ]
    y = 108
    for idx, (title, body, color) in enumerate(layers):
        add_box(slide, f"{title}\n{body}", 105, y, 510, 58, fill=WHITE, line=color, size=14, bold=True)
        if idx < len(layers) - 1:
            add_arrow(slide, 360, y + 58, 360, y + 74, color)
        y += 74
    add_footer(slide, 7)


def slide_data_model(slide):
    add_title(slide, "Modelo de datos")
    boxes = [
        ("Canción", 65, 130, TEAL),
        ("Referencia", 245, 130, BLUE),
        ("Sesión", 425, 130, GREEN),
        ("Análisis", 245, 260, AMBER),
        ("Segmento", 65, 390, RED),
        ("Retroalimentación", 245, 390, TEAL),
        ("Comparación", 425, 390, BLUE),
    ]
    for label, x, y, color in boxes:
        add_box(slide, label, x, y, 140, 56, fill=WHITE, line=color, size=15, bold=True)
    add_arrow(slide, 205, 158, 245, 158, TEAL)
    add_arrow(slide, 385, 158, 425, 158, BLUE)
    add_arrow(slide, 495, 186, 315, 260, GREEN)
    add_arrow(slide, 315, 316, 135, 390, AMBER)
    add_arrow(slide, 315, 316, 315, 390, AMBER)
    add_arrow(slide, 315, 316, 495, 390, AMBER)
    add_textbox(
        slide,
        "Propósito: mantener trazabilidad entre canciones, sesiones, análisis, segmentos detectados y evolución histórica.",
        70,
        90,
        600,
        30,
        size=16,
        color=NAVY,
    )
    add_footer(slide, 8)


def slide_status(slide):
    add_title(slide, "Estado actual del prototipo")
    add_panel(
        slide,
        "Implementado",
        ["Catálogo de canciones", "Separación y referencia", "Captura de sesión", "Pitch, DTW y métricas", "Persistencia y visualización"],
        40,
        125,
        210,
        270,
        GREEN,
    )
    add_panel(
        slide,
        "Parcial",
        ["Validación de métricas", "Refinamiento de alineación", "Manejo de errores", "Pruebas sistemáticas"],
        265,
        125,
        210,
        270,
        AMBER,
    )
    add_panel(
        slide,
        "Pendiente",
        ["Nota en tiempo real", "Segmentos dinámicos", "Retroalimentación natural", "Comparación histórica", "Interfaz final"],
        490,
        125,
        210,
        270,
        RED,
    )
    add_textbox(slide, "Avance documentado: mayor o igual al 30% del proyecto.", 95, 425, 540, 36, size=20, bold=True, color=NAVY)
    add_footer(slide, 9)


def slide_plan(slide):
    add_title(slide, "Plan de trabajo restante")
    steps = [
        ("1", "Validar pitch y métricas"),
        ("2", "Incorporar detección en tiempo real"),
        ("3", "Detectar y priorizar segmentos"),
        ("4", "Generar retroalimentación"),
        ("5", "Comparar evolución histórica"),
        ("6", "Cerrar interfaz, pruebas y memoria"),
    ]
    x = 55
    y = 145
    for idx, (num, label) in enumerate(steps):
        add_box(slide, num, x, y, 44, 44, fill=NAVY, line=NAVY, size=18, bold=True)
        slide.Shapes(slide.Shapes.Count).TextFrame.TextRange.Font.Color.RGB = WHITE
        add_textbox(slide, label, x + 52, y + 4, 155, 48, size=14, color=DARK)
        if idx in (0, 2, 4):
            x += 220
        else:
            x = 55
            y += 105
    add_panel(
        slide,
        "Riesgos a controlar",
        ["Latencia y calidad del pitch en tiempo real", "Dependencias externas y distribución", "Decisión final sobre LLM e interfaz"],
        475,
        292,
        230,
        160,
        AMBER,
    )
    add_footer(slide, 10)


SLIDE_BUILDERS = [
    slide_context,
    slide_problem,
    slide_proposal,
    slide_objectives,
    slide_foundations,
    slide_architecture,
    slide_data_model,
    slide_status,
    slide_plan,
]


def normalize_cover(presentation) -> None:
    cover = presentation.Slides(1)
    for shape in cover.Shapes:
        try:
            if shape.HasTextFrame and shape.TextFrame.HasText:
                text = shape.TextFrame.TextRange.Text
                if "Propuesta" in text:
                    shape.TextFrame.TextRange.Text = text.replace("Propuesta", "Avance")
        except Exception:
            continue


def main() -> None:
    if OUTPUT.exists():
        OUTPUT.unlink()

    app = win32com.client.Dispatch("PowerPoint.Application")
    presentation = None
    try:
        presentation = app.Presentations.Open(str(SOURCE), False, False, False)
        normalize_cover(presentation)

        for idx in range(presentation.Slides.Count, 1, -1):
            presentation.Slides(idx).Delete()

        # Mantiene la portada del archivo base y reemplaza todo el contenido posterior.
        for builder in SLIDE_BUILDERS:
            slide = presentation.Slides.Add(presentation.Slides.Count + 1, ppLayoutBlank)
            builder(slide)

        presentation.SaveAs(str(OUTPUT))
    finally:
        if presentation is not None:
            presentation.Close()
        app.Quit()

    print(f"Base: {SOURCE}")
    print(f"Salida: {OUTPUT}")


if __name__ == "__main__":
    main()
