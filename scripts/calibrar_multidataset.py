"""Calibración agrupada reproducible; nunca selecciona con la validación."""
from pathlib import Path
import csv, hashlib, importlib.util, json, sys, argparse, time
from types import SimpleNamespace
import numpy as np
import librosa
import soundfile as sf

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.comparar_live_vocadito import ui_policy
from scripts.evaluar_vocadito import align, counts, percentages, check_evaluator
from scripts.evaluar_mir1k import mixture
OUT=ROOT/'output/calibracion_multidataset'
VARIANTS={'base':(.7,.7,0), 'umbral_060':(.6,.6,0), 'umbral_050':(.5,.5,0),
          'continuidad_050':(.7,.5,2), 'continuidad_040':(.7,.4,2),
          'continuidad_060':(.7,.6,2), 'continuidad_065_045':(.65,.45,2)}

def save(path,value):
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False),encoding='utf-8')

def periodic_mask(f0, p, start, hold, max_weak):
    """Solo apoya candidatos reales: no genera frecuencias ni cruza silencios."""
    accepted=np.zeros(len(f0),dtype=bool)
    last=0.; weak=0
    for i,(f,c) in enumerate(zip(f0,p)):
        strong=f>0 and c>=start
        continuous=f>0 and last>0 and abs(12*np.log2(f/last))<=2
        if strong:
            accepted[i]=True; weak=0; last=f
        elif continuous and c>=hold and weak<max_weak:
            accepted[i]=True; weak+=1; last=f
        else:
            last=0.; weak=0
    return accepted

def inventory():
    rows=[]
    for r in csv.DictReader((ROOT/'data/vocadito_benchmark/vocadito_metadata.csv').open(encoding='utf-8')):
        rows.append(dict(dataset='vocadito',name='vocadito_'+r['track_id'],group=r['singer_id']))
    m=json.loads((ROOT/'data/mir1k_muestra/manifest.json').read_text())
    for name in m['selected_tracks']:
        rows.append(dict(dataset='mir1k',name=name,group=name.split('_')[0]))
    m=json.loads((ROOT/'data/mdb_stem_synth/manifest.json').read_text())
    for r in m['selected']:
        # Todas las canciones del mismo artista quedan en la misma partición.
        rows.append(dict(dataset='mdb',name=r['track'],group=r['song'].split('_')[0],audio=r['audio'][0],f0=r['f0'][0]))
    for ds in ['vocadito','mir1k','mdb']:
        groups=sorted({r['group'] for r in rows if r['dataset']==ds},key=lambda g:hashlib.sha256(('calibracion-v1:'+ds+':'+g).encode()).hexdigest())
        validation=set(groups[:max(1,round(len(groups)*.3))])
        for r in rows:
            if r['dataset']==ds: r['split']='validacion' if r['group'] in validation else 'calibracion'
    return rows

def audio(row):
    ds,name=row['dataset'],row['name']
    if ds=='vocadito':
        root=ROOT/'data/vocadito_benchmark'
        y,sr=sf.read(root/'Audio'/(name+'.wav'),dtype='float32')
        rt,ref=np.loadtxt(root/'Annotations/F0'/(name+'_f0.csv'),delimiter=',').T
        return {'voz':y},sr,rt,ref
    if ds=='mdb':
        root=ROOT/'data/mdb_stem_synth'
        y,sr=sf.read(root/row['audio'],dtype='float32')
        rt,ref=np.loadtxt(root/row['f0'],delimiter=',').T
        return {'voz':y},sr,rt,ref
    root=ROOT/'data/mir1k_muestra/MIR-1K'
    y,sr=sf.read(root/'Wavfile'/(name+'.wav'),dtype='float32')
    midi=np.loadtxt(root/'PitchLabel'/(name+'.pv'))
    rt=.02+np.arange(len(midi))*.02
    ref=np.where(midi>0,440*2**((midi-69)/12),0)
    y=librosa.resample(y.T,orig_sr=sr,target_sr=44100).T
    return {'voz':y[:,1],'musica10':mixture(y[:,1],y[:,0],10)[0],'musica0':mixture(y[:,1],y[:,0],0)[0]},44100,rt,ref

def module():
    spec=importlib.util.spec_from_file_location('calibration_base',OUT/'pitch_base.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m

def run_signal(y,sr,variants,profile):
    m=module(); original=m._filtrar_pitch_tiempo_real
    config,accept=ui_policy()
    interval,window=(config['LIVE_PITCH_INTERVAL'],config['LIVE_PITCH_CHUNK']) if profile=='desktop' else (.06,.38)
    states={v:dict(last=0.,ui=SimpleNamespace(_ultimo_punto_usuario=None),ts=[],fs=[]) for v in variants}
    captured={}
    def filt(t,f0,signal,rate,**kw):
        p=kw.pop('periodicidad')
        for v in variants:
            start,hold,maxweak=VARIANTS[v]
            conf=p if v=='base' else periodic_mask(f0,p,start,hold,maxweak).astype(float)
            captured[v]=original(t,f0.copy(),signal,rate,periodicidad=conf,**kw)
        return captured[variants[0]]
    m._filtrar_pitch_tiempo_real=filt
    for end in np.arange(interval,len(y)/sr,interval):
        start=max(0.,end-window); captured.clear()
        m.extraer_pitch_ligero_desde_audio(y[int(start*sr):int(end*sr)],sr)
        for v,(t,f) in captured.items():
            state=states[v];t=t+start;new=t>state['last']
            if np.any(new):
                state['last']=float(t[new].max())
                for ti,fi in zip(t[new],f[new]):
                    if profile=='clasica' or accept(state['ui'],[float(ti),float(69+12*np.log2(fi/440))]):
                        state['ts'].append(ti);state['fs'].append(fi)
    return {v:(np.asarray(s['ts']),np.asarray(s['fs'])) for v,s in states.items()}

def aggregate(rows):
    out={}
    for r in rows:
        for condition,metrics in r['metrics'].items():
            group=r['dataset']+'/'+condition
            for variant,c in metrics.items():
                target=out.setdefault(group,{}).setdefault(variant,{k:0 for k in c})
                for k,value in c.items():target[k]+=value
    return {g:{v:{**percentages(c),'counts':c} for v,c in vs.items()} for g,vs in out.items()}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['calibracion','validacion','clasica']);args=parser.parse_args()
    check_evaluator();OUT.mkdir(exist_ok=True)
    inv=inventory(); ip=OUT/'particion.json'
    if ip.exists():assert json.loads(ip.read_text(encoding='utf-8'))==inv
    else:save(ip,inv)
    protocol={'variants':VARIANTS,'max_continuity_semitones':2,'selection':'Promedio por escenario de aciertos - 0.5*falsas; cada escenario: aciertos >= base-0.5pp, falsas <= base+1pp, omisiones <= base+0.5pp. Debe superar base en 0.2 puntos del objetivo.',
              'baseline_sha256':hashlib.sha256((OUT/'pitch_base.py').read_bytes()).hexdigest(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'note':'Validación interna: estos datasets ya se inspeccionaron. Grupos por cantante (Vocadito/MIR) y artista (MDB). Parámetros elegidos solo en calibración.'}
    pp=OUT/'protocolo.json'
    if pp.exists():assert json.loads(pp.read_text(encoding='utf-8'))==json.loads(json.dumps(protocol))
    else:save(pp,protocol)
    if args.phase=='calibracion':variants=list(VARIANTS);selected=[r for r in inv if r['split']=='calibracion'];profile='desktop'
    else:
        choice=json.loads((OUT/'seleccion.json').read_text())['selected']
        variants=list(dict.fromkeys(['base',choice]));profile='clasica' if args.phase=='clasica' else 'desktop'
        selected=inv if args.phase=='clasica' else [r for r in inv if r['split']=='validacion']
    folder=OUT/args.phase;folder.mkdir(exist_ok=True);results=[]
    for i,r in enumerate(selected,1):
        path=folder/(r['dataset']+'_'+r['name']+'.json')
        if path.exists():results.append(json.loads(path.read_text()));continue
        scenarios,sr,rt,ref=audio(r);record={**r,'duration_s':len(next(iter(scenarios.values())))/sr,'metrics':{}}
        for condition,y in scenarios.items():
            predictions=run_signal(y,sr,variants,profile)
            record['metrics'][condition]={v:counts(ref,align(t,f,rt,1024/sr/2))[0] for v,(t,f) in predictions.items()}
        save(path,record);results.append(record)
        print(f'{args.phase} {i}/{len(selected)} {r["dataset"]}/{r["name"]}',flush=True)
    summary=aggregate(results);save(OUT/(args.phase+'_resumen.json'),summary)
    if args.phase=='calibracion':
        eligible=[];scores={}
        for v in variants:
            scores[v]=float(np.mean([s[v]['pitch_correct_50c_pct']-.5*s[v]['false_voiced_pct'] for s in summary.values()]))
            if all(s[v]['pitch_correct_50c_pct']>=s['base']['pitch_correct_50c_pct']-.5 and s[v]['false_voiced_pct']<=s['base']['false_voiced_pct']+1 and s[v]['missed_voiced_pct']<=s['base']['missed_voiced_pct']+.5 for s in summary.values()):eligible.append(v)
        best=max(eligible,key=lambda v:scores[v]);best=best if scores[best]>=scores['base']+.2 else 'base'
        save(OUT/'seleccion.json',{'selected':best,'scores':scores,'eligible':eligible,'variants':VARIANTS})
        print('SELECCION CONGELADA:',best,scores,flush=True)
    print('COMPLETO',args.phase,len(results),flush=True)

if __name__=='__main__':main()
