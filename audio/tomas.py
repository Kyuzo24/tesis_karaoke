import json
import os
from datetime import datetime

import soundfile as sf

from audio.catalogo import carpeta_grabaciones
from audio.retroalimentacion import generar_retroalimentacion, preparar_contexto_modelo


def guardar_toma(cancion, ruta_grabacion, resultado, diagnostico=None):
    toma = _crear_metadata_toma(cancion, ruta_grabacion, resultado, diagnostico)
    _guardar_metadata_toma(toma)
    return toma


def obtener_contexto_retroalimentacion(cancion, toma_id, fragmento_id=None):
    """Recalcula evidencia con compensación compartida; conserva el resultado original."""
    from audio.alineacion import resolver_ajuste, analizar_alineado
    from audio.segmentacion import preparar_segmentacion
    from audio.catalogo import leer_pitch_csv
    toma = _buscar_toma(cancion, toma_id)
    resultado = _leer_json(toma['result_path']) if os.path.exists(toma['result_path']) else {}
    feedback = resultado.get('retroalimentacion')
    if feedback is not None and feedback.get('version') not in ('1.0.0', '2.0.0', '3.0.0'):
        raise ValueError('Versión de retroalimentación no compatible.')
    graph = resultado.get('grafico') or toma.get('graph') or {}
    tr, fr = graph.get('t_ref', []), graph.get('f_ref', [])
    if cancion.get('pitch_referencia'):
        tr, fr = leer_pitch_csv(cancion['pitch_referencia'])
    tu, fu = graph.get('t_usr', []), graph.get('f_usr', [])
    estado = resolver_ajuste(toma['voice_path'], tr, fr, tu, fu)
    segmentos = preparar_segmentacion(cancion, tr, fr)
    feedback = analizar_alineado(tr, fr, tu, fu, _duracion(toma['voice_path']), segmentos, estado)
    return preparar_contexto_modelo(feedback, fragmento_id=fragmento_id)


def listar_tomas(cancion):
    carpeta = carpeta_grabaciones(cancion["id"])
    tomas = []
    for nombre in os.listdir(carpeta):
        if not nombre.lower().endswith(".wav"):
            continue
        ruta_grabacion = os.path.join(carpeta, nombre)
        toma = cargar_toma_desde_audio(cancion, ruta_grabacion)
        if toma:
            tomas.append(toma)

    return sorted(tomas, key=lambda item: item.get("created_at", ""), reverse=True)


def cargar_toma_desde_audio(cancion, ruta_grabacion):
    metadata_path = _metadata_toma_path(ruta_grabacion)
    if os.path.exists(metadata_path):
        with open(metadata_path, "r", encoding="utf-8") as f:
            toma = json.load(f)
        toma["voice_path"] = ruta_grabacion
        toma["metadata_path"] = metadata_path
        toma["result_path"] = _resultado_path(ruta_grabacion)
        toma["instrumental_path"] = cancion.get("instrumental", "")
        return toma

    resultado_path = _resultado_path(ruta_grabacion)
    resultado = _leer_json(resultado_path) if os.path.exists(resultado_path) else {}
    return _crear_metadata_toma(cancion, ruta_grabacion, resultado, diagnostico=None)


def actualizar_toma(cancion, toma_id, nombre=None, favorita=None):
    toma = _buscar_toma(cancion, toma_id)
    if nombre is not None:
        toma["name"] = str(nombre or "").strip()
    if favorita is not None:
        toma["favorite"] = bool(favorita)
    _guardar_metadata_toma(toma)
    return cargar_toma_desde_audio(cancion, toma["voice_path"])


def eliminar_toma(cancion, toma_id):
    toma = _buscar_toma(cancion, toma_id)
    rutas = [
        os.path.splitext(toma['voice_path'])[0] + '_alineacion.json',
        os.path.splitext(toma['voice_path'])[0] + '_explicaciones.json',
        toma.get("voice_path", ""),
        toma.get("metadata_path", ""),
        toma.get("result_path", ""),
    ]
    for ruta in rutas:
        if ruta and os.path.exists(ruta):
            os.remove(ruta)
    return True


def _crear_metadata_toma(cancion, ruta_grabacion, resultado, diagnostico=None):
    resultado = resultado or {}
    return {
        "id": os.path.splitext(os.path.basename(ruta_grabacion))[0],
        "song_id": cancion["id"],
        "song_title": cancion.get("titulo", "Sin titulo"),
        "artist": cancion.get("artista") or "Sin artista",
        "name": "",
        "favorite": False,
        "created_at": _fecha_toma(ruta_grabacion),
        "voice_path": ruta_grabacion,
        "instrumental_path": cancion.get("instrumental", ""),
        "result_path": _resultado_path(ruta_grabacion),
        "metadata_path": _metadata_toma_path(ruta_grabacion),
        "duration": _duracion(ruta_grabacion),
        "metrics": _metricas(resultado),
        "graph": resultado.get("grafico") or {},
        "diagnostics": diagnostico or {},
    }


def _metricas(resultado):
    return {
        "error_prom": resultado.get("error_prom"),
        "desviacion": resultado.get("desviacion"),
        "tendencia": resultado.get("tendencia"),
        "porcentaje_50": resultado.get("porcentaje_50"),
        "porcentaje_100": resultado.get("porcentaje_100"),
        "puntos_comparados": resultado.get("puntos_comparados"),
        "error_medio_firmado": resultado.get("error_medio_firmado"),
        "mensaje": resultado.get("mensaje"),
    }


def _resultado_path(ruta_grabacion):
    return os.path.splitext(ruta_grabacion)[0] + "_resultado.json"


def _metadata_toma_path(ruta_grabacion):
    return os.path.splitext(ruta_grabacion)[0] + "_toma.json"


def _guardar_metadata_toma(toma):
    with open(toma["metadata_path"], "w", encoding="utf-8") as f:
        json.dump(toma, f, indent=2, ensure_ascii=False)


def _buscar_toma(cancion, toma_id):
    toma_id = str(toma_id or "").strip()
    if not toma_id:
        raise FileNotFoundError("No se indico la toma.")

    carpeta = carpeta_grabaciones(cancion["id"])
    for nombre in os.listdir(carpeta):
        if not nombre.lower().endswith(".wav"):
            continue
        if os.path.splitext(nombre)[0] != toma_id:
            continue
        toma = cargar_toma_desde_audio(cancion, os.path.join(carpeta, nombre))
        if not toma:
            break
        return toma

    raise FileNotFoundError("No se encontro la toma seleccionada.")


def _leer_json(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        return json.load(f)


def _duracion(ruta_audio):
    try:
        return float(sf.info(ruta_audio).duration)
    except RuntimeError:
        return 0.0


def _fecha_toma(ruta_grabacion):
    stem = os.path.splitext(os.path.basename(ruta_grabacion))[0]
    partes = stem.split("_")
    if len(partes) >= 3 and partes[0] == "usuario":
        try:
            fecha = datetime.strptime("_".join(partes[1:3]), "%Y%m%d_%H%M%S")
            return fecha.isoformat(timespec="seconds")
        except ValueError:
            pass
    return datetime.fromtimestamp(os.path.getmtime(ruta_grabacion)).isoformat(timespec="seconds")
