"""Fragmentos de referencia por energía y pitch, independientes de la toma."""
import numpy as np
import soundfile as sf

CONFIGURACION = dict(nivel_db=-15., paso_s=.02, pausa_s=.2,
                     pausa_interna_s=.05, limite_objetivo_s=15., minimo_hijo_s=1.)


def segmentar_referencia(ruta, tiempos, frecuencias):
    y, sr = sf.read(ruta, dtype='float32', always_2d=True)
    if not len(y):
        return []
    hop = round(sr * CONFIGURACION['paso_s'])
    n = int(np.ceil(len(y) / hop))
    power = np.mean(y.astype(float)**2, axis=1)
    widths = np.minimum(hop, len(y)-np.arange(n)*hop)
    rms = np.sqrt(np.pad(power, (0, n*hop-len(y))).reshape(n, hop).sum(axis=1)/widths)
    edges = np.r_[np.arange(n)*hop/sr, len(y)/sr]
    centers = (edges[:-1]+edges[1:])/2
    t, f = np.asarray(tiempos), np.asarray(frecuencias)
    good = np.isfinite(t) & np.isfinite(f) & (t >= 0) & (t <= edges[-1]) & (f > 0)
    t = np.sort(t[good])
    voiced = np.zeros(n, dtype=bool)
    if len(t):
        right = np.clip(np.searchsorted(t, centers), 0, len(t)-1)
        left = np.maximum(0, right-1)
        voiced = np.minimum(abs(centers-t[left]), abs(centers-t[right])) <= .025
    level = float(np.percentile(rms, 95))
    if level <= 1e-10:
        return []
    db = 20*np.log10(np.maximum(rms, 1e-12)/level)
    quiet = (db <= CONFIGURACION['nivel_db']) & ~voiced
    active = np.flatnonzero(~quiet)
    if not len(active):
        return []
    changes = np.diff(np.r_[False, quiet, False].astype(int))
    pauses = [(float(edges[a]), float(edges[b])) for a, b in zip(
        np.flatnonzero(changes == 1), np.flatnonzero(changes == -1))]
    start, stop = float(edges[active[0]]), float(edges[active[-1]+1])
    base = []
    for a, b in pauses:
        if a > start and b < stop and b-a >= CONFIGURACION['pausa_s']-1e-9:
            base.append((start, a))
            start = b
    base.append((start, stop))
    short = [(a, b) for a, b in pauses if b-a >= CONFIGURACION['pausa_interna_s']-1e-9]
    result = []
    pending = list(reversed(base))
    while pending:
        a, b = pending.pop()
        candidates = [(x, y) for x, y in short if x-a >= CONFIGURACION['minimo_hijo_s'] and
                      b-y >= CONFIGURACION['minimo_hijo_s']] if b-a > CONFIGURACION['limite_objetivo_s'] else []
        if candidates:
            x, y = min(candidates, key=lambda p: max(p[0]-a, b-p[1]))
            pending.extend([(y, b), (a, x)])
        else:
            result.append(dict(inicio_s=a, fin_s=b))
    return result


def preparar_segmentacion(cancion, tiempos, frecuencias):
    ruta = cancion.get('vocals')
    if not ruta:
        return None  # Compatibilidad explícita con entradas sin audio de referencia.
    return segmentar_referencia(ruta, tiempos, frecuencias)
