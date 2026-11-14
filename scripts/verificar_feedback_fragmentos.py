"""Valida referencias aprobadas y tomas existentes sin reescribirlas."""
import hashlib
import json
from pathlib import Path
import sys
import soundfile as sf
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from audio.catalogo import leer_pitch_csv
from audio.segmentacion import segmentar_referencia
from audio.retroalimentacion import generar_retroalimentacion, preparar_contexto_modelo


def main():
    aprobados = json.loads((ROOT/'output/segmentacion_revision/segmentos.json').read_text(encoding='utf-8'))
    schema = json.loads((ROOT/'docs/retroalimentacion.schema.json').read_text(encoding='utf-8'))
    validator = Draft202012Validator(schema)
    out = ROOT/'output/retroalimentacion_fragmentos'
    out.mkdir(exist_ok=True)
    audit = []
    approved_by_id = {c['id']: c for c in aprobados['canciones']}
    for metadata in sorted((ROOT/'canciones').glob('*/metadata.json')):
        song = json.loads(metadata.read_text(encoding='utf-8'))
        if not song.get('preparada') or not Path(song.get('pitch_referencia', '')).is_file():
            audit.append(dict(id=song['id'], omitida='Referencia todavía no preparada'))
            continue
        if song['id'] == 'qué_gano_olvidandote_84dce906' and (ROOT/'canciones/que_gano_olvidandote_a7c974ca/metadata.json').exists():
            continue
        approved = approved_by_id.get(song['id'])
        tr, fr = leer_pitch_csv(song['pitch_referencia'])
        segments = segmentar_referencia(song['vocals'], tr, fr)
        if approved:
            assert segments == [{k: s[k] for k in ['inicio_s','fin_s']} for s in approved['segmentos']]
        checked = 0
        for path in sorted((ROOT/'grabaciones'/song['id']).glob('*_resultado.json')):
            original = path.read_bytes()
            data = json.loads(original)
            wav = path.with_name(path.name.removesuffix('_resultado.json')+'.wav')
            g = data.get('grafico')
            if not wav.exists() or not g:
                continue
            report = generar_retroalimentacion(tr, fr, g['t_usr'], g['f_usr'], sf.info(wav).duration, segmentos=segments)
            context = preparar_contexto_modelo(report)
            for payload in [report, context]:
                validator.validate(payload)
                json.dumps(payload, allow_nan=False)
            for f in report['fragmentos']:
                validator.validate(preparar_contexto_modelo(report, f['id']))
            assert path.read_bytes() == original
            if checked == 0:
                for name, payload in [('analisis', report), ('contexto', context)]:
                    (out/f"{song['id']}_{name}.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
            checked += 1
        audit.append(dict(id=song['id'], segmentos=len(segments), tomas_verificadas=checked, cortes_con_baseline=approved is not None,
                          audio_sha256=hashlib.sha256(Path(song['vocals']).read_bytes()).hexdigest()))
    (out/'verificacion.json').write_text(json.dumps(audit,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(audit,ensure_ascii=True))


if __name__ == '__main__':
    main()
