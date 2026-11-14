"""Comprueba reglas y alineación sobre el catálogo actual, sin modificar tomas."""
import hashlib
import json
from pathlib import Path
import sys
import time
from unittest.mock import patch
from collections import Counter
from jsonschema import Draft202012Validator
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from audio.catalogo import cargar_canciones
from audio.tomas import listar_tomas, obtener_contexto_retroalimentacion
from audio import explicaciones as ex

validator = Draft202012Validator(json.loads((ROOT/'docs/retroalimentacion.schema.json').read_text(encoding='utf-8')))
results = []
with patch('audio.alineacion._guardar'):
    for song in cargar_canciones():
        if not song.get('preparada'):
            continue
        for take in listar_tomas(song):
            path = Path(take['result_path'])
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            start = time.perf_counter()
            context = obtener_contexto_retroalimentacion(song,take['id'])
            validator.validate(context)
            notes=context['musical']
            assert notes['metricas']['notas_comparadas'] == sum(f['musical']['metricas']['notas_comparadas'] for f in context['analisis_fragmentos'])
            users=[n['usuario']['id'] for n in notes['notas'] if n['usuario']]
            assert len(users)==len(set(users))
            summary, audit = ex._redactar(ex._contexto(context,None))
            for fragment in context['analisis_fragmentos']:
                fc = dict(context, analisis_fragmentos=[fragment])
                response = ex.plantilla(ex._contexto(fc,fragment['id']))
                assert len(response['aciertos']) <= 1
                assert len(response['aspectos_a_revisar']) <= 2
                assert len(response['practica_sugerida']) <= 1
            assert hashlib.sha256(path.read_bytes()).hexdigest() == before
            results.append(dict(cancion=song['id'],toma=take['id'],segundos=round(time.perf_counter()-start,3),
                                alineacion=context['metodo']['alineacion'],fragmentos=len(context['analisis_fragmentos']),
                                musical=notes['metricas'], resumen=summary,trazabilidad=audit))
output=ROOT/'output/verificacion_reglas_alineacion.json'
output.write_text(json.dumps(results,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
print(json.dumps(dict(tomas=len(results),estados=dict(Counter(r['alineacion']['estado'] for r in results)),
                      segundos_total=sum(r['segundos'] for r in results)),ensure_ascii=True))
