"""Evidencia musical determinista para una futura explicación en lenguaje natural.

No invoca modelos ni interpreta ausencia de pitch como ausencia de canto.
La comparación temporal es independiente del resumen DTW histórico.
"""
from dataclasses import asdict, dataclass
import math

import numpy as np
from audio.segmentacion import CONFIGURACION as CONFIG_SEGMENTACION

VERSION = '3.0.0'


@dataclass(frozen=True)
class ConfiguracionRetroalimentacion:
    paso_s: float = .02
    tolerancia_temporal_s: float = .025
    fragmento_s: float = 5.
    minimo_referencia_s: float = .5
    minimo_comparable_s: float = 1.
    cobertura_minima: float = .4
    cobertura_suficiente: float = .8
    tolerancia_afinacion_cents: float = 50.
    tolerancia_amplia_cents: float = 100.
    proporcion_cercana: float = .85
    proporcion_direccion: float = .7
    proporcion_desviacion_grande: float = .3
    proporcion_cercana_amplia: float = .7
    desviacion_grande_cents: float = 600.
    duracion_maxima_s: float = 14400.
    minimo_evento_s: float = .3

    def __post_init__(self):
        positive = [self.minimo_evento_s, self.paso_s, self.tolerancia_temporal_s, self.fragmento_s,
                    self.minimo_referencia_s, self.minimo_comparable_s,
                    self.tolerancia_afinacion_cents, self.tolerancia_amplia_cents,
                    self.desviacion_grande_cents, self.duracion_maxima_s]
        if any(not math.isfinite(x) or x <= 0 for x in positive):
            raise ValueError('Los tiempos y umbrales deben ser positivos y finitos.')
        if not self.paso_s <= self.fragmento_s <= self.duracion_maxima_s:
            raise ValueError('Orden de duraciones incorrecto.')
        if not 0 < self.cobertura_minima <= self.cobertura_suficiente <= 1:
            raise ValueError('Coberturas fuera de rango.')
        if not all(math.isfinite(x) and 0 < x <= 1 for x in [self.proporcion_cercana, self.proporcion_direccion,
                                                            self.proporcion_desviacion_grande, self.proporcion_cercana_amplia]):
            raise ValueError('Proporciones fuera de rango.')
        if not self.tolerancia_afinacion_cents < self.tolerancia_amplia_cents < self.desviacion_grande_cents:
            raise ValueError('Orden de tolerancias incorrecto.')


def _serie(tiempos, frecuencias, duracion):
    t, f = np.asarray(tiempos, dtype=float), np.asarray(frecuencias, dtype=float)
    if t.ndim != 1 or f.ndim != 1 or len(t) != len(f):
        raise ValueError('Tiempos y frecuencias deben ser vectores de igual longitud.')
    valid = np.isfinite(t) & np.isfinite(f) & (t >= 0) & (t <= duracion) & (f >= 0)
    discarded = int((~valid).sum())
    t, f = t[valid], f[valid]
    order = np.argsort(t, kind='stable')
    t, f = t[order], f[order]
    # En un tiempo duplicado conserva la última observación, incluidos ceros.
    keep = np.r_[t[:-1] != t[1:], True] if len(t) else np.array([], dtype=bool)
    duplicates = int(len(t) - keep.sum())
    return t[keep], f[keep], {'puntos_descartados': discarded, 'tiempos_duplicados': duplicates}


def _muestrear(t, f, centros, tolerancia):
    result = np.zeros(len(centros))
    if not len(t):
        return result
    right = np.clip(np.searchsorted(t, centros), 0, len(t) - 1)
    left = np.maximum(0, right - 1)
    nearest = np.where(abs(t[left] - centros) <= abs(t[right] - centros), left, right)
    valid = abs(t[nearest] - centros) <= tolerancia + 1e-10
    result[valid] = f[nearest[valid]]
    return result


def _porcentaje(n, d):
    return float(np.clip(100 * n / d, 0, 100)) if d > 0 else None


def _metricas(ref, usr, pesos, cfg):
    vr, vu = ref > 0, usr > 0
    both = vr & vu
    sr, su, sb = [float(pesos[m].sum()) for m in [vr, vu, both]]
    metrics = {
        'duracion_s': float(pesos.sum()),
        'referencia_detectada_s': sr, 'usuario_detectado_s': su,
        'comparable_s': sb, 'referencia_sin_deteccion_usuario_s': float(pesos[vr & ~vu].sum()),
        'usuario_sin_referencia_detectada_s': float(pesos[~vr & vu].sum()),
        'cobertura_comparable_pct': _porcentaje(sb, sr),
        'puntos_comparados': int(both.sum()),
        'error_absoluto_medio_cents': None, 'error_mediano_firmado_cents': None,
        'error_absoluto_p90_cents': None, 'porcentaje_dentro_tolerancia': None,
        'porcentaje_dentro_tolerancia_amplia': None,
        'porcentaje_agudo': None, 'porcentaje_grave': None,
        'porcentaje_desviacion_grande': None,
    }
    if both.any():
        errors = 1200 * (np.log2(usr[both]) - np.log2(ref[both]))
        w = pesos[both]
        def pct(mask):
            return _porcentaje(float(w[mask].sum()), sb)
        def quantile(values, q):
            order = np.argsort(values)
            i = np.searchsorted(np.cumsum(w[order]), q * sb)
            return float(values[order[min(i, len(order) - 1)]])
        metrics.update(
            error_absoluto_medio_cents=float(np.average(abs(errors), weights=w)),
            error_mediano_firmado_cents=quantile(errors, .5),
            error_absoluto_p90_cents=quantile(abs(errors), .9),
            porcentaje_dentro_tolerancia=pct(abs(errors) <= cfg.tolerancia_afinacion_cents + 1e-8),
            porcentaje_dentro_tolerancia_amplia=pct(abs(errors) <= cfg.tolerancia_amplia_cents + 1e-8),
            porcentaje_agudo=pct(errors > cfg.tolerancia_afinacion_cents + 1e-8),
            porcentaje_grave=pct(errors < -cfg.tolerancia_afinacion_cents - 1e-8),
            porcentaje_desviacion_grande=pct(abs(errors) >= cfg.desviacion_grande_cents),
        )
    return metrics


def _suficiencia(metrics, cfg):
    if metrics['referencia_detectada_s'] + 1e-8 < cfg.minimo_referencia_s:
        return 'referencia_insuficiente'
    coverage = metrics['cobertura_comparable_pct'] or 0.
    if metrics['comparable_s'] + 1e-8 < cfg.minimo_comparable_s or coverage + 1e-8 < 100 * cfg.cobertura_minima:
        return 'deteccion_insuficiente'
    return 'suficiente' if coverage + 1e-8 >= 100 * cfg.cobertura_suficiente and metrics['comparable_s'] + 1e-8 >= 2 else 'parcial'


ACCIONES = {
    'escuchar_y_repetir': 'Escuchar el fragmento de referencia y repetirlo por separado antes de volver a grabarlo.',
    'comparar_altura': 'Comparar la altura de las notas con la referencia y repetir el fragmento sin intentar imitar el timbre.',
    'revisar_deteccion': 'Escuchar la grabación y revisar el nivel del micrófono y el acompañamiento antes de repetir la evaluación.',
    'revisar_referencia': 'Revisar que la referencia preparada corresponda a la voz y al fragmento grabado.',
    'comprobar_correspondencia': 'Escuchar ambas pistas y comprobar referencia, sincronización y detección antes de atribuir la diferencia a la interpretación.',
}


def _hallazgo(fragmento, cfg):
    m, state = fragmento['metricas'], fragmento['suficiencia_evidencia']
    category, action = 'limitacion', None
    if state == 'referencia_insuficiente':
        kind, action = 'referencia_insuficiente', 'revisar_referencia'
    elif state == 'deteccion_insuficiente':
        kind, action = 'deteccion_insuficiente', 'revisar_deteccion'
    elif m['porcentaje_desviacion_grande'] >= 100 * cfg.proporcion_desviacion_grande:
        kind, action = 'discrepancia_grande', 'comprobar_correspondencia'
    elif state == 'parcial':
        # Describe la cobertura, pero no transforma el tramo no observado en juicio vocal.
        kind, action = 'cobertura_parcial', 'revisar_deteccion'
    elif m['porcentaje_dentro_tolerancia'] >= 100 * cfg.proporcion_cercana:
        kind, category = 'afinacion_cercana', 'fortaleza'
    elif m['porcentaje_agudo'] >= cfg.proporcion_direccion * (m['porcentaje_agudo'] + m['porcentaje_grave']) and m['comparable_s'] * m['porcentaje_agudo']/100 >= 1:
        kind, category, action = 'tendencia_aguda', 'aspecto_por_mejorar', 'comparar_altura'
    elif m['porcentaje_grave'] >= cfg.proporcion_direccion * (m['porcentaje_agudo'] + m['porcentaje_grave']) and m['comparable_s'] * m['porcentaje_grave']/100 >= 1:
        kind, category, action = 'tendencia_grave', 'aspecto_por_mejorar', 'comparar_altura'
    elif m['porcentaje_dentro_tolerancia_amplia'] < 100 * cfg.proporcion_cercana_amplia:
        kind, category, action = 'desviaciones_frecuentes', 'aspecto_por_mejorar', 'escuchar_y_repetir'
    else:
        return None
    return {
        'id': 'h_' + fragmento['id'], 'tipo': kind, 'categoria': category,
        'fragmento_id': fragmento['id'], 'inicio_s': fragmento['inicio_s'], 'fin_s': fragmento['fin_s'],
        'suficiencia_evidencia': state,
        'evidencia': {key: m[key] for key in [
            'referencia_detectada_s', 'comparable_s', 'cobertura_comparable_pct',
            'error_mediano_firmado_cents', 'error_absoluto_medio_cents',
            'porcentaje_dentro_tolerancia', 'porcentaje_dentro_tolerancia_amplia',
            'porcentaje_agudo', 'porcentaje_grave', 'porcentaje_desviacion_grande']},
        'accion_sugerida': {'id': action, 'descripcion': ACCIONES[action]} if action else None,
    }


LIMITACIONES = [
    'La referencia y la voz del usuario son estimaciones automáticas, no anotaciones de verdad terreno.',
    'La ausencia de pitch no demuestra silencio, una nota omitida ni un error del cantante.',
    'La comparación supone un mismo origen temporal; no se estimó ni corrigió latencia de reproducción o captura.',
    'No se evaluaron ritmo, respiración, dicción, técnica vocal, emoción, timbre ni salud vocal.',
    'Los límites son automáticos; no identifican estrofas, estribillos ni garantizan frases musicales completas.',
    'La suficiencia indica cantidad y cobertura de evidencia, no una probabilidad de que el detector acierte.',
    'Los porcentajes de afinación usan solo tiempo comparable; deben comunicarse junto con la cobertura.',
    'El análisis usa el pitch final de archivos, que puede contener correcciones de octava; no son resultados del filtro YIN en vivo.',
]


def _eventos(ref, usr, edges, widths, cfg, fid):
    """Rachas continuas: nunca se unen a través de huecos de detección."""
    both = (ref > 0) & (usr > 0)
    errors = np.zeros(len(ref))
    errors[both] = 1200 * (np.log2(usr[both])-np.log2(ref[both]))
    labels = np.full(len(ref), 'sin_referencia', dtype=object)
    labels[(ref > 0) & (usr <= 0)] = 'sin_deteccion_usuario'
    labels[both] = 'afinacion_cercana'
    labels[both & (errors > cfg.tolerancia_afinacion_cents+1e-8)] = 'desviacion_aguda'
    labels[both & (errors < -cfg.tolerancia_afinacion_cents-1e-8)] = 'desviacion_grave'
    labels[both & (abs(errors) >= cfg.desviacion_grande_cents)] = 'discrepancia_grande'
    bounds = np.r_[0, np.flatnonzero(labels[1:] != labels[:-1])+1, len(labels)]
    result = []
    for a, b in zip(bounds, bounds[1:]):
        if b == a or widths[a:b].sum() < cfg.minimo_evento_s-1e-9:
            continue
        kind = labels[a]
        category = ('fortaleza' if kind == 'afinacion_cercana' else
                    'aspecto_por_mejorar' if kind in ('desviacion_aguda', 'desviacion_grave') else 'limitacion')
        action = ('comparar_altura' if category == 'aspecto_por_mejorar' else
                  'comprobar_correspondencia' if kind == 'discrepancia_grande' else
                  'revisar_deteccion' if kind == 'sin_deteccion_usuario' else
                  'revisar_referencia' if kind == 'sin_referencia' else None)
        result.append(dict(id=f'e_{fid}_{len(result)+1:04d}', tipo=str(kind), categoria=category,
            inicio_s=float(edges[a]), fin_s=float(edges[b-1]+widths[b-1]),
            metricas=_metricas(ref[a:b], usr[a:b], widths[a:b], cfg),
            accion_sugerida={'id': action, 'descripcion': ACCIONES[action]} if action else None))
    return result


def generar_retroalimentacion(t_ref, f_ref, t_usr, f_usr, duracion_s, config=None, segmentos=None):
    """Genera un objeto JSON sin rutas, audio ni texto libre aportado por usuarios."""
    cfg = config or ConfiguracionRetroalimentacion()
    duration = float(duracion_s)
    if not math.isfinite(duration) or not 0 <= duration <= cfg.duracion_maxima_s:
        raise ValueError('Duración inválida o superior al máximo admitido.')
    if duration / cfg.paso_s > 2_000_000:
        raise ValueError('Resolución temporal excesiva para esta duración.')
    tr, fr, audit_ref = _serie(t_ref, f_ref, duration)
    tu, fu, audit_usr = _serie(t_usr, f_usr, duration)
    fragments, all_ref, all_usr, all_weights = [], [], [], []
    bounds = []
    if segmentos is None:
        bounds = [(float(s), min(duration, float(s)+cfg.fragmento_s)) for s in np.arange(0, duration, cfg.fragmento_s)]
    else:
        previous = 0.
        for s in segmentos:
            a, b = float(s['inicio_s']), float(s['fin_s'])
            if not math.isfinite(a) or not math.isfinite(b) or a < previous or b <= a:
                raise ValueError('Segmentos inválidos, desordenados o superpuestos.')
            previous = b
            if a < duration:
                bounds.append((a, min(b, duration)))
    # Construye celdas dentro de cada fragmento para que los segundos nunca excedan sus límites.
    for i, (start, end) in enumerate(bounds):
        edges = np.arange(start, end, cfg.paso_s)
        widths = np.minimum(cfg.paso_s, end - edges)
        centers = edges + widths / 2
        ref = _muestrear(tr, fr, centers, cfg.tolerancia_temporal_s)
        usr = _muestrear(tu, fu, centers, cfg.tolerancia_temporal_s)
        metrics = _metricas(ref, usr, widths, cfg)
        fid = f'f{i+1:04d}'
        fragments.append({'id': fid, 'inicio_s': float(start), 'fin_s': end,
                          'eventos': _eventos(ref, usr, edges, widths, cfg, fid),
                          'metricas': metrics, 'suficiencia_evidencia': _suficiencia(metrics, cfg)})
        all_ref.append(ref); all_usr.append(usr); all_weights.append(widths)
    def join(parts):
        return np.concatenate(parts) if parts else np.array([])
    total = _metricas(join(all_ref), join(all_usr), join(all_weights), cfg)
    findings = [h for fragment in fragments if (h := _hallazgo(fragment, cfg)) is not None]
    strengths = [h for h in findings if h['categoria'] == 'fortaleza']
    issues = [h for h in findings if h['categoria'] == 'aspecto_por_mejorar']
    limits = [h for h in findings if h['categoria'] == 'limitacion']
    strengths.sort(key=lambda h: (-h['evidencia']['porcentaje_dentro_tolerancia'], -h['evidencia']['comparable_s'], h['inicio_s']))
    issues.sort(key=lambda h: (-h['evidencia']['comparable_s'] * (1-h['evidencia']['porcentaje_dentro_tolerancia']/100), h['inicio_s']))
    limits.sort(key=lambda h: (h['tipo'] != 'discrepancia_grande', h['inicio_s']))
    return {
        'version': VERSION,
        'metodo': {'id': 'comparacion_temporal_acotada', 'dtw': False,
                   'segmentacion': {'tipo': 'pausas_referencia' if segmentos is not None else 'ventanas_fijas_respaldo',
                                    'configuracion': dict(CONFIG_SEGMENTACION) if segmentos is not None else {},
                                    'duracion_grabacion_s': duration,
                                    'duracion_fuera_fragmentos_s': max(0., duration-total['duracion_s'])},
                   'sincronizacion': 'no_verificada',
                   'compensacion_temporal_s': 0., 'extremos_no_capturados_s': 0.,
                   'alineacion': {'modo': 'automatico', 'estado': 'pendiente', 'desfase_s': 0.,
                                 'motivo': 'Compensación temporal todavía no calculada.'},
                   'origen': 'pitch_final_archivos', 'latencia_estimada_s': None,
                   'denominador_afinacion': 'tiempo con pitch positivo en referencia y usuario',
                   'denominador_cobertura': 'tiempo con pitch positivo en la referencia',
                   'configuracion': asdict(cfg), 'umbrales_hallazgos': 'reglas heurísticas de producto, no validadas como puntuación global'},
        'calidad': {'suficiencia_evidencia': _suficiencia(total, cfg),
                    'entrada_referencia': audit_ref, 'entrada_usuario': audit_usr,
                    'limitaciones': list(LIMITACIONES)},
        'resumen_metricas': total, 'fragmentos': fragments, 'hallazgos': findings,
        'seleccion': {'fortalezas': [h['id'] for h in strengths[:2]],
                     'aspectos_por_mejorar': [h['id'] for h in issues[:3]],
                     'limitaciones': [h['id'] for h in limits[:3]]},
    }


def preparar_contexto_modelo(retroalimentacion, fragmento_id=None):
    """Contrato compacto para el futuro LLM; no envía ninguna solicitud externa."""
    if retroalimentacion.get('version') != VERSION:
        raise ValueError('Versión de retroalimentación no compatible.')
    ids = {i for values in retroalimentacion['seleccion'].values() for i in values}
    selected = [h for h in retroalimentacion['hallazgos'] if h['id'] in ids]
    fragments = retroalimentacion['fragmentos']
    if fragmento_id is not None:
        fragments = [f for f in fragments if f['id'] == fragmento_id]
        if not fragments:
            raise ValueError('Fragmento no encontrado.')
        selected = [h for h in retroalimentacion['hallazgos'] if h['fragmento_id'] == fragmento_id]
    selection = {category: [h['id'] for h in selected if h['categoria'] == kind] for category, kind in [
        ('fortalezas', 'fortaleza'), ('aspectos_por_mejorar', 'aspecto_por_mejorar'), ('limitaciones', 'limitacion')]}
    details = []
    for f in fragments:
        # Tres eventos por categoría: duración primero, orden temporal para redactar.
        chosen = []
        for category in ['fortaleza', 'aspecto_por_mejorar', 'limitacion']:
            candidates = [e for e in f['eventos'] if e['categoria'] == category]
            chosen.extend(sorted(candidates, key=lambda e: (-(e['fin_s']-e['inicio_s']), e['inicio_s']))[:3])
        details.append({k: v for k, v in f.items() if k != 'eventos'} | {
            'eventos_seleccionados': sorted(chosen, key=lambda e: e['inicio_s']),
            'eventos_no_incluidos': len(f['eventos'])-len(chosen)})
    return {
        'version': VERSION, 'idioma': 'es',
        **({'musical': retroalimentacion['musical']} if 'musical' in retroalimentacion else {}),
        'metodo': retroalimentacion['metodo'], 'calidad': retroalimentacion['calidad'],
        'resumen_metricas': retroalimentacion['resumen_metricas'],
        'hallazgos_seleccionados': selected, 'seleccion': selection,
        'hallazgos_totales': len(retroalimentacion['hallazgos']),
        'hallazgos_no_incluidos': len(retroalimentacion['hallazgos']) - len(selected),
        'analisis_fragmentos': details,
        'instrucciones_redaccion': [
            'Redactar solo a partir de estos datos; no recalcular ni inventar métricas, tiempos o hallazgos.',
            'Vincular cada fortaleza, aspecto y práctica a uno o más IDs de hallazgo existentes.',
            'Mantener las limitaciones y distinguir detección insuficiente de un fallo de interpretación.',
            'Usar los tiempos de grabación; no inventar nombres de secciones ni atribuir causas técnicas o fisiológicas.',
            'Si la evidencia global es insuficiente, evitar una valoración global y explicar qué sí pudo observarse localmente.',
            'No convertir estos porcentajes en una nota global de calidad ni afirmar una mejora respecto de otras tomas.',
            'Para cada fragmento describir aciertos, aspectos a revisar y práctica solo si hay evidencia; citar IDs de evento o hallazgo.',
            'Consultar el estado de sincronización del método; la compensación no distingue latencia del equipo de retraso global al cantar.',
            'Los eventos describen solo intervalos continuos observados; los eventos omitidos o breves no son necesariamente correctos.',
            'El resumen global cubre únicamente los fragmentos analizados, no las pausas excluidas. En consulta de un fragmento, centrar la respuesta en analisis_fragmentos.',
        ],
        'salida_esperada': {
            'resumen': 'texto breve con alcance y hallazgo principal',
            'fortalezas': 'lista de {hallazgo_ids, texto}',
            'aspectos_por_mejorar': 'lista de {hallazgo_ids, texto}',
            'practica_sugerida': 'lista de {hallazgo_ids, accion_id, texto}',
            'alcance_analisis': 'texto con cobertura y limitaciones relevantes',
            'por_fragmento': 'lista de {fragmento_id, resumen, aciertos, aspectos_a_revisar, practica_sugerida, evidencia_ids, limitaciones}; no rellenar aciertos o problemas inexistentes',
        },
    }
