import numpy as np


def hz_to_midi(frecuencias):
    frecuencias = np.asarray(frecuencias, dtype=float)
    midi = np.full_like(frecuencias, np.nan, dtype=float)
    mask = frecuencias > 0
    midi[mask] = 69 + 12 * np.log2(frecuencias[mask] / 440.0)
    return midi


def hz_to_cents(f_usuario, f_referencia):
    f_usuario = np.asarray(f_usuario, dtype=float)
    f_referencia = np.asarray(f_referencia, dtype=float)
    return 1200 * np.log2(f_usuario / f_referencia)


def calcular_metricas_errores(errores_cents):
    errores = np.asarray(errores_cents, dtype=float)
    errores = errores[~np.isnan(errores)]

    if len(errores) == 0:
        return {
            "error_prom": None,
            "desviacion": None,
            "tendencia": "sin datos",
            "porcentaje_50": None,
            "porcentaje_100": None,
            "puntos_comparados": 0,
            "mensaje": "No quedaron puntos comparables despues del alineamiento.",
        }

    abs_errors = np.abs(errores)
    media = float(np.mean(errores))

    return {
        "error_prom": float(np.mean(abs_errors)),
        "desviacion": float(np.std(errores)),
        "tendencia": tendencia_desde_media(media),
        "porcentaje_50": porcentaje_dentro_de_umbral(abs_errors, 50),
        "porcentaje_100": porcentaje_dentro_de_umbral(abs_errors, 100),
        "puntos_comparados": int(len(errores)),
        "error_medio_firmado": media,
    }


def porcentaje_dentro_de_umbral(abs_errors, umbral):
    if len(abs_errors) == 0:
        return None
    return float(np.mean(abs_errors <= umbral) * 100)


def tendencia_desde_media(media_cents, tolerancia=10):
    if abs(media_cents) <= tolerancia:
        return "estable"
    return "agudo" if media_cents > 0 else "grave"
