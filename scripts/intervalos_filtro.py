"""Bootstrap pareado por cantante/artista, solo validación reservada."""
from pathlib import Path
import json
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/filtro_aprendido'

def main():
    choice=json.loads((OUT/'seleccion.json').read_text())['selected']
    rows=[json.loads(p.read_text()) for p in (OUT/'validacion').glob('*.json')]
    groups={}
    keys=['correct_pitch','voiced','false_voiced','unvoiced','missed']
    for r in rows:
        for condition,metrics in r['metrics'].items():
            group=groups.setdefault(r['dataset']+'/'+condition,{})
            arr=np.array([[metrics[v][k] for k in keys] for v in ['base',choice]])
            group[r['group']]=group.get(r['group'],np.zeros_like(arr))+arr
    rng=np.random.default_rng(20260929);out={}
    for condition,group in groups.items():
        arr=np.array(list(group.values()));n=len(arr)
        sampled=arr[rng.integers(n,size=(2000,n))].sum(axis=1)
        values={}
        for label,num,den in [('aciertos_pp',0,1),('falsas_pp',2,3),('omisiones_pp',4,1)]:
            diff=100*(sampled[:,1,num]/sampled[:,1,den]-sampled[:,0,num]/sampled[:,0,den])
            values[label]=[float(v) for v in np.percentile(diff,[2.5,97.5])]
        out[condition]={'groups':n,'percentile_95':values}
    (OUT/'intervalos_validacion.json').write_text(json.dumps({'replicates':2000,'unit':'cantante en Vocadito/MIR, artista en MDB','paired':True,'seed':20260929,'results':out},indent=2),encoding='utf-8')
    print(json.dumps(out,indent=2))

if __name__=='__main__':main()
