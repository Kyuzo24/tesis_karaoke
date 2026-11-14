"""Demostración sintética y auditoría opcional de tomas reales, sin modificarlas."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
import soundfile as sf
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from audio.retroalimentacion import generar_retroalimentacion, preparar_contexto_modelo


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verificar-historicos', action='store_true')
    args = parser.parse_args()
    schema = json.loads((ROOT/'docs/retroalimentacion.schema.json').read_text(encoding='utf-8'))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    t = np.arange(0, 20., .01)
    ref = np.full(len(t), 440.)
    usr = ref.copy()
    usr[(t >= 5) & (t < 10)] *= 2 ** (-150/1200)
    usr[(t >= 10) & (t < 15)] = 0
    usr[t >= 15] *= 2 ** (1200/1200)
    report = generar_retroalimentacion(t, ref, t, usr, 20.)
    context = preparar_contexto_modelo(report)
    out = ROOT/'output/retroalimentacion_demo'
    out.mkdir(exist_ok=True)
    for name, data in [('analisis_sintetico.json', report), ('contexto_sintetico.json', context)]:
        validator.validate(data)
        (out/name).write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    (out/'LEEME.md').write_text('# Ejemplo sintético\n\nNo describe una interpretación real.\n\n0–5 s: tono coincidente; 5–10 s: 150 cents más grave; 10–15 s: sin pitch de usuario; 15–20 s: una octava por encima. El último caso se comunica como discrepancia que requiere revisión.\n', encoding='utf-8')
    checked, skipped = 0, 0
    if args.verificar_historicos:
        for path in sorted((ROOT/'grabaciones').rglob('*_resultado.json')):
            result = json.loads(path.read_text(encoding='utf-8'))
            wav = path.with_name(path.name.removesuffix('_resultado.json') + '.wav')
            if not wav.exists() or not result.get('grafico'):
                skipped += 1
                continue
            g = result['grafico']
            report = generar_retroalimentacion(g['t_ref'], g['f_ref'], g['t_usr'], g['f_usr'], sf.info(wav).duration)
            for data in [report, preparar_contexto_modelo(report)]:
                validator.validate(data)
                json.dumps(data, allow_nan=False)
            checked += 1
        (out/'verificacion_historicos.json').write_text(json.dumps({'verificados': checked, 'omitidos_sin_audio_o_grafico': skipped,
                                                                   'modifico_tomas': False}, indent=2), encoding='utf-8')
    print(f'Ejemplos y esquema válidos. Tomas históricas comprobadas: {checked}; omitidas: {skipped}.')


if __name__ == '__main__':
    main()
