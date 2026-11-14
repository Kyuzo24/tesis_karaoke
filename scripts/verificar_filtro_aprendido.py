"""Paridad del modelo exportado y comprobación extremo a extremo con audio."""
from pathlib import Path
import argparse,json,sys,hashlib
from functools import partial
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from audio import pitch,filtro_aprendido
from scripts import entrenar_filtro as train
from scripts.comparar_live_vocadito import simulate,ui_policy
from scripts.evaluar_vocadito import align,counts

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--profile',choices=['desktop','clasica'],default='desktop');args=parser.parse_args()
    inv=train.partition();model=json.loads((train.OUT/'modelo.json').read_text());windows=0
    for row in inv:
        for path in train.paths(row,args.profile):
            with np.load(path) as archive:z={k:archive[k] for k in archive.files}
            offsets=np.r_[0,np.cumsum(z['sizes'])]
            for i in sorted({0,len(z['sizes'])//2,len(z['sizes'])-1}):
                sl=slice(offsets[i],offsets[i+1])
                actual_x=filtro_aprendido.caracteristicas(z['f'][sl],z['p'][sl],z['e'][sl])
                np.testing.assert_array_equal(actual_x,z['X'][sl])
                actual=filtro_aprendido.aceptar_candidatos(z['f'][sl],z['p'][sl],z['e'][sl])
                expected=(train.predict(model['tree'],z['X'][sl])>=model['cutoff'])&(z['p'][sl]>=model['periodicity_floor'])
                np.testing.assert_array_equal(actual,expected);windows+=1
    config,accept=ui_policy();interval,window=(config['LIVE_PITCH_INTERVAL'],config['LIVE_PITCH_CHUNK']) if args.profile=='desktop' else (.06,.38)
    selected=[next(r for r in inv if r['dataset']==ds and r['stage']=='validacion') for ds in ['vocadito','mir1k','mdb']]
    detector=partial(pitch.extraer_pitch_ligero_desde_audio,usar_filtro_aprendido=True)
    checks=[];timings=[]
    for row in selected:
        scenarios,sr,rt,ref=train.c.audio(row)
        folder='todos' if args.profile=='desktop' else 'clasica'
        expected=json.loads((train.OUT/folder/(row['dataset']+'_'+row['name']+'.json')).read_text())
        for condition,y in scenarios.items():
            t,f,durations=simulate(y,sr,detector,interval,window,accept if args.profile=='desktop' else None)
            result=counts(ref,align(t,f,rt,1024/sr/2))[0]
            assert result==expected['metrics'][condition][model['name']],(row['name'],condition)
            checks.append(row['dataset']+'/'+row['name']+'/'+condition);timings.extend(durations)
            print('Audio completo coincide:',checks[-1],flush=True)
    train.c.save(train.OUT/('integracion_'+args.profile+'.json'),{'feature_windows_checked':windows,'full_audio_checks':checks,'processing_ms':{'median':float(np.median(timings)*1000),'p95':float(np.percentile(timings,95)*1000)},'model_sha256':hashlib.sha256(filtro_aprendido.RUTA_MODELO.read_bytes()).hexdigest(),'pitch_sha256':hashlib.sha256((ROOT/'audio/pitch.py').read_bytes()).hexdigest(),'inference_sha256':hashlib.sha256((ROOT/'audio/filtro_aprendido.py').read_bytes()).hexdigest()})
    print('Integración verificada:',windows,'ventanas y',len(checks),'audios/condiciones completos.',flush=True)

if __name__=='__main__':main()
