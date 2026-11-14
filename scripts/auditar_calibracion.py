"""Comprueba que la base reproduce las pruebas previas y registra sus entradas."""
from pathlib import Path
import json,hashlib,sys,importlib.metadata
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.calibrar_multidataset import save
OUT=ROOT/'output/calibracion_multidataset_v3'

def main():
    old={}
    for ds,path in [('vocadito','vocadito_mejoras/comparacion_live.json'),('mir1k','mir1k_evaluacion/resultados.json'),('mdb','mdb_evaluacion/resultados.json')]:
        data=json.loads((ROOT/'output'/path).read_text())
        old[ds]={r['track']:r for r in data['per_track']}
    checked=0
    for folder in ['calibracion','validacion']:
        for p in (OUT/folder).glob('*.json'):
            r=json.loads(p.read_text()); ds=r['dataset']
            for cond,m in r['metrics'].items():
                key={'voz':'voz_sola_despues','musica10':'musica_10dB_despues','musica0':'musica_0dB_despues'}[cond] if ds=='mir1k' else ('desktop_despues' if ds=='vocadito' else 'despues')
                assert m['base']==old[ds][r['name']]['metrics'][key]['counts'],(ds,r['name'],cond)
                checked+=1
    assert checked==385,checked
    inv=json.loads((OUT/'particion.json').read_text(encoding='utf-8'))
    files=[]
    for r in inv:
        ds,n=r['dataset'],r['name']
        if ds=='vocadito':paths=[ROOT/'data/vocadito_benchmark/Audio'/(n+'.wav'),ROOT/'data/vocadito_benchmark/Annotations/F0'/(n+'_f0.csv')]
        elif ds=='mdb':paths=[ROOT/'data/mdb_stem_synth'/r[k] for k in ['audio','f0']]
        else:paths=[ROOT/'data/mir1k_muestra/MIR-1K/Wavfile'/(n+'.wav'),ROOT/'data/mir1k_muestra/MIR-1K/PitchLabel'/(n+'.pv')]
        for p in paths:
            with p.open('rb') as f:d=hashlib.file_digest(f,'sha256').hexdigest()
            files.append({'path':str(p.relative_to(ROOT)),'sha256':d})
    save(OUT/'auditoria.json',{'exact_baseline_comparisons':checked,'input_files':files,'python':sys.version,'versions':{p:importlib.metadata.version(p) for p in ['numpy','librosa','soundfile']}})
    print('OK:',checked,'comparaciones exactas con resultados previos;',len(files),'archivos registrados.')

if __name__=='__main__':main()
