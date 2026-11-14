import numpy as np
from dtw import dtw

from audio.metricas import calcular_metricas_errores, hz_to_cents

def comparar(f_ref, f_usr):
    if len(f_ref) == 0 or len(f_usr) == 0:
        return {
            "error_prom": None,
            "desviacion": None,
            "tendencia": "sin datos",
            "mensaje": "No se detecto pitch suficiente para comparar.",
        }

    alignment = dtw(f_ref, f_usr, keep_internals=True)

    errors = []

    for i, j in zip(alignment.index1, alignment.index2):
        if f_ref[i] > 0 and f_usr[j] > 0:
            error = hz_to_cents(f_usr[j], f_ref[i])
            if abs(error) < 1000:
                errors.append(error)

    errors = np.array(errors)
    return calcular_metricas_errores(errors)
