"""Árbol de decisión pequeño, entrenado por grupos, con replay exacto del worker."""
from pathlib import Path
import argparse,json,sys,hashlib
import numpy as np
from sklearn.tree import DecisionTreeClassifier
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts import calibrar_multidataset as c
from scripts.evaluar_vocadito import counts,align,percentages
OUT=ROOT/'output/filtro_aprendido'
FEATURES=['periodicidad','energia_relativa','log10_rms','periodicidad_anterior','periodicidad_siguiente','salto_min_semitonos','salto_max_semitonos','periodicidad_media','fraccion_periodica']

def features(f,p,e):
    n=len(f);prev=np.r_[p[0],p[:-1]];nxt=np.r_[p[1:],p[-1]]
    midi=69+12*np.log2(np.maximum(f,1)/440)
    dp=np.minimum(24,abs(midi-np.r_[midi[0],midi[:-1]]))
    dn=np.minimum(24,abs(midi-np.r_[midi[1:],midi[-1]]))
    return np.column_stack([p,e/max(float(e.max()),1e-12),np.log10(np.maximum(e,1e-8)),prev,nxt,np.minimum(dp,dn),np.maximum(dp,dn),np.full(n,np.mean(p)),np.full(n,np.mean(p>=.7))]).astype(np.float32)

def partition():
    inv=c.inventory()
    for ds in ['vocadito','mir1k','mdb']:
        gs=sorted({r['group'] for r in inv if r['dataset']==ds and r['split']=='calibracion'},key=lambda g:hashlib.sha256(('arbol-ajuste:'+g).encode()).hexdigest())
        tune=set(gs[:max(1,round(.3*len(gs)))])
        for r in inv:
            if r['dataset']==ds:r['stage']='validacion' if r['split']=='validacion' else ('ajuste' if r['group'] in tune else 'entrenamiento')
    return inv

def build_cache(row,profile):
    folder=OUT/'cache'/profile;folder.mkdir(parents=True,exist_ok=True)
    scenarios,sr,rt,ref=c.audio(row)
    interval,window=(.1,.24) if profile=='desktop' else (.06,.38)
    for condition,y in scenarios.items():
        path=folder/(row['dataset']+'_'+row['name']+'_'+condition+'.npz')
        if path.exists():continue
        m=c.module();windows=[]
        def capture(t,f,signal,rate,**kw):
            p=kw['periodicidad'];e=m._energia_por_tiempo(signal,rate,t)
            windows.append((t.copy(),f.copy(),p.copy(),e.copy(),features(f,p,e)))
            return t[f>0],f[f>0]
        m._filtrar_pitch_tiempo_real=capture
        starts=[]
        for end in np.arange(interval,len(y)/sr,interval):
            start=max(0.,end-window);n=len(windows)
            m.extraer_pitch_ligero_desde_audio(y[int(start*sr):int(end*sr)],sr)
            if len(windows)>n:starts.append(start)
        sizes=np.array([len(w[0]) for w in windows]);flat=[np.concatenate([w[i] for w in windows]) for i in range(5)]
        absolute=flat[0]+np.repeat(starts,sizes)
        right=np.clip(np.searchsorted(rt,absolute),0,len(rt)-1);left=np.maximum(0,right-1)
        idx=np.where(abs(rt[left]-absolute)<=abs(rt[right]-absolute),left,right)
        target=ref[idx]
        np.savez_compressed(path,t=flat[0],f=flat[1],p=flat[2],e=flat[3],X=flat[4],sizes=sizes,starts=starts,target=target,rt=rt,ref=ref)

def paths(row,profile):
    result=sorted((OUT/'cache'/profile).glob(row['dataset']+'_'+row['name']+'_*.npz'))
    assert len(result)==(3 if row['dataset']=='mir1k' else 1),(row['name'],profile,'cache incompleta')
    return result

def condition_of(path,row):return path.stem[len(row['dataset']+'_'+row['name']+'_'):]

def export_tree(model):
    tree=model.tree_
    return {'feature':tree.feature.tolist(),'threshold':tree.threshold.tolist(),'left':tree.children_left.tolist(),'right':tree.children_right.tolist(),'probability':tree.value[:,0,1].tolist()}

def predict(tree,X):
    nodes=np.zeros(len(X),dtype=int)
    f=np.array(tree['feature']);threshold=np.array(tree['threshold']);left=np.array(tree['left']);right=np.array(tree['right'])
    while np.any(f[nodes]>=0):
        ids=np.flatnonzero(f[nodes]>=0);nd=nodes[ids]
        nodes[ids]=np.where(X[ids,f[nd]]<=threshold[nd],left[nd],right[nd])
    return np.array(tree['probability'])[nodes]

def replay(z,accepted,profile):
    m=c.module();config,accept=c.ui_policy();state=c.SimpleNamespace(_ultimo_punto_usuario=None)
    ts=[];fs=[];last=0.;pos=0
    for start,size in zip(z['starts'],z['sizes']):
        sl=slice(pos,pos+size);pos+=size
        m._energia_por_tiempo=lambda *a,**k:z['e'][sl]
        t,f=m._filtrar_pitch_tiempo_real(z['t'][sl],z['f'][sl].copy(),np.zeros(1),44100,periodicidad=accepted[sl].astype(float))
        t=t+start;new=t>last
        if np.any(new):
            last=float(t[new].max())
            for ti,fi in zip(t[new],f[new]):
                if profile=='clasica' or accept(state,[float(ti),float(69+12*np.log2(fi/440))]):ts.append(ti);fs.append(fi)
    return counts(z['ref'],align(np.array(ts),np.array(fs),z['rt'],1024/44100/2))[0]

def summarize(rows):return c.aggregate(rows)

def evaluate(rows,models,profile,folder):
    folder=OUT/folder;folder.mkdir(exist_ok=True);result=[]
    signature={'models':models,'profile':profile,'tracks':[(r['dataset'],r['name']) for r in rows],
               'baseline_sha256':hashlib.sha256((c.OUT/'pitch_base.py').read_bytes()).hexdigest()}
    signature=json.loads(json.dumps(signature))
    protocol=OUT/(folder.name+'_protocolo.json')
    if protocol.exists():assert json.loads(protocol.read_text())==signature,'Protocolo diferente'
    else:c.save(protocol,signature)
    for i,row in enumerate(rows,1):
        dest=folder/(row['dataset']+'_'+row['name']+'.json')
        if dest.exists():result.append(json.loads(dest.read_text()));continue
        record={**row,'metrics':{}}
        for path in paths(row,profile):
            with np.load(path) as archive:
                z={key:archive[key] for key in archive.files}
                preds={'base':z['p']>=.7}
                for name,model in models.items():
                    preds[name]=(predict(model['tree'],z['X'])>=model['cutoff'])&(z['p']>=.35)
                record['metrics'][condition_of(path,row)]={name:replay(z,mask,profile) for name,mask in preds.items()}
        c.save(dest,record);result.append(record)
        print(folder.name,i,len(rows),row['dataset'],row['name'],flush=True)
    summary=summarize(result);c.save(OUT/(folder.name+'_resumen.json'),summary)
    return summary

def main():
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['cache','train','tune','validate','classic','all']);args=p.parse_args()
    OUT.mkdir(exist_ok=True);inv=partition()
    pp=OUT/'particion.json'
    if pp.exists():assert json.loads(pp.read_text(encoding='utf-8'))==inv
    else:c.save(pp,inv)
    if args.phase in ['cache','classic']:
        profile='clasica' if args.phase=='classic' else 'desktop'
        for i,row in enumerate(inv,1):
            build_cache(row,profile);print('cache',profile,i,len(inv),row['dataset'],row['name'],flush=True)
        if args.phase=='cache':return
    if args.phase=='train':
        arrays=[];labels=[];weights=[]
        # Cada escenario pesa igual; positivos por tiempo vocal y negativos por silencio.
        records=[];totals={}
        for row in inv:
            if row['stage']!='entrenamiento':continue
            for path in paths(row,'desktop'):
                z=np.load(path);group=row['dataset']+'/'+condition_of(path,row);ref=z['target'];f=z['f']
                voiced=ref>0;correct=voiced&(abs(1200*np.log2(np.maximum(f,1)/np.maximum(ref,1)))<=50)
                records.append((group,z['X'],voiced,correct));z.close()
                a,b=totals.get(group,(0,0));totals[group]=(a+int(voiced.sum()),b+int((~voiced).sum()))
        for group,X,voiced,correct in records:
            nv,nu=totals[group]
            # Los errores de frecuencia con voz no se usan como ejemplos negativos.
            weight=np.where(voiced,np.where(correct,1.,.05)/nv,.5/nu)
            arrays.append(X);labels.append(voiced);weights.append(weight)
        X=np.concatenate(arrays);target=np.concatenate(labels);weight=np.concatenate(weights)
        models={}
        for depth in [3,5,7]:
            model=DecisionTreeClassifier(max_depth=depth,min_samples_leaf=300,random_state=20260929)
            model.fit(X,target,sample_weight=weight)
            tree=export_tree(model)
            assert np.allclose(predict(tree,X[::101]),model.predict_proba(X[::101])[:,1])
            for cutoff in [.4,.5,.6]:models[f'arbol{depth}_{cutoff}']={'tree':tree,'cutoff':cutoff}
        c.save(OUT/'candidatos.json',models)
        c.save(OUT/'entrenamiento.json',{'features':FEATURES,'samples':len(X),'groups':totals,'depths':[3,5,7],'min_samples_leaf':300,'seed':20260929,'periodicity_floor':.35,'selection':'Mismos límites por escenario: acierto >= base-0.5, falsas <= base+1, omisiones <= base+0.5. Ganancia media aciertos-0.5*falsas >=0.2. Selección solo en ajuste, no entrenamiento ni validación.','script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
        print('Entrenado',len(X),'frames',flush=True);return
    if args.phase=='tune':
        models=json.loads((OUT/'candidatos.json').read_text());summary=evaluate([r for r in inv if r['stage']=='ajuste'],models,'desktop','ajuste')
        scores={v:float(np.mean([s[v]['pitch_correct_50c_pct']-.5*s[v]['false_voiced_pct'] for s in summary.values()])) for v in ['base',*models]}
        eligible=[v for v in models if all(s[v]['pitch_correct_50c_pct']>=s['base']['pitch_correct_50c_pct']-.5 and s[v]['false_voiced_pct']<=s['base']['false_voiced_pct']+1 and s[v]['missed_voiced_pct']<=s['base']['missed_voiced_pct']+.5 for s in summary.values()) and scores[v]>=scores['base']+.2]
        selected=max(eligible,key=lambda v:scores[v]) if eligible else 'base'
        c.save(OUT/'seleccion.json',{'selected':selected,'scores':scores,'eligible':eligible})
        if selected!='base':c.save(OUT/'modelo.json',{'name':selected,**models[selected],'features':FEATURES,'periodicity_floor':.35})
        print('SELECCION',selected,scores,flush=True);return
    choice=json.loads((OUT/'seleccion.json').read_text())['selected']
    models={} if choice=='base' else {choice:json.loads((OUT/'modelo.json').read_text())}
    if args.phase=='validate':evaluate([r for r in inv if r['stage']=='validacion'],models,'desktop','validacion')
    elif args.phase=='classic':evaluate(inv,models,'clasica','clasica')
    elif args.phase=='all':evaluate(inv,models,'desktop','todos')

if __name__=='__main__':main()
