import json
import os
import queue
import threading
import time
from datetime import datetime

import librosa
import numpy as np
import sounddevice as sd
import soundfile as sf

from audio.catalogo import carpeta_grabaciones, leer_pitch_csv
from audio.comparacion import comparar
from audio.metricas import hz_to_midi
from audio.retroalimentacion import generar_retroalimentacion
from audio.segmentacion import preparar_segmentacion
from audio.pitch import extraer_pitch, extraer_pitch_ligero_desde_audio, extraer_pitch_detallado


def grabar_con_instrumental(
    cancion,
    samplerate=44100,
    detener_evento=None,
    progreso_callback=None,
    pitch_callback=None,
    diagnostico_callback=None,
    intervalo_pitch=0.06,
    segundos_chunk_pitch=0.38,
    duracion_calibracion_ruido=0.6,
    usar_filtro_aprendido=False,
):
    instrumental_path = cancion["instrumental"]
    if not os.path.exists(instrumental_path):
        raise FileNotFoundError("No existe la pista instrumental de la cancion.")

    reproduccion = _cargar_reproduccion(instrumental_path, samplerate)

    duracion_frames = reproduccion.shape[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    salida = os.path.join(carpeta_grabaciones(cancion["id"]), f"usuario_{timestamp}.wav")

    ruido_base = medir_ruido_ambiente(samplerate, duracion_calibracion_ruido)
    if diagnostico_callback is not None:
        diagnostico_callback({
            "noise_floor": ruido_base,
            "rms": ruido_base,
            "energy_threshold": 0.0,
            "raw_points": 0,
            "filtered_points": 0,
            "rejected_points": 0,
        })

    grabacion = sd.playrec(
        reproduccion,
        samplerate=samplerate,
        channels=1,
        dtype="float32",
        blocking=False,
    )

    inicio = time.monotonic()
    ultimo_analisis = 0
    pitch_queue = None
    pitch_stop = None
    pitch_worker = None

    if pitch_callback is not None:
        pitch_queue = queue.Queue(maxsize=2)
        pitch_stop = threading.Event()
        pitch_worker = threading.Thread(
            target=_worker_pitch_tiempo_real,
            args=(pitch_queue, pitch_stop, pitch_callback, diagnostico_callback, samplerate, ruido_base,
                  usar_filtro_aprendido),
            daemon=True,
        )
        pitch_worker.start()

    try:
        while True:
            transcurrido = time.monotonic() - inicio
            frames_grabados = int(transcurrido * samplerate)
            if frames_grabados >= duracion_frames:
                break
            if detener_evento is not None and detener_evento.is_set():
                break
            if progreso_callback is not None:
                progreso_callback(transcurrido)
            if pitch_callback is not None and transcurrido - ultimo_analisis >= intervalo_pitch:
                inicio_chunk_t = max(0, transcurrido - segundos_chunk_pitch)
                inicio_chunk = int(inicio_chunk_t * samplerate)
                fin_chunk = min(frames_grabados, duracion_frames)
                chunk = np.asarray(grabacion[inicio_chunk:fin_chunk]).reshape(-1)
                _encolar_pitch_reciente(pitch_queue, inicio_chunk_t, chunk)
                ultimo_analisis = transcurrido
            sd.sleep(18)
    finally:
        sd.stop()
        if pitch_stop is not None:
            pitch_stop.set()
        if pitch_worker is not None:
            pitch_worker.join(timeout=0.4)

    frames_grabados = min(max(int((time.monotonic() - inicio) * samplerate), 1), duracion_frames)
    if progreso_callback is not None:
        progreso_callback(frames_grabados / samplerate)
    grabacion = np.asarray(grabacion[:frames_grabados]).reshape(frames_grabados, 1)
    sf.write(salida, grabacion, samplerate)
    return salida


def medir_ruido_ambiente(samplerate=44100, duracion=0.6):
    muestras = max(1, int(samplerate * duracion))
    grabacion = sd.rec(
        muestras,
        samplerate=samplerate,
        channels=1,
        dtype="float32",
    )
    sd.wait()
    datos = np.asarray(grabacion, dtype=float).reshape(-1)
    return float(np.sqrt(np.mean(datos * datos))) if len(datos) else 0.0


def _cargar_reproduccion(ruta_audio, samplerate):
    try:
        audio, sr = sf.read(ruta_audio, dtype="float32", always_2d=True)
        if audio.shape[1] > 2:
            audio = audio[:, :2]

        if sr != samplerate:
            audio = librosa.resample(
                audio.T,
                orig_sr=sr,
                target_sr=samplerate,
                axis=1,
            ).T.astype("float32", copy=False)
    except Exception:
        audio, _ = librosa.load(ruta_audio, sr=samplerate, mono=False)
        if audio.ndim == 1:
            audio = audio.reshape(-1, 1)
        else:
            audio = audio.T

    audio = np.nan_to_num(audio.astype("float32", copy=False), nan=0.0, posinf=0.0, neginf=0.0)
    peak = float(np.max(np.abs(audio))) if audio.size else 0.0
    if peak > 0.98:
        audio = audio / peak * 0.98
    return np.ascontiguousarray(audio)


def _encolar_pitch_reciente(pitch_queue, inicio_t, chunk):
    if pitch_queue is None:
        return

    chunk = np.asarray(chunk, dtype="float32").copy()
    if not len(chunk):
        return

    try:
        pitch_queue.put_nowait((inicio_t, chunk))
    except queue.Full:
        try:
            pitch_queue.get_nowait()
            pitch_queue.task_done()
        except queue.Empty:
            pass
        try:
            pitch_queue.put_nowait((inicio_t, chunk))
        except queue.Full:
            pass


def _worker_pitch_tiempo_real(
    pitch_queue,
    pitch_stop,
    pitch_callback,
    diagnostico_callback,
    samplerate,
    ruido_base,
    usar_filtro_aprendido=False,
):
    ultimo_pitch_t = 0
    while not pitch_stop.is_set() or not pitch_queue.empty():
        try:
            inicio_chunk_t, chunk = pitch_queue.get(timeout=0.04)
        except queue.Empty:
            continue

        try:
            t_pitch, f_pitch, info = extraer_pitch_ligero_desde_audio(
                chunk,
                samplerate,
                offset_t=inicio_chunk_t,
                ruido_base=ruido_base,
                devolver_info=True,
                usar_filtro_aprendido=usar_filtro_aprendido,
            )
            if diagnostico_callback is not None:
                diagnostico_callback(info)
            nuevos = t_pitch > ultimo_pitch_t
            if np.any(nuevos):
                ultimo_pitch_t = float(np.max(t_pitch[nuevos]))
                pitch_callback(
                    [float(t) for t in t_pitch[nuevos]],
                    [float(f) for f in f_pitch[nuevos]],
                )
        except Exception:
            if diagnostico_callback is not None:
                diagnostico_callback({
                    "noise_floor": ruido_base,
                    "rms": 0.0,
                    "energy_threshold": 0.0,
                    "raw_points": 0,
                    "filtered_points": 0,
                    "rejected_points": 0,
                    "pitch_errors": 1,
                })
        finally:
            pitch_queue.task_done()


def comparar_grabacion(cancion, ruta_grabacion):
    t_ref, f_ref = leer_pitch_csv(cancion["pitch_referencia"])
    segmentos = preparar_segmentacion(cancion, t_ref, f_ref)
    t_usr, f_usr = extraer_pitch(ruta_grabacion)
    duracion_usuario = sf.info(ruta_grabacion).duration
    referencia_completa = (t_ref, f_ref)
    puntos_ref = [(t, f) for t, f in zip(t_ref, f_ref) if t <= duracion_usuario]
    if puntos_ref:
        t_ref, f_ref = zip(*puntos_ref)
    else:
        t_ref, f_ref = [], []

    resultado = comparar(np.array(f_ref), np.array(f_usr))
    resultado["grafico"] = {
        "t_ref": [float(t) for t in t_ref],
        "f_ref": [float(f) for f in f_ref],
        "t_usr": [float(t) for t in t_usr],
        "f_usr": [float(f) for f in f_usr],
    }

    from audio.alineacion import resolver_ajuste, analizar_alineado
    tr_completa, fr_completa = referencia_completa
    estado = resolver_ajuste(ruta_grabacion, tr_completa, fr_completa, t_usr, f_usr)
    resultado["retroalimentacion"] = analizar_alineado(
        tr_completa, fr_completa, t_usr, f_usr, duracion_usuario, segmentos, estado)

    resultado_path = os.path.splitext(ruta_grabacion)[0] + "_resultado.json"
    with open(resultado_path, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)

    return resultado


def diagnosticar_filtros(cancion, ruta_grabacion=None):
    diagnostico = {
        "referencia": _diagnosticar_archivo(cancion["vocals"]),
        "usuario": None,
    }

    if ruta_grabacion and os.path.exists(ruta_grabacion):
        diagnostico["usuario"] = _diagnosticar_archivo(ruta_grabacion)

    return diagnostico


def _diagnosticar_archivo(ruta_audio):
    datos = extraer_pitch_detallado(ruta_audio)
    crudos = len(datos["f_crudo"])
    filtrados = len(datos["f_filtrado"])
    corregidos = len(datos.get("f_corregido", []))
    conservacion = (filtrados / crudos * 100) if crudos else 0.0
    midi_filtrado = hz_to_midi(datos["f_filtrado"])
    midi_corregido = hz_to_midi(datos.get("f_corregido", []))
    correcciones_octava = _contar_correcciones_octava(
        datos["t_filtrado"],
        midi_filtrado,
        datos.get("t_corregido", []),
        midi_corregido,
    )

    return {
        "ruta": ruta_audio,
        "puntos_crudos": crudos,
        "puntos_filtrados": filtrados,
        "puntos_corregidos": corregidos,
        "correcciones_octava": correcciones_octava,
        "conservacion": float(conservacion),
        "t_crudo": [float(t) for t in datos["t_crudo"]],
        "f_crudo": [float(f) for f in datos["f_crudo"]],
        "t_filtrado": [float(t) for t in datos["t_filtrado"]],
        "f_filtrado": [float(f) for f in datos["f_filtrado"]],
        "t_corregido": [float(t) for t in datos.get("t_corregido", [])],
        "f_corregido": [float(f) for f in datos.get("f_corregido", [])],
    }


def _contar_correcciones_octava(t_filtrado, midi_filtrado, t_corregido, midi_corregido):
    t_filtrado = np.asarray(t_filtrado, dtype=float)
    midi_filtrado = np.asarray(midi_filtrado, dtype=float)
    t_corregido = np.asarray(t_corregido, dtype=float)
    midi_corregido = np.asarray(midi_corregido, dtype=float)
    if not len(t_filtrado) or not len(t_corregido):
        return 0

    indices = np.searchsorted(t_filtrado, t_corregido)
    correcciones = 0
    for i, tiempo in enumerate(t_corregido):
        candidatos = []
        for indice in (indices[i] - 1, indices[i]):
            if 0 <= indice < len(t_filtrado):
                candidatos.append((abs(t_filtrado[indice] - tiempo), indice))
        if not candidatos:
            continue
        distancia, indice = min(candidatos)
        if distancia <= 1e-4 and abs(midi_filtrado[indice] - midi_corregido[i]) > 6:
            correcciones += 1
    return int(correcciones)
