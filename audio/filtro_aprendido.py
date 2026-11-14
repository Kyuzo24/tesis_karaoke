"""Aceptación de candidatos YIN con un árbol exportado a JSON.

No requiere scikit-learn en ejecución. El entrenamiento y la validación están
documentados en output/filtro_aprendido/informe.md.
"""
from functools import lru_cache
import json
from pathlib import Path

import numpy as np

CARACTERISTICAS = [
    'periodicidad', 'energia_relativa', 'log10_rms',
    'periodicidad_anterior', 'periodicidad_siguiente',
    'salto_min_semitonos', 'salto_max_semitonos',
    'periodicidad_media', 'fraccion_periodica',
]
RUTA_MODELO = Path(__file__).with_name('filtro_pitch.json')


def caracteristicas(f0, periodicidad, energia):
    """Describe candidatos con las muestras ya disponibles en la ventana."""
    f0 = np.asarray(f0, dtype=float)
    p = np.asarray(periodicidad, dtype=float)
    e = np.asarray(energia, dtype=float)
    if not len(f0):
        return np.empty((0, len(CARACTERISTICAS)), dtype=np.float32)
    anterior = np.r_[p[0], p[:-1]]
    siguiente = np.r_[p[1:], p[-1]]
    midi = 69 + 12 * np.log2(np.maximum(f0, 1) / 440)
    salto_a = np.minimum(24, abs(midi - np.r_[midi[0], midi[:-1]]))
    salto_s = np.minimum(24, abs(midi - np.r_[midi[1:], midi[-1]]))
    return np.column_stack([
        p, e / max(float(e.max()), 1e-12), np.log10(np.maximum(e, 1e-8)),
        anterior, siguiente, np.minimum(salto_a, salto_s),
        np.maximum(salto_a, salto_s), np.full(len(f0), np.mean(p)),
        np.full(len(f0), np.mean(p >= .7)),
    ]).astype(np.float32)


@lru_cache(maxsize=1)
def _cargar_modelo():
    try:
        data = json.loads(RUTA_MODELO.read_text(encoding='utf-8'))
        if data['features'] != CARACTERISTICAS:
            return None
        tree = data['tree']
        result = {k: np.asarray(tree[k], dtype=int if k in ['feature', 'left', 'right'] else float)
                  for k in ['feature', 'threshold', 'left', 'right', 'probability']}
        n = len(result['feature'])
        if not n or any(a.shape != (n,) or not np.isfinite(a).all() for a in result.values()):
            return None
        branches = result['feature'] >= 0
        if np.any(result['feature'][branches] >= len(CARACTERISTICAS)):
            return None
        # Los hijos posteriores al padre impiden ciclos en un JSON dañado.
        for key in ['left', 'right']:
            children = result[key][branches]
            if np.any(children <= np.flatnonzero(branches)) or np.any(children >= n):
                return None
        cutoff, floor = float(data['cutoff']), float(data['periodicity_floor'])
        if not (0 <= cutoff <= 1 and 0 <= floor <= 1):
            return None
        result.update(cutoff=cutoff, floor=floor)
        return result
    except (OSError, ValueError, KeyError, TypeError):
        return None


def aceptar_candidatos(f0, periodicidad, energia):
    """Devuelve None si no hay modelo válido para conservar el filtro anterior."""
    model = _cargar_modelo()
    if model is None:
        return None
    x = caracteristicas(f0, periodicidad, energia)
    nodes = np.zeros(len(x), dtype=int)
    feature = model['feature']
    while np.any(feature[nodes] >= 0):
        ids = np.flatnonzero(feature[nodes] >= 0)
        current = nodes[ids]
        nodes[ids] = np.where(
            x[ids, feature[current]] <= model['threshold'][current],
            model['left'][current], model['right'][current],
        )
    return ((model['probability'][nodes] >= model['cutoff'])
            & (np.asarray(periodicidad) >= model['floor']))
