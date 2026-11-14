"""Compensación global automática y revisión manual; no modifica el audio."""
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile
import threading
import numpy as np

VERSION = '2.0.0'
CRITERIOS = dict(rango_s=2., paso_s=.02, refinamiento_s=.005, minimo_comparable_s=5.,
                mejora_minima=.03, margen_alternativa=.015, margen_relativo=.1, separacion_alternativa_s=.12,
                acuerdo_minimo=2/3, tolerancia_acuerdo_s=.06, minimo_ventanas=2)
_lock = threading.RLock()


def ruta_ajuste(ruta_audio):
    p = Path(ruta_audio)
    return p.with_name(p.stem+'_alineacion.json')


def leer_estado(ruta_audio):
    try:
        state = json.loads(ruta_ajuste(ruta_audio).read_text(encoding='utf-8'))
        value = float(state['desfase_s'])
        if not math.isfinite(value) or abs(value) > 2:
            raise ValueError('Desfase inválido')
        mode = state.get('modo', 'manual' if state.get('origen') == 'ajuste_usuario' else 'automatico')
        if mode not in ('manual', 'automatico', 'desactivado'):
            raise ValueError('Modo inválido')
        state.setdefault('estado', mode if mode != 'automatico' else 'pendiente')
        state.setdefault('motivo', 'Ajuste manual conservado para esta toma.' if mode == 'manual' else 'Compensación temporal por revisar.')
        return dict(state, modo=mode, desfase_s=0. if mode == 'desactivado' else value)
    except (OSError, ValueError, KeyError, TypeError):
        return dict(modo='automatico', desfase_s=0., estado='pendiente')


def leer_ajuste(ruta_audio):
    return leer_estado(ruta_audio)['desfase_s']


def _guardar(ruta_audio, state):
    path = ruta_ajuste(ruta_audio)
    # Un archivo temporal único evita colisiones entre vistas/procesos.
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                     prefix=path.stem, suffix='.tmp', delete=False) as stream:
        temp = Path(stream.name)
        json.dump(state, stream, ensure_ascii=False, allow_nan=False)
    try:
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def guardar_ajuste(ruta_audio, milisegundos=0, modo='manual'):
    if modo not in ('manual', 'automatico', 'desactivado'):
        raise ValueError('Modo de sincronización inválido.')
    value = float(milisegundos)/1000
    if not math.isfinite(value) or abs(value) > 2:
        raise ValueError('El desfase debe estar entre −2000 y 2000 ms.')
    if modo != 'manual':
        value = 0.
    state = dict(version=VERSION, modo=modo, desfase_s=value,
                 estado='pendiente' if modo == 'automatico' else modo,
                 origen='ajuste_usuario' if modo == 'manual' else modo,
                 motivo={'manual': 'Ajuste manual conservado para esta toma.',
                         'automatico': 'La compensación se calculará automáticamente.',
                         'desactivado': 'Compensación temporal desactivada por el usuario.'}[modo])
    with _lock:
        _guardar(ruta_audio, state)
    return value


def sugerir_desfase(t_ref, f_ref, t_usr, f_usr):
    """Estima con denominador fijo, alternativas y ventanas independientes.

    Los umbrales son heurísticos. No mide la latencia instrumental ni distingue
    un retraso global del cantante de un retraso de captura.
    """
    from audio.retroalimentacion import _muestrear, _serie
    result = dict(disponible=False, desfase_ms=0, estado='insuficiente',
                  motivo='No hay curvas suficientes para estimar un desfase.',
                  criterios=dict(CRITERIOS))
    if not len(t_ref) or not len(t_usr):
        return result
    finite_times = np.asarray(t_usr, dtype=float)
    finite_times = finite_times[np.isfinite(finite_times)]
    if not len(finite_times):
        return result
    duration = min(14400., max(0., float(finite_times.max())))
    tr, fr, _ = _serie(t_ref, f_ref, min(14400., duration+2))
    tu, fu, _ = _serie(t_usr, f_usr, duration)
    # Mismo soporte y denominador para TODOS los candidatos, incluidos los bordes.
    step = max(.02, duration/60000)
    times = np.arange(0., duration, step)
    ref = _muestrear(tr, fr, times, .025)
    voiced = ref > 0
    ref_count = int(voiced.sum())
    if ref_count*step < 5:
        return dict(result, motivo='Menos de cinco segundos de referencia detectada.')

    def cambios(values):
        # Cambios separados al menos 100 ms: evita contar vibrato/jitter como notas.
        sampled = values[::max(1, round(.1/step))]
        both = (sampled[:-1] > 0) & (sampled[1:] > 0)
        return int((abs(1200*np.log2(sampled[1:][both]/sampled[:-1][both])) >= 80).sum())

    if cambios(ref) < 6:
        return dict(result, motivo='No hay suficientes cambios de notas para una estimación fiable.')
    # Ventanas no superpuestas sobre las partes con referencia; hasta nueve.
    a, b = times[voiced][0], times[voiced][-1]+step
    n = min(9, max(2, int((b-a)/5)))
    edges = np.linspace(a, b, n+1)
    windows = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        mask = (times >= lo) & (times < hi)
        if (voiced & mask).sum()*step >= 2 and cambios(ref[mask]) >= 3:
            windows.append(mask)
    if len(windows) < 2:
        return dict(result, motivo='No hay dos ventanas informativas para verificar un desfase global.')

    def evaluate(lag, with_windows=False):
        usr = _muestrear(tu-lag, fu, times, .025)
        both = voiced & (usr > 0)
        values = np.zeros(len(times))
        values[both] = np.clip(1-abs(1200*np.log2(usr[both]/ref[both]))/300, 0, 1)
        score = float(values.sum()/ref_count)
        if with_windows:
            return score, [float(values[w].sum()/(voiced & w).sum()) for w in windows], float(both.sum()*step)
        return score

    offsets = np.arange(-100, 101)*.02
    evaluated = [evaluate(lag, True) for lag in offsets]
    scores = np.array([v[0] for v in evaluated])
    best = int(np.argmax(scores))
    coarse = offsets[best]
    fine = np.arange(max(-2., coarse-.02), min(2., coarse+.02)+.0025, .005)
    fine_scores = np.array([evaluate(lag) for lag in fine])
    # En empates no inventa precisión: conserva el candidato de la búsqueda gruesa.
    tied = np.flatnonzero(fine_scores >= fine_scores.max()-1e-9)
    lag = float(fine[tied[np.argmin(abs(fine[tied]-coarse))]])
    score, _, comparable = evaluate(lag, True)
    gain = score-scores[100]
    alternative = float(scores[abs(offsets-lag) >= .12-1e-9].max())
    window_scores = np.array([v[1] for v in evaluated]).T
    window_lags = [float(offsets[int(np.argmax(s))]) for s in window_scores]
    agreement = sum(abs(w-lag) <= .06+1e-9 for w in window_lags)/len(windows)
    result.update(desfase_ms=round(lag*1000), mejora_objetivo=float(gain),
                  objetivo_sin_ajuste=float(scores[100]), objetivo_ajustado=score,
                  margen_alternativa=score-alternative, comparable_s=comparable,
                  ventanas_ms=[round(w*1000) for w in window_lags], acuerdo_ventanas=agreement)
    if abs(lag) >= 1.96:
        return dict(result, estado='limite', motivo='El candidato alcanza el límite de búsqueda; no se aplicó.')
    if comparable < 5:
        return dict(result, motivo='Menos de cinco segundos comparables en el mejor candidato.')
    if score-alternative < max(.015, .1*gain):
        return dict(result, estado='ambiguo', motivo='Hay desplazamientos alternativos con coincidencias similares; se conserva cero.')
    if agreement < 2/3:
        return dict(result, estado='inconsistente', motivo='Las partes de la toma no respaldan un mismo desfase global; se conserva cero.')
    if gain < .03:
        return dict(result, estado='sin_cambio', motivo='El desplazamiento no mejora suficientemente la comparación; se conserva cero.')
    return dict(result, disponible=True, estado='aplicado', motivo='Compensación global automática respaldada por varias partes de la toma; no es una medición de latencia del dispositivo.')


def resolver_ajuste(ruta_audio, t_ref, f_ref, t_usr, f_usr):
    with _lock:
        state = leer_estado(ruta_audio)
        if state['modo'] != 'automatico':
            return state
        digest = hashlib.sha256(VERSION.encode())
        for values in (t_ref, f_ref, t_usr, f_usr):
            array = np.asarray(values, dtype='<f8')
            digest.update(str(array.shape).encode()); digest.update(array.tobytes())
        fingerprint = digest.hexdigest()
        if state.get('huella') == fingerprint and state.get('version') == VERSION:
            return state
        estimate = sugerir_desfase(t_ref, f_ref, t_usr, f_usr)
        state = dict(version=VERSION, modo='automatico', origen='automatico', huella=fingerprint,
                     desfase_s=estimate['desfase_ms']/1000 if estimate['disponible'] else 0.,
                     estado=estimate['estado'], motivo=estimate['motivo'], diagnostico=estimate)
        if Path(ruta_audio).is_file():
            try:
                _guardar(ruta_audio, state)
            except OSError:
                state['motivo'] += ' No pudo guardarse el ajuste; se utiliza en esta consulta.'
        return state


def analizar_alineado(tr, fr, tu, fu, duracion, segmentos, estado):
    from audio.retroalimentacion import generar_retroalimentacion
    lag = estado['desfase_s']
    lower, upper = max(0., -lag), min(duracion, duracion-lag)
    if segmentos is None:
        segmentos_base = [dict(inicio_s=float(a), fin_s=min(float(a)+5, duracion)) for a in np.arange(0, duracion, 5)]
    else:
        segmentos_base = segmentos
    clipped = [dict(inicio_s=max(s['inicio_s'], lower), fin_s=min(s['fin_s'], upper))
               for s in segmentos_base if max(s['inicio_s'], lower) < min(s['fin_s'], upper)]
    report = generar_retroalimentacion(tr, fr, np.asarray(tu)-lag, fu, duracion, segmentos=clipped)
    if segmentos is None:
        report['metodo']['segmentacion'].update(tipo='ventanas_fijas_respaldo', configuracion={})
    sync = ('ajuste_manual' if estado['modo'] == 'manual' else
            'desactivada' if estado['modo'] == 'desactivado' else
            'ajuste_automatico' if estado['estado'] == 'aplicado' else 'automatico_no_concluyente')
    report['metodo'].update(sincronizacion=sync, compensacion_temporal_s=lag,
                           latencia_estimada_s=None, alineacion=estado,
                           extremos_no_capturados_s=max(0., lower)+max(0., duracion-upper))
    report['calidad']['limitaciones'][2] = (
        f"Compensación temporal {dict(automatico='automática', manual='manual', desactivado='desactivada')[estado['modo']]}: {round(lag*1000)} ms. "
        + estado.get('motivo', 'Ajuste elegido por el usuario.')
        + ' No distingue retraso del equipo de retraso global al cantar ni evalúa ritmo.')
    from audio.notas_musicales import analizar_notas
    musical, fragments = analizar_notas(tr, fr, np.asarray(tu)-lag, fu, report['fragmentos'])
    report['musical'] = musical
    for fragment in report['fragmentos']:
        fragment['musical'] = fragments[fragment['id']]
    return report
