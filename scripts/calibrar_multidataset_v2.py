"""Segunda familia: huecos con apoyo bilateral y filtro de energía."""
from pathlib import Path
import sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts import calibrar_multidataset as c

c.OUT=ROOT/'output/calibracion_multidataset_v2'
# (umbral periódico, mínimo para recuperar un hueco, energía relativa máxima).
c.VARIANTS={'base':(.7,.7,.08),'puente050':(.7,.5,.08),'puente060':(.7,.6,.08),
            'energia012':(.7,.7,.12),'energia020':(.7,.7,.2),'energia030':(.7,.7,.3),
            'relax060_e020':(.6,.6,.2),'relax060_e030':(.6,.6,.3),
            'puente050_e012':(.7,.5,.12),'puente050_e020':(.7,.5,.2)}

def mask(f0,p,start,minimum,unused):
    valid=(f0>0)&(p>=start)
    result=valid.copy()
    for i in range(1,len(f0)-1):
        if not valid[i] and f0[i]>0 and p[i]>=minimum and valid[i-1] and valid[i+1]:
            if max(abs(12*np.log2(f0[i]/f0[i-1])),abs(12*np.log2(f0[i]/f0[i+1])))<=1:
                result[i]=True
    return result

def run_signal(y,sr,variants,profile):
    m=c.module();original=m._filtrar_pitch_tiempo_real
    config,accept=c.ui_policy()
    interval,window=(config['LIVE_PITCH_INTERVAL'],config['LIVE_PITCH_CHUNK']) if profile=='desktop' else (.06,.38)
    states={v:dict(last=0.,ui=c.SimpleNamespace(_ultimo_punto_usuario=None),ts=[],fs=[]) for v in variants}
    captured={}
    def filt(t,f0,signal,rate,**kw):
        p=kw.pop('periodicidad')
        for v in variants:
            start,minimum,energy=c.VARIANTS[v]
            conf=p if v=='base' else mask(f0,p,start,minimum,energy).astype(float)
            cfg=dict(m.FILTRO_TIEMPO_REAL,factor_rms_max=energy)
            captured[v]=original(t,f0.copy(),signal,rate,periodicidad=conf,config=cfg,**kw)
        return captured[variants[0]]
    m._filtrar_pitch_tiempo_real=filt
    for end in np.arange(interval,len(y)/sr,interval):
        start=max(0.,end-window);captured.clear()
        m.extraer_pitch_ligero_desde_audio(y[int(start*sr):int(end*sr)],sr)
        for v,(t,f) in captured.items():
            state=states[v];t=t+start;new=t>state['last']
            if np.any(new):
                state['last']=float(t[new].max())
                for ti,fi in zip(t[new],f[new]):
                    if profile=='clasica' or accept(state['ui'],[float(ti),float(69+12*np.log2(fi/440))]):
                        state['ts'].append(ti);state['fs'].append(fi)
    return {v:(np.asarray(s['ts']),np.asarray(s['fs'])) for v,s in states.items()}

c.run_signal=run_signal
c.__file__=__file__
if __name__=='__main__':
    c.OUT.mkdir(exist_ok=True)
    c.save(c.OUT/'familia.json',{'description':'Recupera solo un hueco con periodicidad mínima entre dos candidatos fuertes, distantes como máximo 1 semitono; filtro de energía relativo. Sin estado entre llamadas ni latencia adicional.',
        'variants':c.VARIANTS,'first_family':'Descartada en calibración por superar el límite de falsas notas; no se consultó validación.',
        'selection_constraints':'Mismos límites y objetivo de la primera familia.',
        'parent_script_sha256':c.hashlib.sha256((ROOT/'scripts/calibrar_multidataset.py').read_bytes()).hexdigest()})
    c.main()
