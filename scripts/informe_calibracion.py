"""Audita particiones y resume calibración/validación sin seleccionar parámetros."""
from pathlib import Path
import json,sys,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.calibrar_multidataset import aggregate,save
OUT=ROOT/'output/calibracion_multidataset_v3'

def verdict(summary,selected):
    changes={g:{k:s[selected][k]-s['base'][k] for k in ['pitch_correct_50c_pct','false_voiced_pct','missed_voiced_pct']} for g,s in summary.items()}
    gain=float(np.mean([d['pitch_correct_50c_pct']-.5*d['false_voiced_pct'] for d in changes.values()]))
    ok=all(d['pitch_correct_50c_pct']>=-.5 and d['false_voiced_pct']<=1 and d['missed_voiced_pct']<=.5 for d in changes.values()) and gain>0
    return {'passes':ok,'objective_gain':gain,'changes':changes}

def main():
    inv=json.loads((OUT/'particion.json').read_text(encoding='utf-8'))
    selected=json.loads((OUT/'seleccion.json').read_text())['selected']
    for ds in ['vocadito','mir1k','mdb']:
        a={r['group'] for r in inv if r['dataset']==ds and r['split']=='calibracion'}
        b={r['group'] for r in inv if r['dataset']==ds and r['split']=='validacion'}
        assert a.isdisjoint(b)
    groups={}
    for phase in ['calibracion','validacion','clasica']:
        rows=[json.loads(p.read_text(encoding='utf-8')) for p in (OUT/phase).glob('*.json')]
        expected=inv if phase=='clasica' else [r for r in inv if r['split']==phase]
        assert {(r['dataset'],r['name']) for r in rows}=={(r['dataset'],r['name']) for r in expected},phase
        for r in rows:
            r['metrics']={condition:{v:m[v] for v in ['base',selected]} for condition,m in r['metrics'].items()}
        groups[phase]=rows
    summaries={phase:aggregate(rows) for phase,rows in groups.items()}
    summaries['todos_desktop']=aggregate(groups['calibracion']+groups['validacion'])
    # La interfaz clásica usa los mismos parámetros: comprobación adicional por partición.
    summaries['clasica_validacion']=aggregate([r for r in groups['clasica'] if r['split']=='validacion'])
    decision={phase:verdict(summaries[phase],selected) for phase in ['validacion','clasica_validacion','todos_desktop','clasica']}
    save(OUT/'comparacion_final.json',{'selected':selected,'summaries':summaries,'checks':decision})
    lines=['# Calibración del detector con tres datasets','',
        'Se calibraron parámetros del filtro de YIN; no se entrenó una red neuronal. Se utilizaron las 40 grabaciones de Vocadito, las 95 grabaciones disponibles de MIR-1K (de 1.000) y las 60 pistas vocales completas de MDB-stem-synth (de 230 pistas vocales e instrumentales).', '',
        '**Partición:** 140 grabaciones para calibración y 55 para validación. Vocadito: 30/10; MIR-1K: 65/30; MDB: 45/15. No se comparten cantantes entre particiones en Vocadito/MIR, ni artistas en MDB. Todas las condiciones de mezcla de una grabación quedan juntas.', '',
        '**Límite metodológico:** los tres datasets ya habían sido examinados anteriormente. Esta es una validación interna agrupada, no un test externo nunca visto. Las voces de MDB son resintetizadas. No se evaluó hardware de micrófono ni ruido ambiental real.', '',
        '## Selección', '',f'Variante seleccionada exclusivamente en calibración: **{selected}**.', '',
        'Se probaron umbrales fijos, continuidad limitada, recuperación bilateral de un hueco y ajustes de energía relativa. Se interrumpieron dos familias exploratorias tras descartar variantes por sus resultados de calibración en Vocadito/MIR; los resultados parciales se conservan en `output/calibracion_multidataset` y `output/calibracion_multidataset_v2`. La tercera familia restringe la recuperación a ventanas mayoritariamente periódicas e incluye el ajuste moderado de energía de la familia anterior. Sus resultados completos están en esta carpeta.', '',
        'Objetivo fijado: promedio de (aciertos − 0,5 × falsas detecciones), dando el mismo peso a los cinco escenarios. Para ser admisible, ningún escenario de calibración podía perder más de 0,5 puntos de aciertos, aumentar más de 1 punto las falsas detecciones ni aumentar más de 0,5 puntos las omisiones. La mejora del objetivo debía superar 0,2 puntos. Se congeló la selección antes de ejecutar validación.', '',
        '“Base” es la versión existente al iniciar esta calibración, con periodicidad mínima 0,7; no es la versión original sin ese filtro. Se evalúa el detector en vivo compartido por ambas interfaces. pYIN/WORLD de archivos no se recalibró.', '']
    labels={'vocadito/voz':'Vocadito, voz','mir1k/voz':'MIR-1K, voz','mdb/voz':'MDB, voz','mir1k/musica10':'MIR-1K, voz 10 dB sobre música','mir1k/musica0':'MIR-1K, voz/música igual nivel'}
    for phase,title in [('validacion','Validación reservada, interfaz nueva'),('todos_desktop','Todos los datos, interfaz nueva (incluye calibración)'),('clasica_validacion','Validación reservada, interfaz clásica'),('clasica','Todos los datos, interfaz clásica')]:
        lines += ['## '+title,'','| Escenario | Aciertos base → propuesta | Falsas notas base → propuesta | Omisiones base → propuesta |','|---|---:|---:|---:|']
        for g,s in summaries[phase].items():
            a,b=s['base'],s[selected]
            cells=[f'{a[k]:.2f}% → {b[k]:.2f}%' for k in ['pitch_correct_50c_pct','false_voiced_pct','missed_voiced_pct']]
            lines.append('| '+labels[g]+' | '+' | '.join(cells)+' |')
        lines+=['',f"Comprobación de límites: **{'cumple' if decision[phase]['passes'] else 'no cumple'}**. Cambio del objetivo medio: {decision[phase]['objective_gain']:+.3f} puntos.",'']
    lines+=['## Interpretación y reproducción','',
        'Los aciertos se miden sobre todos los instantes con voz, dentro de ±50 cents. Las omisiones cuentan como fallos. Las falsas detecciones se dividen por los instantes sin voz; los tres porcentajes no se suman. Dentro de cada escenario se agrupan los instantes; el objetivo da igual peso a cada escenario para que la duración de MDB no domine la selección.', '',
        'Ventanas e intervalos reales: interfaz nueva 0,24/0,10 s, con su filtro de saltos; interfaz clásica 0,38/0,06 s. Sin piso de ruido de micrófono. MIR-1K se remuestrea de 16 a 44,1 kHz y se usan las mismas mezclas normalizadas que en la evaluación previa. Las frecuencias se alinean por vecino más cercano con tolerancia de medio salto de análisis.', '',
        'Archivos: `particion.json`, `protocolo.json`, `familia.json`, `seleccion.json`, `comparacion_final.json` y resultados por grabación en las carpetas de cada fase. `pitch_base.py` conserva la versión previa. Los parámetros están en `scripts/calibrar_multidataset_v3.py`. Ejecutar sus fases `calibracion`, `validacion`, `clasica`, luego `python scripts/informe_calibracion.py`.', '',
        'La mejora sobre una mezcla con música no equivale a separar la voz: YIN sigue siendo un estimador monofónico y puede seguir instrumentos. Un futuro test externo debe usar grabaciones no utilizadas para diseñar estas familias de filtros.', '']
    (OUT/'informe.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps(decision,indent=2))

if __name__=='__main__':main()
