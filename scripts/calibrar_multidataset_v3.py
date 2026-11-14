"""Familia final: recuperación bilateral solo en ventanas de alta periodicidad."""
from pathlib import Path
import sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts import calibrar_multidataset as c
c.OUT=ROOT/'output/calibracion_multidataset_v3'
# Umbral fuerte, umbral del hueco, fracción mínima de candidatos fuertes.
c.VARIANTS={'base':(.7,.7,1.),'energia012':(.7,.7,1.),
            'apoyo065':(.7,.5,.65),'apoyo080':(.7,.5,.8)}

def mask(f0,p,start,minimum,fraction):
    valid=(f0>0)&(p>=start)
    result=valid.copy()
    if np.mean(valid)<fraction:return result
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
        # La energía es idéntica para todas las variantes; se calcula una vez.
        energy=m._energia_por_tiempo(signal,rate,t)
        energy_fn=m._energia_por_tiempo
        m._energia_por_tiempo=lambda *a,**k:energy
        try:
            for v in variants:
                conf=p if v=='base' else mask(f0,p,*c.VARIANTS[v]).astype(float)
                cfg=dict(m.FILTRO_TIEMPO_REAL,factor_rms_max=.08 if v=='base' else .12)
                captured[v]=original(t,f0.copy(),signal,rate,periodicidad=conf,config=cfg,**kw)
        finally:m._energia_por_tiempo=energy_fn
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
    c.save(c.OUT/'familia.json',{'description':'Umbral fuerte 0.7; recupera un hueco de al menos 0.5 entre dos candidatos fuertes a <=1 semitono, solo con fracción fuerte >=0.65 o >=0.8. Energía relativa 0.12 (base 0.08). Sin latencia adicional.',
        'variants':c.VARIANTS,'previous_families':'Pruebas exploratorias interrumpidas tras descartar variantes por límites de calibración en Vocadito/MIR. Los resultados parciales se conservan. Se retiene energía 0.12 para evaluación completa en esta familia.',
        'parent_script_sha256':c.hashlib.sha256((ROOT/'scripts/calibrar_multidataset.py').read_bytes()).hexdigest()})
    c.main()
