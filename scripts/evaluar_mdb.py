"""Todas las pistas vocales de MDB-stem-synth; solo interfaz nueva en vivo.

Comparacion congelada antes/despues, con resultados reanudables por pista.
"""
from pathlib import Path
import hashlib
import importlib.metadata
import json
import sys
import numpy as np
import soundfile as sf

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from audio import pitch
from scripts.comparar_live_vocadito import load_before,ui_policy,simulate
from scripts.evaluar_vocadito import align,counts,percentages,check_evaluator

DATA=ROOT/'data/mdb_stem_synth'
OUT=ROOT/'output/mdb_evaluacion'


def digest(path,algorithm='sha256'):
    with path.open('rb') as f:
        return hashlib.file_digest(f,algorithm).hexdigest()


def main():
    check_evaluator()
    manifest=json.loads((DATA/'manifest.json').read_text(encoding='utf-8'))
    selected=manifest['selected']
    assert len(selected)==manifest['vocal_tracks']==60
    assert len(manifest['inventory'])==manifest['total_tracks']==230
    before=load_before()
    config,accept=ui_policy()
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'tracks').mkdir(exist_ok=True)
    (OUT/'predicciones').mkdir(exist_ok=True)
    protocol={
        'pitch_sha256':digest(ROOT/'audio/pitch.py'),
        'before_sha256':digest(ROOT/'output/vocadito_mejoras/antes/pitch.py'),
        'ui_sha256':digest(ROOT/'desktop_live.py'),
        'script_sha256':digest(Path(__file__)),
        'simulation_helpers_sha256':digest(ROOT/'scripts/comparar_live_vocadito.py'),
        'metric_helpers_sha256':digest(ROOT/'scripts/evaluar_vocadito.py'),
        'manifest_sha256':digest(DATA/'manifest.json'),
        'config_live':pitch.FILTRO_TIEMPO_REAL,'desktop_config':config,
        'scope':'60 pistas vocales completas de las 230; solo YIN en vivo, interfaz nueva',
        'sample_rate':44100,'reference_hop':128/44100,'noise_floor':None,
        'versions':{p:importlib.metadata.version(p) for p in ['librosa','numpy','soundfile']},
        'python':sys.version,
    }
    pp=OUT/'protocolo.json'
    if pp.exists():
        assert json.loads(pp.read_text(encoding='utf-8'))==protocol,'Protocolo diferente: no mezclar resultados.'
    else:
        pp.write_text(json.dumps(protocol,indent=2),encoding='utf-8')
    for row in selected:
        for key in ['audio','f0']:
            assert digest(DATA/row[key][0],'md5')==row[key][1],row['track']
    warm=.1*np.sin(2*np.pi*220*np.arange(16758)/44100)
    for mod in [before,pitch]:
        mod.extraer_pitch_ligero_desde_audio(warm,44100)
    rows=[]
    for i,track in enumerate(selected,1):
        name=track['track']
        cache=OUT/'tracks'/(name+'.json')
        if cache.exists():
            rows.append(json.loads(cache.read_text(encoding='utf-8')))
            print(f'{i}/60 {name}: recuperado',flush=True)
            continue
        y,sr=sf.read(DATA/track['audio'][0],dtype='float32')
        assert sr==44100 and y.ndim==1
        rt,ref=np.loadtxt(DATA/track['f0'][0],delimiter=',').T
        assert np.isfinite(ref).all() and np.all(ref>=0)
        # Los CSV oficiales guardan seis decimales (precisión de microsegundos).
        assert np.allclose(rt,np.arange(len(rt))*128/44100,atol=1e-6,rtol=0)
        assert abs(len(y)/sr-rt[-1])<.05
        row={'track':name,'song':track['song'],'instrument':track['instrument'],
             'duration_s':len(y)/sr,'metrics':{},'timing':{},
             'reference_below_C2':int(((ref>0)&(ref<65.4063913)).sum()),
             'reference_above_C6':int((ref>1046.5022612).sum())}
        predictions={'time':rt,'reference':ref}
        for label,mod in [('antes',before),('despues',pitch)]:
            t,f,timings=simulate(y,sr,mod.extraer_pitch_ligero_desde_audio,
                                config['LIVE_PITCH_INTERVAL'],config['LIVE_PITCH_CHUNK'],accept)
            est=align(t,f,rt,1024/sr/2)
            assert np.isfinite(est).all()
            c,error=counts(ref,est)
            row['metrics'][label]={**percentages(c),'counts':c,
                                  'median_abs_cents_both_voiced':float(np.median(error)) if len(error) else None}
            row['timing'][label]={'median_ms':float(np.median(timings)*1000),
                                  'p95_ms':float(np.percentile(timings,95)*1000)}
            predictions[label]=est
        np.savez_compressed(OUT/'predicciones'/(name+'.npz'),**predictions)
        cache.write_text(json.dumps(row,indent=2),encoding='utf-8')
        rows.append(row)
        print(f'{i}/60 {name}: aciertos {row["metrics"]["antes"]["pitch_correct_50c_pct"]:.1f}% '
              f'-> {row["metrics"]["despues"]["pitch_correct_50c_pct"]:.1f}%',flush=True)
    def summarize(group):
        result={}
        for label in ['antes','despues']:
            c={k:sum(r['metrics'][label]['counts'][k] for r in group) for k in group[0]['metrics'][label]['counts']}
            result[label]={**percentages(c),'counts':c,
                           'macro_pitch_correct_50c_pct':float(np.mean([r['metrics'][label]['pitch_correct_50c_pct'] for r in group]))}
        return result
    result={'protocol':protocol,'tracks':len(rows),'dataset_total_tracks':230,
            'songs':len({r['song'] for r in rows}),'duration_s':sum(r['duration_s'] for r in rows),
            'summary':summarize(rows),'per_track':rows,
            'by_instrument':{inst:summarize([r for r in rows if r['instrument']==inst]) for inst in sorted({r['instrument'] for r in rows})},
            'reference_below_C2':sum(r['reference_below_C2'] for r in rows),
            'reference_above_C6':sum(r['reference_above_C6'] for r in rows)}
    assert digest(ROOT/'audio/pitch.py')==protocol['pitch_sha256']
    (OUT/'resultados.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('Evaluacion completa: 60/60 pistas vocales.',flush=True)


if __name__=='__main__':
    main()
