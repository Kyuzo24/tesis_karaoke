import librosa
import numpy as np
from audio.filtro_aprendido import aceptar_candidatos

try:
    import pyworld as pw
except ImportError:
    pw = None


FILTRO_SUAVE = {
    "nota_min": "A1",
    "nota_max": "C7",
    "percentil_rms": 25,
    "factor_rms": 1.25,
    "factor_rms_max": 0.012,
    "max_gap": 5,
    "min_frames": 2,
    "ventana_mediana": 7,
    "max_salto_midi": 9,
}

FILTRO_TIEMPO_REAL = {
    "nota_min": "C2",
    "nota_max": "C6",
    "factor_rms_max": 0.08,
    "factor_ruido": 2.2,
    "min_rms_absoluto": 0.002,
    "max_gap": 1,
    "min_frames": 3,
    "ventana_mediana": 3,
    "max_salto_midi": 8,
    "min_periodicidad": 0.7,
    "usar_filtro_aprendido": False,
}


def _rellenar_huecos_cortos(f0, max_gap):
    f0 = np.asarray(f0, dtype=float).copy()
    validos = np.where(f0 > 0)[0]
    if len(validos) < 2:
        return f0

    for inicio, fin in zip(validos[:-1], validos[1:]):
        gap = fin - inicio - 1
        if 0 < gap <= max_gap:
            f0[inicio + 1 : fin] = np.linspace(f0[inicio], f0[fin], gap + 2)[1:-1]
    return f0


def _quitar_segmentos_cortos(f0, min_frames):
    f0 = np.asarray(f0, dtype=float).copy()
    mask = f0 > 0
    inicio = None

    for i, activo in enumerate(np.r_[mask, False]):
        if activo and inicio is None:
            inicio = i
        elif not activo and inicio is not None:
            if i - inicio < min_frames:
                f0[inicio:i] = 0
            inicio = None
    return f0


def _mediana_movil(valores, ventana=7):
    valores = np.asarray(valores, dtype=float)
    salida = np.full_like(valores, np.nan, dtype=float)
    radio = ventana // 2

    for i in range(len(valores)):
        inicio = max(0, i - radio)
        fin = min(len(valores), i + radio + 1)
        segmento = valores[inicio:fin]
        segmento = segmento[~np.isnan(segmento)]
        if len(segmento):
            salida[i] = np.median(segmento)
    return salida


def _filtrar_pitch(t, f0, y, sr, config=None, corregir_octavas=True):
    config = config or FILTRO_SUAVE
    f0 = np.nan_to_num(np.asarray(f0, dtype=float), nan=0.0)
    t = np.asarray(t, dtype=float)

    f_min = librosa.note_to_hz(config["nota_min"])
    f_max = librosa.note_to_hz(config["nota_max"])
    f0[(f0 < f_min) | (f0 > f_max)] = 0

    rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
    t_rms = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=512)
    energia = np.interp(t, t_rms, rms, left=0, right=0)
    umbral_energia = max(
        np.percentile(rms, config["percentil_rms"]) * config["factor_rms"],
        np.max(rms) * config["factor_rms_max"],
    )
    f0[energia < umbral_energia] = 0

    f0 = _rellenar_huecos_cortos(f0, max_gap=config["max_gap"])
    f0 = _quitar_segmentos_cortos(f0, min_frames=config["min_frames"])

    mask = f0 > 0
    if np.sum(mask) >= 7:
        midi = np.full_like(f0, np.nan, dtype=float)
        midi[mask] = 69 + 12 * np.log2(f0[mask] / 440.0)
        mediana = _mediana_movil(midi, ventana=config["ventana_mediana"])
        saltos = np.abs(midi - mediana) > config["max_salto_midi"]
        f0[saltos & mask] = 0

    f0 = _quitar_segmentos_cortos(f0, min_frames=config["min_frames"])
    mask = f0 > 0
    t_filtrado = t[mask]
    f_filtrado = f0[mask]
    if corregir_octavas:
        return _corregir_octavas_por_registro(t_filtrado, f_filtrado)
    return t_filtrado, f_filtrado


def _energia_por_tiempo(y, sr, tiempos, ventana=1024):
    y = np.asarray(y, dtype=float).reshape(-1)
    tiempos = np.asarray(tiempos, dtype=float)
    if len(y) == 0 or len(tiempos) == 0:
        return np.array([])

    cuadrado = y * y
    acumulado = np.concatenate(([0.0], np.cumsum(cuadrado)))
    centros = np.clip((tiempos * sr).astype(int), 0, len(y) - 1)
    radio = ventana // 2
    inicios = np.maximum(0, centros - radio)
    fines = np.minimum(len(y), centros + radio)
    muestras = np.maximum(1, fines - inicios)
    energia = (acumulado[fines] - acumulado[inicios]) / muestras
    return np.sqrt(np.maximum(energia, 0.0))


def _filtrar_pitch_tiempo_real(t, f0, y, sr, config=None, ruido_base=None, devolver_info=False,
                             periodicidad=None):
    config = config or FILTRO_TIEMPO_REAL
    f0 = np.nan_to_num(np.asarray(f0, dtype=float), nan=0.0)
    t = np.asarray(t, dtype=float)
    raw_points = int(np.sum(f0 > 0))
    candidatos = f0.copy()
    rms_chunk = float(np.sqrt(np.mean(np.asarray(y, dtype=float) ** 2))) if len(y) else 0.0

    f_min = librosa.note_to_hz(config["nota_min"])
    f_max = librosa.note_to_hz(config["nota_max"])
    f0[(f0 < f_min) | (f0 > f_max)] = 0

    energia = _energia_por_tiempo(y, sr, t)
    umbral_energia = 0.0
    if len(energia):
        umbral_energia = max(
            float(np.max(energia)) * config["factor_rms_max"],
            config["min_rms_absoluto"],
        )
        if ruido_base is not None and ruido_base > 0:
            umbral_energia = max(umbral_energia, float(ruido_base) * config["factor_ruido"])
        f0[energia < umbral_energia] = 0

    periodicos = None
    if periodicidad is not None:
        periodicos = np.asarray(periodicidad) >= config.get("min_periodicidad", 0.7)
        if config.get("usar_filtro_aprendido", False):
            aprendidos = aceptar_candidatos(candidatos, periodicidad, energia)
            if aprendidos is not None:
                periodicos = aprendidos
        f0[~periodicos] = 0

    f0 = _rellenar_huecos_cortos(f0, max_gap=config["max_gap"])
    # Un hueco rechazado por falta de periodicidad no debe volver a ser una nota.
    if periodicos is not None:
        f0[~periodicos] = 0
    f0 = _quitar_segmentos_cortos(f0, min_frames=config["min_frames"])

    mask = f0 > 0
    if np.sum(mask) >= config["ventana_mediana"]:
        midi = np.full_like(f0, np.nan, dtype=float)
        midi[mask] = 69 + 12 * np.log2(f0[mask] / 440.0)
        mediana = _mediana_movil(midi, ventana=config["ventana_mediana"])
        saltos = np.abs(midi - mediana) > config["max_salto_midi"]
        f0[saltos & mask] = 0

    mask = f0 > 0
    t_filtrado = t[mask]
    f_filtrado = f0[mask]

    if devolver_info:
        return t_filtrado, f_filtrado, {
            "raw_points": raw_points,
            "filtered_points": int(len(f_filtrado)),
            "rejected_points": max(0, raw_points - int(len(f_filtrado))),
            "rms": rms_chunk,
            "energy_threshold": float(umbral_energia),
            "noise_floor": float(ruido_base or 0.0),
        }
    return t_filtrado, f_filtrado


def _corregir_octavas_por_registro(t, f0, min_puntos=30):
    t = np.asarray(t, dtype=float)
    f0 = np.asarray(f0, dtype=float)
    if len(f0) < min_puntos:
        return t, f0

    midi = 69 + 12 * np.log2(f0 / 440.0)
    midi = np.nan_to_num(midi, nan=0.0, posinf=0.0, neginf=0.0)
    if np.sum(midi > 0) < min_puntos:
        return t, f0

    corregido = midi.copy()
    valores = midi[midi > 0]
    umbral_octava_alta = max(70.5, float(np.percentile(valores, 90)) + 4.0)
    segmentos = _segmentos_pitch(t, midi)
    for indice, segmento in enumerate(segmentos):
        inicio, fin, mediana, duracion, _inicio_t, _fin_t = segmento
        if mediana < umbral_octava_alta or duracion > 0.9:
            continue

        vecinos = [
            nota
            for nota in _medianas_vecinas(segmentos, indice, max_distancia=1.5)
            if nota < umbral_octava_alta
        ]
        if not vecinos:
            continue

        actual = float(np.median(np.abs(np.asarray(vecinos) - mediana)))
        una_octava_abajo = float(np.median(np.abs(np.asarray(vecinos) - (mediana - 12.0))))
        if actual >= 8.0 and una_octava_abajo <= 5.5 and una_octava_abajo + 2.0 < actual:
            segmento = corregido[inicio:fin]
            segmento[segmento >= umbral_octava_alta] -= 12.0

    f0_corregido = 440.0 * np.power(2.0, (corregido - 69.0) / 12.0)
    return _limpiar_segmentos_erraticos(t, f0_corregido)


def _limpiar_segmentos_erraticos(t, f0, min_puntos=30):
    t = np.asarray(t, dtype=float)
    f0 = np.asarray(f0, dtype=float)
    if len(f0) < min_puntos:
        return t, f0

    midi = 69 + 12 * np.log2(f0 / 440.0)
    midi = np.nan_to_num(midi, nan=0.0, posinf=0.0, neginf=0.0)
    valores = midi[midi > 0]
    if len(valores) < min_puntos:
        return t, f0

    umbral_octava_alta = max(70.5, float(np.percentile(valores, 90)) + 4.0)
    segmentos = _segmentos_pitch(t, midi)
    conservar = np.ones(len(midi), dtype=bool)

    for indice, segmento in enumerate(segmentos):
        inicio, fin, mediana, duracion, _inicio_t, _fin_t = segmento
        vecinos = _medianas_vecinas(segmentos, indice, max_distancia=1.5)
        distancia_vecinos = float(np.median(np.abs(np.asarray(vecinos) - mediana))) if vecinos else 99.0

        if mediana >= umbral_octava_alta + 5.0 and duracion <= 0.45 and distancia_vecinos >= 7.0:
            conservar[inicio:fin] = False
        elif mediana >= umbral_octava_alta and duracion <= 0.06 and distancia_vecinos >= 5.0:
            conservar[inicio:fin] = False

    return t[conservar], f0[conservar]


def _segmentos_pitch(t, midi, max_gap=0.18, max_jump=4.5):
    segmentos = []
    if len(midi) == 0:
        return segmentos

    inicio = 0
    for i in range(1, len(midi)):
        if t[i] - t[i - 1] > max_gap or abs(midi[i] - midi[i - 1]) > max_jump:
            segmentos.append(_describir_segmento(t, midi, inicio, i))
            inicio = i
    segmentos.append(_describir_segmento(t, midi, inicio, len(midi)))
    return [segmento for segmento in segmentos if segmento is not None]


def _describir_segmento(t, midi, inicio, fin):
    if fin <= inicio:
        return None
    duracion = max(0.0, float(t[fin - 1] - t[inicio]))
    mediana = float(np.median(midi[inicio:fin]))
    return inicio, fin, mediana, duracion, float(t[inicio]), float(t[fin - 1])


def _medianas_vecinas(segmentos, indice, max_distancia=1.0):
    _inicio, _fin, _mediana, _duracion, inicio_t, fin_t = segmentos[indice]
    vecinos = []

    for anterior in range(indice - 1, max(-1, indice - 4), -1):
        _a_inicio, _a_fin, a_mediana, _a_duracion, _a_inicio_t, a_fin_t = segmentos[anterior]
        distancia = max(0.0, inicio_t - a_fin_t)
        if distancia > max_distancia:
            break
        vecinos.append(a_mediana)

    for siguiente in range(indice + 1, min(len(segmentos), indice + 4)):
        _s_inicio, _s_fin, s_mediana, _s_duracion, s_inicio_t, _s_fin_t = segmentos[siguiente]
        distancia = max(0.0, s_inicio_t - fin_t)
        if distancia > max_distancia:
            break
        vecinos.append(s_mediana)

    return vecinos


def _info_pitch_vacio(ruido_base=0.0, rms=0.0):
    return {
        "raw_points": 0,
        "filtered_points": 0,
        "rejected_points": 0,
        "rms": float(rms),
        "energy_threshold": 0.0,
        "noise_floor": float(ruido_base or 0.0),
    }


def _lag_parabolico(autocorrelacion, indice):
    if indice <= 0 or indice >= len(autocorrelacion) - 1:
        return float(indice)

    izquierda = autocorrelacion[indice - 1]
    centro = autocorrelacion[indice]
    derecha = autocorrelacion[indice + 1]
    denominador = izquierda - 2 * centro + derecha
    if abs(denominador) < 1e-12:
        return float(indice)

    return float(indice + 0.5 * (izquierda - derecha) / denominador)


def _pitch_autocorrelacion(frame, sr, f_min, f_max, umbral_confianza=0.24):
    frame = np.asarray(frame, dtype=np.float32)
    frame = frame - float(np.mean(frame))
    energia = float(np.dot(frame, frame))
    if energia <= 1e-9:
        return 0.0

    ventana = np.hanning(len(frame)).astype(np.float32)
    frame = frame * ventana
    n_fft = 1 << (2 * len(frame) - 1).bit_length()
    espectro = np.fft.rfft(frame, n=n_fft)
    autocorrelacion = np.fft.irfft(espectro * np.conj(espectro), n=n_fft)[: len(frame)]
    if autocorrelacion[0] <= 0:
        return 0.0

    lag_min = max(1, int(sr / f_max))
    lag_max = min(len(frame) - 1, int(sr / f_min))
    if lag_max <= lag_min:
        return 0.0

    region = autocorrelacion[lag_min : lag_max + 1]
    indice = int(np.argmax(region)) + lag_min
    confianza = float(autocorrelacion[indice] / autocorrelacion[0])
    if confianza < umbral_confianza:
        return 0.0

    lag = _lag_parabolico(autocorrelacion, indice)
    if lag <= 0:
        return 0.0
    return float(sr / lag)


def _periodicidad_candidatos(y, sr, f0, frame_length, hop_length):
    """Similitud normalizada de cada frame con una copia desplazada un periodo.

    YIN puede devolver un candidato incluso para ruido. Esta comprobacion es
    independiente del volumen: resta DC y compara la energia de ambas copias.
    No interpreta la similitud como una probabilidad estadistica.
    """
    confianza = np.zeros(len(f0), dtype=float)
    for i, frecuencia in enumerate(f0):
        if not np.isfinite(frecuencia) or frecuencia <= 0:
            continue
        frame = np.asarray(y[i * hop_length:i * hop_length + frame_length], dtype=float)
        if len(frame) != frame_length:
            continue
        frame = frame - np.mean(frame)
        periodo = sr / frecuencia
        lag = int(np.floor(periodo))
        if lag < 1 or lag + 1 >= frame_length:
            continue
        # Interpolacion del desplazamiento para no penalizar periodos no enteros.
        fraccion = periodo - lag
        original = frame[:frame_length - lag - 1]
        desplazado = (1 - fraccion) * frame[lag:-1] + fraccion * frame[lag + 1:]
        energia = np.dot(original, original) + np.dot(desplazado, desplazado)
        if energia > np.finfo(float).tiny:
            confianza[i] = np.clip(2 * np.dot(original, desplazado) / energia, 0, 1)
    return confianza


def extraer_pitch_ligero_desde_audio(y, sr, offset_t=0, ruido_base=None, devolver_info=False,
                                   usar_filtro_aprendido=None):
    y = np.asarray(y, dtype=np.float32).reshape(-1)
    y = np.nan_to_num(y, nan=0.0, posinf=0.0, neginf=0.0)
    rms_chunk = float(np.sqrt(np.mean(y.astype(float) ** 2))) if len(y) else 0.0
    if len(y) < int(sr * 0.12):
        if devolver_info:
            return np.array([]), np.array([]), _info_pitch_vacio(ruido_base, rms_chunk)
        return np.array([]), np.array([])

    frame_length = min(2048, len(y))
    hop_length = 1024
    f_min = librosa.note_to_hz(FILTRO_TIEMPO_REAL["nota_min"])
    f_max = librosa.note_to_hz(FILTRO_TIEMPO_REAL["nota_max"])
    umbral_silencio = max(
        FILTRO_TIEMPO_REAL["min_rms_absoluto"],
        float(ruido_base or 0.0) * 1.6,
    )

    try:
        f0 = librosa.yin(
            y.astype(float, copy=False),
            fmin=f_min,
            fmax=f_max,
            sr=sr,
            frame_length=frame_length,
            hop_length=hop_length,
            center=False,
            trough_threshold=0.15,
        )
        t = (np.arange(len(f0), dtype=float) * hop_length + frame_length / 2) / sr
        f0 = np.nan_to_num(f0, nan=0.0, posinf=0.0, neginf=0.0)
    except Exception:
        tiempos = []
        frecuencias = []
        for inicio in range(0, len(y) - frame_length + 1, hop_length):
            frame = y[inicio : inicio + frame_length]
            rms_frame = float(np.sqrt(np.mean(frame.astype(float) ** 2))) if len(frame) else 0.0
            frecuencia = 0.0
            if rms_frame >= umbral_silencio:
                frecuencia = _pitch_autocorrelacion(frame, sr, f_min, f_max)
            tiempos.append((inicio + frame_length / 2) / sr)
            frecuencias.append(frecuencia)
        t = np.asarray(tiempos, dtype=float)
        f0 = np.asarray(frecuencias, dtype=float)

    if not len(t):
        if devolver_info:
            return np.array([]), np.array([]), _info_pitch_vacio(ruido_base, rms_chunk)
        return np.array([]), np.array([])

    resultado = _filtrar_pitch_tiempo_real(
        t,
        f0,
        y,
        sr,
        ruido_base=ruido_base,
        devolver_info=devolver_info,
        periodicidad=_periodicidad_candidatos(y, sr, f0, frame_length, hop_length),
        config=(dict(FILTRO_TIEMPO_REAL, usar_filtro_aprendido=bool(usar_filtro_aprendido))
                if usar_filtro_aprendido is not None else None),
    )
    if devolver_info:
        t_filtrado, f_filtrado, info = resultado
        return t_filtrado + offset_t, f_filtrado, info

    t_filtrado, f_filtrado = resultado
    return t_filtrado + offset_t, f_filtrado


def extraer_pitch_crudo(ruta_audio):
    y, sr = librosa.load(ruta_audio, sr=None)

    if pw is not None:
        y = y.astype(np.float64)
        f0, t = pw.dio(y, sr)
        f0 = pw.stonemask(y, f0, t, sr)
    else:
        f0, voiced_flag, voiced_prob = librosa.pyin(
            y,
            sr=sr,
            fmin=librosa.note_to_hz("C2"),
            fmax=librosa.note_to_hz("C7"),
        )
        t = librosa.times_like(f0, sr=sr)
        f0 = np.nan_to_num(f0, nan=0.0)

    mask = f0 > 0
    return t[mask], f0[mask]


def _extraer_pitch_base(y, sr):
    if pw is not None:
        y = y.astype(np.float64)
        f0, t = pw.dio(y, sr)
        f0 = pw.stonemask(y, f0, t, sr)
    else:
        f0, voiced_flag, voiced_prob = librosa.pyin(
            y,
            sr=sr,
            fmin=librosa.note_to_hz("C2"),
            fmax=librosa.note_to_hz("C7"),
        )
        t = librosa.times_like(f0, sr=sr)
        f0 = np.nan_to_num(f0, nan=0.0)
    return t, f0




def extraer_pitch_detallado(ruta_audio):
    y, sr = librosa.load(ruta_audio, sr=None)

    t, f0 = _extraer_pitch_base(y, sr)

    mask_crudo = f0 > 0
    t_filtrado, f_filtrado = _filtrar_pitch(t, f0, y, sr, corregir_octavas=False)
    t_corregido, f_corregido = _corregir_octavas_por_registro(t_filtrado, f_filtrado)
    return {
        "t_crudo": t[mask_crudo],
        "f_crudo": f0[mask_crudo],
        "t_filtrado": t_filtrado,
        "f_filtrado": f_filtrado,
        "t_corregido": t_corregido,
        "f_corregido": f_corregido,
    }


def extraer_pitch(ruta_audio):
    y, sr = librosa.load(ruta_audio, sr=None)
    t, f0 = _extraer_pitch_base(y, sr)

    return _filtrar_pitch(t, f0, y, sr)

def hz_to_nota(f):
    if f <= 0:
        return None

    A4 = 440.0
    C0 = A4 * pow(2, -4.75)

    h = round(12 * np.log2(f / C0))
    octava = h // 12
    n = h % 12

    nombres = ['C', 'C#', 'D', 'D#', 'E', 'F',
               'F#', 'G', 'G#', 'A', 'A#', 'B']

    return f"{nombres[n]}{octava}"
