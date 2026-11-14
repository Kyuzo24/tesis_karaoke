"""Retroalimentación local determinista, con evidencia y reglas versionadas."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import threading
from audio.tomas import obtener_contexto_retroalimentacion, _buscar_toma

VERSION_REGLAS = '2.1.0'
_lock = threading.RLock()


def estado_configuracion():
    return dict(proveedor='reglas', modelo=None, activo=False, configurado=True,
                version=VERSION_REGLAS, mensaje='Retroalimentación local por reglas, sin cuentas ni modelos.')


def configurar(proveedor='plantillas', modelo=None, **_):
    # Compatibilidad de scripts locales; no permite reactivar proveedores externos.
    if proveedor not in ('plantillas', 'reglas'):
        raise ValueError('La aplicación utiliza exclusivamente reglas locales.')
    return estado_configuracion()


def _obj(properties):
    return dict(type='object', properties=properties, required=list(properties), additionalProperties=False)


TEXTO = dict(type='string')
ITEM = _obj(dict(texto=TEXTO, evidencia_ids=dict(type='array', items=TEXTO)))
ESQUEMA = _obj(dict(resumen=TEXTO, aciertos=dict(type='array', items=ITEM),
                    aspectos_a_revisar=dict(type='array', items=ITEM),
                    practica_sugerida=dict(type='array', items=_obj(dict(
                        texto=TEXTO, evidencia_ids=dict(type='array', items=TEXTO), accion_id=TEXTO))),
                    limitaciones=dict(type='array', items=TEXTO)))
def _contexto(context, fragmento_id):
    # No envía los 36 fragmentos para redactar un resumen ni datos globales en una consulta local.
    if fragmento_id:
        f = context['analisis_fragmentos'][0]
        evidence = f['eventos_seleccionados']
        return dict(alcance='fragmento', musical=f.get('musical'), fragmento_id=f['id'], inicio_s=f['inicio_s'], fin_s=f['fin_s'],
                    metricas=f['metricas'], suficiencia=f['suficiencia_evidencia'],
                    evidencias=evidence, eventos_no_incluidos=f['eventos_no_incluidos'],
                    metodo=context['metodo'], limitaciones=context['calidad']['limitaciones'])
    return dict(alcance='resumen', musical=context.get('musical'), metricas=context['resumen_metricas'],
                suficiencia=context['calidad']['suficiencia_evidencia'],
                metodo=context['metodo'], evidencias=context['hallazgos_seleccionados'], limitaciones=context['calidad']['limitaciones'])


def validar(respuesta, contexto):
    if not isinstance(respuesta, dict) or set(respuesta) != set(ESQUEMA['properties']):
        raise ValueError('Estructura de respuesta inválida.')
    if not isinstance(respuesta['resumen'], str) or not respuesta['resumen'].strip() or len(respuesta['resumen']) > 3000:
        raise ValueError('Resumen inválido.')
    ev = {e['id']: e for e in contexto['evidencias']}
    for key, category in [('aciertos', 'fortaleza'), ('aspectos_a_revisar', 'aspecto_por_mejorar'), ('practica_sugerida', None)]:
        items = respuesta[key]
        if not isinstance(items, list) or len(items) > 3:
            raise ValueError('Lista inválida.')
        for item in items:
            keys = {'texto', 'evidencia_ids'} | ({'accion_id'} if category is None else set())
            if not isinstance(item, dict) or set(item) != keys or not isinstance(item['texto'], str) or not 1 <= len(item['texto']) <= 2000:
                raise ValueError('Elemento inválido.')
            ids = item['evidencia_ids']
            if not isinstance(ids, list) or not ids or not all(isinstance(i, str) and i in ev for i in ids):
                raise ValueError('Evidencia inexistente o ajena al fragmento.')
            if category and any(ev[i]['categoria'] != category for i in ids):
                raise ValueError('La categoría no coincide con la evidencia.')
            if category is None and (not isinstance(item['accion_id'], str) or not all(
                (ev[i].get('accion_sugerida') or {}).get('id') == item['accion_id'] for i in ids)):
                raise ValueError('Práctica sin respaldo.')
    limits = respuesta['limitaciones']
    if not isinstance(limits, list) or len(limits) > 10 or not all(isinstance(v, str) and len(v) <= 2000 for v in limits):
        raise ValueError('Limitaciones inválidas.')
    return respuesta


ETIQUETAS = dict(afinacion_cercana='Las notas detectadas estuvieron cerca de la referencia.',
    tendencia_aguda='Se observó una tendencia por encima de la referencia.',
    tendencia_grave='Se observó una tendencia por debajo de la referencia.',
    desviacion_aguda='Las notas detectadas estuvieron por encima de la referencia.',
    desviacion_grave='Las notas detectadas estuvieron por debajo de la referencia.',
    desviaciones_frecuentes='Se observaron diferencias frecuentes respecto de la referencia.',
    discrepancia_grande='Hay diferencias grandes que requieren revisar la detección y la sincronización.',
    sin_deteccion_usuario='No se detectó suficiente pitch del usuario en este intervalo.',
    sin_referencia='No hay referencia detectada suficiente para comparar este intervalo.',
    referencia_insuficiente='La referencia detectada no es suficiente para evaluar este fragmento.',
    deteccion_insuficiente='No hay suficiente tiempo comparable para valorar el fragmento.',
    cobertura_parcial='Solo se pudo comparar una parte del fragmento.')


def _redactar(ctx):
    if ctx.get('musical') is not None:
        from audio.retro_notas import redactar
        content, audit, evidence = redactar(ctx['musical'], ctx['metodo'])
        return validar(content, dict(ctx, evidencias=evidence)), audit
    m = ctx['metricas']
    coverage, seconds = m['cobertura_comparable_pct'], m['comparable_s']
    enough = m['referencia_detectada_s'] + 1e-8 >= .5 and seconds + 1e-8 >= 1 and (coverage or 0) + 1e-8 >= 40
    broad = enough and seconds + 1e-8 >= 2 and coverage + 1e-8 >= 80
    audit = []
    def trace(rule, ids=(), values=None, action=None):
        audit.append(dict(regla=rule, plantilla=rule, version=VERSION_REGLAS,
                          evidencia_ids=list(ids), valores=values or {}, accion_id=action))
    if m['referencia_detectada_s'] + 1e-8 < .5:
        summary = 'No hay suficiente referencia detectada para evaluar este fragmento.' if ctx['alcance'] == 'fragmento' else 'No hay suficiente referencia detectada para evaluar la toma.'
        trace('referencia_insuficiente', values={'referencia_detectada_s': m['referencia_detectada_s']})
    else:
        summary = (f"Se compararon {seconds:.1f} de {m['referencia_detectada_s']:.1f} segundos con notas de referencia detectadas "
                   f"({coverage:.1f}% de cobertura).")
        trace('alcance', values={k: m[k] for k in ('comparable_s', 'referencia_detectada_s', 'cobertura_comparable_pct')})
        if not enough:
            summary += ' La evidencia es insuficiente para valorar la afinación; escucha la grabación y revisa la detección.'
            trace('evidencia_insuficiente')
        else:
            close = m['porcentaje_dentro_tolerancia']
            if broad:
                phrase = ('Las notas estuvieron cerca de la referencia durante la mayor parte del tiempo comparable.' if close >= 85 else
                          'Hubo varios intervalos cercanos a la referencia y otros con diferencias.' if close >= 65 else
                          'Se alternaron intervalos cercanos a la referencia con desviaciones frecuentes.' if close >= 40 else
                          'Las diferencias respecto de la referencia fueron frecuentes en los intervalos comparables.')
            else:
                phrase = 'La evidencia es parcial: estos resultados describen únicamente los intervalos comparados.'
            summary += f' El {close:.1f}% del tiempo comparable estuvo dentro de ±50 cents (medio semitono). '+phrase
            trace('cercania_amplia' if broad else 'alcance_parcial', values={'porcentaje_dentro_tolerancia': close})
            sharp, flat = m['porcentaje_agudo'], m['porcentaje_grave']
            outside = sharp+flat
            direction = 'aguda' if sharp >= flat else 'grave'
            dominant = max(sharp, flat)
            if outside > 0 and dominant/outside >= .7 and seconds*dominant/100 >= 1:
                summary += (' Las desviaciones se concentraron principalmente por encima de la referencia (más agudas).' if direction == 'aguda' else
                            ' Las desviaciones se concentraron principalmente por debajo de la referencia (más graves).')
                trace('direccion_'+direction, values={'porcentaje_agudo': sharp, 'porcentaje_grave': flat, 'comparable_s': seconds})
    limits = [ctx['limitaciones'][2], 'La falta de detección no demuestra que hayas dejado de cantar.',
              'La referencia y tu voz se estiman automáticamente. No se evaluaron ritmo ni técnica vocal.']
    result = dict(resumen=summary, aciertos=[], aspectos_a_revisar=[], practica_sugerida=[], limitaciones=limits)
    def weight(e):
        metrics = e.get('metricas', e.get('evidencia', {}))
        return metrics.get('comparable_s', e['fin_s']-e['inicio_s'])
    evidence = sorted(ctx['evidencias'], key=lambda e: (-weight(e), e['inicio_s'], e['id']))
    huge = (m.get('porcentaje_desviacion_grande') or 0) >= 30
    selected = []
    if enough:
        strengths = [e for e in evidence if e['categoria'] == 'fortaleza'][:1]
        issues, kinds = [], set()
        for e in evidence:
            if e['categoria'] == 'aspecto_por_mejorar' and e['tipo'] not in kinds:
                issues.append(e); kinds.add(e['tipo'])
            if len(issues) == 2:
                break
        selected = strengths+issues
        for e in selected:
            key = 'aciertos' if e['categoria'] == 'fortaleza' else 'aspectos_a_revisar'
            location = f"{e['inicio_s']:.2f}–{e['fin_s']:.2f} s"
            if ctx['alcance'] == 'fragmento':
                length = ctx['fin_s']-ctx['inicio_s']
                if e['fin_s'] <= ctx['inicio_s']+length/3:
                    location += ', al comienzo'
                elif e['inicio_s'] >= ctx['inicio_s']+2*length/3:
                    location += ', hacia el final'
            result[key].append(dict(texto=location+': '+ETIQUETAS[e['tipo']], evidencia_ids=[e['id']]))
            trace('evento_'+e['tipo'], [e['id']], {'inicio_s': e['inicio_s'], 'fin_s': e['fin_s'], 'metricas': e.get('metricas', e.get('evidencia'))})
    limitations = sorted([e for e in evidence if e['categoria'] == 'limitacion'],
                         key=lambda e: (e['tipo'] != 'discrepancia_grande', -weight(e)))
    for e in limitations[:2]:
        result['limitaciones'].append(f"{e['inicio_s']:.2f}–{e['fin_s']:.2f} s: "+ETIQUETAS[e['tipo']])
        trace('limite_'+e['tipo'], [e['id']])
    if huge:
        result['limitaciones'].append('Las discrepancias grandes son frecuentes: revisa la comparación antes de atribuirlas a tu interpretación.')
    # Una única práctica: revisar la comparación tiene prioridad sobre corregir alturas dudosas.
    if not enough or huge:
        candidates = [e for e in limitations if e.get('accion_sugerida')]
    else:
        candidates = [e for e in selected if e['categoria'] == 'aspecto_por_mejorar' and e.get('accion_sugerida')]
        if not candidates:
            candidates = [e for e in limitations if e.get('accion_sugerida')]
    if candidates:
        e = candidates[0]; action = e['accion_sugerida']
        text = action['descripcion']
        if enough and not huge and e['tipo'] in ('tendencia_grave', 'desviacion_grave'):
            text = 'Escucha la altura de referencia y repite este intervalo buscando acercarte gradualmente a ella desde la nota más grave detectada. Después únelo con el resto de la frase.'
        elif enough and not huge and e['tipo'] in ('tendencia_aguda', 'desviacion_aguda'):
            text = 'Alterna la escucha de la referencia con una repetición de este intervalo, buscando una altura algo menor. Después únelo con el resto de la frase.'
        elif enough and not huge and e['tipo'] == 'desviaciones_frecuentes':
            text = 'Practica una porción más corta de este intervalo y compara las alturas por separado antes de repetir la frase completa.'
        text = f"Prioriza {e['inicio_s']:.2f}–{e['fin_s']:.2f} s. "+text
        result['practica_sugerida'].append(dict(texto=text, evidencia_ids=[e['id']], accion_id=action['id']))
        trace('practica_'+e['tipo'], [e['id']], {'inicio_s': e['inicio_s'], 'fin_s': e['fin_s']}, action['id'])
    trace('sincronizacion', values=ctx['metodo'].get('alineacion', {'estado': ctx['metodo']['sincronizacion']}))
    return validar(result, ctx), audit


def plantilla(ctx):
    return _redactar(ctx)[0]


def ruta_cache(ruta_audio):
    return Path(ruta_audio).with_name(Path(ruta_audio).stem+'_explicaciones.json')


def _explicar_contexto(context, toma, fragmento_id):
    ctx = _contexto(context, fragmento_id)
    key = hashlib.sha256(json.dumps(dict(contexto=ctx, reglas=VERSION_REGLAS),
                                   sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()
    content, audit = _redactar(ctx)
    response = dict(origen='reglas', guardada=False, aviso='', contenido=content,
                    version_reglas=VERSION_REGLAS, trazabilidad=audit)
    path = ruta_cache(toma['voice_path'])
    with _lock:
        try:
            saved = json.loads(path.read_text(encoding='utf-8'))
            entries = saved.get('entradas', {}) if saved.get('version_reglas') == VERSION_REGLAS else {}
            if not isinstance(entries, dict):
                entries = {}
        except (OSError, ValueError, AttributeError):
            entries = {}
        # Se redacta siempre de forma determinista: nunca devuelve texto antiguo de un LLM.
        if entries.get(key) == dict(contenido=content, trazabilidad=audit):
            response['guardada'] = True
            return response
        entries[key] = dict(contenido=content, trazabilidad=audit)
        if Path(toma['voice_path']).exists():
            temp = None
            try:
                with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, suffix='.tmp', delete=False) as stream:
                    temp = Path(stream.name)
                    json.dump(dict(version_reglas=VERSION_REGLAS, entradas=entries), stream, ensure_ascii=False, allow_nan=False)
                os.replace(temp, path)
            except OSError:
                response['aviso'] = 'La explicación está disponible, pero no pudo guardarse.'
            finally:
                if temp:
                    temp.unlink(missing_ok=True)
    return response


def explicar(cancion, toma_id, fragmento_id=None, generar=True):
    context = obtener_contexto_retroalimentacion(cancion, toma_id, fragmento_id)
    return _explicar_contexto(context, _buscar_toma(cancion, toma_id), fragmento_id)


def panel(cancion, toma_id):
    context = obtener_contexto_retroalimentacion(cancion, toma_id)
    alignment = context['metodo']['alineacion']
    return dict(configuracion=estado_configuracion(), musical=context.get('musical'), metricas=context['resumen_metricas'],
                calidad=context['calidad'], fragmentos=context['analisis_fragmentos'],
                alineacion=alignment, desfase_ms=round(alignment['desfase_s']*1000),
                explicacion=_explicar_contexto(context, _buscar_toma(cancion, toma_id), None))
