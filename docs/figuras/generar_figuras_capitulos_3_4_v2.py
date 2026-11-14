from pathlib import Path

from generar_figuras_capitulos_3_4 import (
    INK,
    LINE,
    MUTED,
    OUT,
    RESOURCES,
    arrow,
    card,
    data_url,
    defs,
    drawio,
    text,
)


def generate_iteration_evidence():
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="760" viewBox="0 0 1500 760">', defs(),
        '<rect width="1500" height="760" fill="#FFFFFF"/>',
        text(750, 52, "Iteración orientada por evidencia técnica", 24, "bold"),
        card(45, 170, 240, 145, "Entrada", ["requisito + HU", "riesgo técnico"], "#DCEAF7", "#4779A8"),
        card(345, 170, 240, 145, "Hipótesis", ["algoritmo", "parámetros"], "#F3F4F6", "#6B7280"),
        card(645, 135, 270, 215, "Incremento", ["módulo Python", "integración acotada", "manejo de error", "refactorización"], "#E5F2EA", "#4D8064"),
        card(975, 170, 240, 145, "Prueba", ["audio controlado", "casos imperfectos"], "#FFF3D6", "#A87822"),
        card(1275, 170, 180, 145, "Decisión", ["aceptar", "ajustar"], "#FBE8E8", "#A84B4B"),
        arrow(285, 242, 345, 242), arrow(585, 242, 645, 242), arrow(915, 242, 975, 242), arrow(1215, 242, 1275, 242),
        card(165, 470, 270, 145, "Artefactos", ["WAV", "CSV / JSON"], "#DCEAF7", "#4779A8"),
        card(615, 470, 270, 145, "Mediciones", ["cents y cobertura", "latencia / tiempo"], "#E5F2EA", "#4D8064"),
        card(1065, 470, 270, 145, "Trazabilidad", ["configuración", "estado del requisito"], "#FFF3D6", "#A87822"),
        arrow(1095, 315, 300, 470), arrow(435, 542, 615, 542), arrow(885, 542, 1065, 542),
        f'<path d="M1365 315V685H465V315" fill="none" stroke="{LINE}" stroke-width="2.5" stroke-dasharray="8 7" marker-end="url(#arrow)"/>',
        text(750, 718, "Una función se acepta por evidencia reproducible, no solo porque la interfaz la ejecute", 17, "normal", MUTED),
        '</svg>',
    ]
    (OUT / "figura_3_1_iteracion_evidencia_v2.svg").write_text("".join(parts), encoding="utf-8")


def generate_physical_v2():
    image = data_url(RESOURCES / "entorno_fisico_karaoke.png")
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1700" height="980" viewBox="0 0 1700 980">', defs(),
        '<rect width="1700" height="980" fill="#FFFFFF"/>',
        text(850, 52, "Despliegue físico y procesos locales del prototipo", 24, "bold"),
        f'<image href="{image}" x="35" y="95" width="710" height="395" preserveAspectRatio="xMidYMid slice" clip-path="url(#rounded)"/>',
        '<rect x="35" y="95" width="710" height="395" rx="12" fill="none" stroke="#CBD5E1" stroke-width="2"/>',
        text(390, 525, "Captura y reproducción en el mismo equipo", 17, "normal", MUTED),
        card(815, 95, 820, 115, "Proceso principal", ["app.py · Python · Tkinter · hilos de trabajo"], "#DCEAF7", "#4779A8", 21),
        card(815, 255, 250, 145, "Audio", ["sounddevice", "44,1 kHz · mono"], "#E5F2EA", "#4D8064"),
        card(1100, 255, 250, 145, "Subproceso", ["py -3.10 -m demucs", "modelo htdemucs"], "#FFF3D6", "#A87822"),
        card(1385, 255, 250, 145, "Análisis", ["Pyworld / librosa", "dtw-python"], "#F3F4F6", "#6B7280"),
        arrow(1225, 210, 940, 255), arrow(1225, 210, 1225, 255), arrow(1225, 210, 1510, 255),
        card(100, 665, 330, 145, "Catálogo", ["canciones/&lt;id&gt;/", "metadata.json · ref_pitch.csv"], "#DCEAF7", "#4779A8"),
        card(500, 665, 330, 145, "Stems", ["output/htdemucs/&lt;id&gt;/", "vocals · instrumental"], "#E5F2EA", "#4D8064"),
        card(900, 665, 330, 145, "Sesiones", ["grabaciones/&lt;id&gt;/", "usuario_&lt;fecha&gt;.wav"], "#FFF3D6", "#A87822"),
        card(1300, 665, 300, 145, "Resultados", ["*_resultado.json", "métricas + curvas"], "#FBE8E8", "#A84B4B"),
        arrow(430, 737, 500, 737), arrow(830, 737, 900, 737), arrow(1230, 737, 1300, 737),
        text(850, 900, "Internet no es requisito del flujo actual; solo sería necesario para descargas o un LLM remoto", 17, "normal", MUTED),
        '</svg>',
    ]
    (OUT / "figura_4_1_despliegue_especifico_v2.svg").write_text("".join(parts), encoding="utf-8")


def generate_logical_v2():
    image = data_url(RESOURCES / "flujo_conceptual_audio.png")
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1800" height="1220" viewBox="0 0 1800 1220">', defs(),
        '<rect width="1800" height="1220" fill="#FFFFFF"/>',
        text(900, 50, "Arquitectura lógica actual y extensiones pendientes", 24, "bold"),
        f'<image href="{image}" x="500" y="80" width="800" height="285" preserveAspectRatio="xMidYMid meet"/>',
        '<rect x="500" y="80" width="800" height="285" rx="12" fill="none" stroke="#CBD5E1" stroke-width="2"/>',
        text(900, 395, "Flujo conceptual objetivo", 16, "normal", MUTED),
        card(55, 455, 240, 125, "app.py", ["estado y eventos", "hilos Tkinter"], "#FBE8E8", "#A84B4B"),
        card(355, 455, 260, 125, "catalogo.py", ["IDs y metadatos", "ciclo de canción"], "#FFF3D6", "#A87822"),
        card(675, 455, 260, 125, "separacion.py", ["Demucs", "mezcla instrumental"], "#DCEAF7", "#4779A8"),
        card(995, 455, 260, 125, "pitch.py", ["DIO + StoneMask", "filtro de F0"], "#E5F2EA", "#4D8064"),
        card(1315, 455, 240, 125, "guardar.py", ["CSV", "nota aproximada"], "#F3F4F6", "#6B7280"),
        arrow(295, 518, 355, 518), arrow(615, 518, 675, 518), arrow(935, 518, 995, 518), arrow(1255, 518, 1315, 518),
        card(55, 700, 280, 145, "karaoke.py", ["playrec 44,1 kHz", "WAV + duración"], "#FFF3D6", "#A87822"),
        card(405, 700, 280, 145, "comparacion.py", ["DTW sobre Hz", "descarta ruta"], "#DCEAF7", "#4779A8"),
        card(755, 700, 280, 145, "metricas.py", ["cents", "error y umbrales"], "#E5F2EA", "#4D8064"),
        card(1105, 700, 280, 145, "visualizacion.py", ["MIDI / tiempo", "cortes por silencio"], "#F3F4F6", "#6B7280"),
        card(1455, 700, 280, 145, "JSON de sesión", ["métricas", "curvas completas"], "#FBE8E8", "#A84B4B"),
        arrow(335, 772, 405, 772), arrow(685, 772, 755, 772), arrow(1035, 772, 1105, 772), arrow(1385, 772, 1455, 772),
        f'<path d="M1125 580V640H195V700" fill="none" stroke="{LINE}" stroke-width="2.5" marker-end="url(#arrow)"/>',
        card(90, 1010, 320, 130, "Captura por bloques", ["InputStream / callback", "latencia &lt; 150 ms"], "#FBE8E8", "#A84B4B"),
        card(500, 1010, 320, 130, "Análisis temporal", ["ruta DTW en cents", "segmentos + evidencia"], "#FBE8E8", "#A84B4B"),
        card(910, 1010, 320, 130, "Retroalimentación", ["plantillas / LLM", "validación obligatoria"], "#FBE8E8", "#A84B4B"),
        card(1320, 1010, 320, 130, "Historial versionado", ["referencia + configuración", "comparación entre sesiones"], "#FBE8E8", "#A84B4B"),
        arrow(410, 1075, 500, 1075, True), arrow(820, 1075, 910, 1075, True), arrow(1230, 1075, 1320, 1075, True),
        text(900, 1185, "Línea continua: implementado o parcial · Línea discontinua: extensión requerida", 17, "normal", MUTED),
        '</svg>',
    ]
    (OUT / "figura_4_2_arquitectura_modulos_v2.svg").write_text("".join(parts), encoding="utf-8")


def generate_drawio_v2():
    drawio("figura_3_1_iteracion_evidencia_v2.drawio", "Figura 3.1 v2", 1500, 760, [], [
        ("input", 45, 170, 240, 145, "Entrada&lt;br&gt;requisito + HU&lt;br&gt;riesgo técnico", "#DCEAF7", "#4779A8"),
        ("hyp", 345, 170, 240, 145, "Hipótesis&lt;br&gt;algoritmo y parámetros", "#F3F4F6", "#6B7280"),
        ("inc", 645, 135, 270, 215, "Incremento&lt;br&gt;módulo, integración,&lt;br&gt;errores y refactorización", "#E5F2EA", "#4D8064"),
        ("test", 975, 170, 240, 145, "Prueba&lt;br&gt;audio controlado&lt;br&gt;y casos imperfectos", "#FFF3D6", "#A87822"),
        ("decision", 1275, 170, 180, 145, "Decisión&lt;br&gt;aceptar o ajustar", "#FBE8E8", "#A84B4B"),
        ("artifacts", 165, 470, 270, 145, "Artefactos&lt;br&gt;WAV, CSV y JSON", "#DCEAF7", "#4779A8"),
        ("metrics", 615, 470, 270, 145, "Mediciones&lt;br&gt;cents, cobertura y latencia", "#E5F2EA", "#4D8064"),
        ("trace", 1065, 470, 270, 145, "Trazabilidad&lt;br&gt;configuración y requisito", "#FFF3D6", "#A87822"),
    ], [("input", "hyp", False), ("hyp", "inc", False), ("inc", "test", False), ("test", "decision", False), ("test", "artifacts", False), ("artifacts", "metrics", False), ("metrics", "trace", False), ("decision", "hyp", True)])

    physical_img = data_url(RESOURCES / "entorno_fisico_karaoke.png")
    drawio("figura_4_1_despliegue_especifico_v2.drawio", "Figura 4.1 v2", 1700, 980, [("photo", 35, 95, 710, 395, physical_img)], [
        ("app", 815, 95, 820, 115, "app.py · Python · Tkinter&lt;br&gt;proceso principal e hilos", "#DCEAF7", "#4779A8"),
        ("audio", 815, 255, 250, 145, "sounddevice&lt;br&gt;44,1 kHz · mono", "#E5F2EA", "#4D8064"),
        ("demucs", 1100, 255, 250, 145, "Subproceso Demucs&lt;br&gt;Python 3.10", "#FFF3D6", "#A87822"),
        ("analysis", 1385, 255, 250, 145, "Pyworld / librosa&lt;br&gt;dtw-python", "#F3F4F6", "#6B7280"),
        ("catalog", 100, 665, 330, 145, "canciones/&lt;id&gt;/&lt;br&gt;metadata.json · ref_pitch.csv", "#DCEAF7", "#4779A8"),
        ("stems", 500, 665, 330, 145, "output/htdemucs/&lt;id&gt;/&lt;br&gt;vocals · instrumental", "#E5F2EA", "#4D8064"),
        ("sessions", 900, 665, 330, 145, "grabaciones/&lt;id&gt;/&lt;br&gt;usuario_&lt;fecha&gt;.wav", "#FFF3D6", "#A87822"),
        ("results", 1300, 665, 300, 145, "*_resultado.json&lt;br&gt;métricas + curvas", "#FBE8E8", "#A84B4B"),
    ], [("app", "audio", False), ("app", "demucs", False), ("app", "analysis", False), ("catalog", "stems", False), ("stems", "sessions", False), ("sessions", "results", False)])

    logical_img = data_url(RESOURCES / "flujo_conceptual_audio.png")
    nodes = [
        ("app", 55, 455, 240, 125, "app.py&lt;br&gt;eventos e hilos", "#FBE8E8", "#A84B4B"),
        ("catalog", 355, 455, 260, 125, "catalogo.py&lt;br&gt;IDs y metadatos", "#FFF3D6", "#A87822"),
        ("separation", 675, 455, 260, 125, "separacion.py&lt;br&gt;Demucs e instrumental", "#DCEAF7", "#4779A8"),
        ("pitch", 995, 455, 260, 125, "pitch.py&lt;br&gt;DIO, StoneMask y filtro", "#E5F2EA", "#4D8064"),
        ("save", 1315, 455, 240, 125, "guardar.py&lt;br&gt;CSV y nota", "#F3F4F6", "#6B7280"),
        ("karaoke", 55, 700, 280, 145, "karaoke.py&lt;br&gt;playrec 44,1 kHz", "#FFF3D6", "#A87822"),
        ("compare", 405, 700, 280, 145, "comparacion.py&lt;br&gt;DTW sobre Hz", "#DCEAF7", "#4779A8"),
        ("metrics", 755, 700, 280, 145, "metricas.py&lt;br&gt;cents y umbrales", "#E5F2EA", "#4D8064"),
        ("view", 1105, 700, 280, 145, "visualizacion.py&lt;br&gt;MIDI y tiempo", "#F3F4F6", "#6B7280"),
        ("json", 1455, 700, 280, 145, "JSON de sesión&lt;br&gt;métricas y curvas", "#FBE8E8", "#A84B4B"),
        ("stream", 90, 1010, 320, 130, "Captura por bloques&lt;br&gt;latencia &lt; 150 ms", "#FBE8E8", "#A84B4B"),
        ("segments", 500, 1010, 320, 130, "Ruta DTW + segmentos&lt;br&gt;evidencia temporal", "#FBE8E8", "#A84B4B"),
        ("feedback", 910, 1010, 320, 130, "Retroalimentación&lt;br&gt;validación obligatoria", "#FBE8E8", "#A84B4B"),
        ("history", 1320, 1010, 320, 130, "Historial versionado&lt;br&gt;sesiones comparables", "#FBE8E8", "#A84B4B"),
    ]
    edges = [("app", "catalog", False), ("catalog", "separation", False), ("separation", "pitch", False), ("pitch", "save", False), ("karaoke", "compare", False), ("compare", "metrics", False), ("metrics", "view", False), ("view", "json", False), ("stream", "segments", True), ("segments", "feedback", True), ("feedback", "history", True)]
    drawio("figura_4_2_arquitectura_modulos_v2.drawio", "Figura 4.2 v2", 1800, 1220, [("concept", 500, 80, 800, 285, logical_img)], nodes, edges)


if __name__ == "__main__":
    generate_iteration_evidence()
    generate_physical_v2()
    generate_logical_v2()
    generate_drawio_v2()
    print(OUT)
