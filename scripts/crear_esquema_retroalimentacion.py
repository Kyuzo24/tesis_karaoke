"""Genera el contrato JSON Schema de la retroalimentación y su contexto."""
import json
from pathlib import Path
import sys
from dataclasses import asdict
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from audio.retroalimentacion import ConfiguracionRetroalimentacion, VERSION, ACCIONES


def obj(props):
    return {'type': 'object', 'properties': props, 'required': list(props), 'additionalProperties': False}


def arr(item, **kwargs):
    return {'type': 'array', 'items': item, **kwargs}


def ref(name):
    return {'$ref': '#/$defs/' + name}


def main():
    number = {'type': 'number', 'minimum': 0}
    nullable = {'type': ['number', 'null']}
    pct = {**nullable, 'minimum': 0, 'maximum': 100}
    text = {'type': 'string'}
    integer = {'type': 'integer', 'minimum': 0}
    evidence_state = {'enum': ['referencia_insuficiente', 'deteccion_insuficiente', 'parcial', 'suficiente']}
    metrics = {key: number for key in ['duracion_s', 'referencia_detectada_s', 'usuario_detectado_s', 'comparable_s',
                                     'referencia_sin_deteccion_usuario_s', 'usuario_sin_referencia_detectada_s']}
    metrics.update({key: pct for key in ['cobertura_comparable_pct', 'porcentaje_dentro_tolerancia',
                                       'porcentaje_dentro_tolerancia_amplia', 'porcentaje_agudo',
                                       'porcentaje_grave', 'porcentaje_desviacion_grande']})
    metrics.update(puntos_comparados=integer, error_mediano_firmado_cents=nullable,
                   error_absoluto_medio_cents={**nullable, 'minimum': 0},
                   error_absoluto_p90_cents={**nullable, 'minimum': 0})
    evkeys = ['referencia_detectada_s', 'comparable_s', 'cobertura_comparable_pct', 'error_mediano_firmado_cents',
              'error_absoluto_medio_cents', 'porcentaje_dentro_tolerancia', 'porcentaje_dentro_tolerancia_amplia',
              'porcentaje_agudo', 'porcentaje_grave', 'porcentaje_desviacion_grande']
    interval = {'inicio_s': number, 'fin_s': number}
    fid = {'type': 'string', 'pattern': '^f[0-9]{4,}$'}
    hid = {'type': 'string', 'pattern': '^h_f[0-9]{4,}$'}
    defs = {
        'metricas': obj(metrics),
        'metodo': obj({'id': {'const': 'comparacion_temporal_acotada'}, 'dtw': {'const': False},
                       'origen': {'const': 'pitch_final_archivos'}, 'latencia_estimada_s': {'type': 'null'},
                       'denominador_afinacion': text, 'denominador_cobertura': text,
                       'configuracion': obj({key: number for key in asdict(ConfiguracionRetroalimentacion())}),
                       'umbrales_hallazgos': text}),
        'calidad': obj({'suficiencia_evidencia': evidence_state,
                        'entrada_referencia': obj({'puntos_descartados': integer, 'tiempos_duplicados': integer}),
                        'entrada_usuario': obj({'puntos_descartados': integer, 'tiempos_duplicados': integer}),
                        'limitaciones': arr(text)}),
        'fragmento': obj({'id': fid, **interval, 'metricas': ref('metricas'), 'suficiencia_evidencia': evidence_state}),
        'hallazgo': obj({'id': hid, 'tipo': {'enum': ['referencia_insuficiente', 'deteccion_insuficiente',
                           'discrepancia_grande', 'cobertura_parcial', 'afinacion_cercana', 'tendencia_aguda',
                           'tendencia_grave', 'desviaciones_frecuentes']},
                         'categoria': {'enum': ['limitacion', 'fortaleza', 'aspecto_por_mejorar']},
                         'fragmento_id': fid, **interval, 'suficiencia_evidencia': evidence_state,
                         'evidencia': obj({key: metrics[key] for key in evkeys}),
                         'accion_sugerida': {'anyOf': [{'type': 'null'}, obj({'id': {'enum': list(ACCIONES)}, 'descripcion': text})]}}),
        'seleccion': obj({'fortalezas': arr(hid, maxItems=2, uniqueItems=True),
                          'aspectos_por_mejorar': arr(hid, maxItems=3, uniqueItems=True),
                          'limitaciones': arr(hid, maxItems=3, uniqueItems=True)}),
    }
    defs['evento'] = obj({'id': {'type': 'string', 'pattern': '^e_f[0-9]{4,}_[0-9]{4,}$'},
        'tipo': {'enum': ['afinacion_cercana', 'desviacion_aguda', 'desviacion_grave',
                         'discrepancia_grande', 'sin_referencia', 'sin_deteccion_usuario']},
        'categoria': {'enum': ['fortaleza', 'aspecto_por_mejorar', 'limitacion']},
        **interval, 'metricas': ref('metricas'),
        'accion_sugerida': defs['hallazgo']['properties']['accion_sugerida']})
    defs['fragmento'] = obj({**defs['fragmento']['properties'], 'eventos': arr(ref('evento'))})
    from audio.segmentacion import CONFIGURACION
    defs['metodo'] = obj({**defs['metodo']['properties'],
        'latencia_estimada_s': {'type': ['number', 'null'], 'minimum': -2, 'maximum': 2},
        'sincronizacion': {'enum': ['no_verificada', 'ajuste_manual', 'ajuste_automatico', 'automatico_no_concluyente', 'desactivada']},
        'compensacion_temporal_s': {'type': 'number', 'minimum': -2, 'maximum': 2},
        'extremos_no_capturados_s': number,
        'alineacion': {'type': 'object'},
        'segmentacion': obj({'tipo': {'enum': ['pausas_referencia', 'ventanas_fijas_respaldo']},
            'configuracion': {'oneOf': [obj({}), obj({k: {'type': 'number'} for k in CONFIGURACION})]},
            'duracion_grabacion_s': number, 'duracion_fuera_fragmentos_s': number})})
    defs['fragmento_contexto'] = obj({k: v for k, v in defs['fragmento']['properties'].items() if k != 'eventos'} | {
        'eventos_seleccionados': arr(ref('evento'), maxItems=9), 'eventos_no_incluidos': integer})
    common = {'version': {'const': VERSION}, 'metodo': ref('metodo'), 'calidad': ref('calidad'),
              'resumen_metricas': ref('metricas'), 'seleccion': ref('seleccion')}
    defs['retroalimentacion'] = obj({**common, 'fragmentos': arr(ref('fragmento')), 'hallazgos': arr(ref('hallazgo'))})
    defs['contexto_modelo'] = obj({**common, 'idioma': {'const': 'es'},
                                 'hallazgos_seleccionados': arr(ref('hallazgo'), maxItems=8),
                                 'hallazgos_totales': integer, 'hallazgos_no_incluidos': integer,
                                 'analisis_fragmentos': arr(ref('fragmento_contexto')),
                                 'instrucciones_redaccion': arr(text),
                                 'salida_esperada': obj({key: text for key in ['resumen', 'fortalezas', 'aspectos_por_mejorar',
                                                                            'practica_sugerida', 'alcance_analisis', 'por_fragmento']})})
    note = obj({'id': text, 'inicio_s': number, 'fin_s': number, 'midi': {'type':'number'},
                'dispersion_cents': number, 'nucleo_s': number})
    extra = obj({**note['properties'], 'fragmento_id': fid})
    pair = obj({'id': text, 'fragmento_id': fid, 'referencia': note,
                'usuario': {'anyOf':[{'type':'null'},note]}, 'error_cents': nullable,
                'diferencia_inicio_ms': nullable, 'diferencia_duracion_ms': nullable,
                'clase': {'enum':['sin_correspondencia','cerca','margen','fuera']}})
    musical_metrics = obj({**{k: integer for k in ['notas_referencia','notas_comparadas','notas_sin_correspondencia']},
                           **{k:pct for k in ['cobertura_notas_pct','porcentaje_50','porcentaje_100']},
                           'error_mediano_cents':nullable,'diferencia_inicio_mediana_ms':nullable})
    musical_fragment = obj({'metricas':musical_metrics,'notas':arr(pair),'usuario_sin_correspondencia':arr(extra)})
    from audio.notas_musicales import PARAMETROS, VERSION as VERSION_NOTAS
    musical = obj({**musical_fragment['properties'],'version':{'const':VERSION_NOTAS},
                   'parametros':obj({k:number for k in PARAMETROS})})
    for name in ['fragmento','fragmento_contexto']:
        defs[name]['properties']['musical'] = musical_fragment
    for name in ['retroalimentacion','contexto_modelo']:
        defs[name]['properties']['musical'] = musical
    schema = {'$schema': 'https://json-schema.org/draft/2020-12/schema',
              'title': 'Retroalimentación musical ' + VERSION, 'oneOf': [ref('retroalimentacion'), ref('contexto_modelo')], '$defs': defs}
    (ROOT/'docs/retroalimentacion.schema.json').write_text(json.dumps(schema, indent=2, ensure_ascii=False), encoding='utf-8')


if __name__ == '__main__':
    main()
