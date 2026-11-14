"""Prueba de solo lectura sobre las referencias del catálogo; no cambia la app."""
from pathlib import Path
import csv
import hashlib
import json
import math

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'output/segmentacion_pausas'
PAUSAS = [.05, .1, .2, .3, .4, .6, .8, 1., 1.5, 2.]
NIVELES_DB = [-30, -35, -40]
PASO_S = .02
# Misma canción subida dos veces; conservar una sola para las pruebas.
IDS_EXCLUIDOS = {'qué_gano_olvidandote_84dce906'}


def intervalos(mask):
    edges = np.diff(np.r_[False, mask, False].astype(int))
    return list(zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)))


def segmentar(silencio, edges, pausa):
    active = np.flatnonzero(~silencio)
    if not len(active):
        return []
    start, stop = int(active[0]), int(active[-1])+1
    segments = []
    for a,b in intervalos(silencio):
        if a <= start or b >= stop or edges[b]-edges[a] < pausa-1e-9:
            continue
        segments.append({'inicio_s':float(edges[start]),'fin_s':float(edges[a])})
        start = b
    segments.append({'inicio_s':float(edges[start]),'fin_s':float(edges[stop])})
    return segments


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    results=[]
    for metadata in sorted((ROOT/'canciones').glob('*/metadata.json')):
        song=json.loads(metadata.read_text(encoding='utf-8'))
        if song['id'] in IDS_EXCLUIDOS and (ROOT/'canciones/que_gano_olvidandote_a7c974ca/metadata.json').exists():
            continue
        path=ROOT/song['vocals'];csvpath=ROOT/song['pitch_referencia']
        y,sr=sf.read(path,dtype='float32',always_2d=True)
        duration=len(y)/sr
        hop=round(sr*PASO_S)
        power=np.mean(y.astype(float)**2,axis=1)
        n=math.ceil(len(power)/hop)
        widths=np.minimum(hop,len(power)-np.arange(n)*hop)
        rms=np.sqrt(np.pad(power,(0,n*hop-len(power))).reshape(n,hop).sum(axis=1)/widths)
        edges=np.r_[np.arange(n)*hop/sr,duration]
        centers=(edges[:-1]+edges[1:])/2
        with csvpath.open(encoding='utf-8',newline='') as f:
            rows=list(csv.DictReader(f))
        t=np.array([float(r['tiempo']) for r in rows]);pitch=np.array([float(r['frecuencia']) for r in rows])
        good=np.isfinite(t)&np.isfinite(pitch)&(t>=0)&(t<=duration)&(pitch>0)
        t=np.sort(t[good])
        voiced=np.zeros(n,dtype=bool)
        if len(t):
            right=np.clip(np.searchsorted(t,centers),0,len(t)-1);left=np.maximum(0,right-1)
            voiced=np.minimum(abs(centers-t[left]),abs(centers-t[right]))<=.025
        level=float(np.percentile(rms,95))
        db=20*np.log10(np.maximum(rms,1e-12)/max(level,1e-12))
        entry={'id':song['id'],'titulo':song['titulo'],'artista':song.get('artista'),
               'duracion_s':duration,'bloques_fijos_5s':math.ceil(duration/5),
               'audio_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
               'pitch_sha256':hashlib.sha256(csvpath.read_bytes()).hexdigest(),
               'rms_p95':level,'comparaciones':{}}
        for threshold in NIVELES_DB:
            quiet=(db<=threshold)&~voiced if level>1e-10 else np.ones(n,dtype=bool)
            data={}
            for pause in PAUSAS:
                segments=segmentar(quiet,edges,pause)
                lengths=np.array([s['fin_s']-s['inicio_s'] for s in segments])
                data[str(pause)]={'cantidad':len(segments),'duracion_mediana_s':float(np.median(lengths)) if len(lengths) else None,
                                  'duracion_maxima_s':float(max(lengths)) if len(lengths) else None,
                                  'menores_1s':int((lengths<1).sum()),'segmentos':segments}
                assert all(0<=s['inicio_s']<s['fin_s']<=duration for s in segments)
                assert all(b['inicio_s']-a['fin_s']>=pause-1e-9 for a,b in zip(segments,segments[1:]))
            assert all(data[str(a)]['cantidad']>=data[str(b)]['cantidad'] for a,b in zip(PAUSAS,PAUSAS[1:]))
            entry['comparaciones'][str(threshold)]=data
        results.append(entry)
        print(song['id'],duration,{p:entry['comparaciones']['-35'][str(p)]['cantidad'] for p in PAUSAS},flush=True)
    doc={'metodo':'Pausa = energía RMS baja en voz separada Y ausencia de pitch de referencia a <=25ms. RMS por bloques de 20ms; nivel relativo al percentil 95. Sin unir ni eliminar segmentos pequeños.',
         'nivel_principal_db':-35,'niveles_sensibilidad_db':NIVELES_DB,'pausas_s':PAUSAS,
         'limites':'Pausas estimadas en stems separados, no silencio manual anotado. El sangrado instrumental o errores de pitch pueden ocultar pausas. Inicio y final sin actividad se excluyen. No se modificó el catálogo ni el backend.',
         'canciones':results}
    (OUT/'resultados.json').write_text(json.dumps(doc,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
    lines=['# Prueba de segmentación por pausas','',doc['metodo'],'',doc['limites'],'',
           '| Canción (ID) | Bloques fijos 5 s | '+' | '.join(f'Pausa {p:g} s' for p in PAUSAS)+' |',
           '|---|---:|'+'---:|'*len(PAUSAS)]
    for r in results:
        counts=[str(r['comparaciones']['-35'][str(p)]['cantidad']) for p in PAUSAS]
        lines.append(f"| {r['titulo']} ({r['id']}) | {r['bloques_fijos_5s']} | "+' | '.join(counts)+' |')
    lines+=['','El nivel principal es −35 dB respecto del RMS P95 de cada voz separada. Es un parámetro experimental. Los bloques fijos incluyen toda la duración; los segmentos vocales excluyen pausas largas y extremos sin actividad, por lo que no representan la misma cobertura temporal.','',
            '## Sensibilidad al nivel de silencio','',
            '| Canción (ID) | Pausa mínima | Segmentos a −30 dB | A −35 dB | A −40 dB | Mediana a −35 dB | Máximo a −35 dB | Menores de 1 s a −35 dB |',
            '|---|---:|---:|---:|---:|---:|---:|---:|']
    for r in results:
        for p in PAUSAS:
            v=r['comparaciones']['-35'][str(p)]
            counts=[str(r['comparaciones'][str(db)][str(p)]['cantidad']) for db in NIVELES_DB]
            median='—' if v['duracion_mediana_s'] is None else f"{v['duracion_mediana_s']:.2f} s"
            maximum='—' if v['duracion_maxima_s'] is None else f"{v['duracion_maxima_s']:.2f} s"
            lines.append(f"| {r['titulo']} ({r['id']}) | {p} s | "+' | '.join(counts)+f" | {median} | {maximum} | {v['menores_1s']} |")
    lines+=['','Los tiempos exactos de cada segmento y los hashes de las entradas están en `resultados.json`. Para reproducir: `python scripts/probar_segmentacion_pausas.py`.','']
    (OUT/'informe.md').write_text('\n'.join(lines),encoding='utf-8')


if __name__=='__main__':main()
