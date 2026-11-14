"""Auditoría y resumen del filtro aprendido: distingue ajuste de validación."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.calibrar_multidataset import aggregate,save
from scripts.informe_calibracion import verdict
OUT=ROOT/'output/filtro_aprendido'
LABELS={'vocadito/voz':'Vocadito, voz','mdb/voz':'MDB, voz','mir1k/voz':'MIR-1K, voz','mir1k/musica10':'MIR-1K, voz +10 dB','mir1k/musica0':'MIR-1K, voz/música 0 dB'}

def main():
    choice=json.loads((OUT/'seleccion.json').read_text())['selected']
    inv=json.loads((OUT/'particion.json').read_text(encoding='utf-8'))
    for ds in ['vocadito','mir1k','mdb']:
        groups=[{r['group'] for r in inv if r['dataset']==ds and r['stage']==stage} for stage in ['entrenamiento','ajuste','validacion']]
        assert all(groups[i].isdisjoint(groups[j]) for i in range(3) for j in range(i))
    old={}
    for ds,path in [('vocadito','vocadito_mejoras/comparacion_live.json'),('mir1k','mir1k_evaluacion/resultados.json'),('mdb','mdb_evaluacion/resultados.json')]:
        data=json.loads((ROOT/'output'/path).read_text());old[ds]={r['track']:r for r in data['per_track']}
    summaries={};checked=0
    for folder in ['validacion','todos','clasica']:
        rows=[json.loads(p.read_text()) for p in (OUT/folder).glob('*.json')]
        expected=[r for r in inv if r['stage']=='validacion'] if folder=='validacion' else inv
        assert {(r['dataset'],r['name']) for r in rows}=={(r['dataset'],r['name']) for r in expected},folder
        summaries[folder]=aggregate(rows)
        if folder=='clasica':summaries['clasica_validacion']=aggregate([r for r in rows if r['stage']=='validacion'])
        if folder=='todos':
            for r in rows:
                ds=r['dataset']
                for condition,m in r['metrics'].items():
                    key={'voz':'voz_sola_despues','musica10':'musica_10dB_despues','musica0':'musica_0dB_despues'}[condition] if ds=='mir1k' else ('desktop_despues' if ds=='vocadito' else 'despues')
                    assert m['base']==old[ds][r['name']]['metrics'][key]['counts'],(ds,r['name'],condition)
                    checked+=1
    assert checked==385
    checks={phase:verdict(s,choice) for phase,s in summaries.items()}
    save(OUT/'comparacion_final.json',{'selected':choice,'summaries':summaries,'checks':checks,'exact_baseline_comparisons':checked})
    model=json.loads((OUT/'modelo.json').read_text()) if choice!='base' else None
    lines=['# Entrenamiento y evaluación del filtro de aceptación de YIN','',
        f'Propuesta seleccionada: **{choice}**. La comparación usa como base el filtro existente con periodicidad mínima 0,7, no la versión anterior a esa mejora.', '',
        '**Integración:** activado explícitamente en `desktop_live.py` (interfaz nueva), usando el mismo backend compartido. La llamada normal del backend y `app.py` conservan el filtro previo. No se cambió el análisis pYIN/WORLD ni el almacenamiento. Reiniciar la aplicación para cargar el cambio.', '',
        '**Corrección de alcance:** los archivos llamados `clasica` en este experimento corresponden a los valores predeterminados del backend (ventana 0,38 s, intervalo 0,06 s). Al verificar la conexión se constató que `app.py` pasa 0,7 s y 0,1 s. Por tanto, esa prueba no representa la interfaz clásica real. Se conserva como prueba adicional de otra configuración; no superó el límite de pérdida de notas en MDB y no justifica activar el modelo en otras configuraciones. La interfaz clásica real no fue evaluada con el modelo y permanece sin cambios.', '',
        '![Resultados de validación](validacion.png)', '',
        '## Datos y partición','',
        '| Dataset | Entrenamiento | Ajuste | Validación | Total disponible usado |','|---|---:|---:|---:|---:|',
        '| Vocadito | 19 | 11 | 10 | 40 |','| MIR-1K | 45 | 20 | 30 | 95 de 1.000 |','| MDB-stem-synth, voz | 36 | 9 | 15 | 60 de 60 pistas vocales |','| Total | 100 | 40 | 55 | 195 |','',
        'Se procesó cada grabación completa. MIR-1K se probó con voz sola, voz 10 dB sobre el acompañamiento y voz/música al mismo nivel. Las 170 pistas instrumentales de MDB no se incluyeron. Los grupos se separaron por cantante en Vocadito/MIR y por artista en MDB; canciones de un mismo artista de MDB permanecen juntas.', '',
        '**Alcance de la validación:** las 55 grabaciones no se usaron para entrenar ni elegir este modelo. Sin embargo, los datasets se habían inspeccionado en trabajos anteriores: esta es validación interna agrupada y no un nuevo test externo. MDB contiene voz resintetizada. Las distintas ventanas de un audio se solapan y no son observaciones independientes.', '',
        '## Qué se entrenó','',
        'YIN sigue calculando la frecuencia fundamental. Se entrenó un árbol de decisión que decide si aceptar cada candidato a partir de nueve características: periodicidad, energía relativa, logaritmo del RMS, periodicidad de ambos vecinos, saltos mínimo y máximo de frecuencia a los vecinos, periodicidad media y proporción de candidatos periódicos en la ventana. No se usa el nombre del dataset, cantante, canción ni el tono absoluto como característica.', '',
        'Las etiquetas indican presencia de voz según la referencia. Los ejemplos vocales cuya frecuencia YIN coincide dentro de ±50 cents reciben peso 1; los demás ejemplos vocales peso 0,05. Los negativos sin voz reciben peso 0,5. Se normaliza por el número de instantes vocales/no vocales de cada escenario para que MDB no domine por su duración. Los árboles usan profundidades máximas 3, 5 y 7, mínimo de 300 observaciones por hoja y semilla fija. En ajuste se comparan umbrales 0,4, 0,5 y 0,6. El valor del árbol es una puntuación basada en estos pesos, no una probabilidad calibrada de acierto.', '',
        'Se mantiene un piso de periodicidad 0,35 y los filtros de energía, duración mínima y saltos. No se crean nuevas frecuencias ni se modifica pYIN/WORLD. La decisión usa muestras que ya están dentro de la ventana de la aplicación, sin añadir espera por audio futuro.', '',
        '## Selección y experimentos descartados','',
        'Antes del árbol se exploraron tres familias de reglas manuales en la partición de calibración. Bajar el umbral e introducir continuidad causó demasiadas falsas detecciones; la mejor regla conservadora mejoró solo 0,151 puntos el objetivo de calibración, por debajo del mínimo 0,2 fijado. Esas reglas no se integraron y sus archivos se conservan en `output/calibracion_multidataset*`.', '',
        'La selección del árbol usa únicamente las 40 grabaciones de ajuste. Objetivo: promedio de (porcentaje de aciertos − 0,5 × porcentaje de falsas notas), con el mismo peso para los cinco escenarios. Requisitos por escenario: no perder más de 0,5 puntos de acierto, no aumentar más de 1 punto las falsas notas ni más de 0,5 puntos las omisiones. Se exige mejorar el objetivo medio en al menos 0,2 puntos. El modelo queda congelado antes de la validación.', '']
    for phase,title in [('validacion','Validación: interfaz nueva'),('clasica_validacion','Validación adicional: valores predeterminados del backend'),('todos','Todos los datos: interfaz nueva (incluye entrenamiento y ajuste)'),('clasica','Todos los datos: valores predeterminados del backend')]:
        lines+=['## '+title,'','| Escenario | Aciertos base → modelo | Falsas notas base → modelo | Omisiones base → modelo |','|---|---:|---:|---:|']
        for group,s in summaries[phase].items():
            a,b=s['base'],s[choice]
            cells=[f'{a[k]:.2f}% → {b[k]:.2f}%' for k in ['pitch_correct_50c_pct','false_voiced_pct','missed_voiced_pct']]
            lines.append('| '+LABELS[group]+' | '+' | '.join(cells)+' |')
        lines+=['',f"Límites de regresión y objetivo positivo: **{'cumple' if checks[phase]['passes'] else 'no cumple'}**. Cambio del objetivo: {checks[phase]['objective_gain']:+.3f} puntos.",'']
    intervals=json.loads((OUT/'intervalos_validacion.json').read_text())
    lines+=['## Variabilidad entre cantantes y artistas','',
        'Se hizo un bootstrap pareado de 2.000 repeticiones, remuestreando grupos completos de la validación, no frames independientes. Los intervalos percentiles del 95% son exploratorios: hay solo seis cantantes de MIR y nueve grupos de cada uno de los otros datasets en validación. No corrigen la inspección histórica de los datasets.', '',
        '| Escenario | Cambio en aciertos: intervalo 95% (pp) | Cambio en falsas notas: intervalo 95% (pp) |','|---|---:|---:|']
    for group,value in intervals['results'].items():
        a=value['percentile_95']['aciertos_pp'];b=value['percentile_95']['falsas_pp']
        lines.append(f'| {LABELS[group]} | [{a[0]:+.2f}, {a[1]:+.2f}] | [{b[0]:+.2f}, {b[1]:+.2f}] |')
    lines+=['','Los aumentos puntuales de acierto no deben interpretarse como mejoras garantizadas para cualquier cantante; varios intervalos incluyen cero.', '',
        '## Medición y reproducibilidad','',
        'Acierto: frecuencia dentro de ±50 cents de la referencia, dividido por todos los instantes con voz. Las omisiones cuentan como fallos. Falsas notas: detecciones durante instantes sin voz, divididas por todos esos instantes. Estos porcentajes tienen denominadores diferentes y no se suman.', '',
        'Interfaz nueva: ventana de 0,24 s, actualización de 0,10 s y política real de aceptación de saltos. Prueba adicional del backend: ventana de 0,38 s y actualización de 0,06 s. Ambas pruebas usan 44,1 kHz, salto de análisis de 1.024 muestras y la alineación por vecino más cercano dentro de medio salto. No se simulan hardware, colas ni piso de ruido de un micrófono calibrado.', '',
        f'Se comprobaron **{checked} coincidencias exactas** entre las cuentas de la base en el replay y las evaluaciones previas de los tres datasets. Se verificó que no se compartan grupos entre entrenamiento, ajuste y validación.', '',
        'Archivos: `particion.json`, `entrenamiento.json`, `candidatos.json`, `seleccion.json`, `modelo.json` (si se seleccionó un modelo), `comparacion_final.json`, protocolos de cada fase, cachés de características y resultados por grabación. `scripts/entrenar_filtro.py` permite repetir las fases `cache`, `train`, `tune`, `validate`, `all`, `classic`; el informe se genera con `scripts/informe_filtro_aprendido.py`.', '',
        'El aprendizaje se realizó con scikit-learn. El modelo se exporta como números y reglas en JSON, sin pickle. La ejecución en la aplicación solo requiere NumPy. Si el modelo falta o no es válido se conserva el filtro anterior. Pasaron 12 pruebas automáticas, incluidas la selección explícita del filtro por sesión y su transmisión al worker. La integración se comprobó en 1.155 ventanas y cinco audios/condiciones completos de los tres datasets.', '',
        'Para una prueba externa futura deben reservarse nuevas grabaciones que no hayan intervenido en el diseño del filtro. Un resultado mejor con música no convierte a YIN en un separador de voz.', '']
    (OUT/'informe.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps(checks,indent=2))

if __name__=='__main__':main()
