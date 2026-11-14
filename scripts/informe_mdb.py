"""Informe reproducible de la evaluación vocal completa de MDB-stem-synth."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/mdb_evaluacion'


def main():
    r = json.loads((OUT/'resultados.json').read_text(encoding='utf-8'))
    assert r['tracks'] == 60 and len(r['per_track']) == 60
    metrics = [
        ('pitch_correct_50c_pct', 'Tono correcto cuando hay voz', 'Mayor es mejor'),
        ('false_voiced_pct', 'Detecta notas cuando no hay voz', 'Menor es mejor'),
        ('missed_voiced_pct', 'No detecta una nota cuando hay voz', 'Menor es mejor'),
        ('octave_error_pct', 'Errores de una octava', 'Menor es mejor'),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.4), layout='constrained')
    for ax, (key, title, direction) in zip(axes, metrics):
        values = [r['summary'][v][key] for v in ['antes', 'despues']]
        bars = ax.bar(['Anterior', 'Mejorado'], values, color=['#8594ab', '#168b8b'], width=.6)
        ax.bar_label(bars, labels=[f'{v:.2f}%' for v in values], padding=5)
        ax.set_ylim(0, 106)
        ax.set_ylabel('Porcentaje')
        ax.set_title(title+'\n'+direction, fontsize=10)
        ax.spines[['top', 'right']].set_visible(False)
        ax.set_axisbelow(True)
        ax.grid(axis='y', alpha=.2)
    fig.suptitle('MDB-stem-synth · las 60 pistas vocales completas\nYIN en vivo, configuración de la interfaz nueva', fontsize=13)
    fig.savefig(OUT/'comparacion.png', dpi=170)
    plt.close(fig)
    lines = [
        '# Evaluación externa con MDB-stem-synth', '',
        f"Se evaluaron **60 de 60 pistas vocales identificadas**, completas, de {r['songs']} canciones: **{r['duration_s']/60:.2f} minutos** de audio. El dataset completo tiene 230 pistas; las otras 170 son instrumentales y no forman parte de esta prueba.", '',
        'Las etiquetas originales clasifican 41 pistas como `male singer` y 19 como `female singer`. Son pistas, no un recuento de personas distintas. La selección incluye todas las etiquetas que contienen `singer` o `vocal`, sin elegir ejemplos por su resultado.', '',
        '## Resultado', '',
        '| Medida | Anterior | Mejorado | Cambio (puntos porcentuales) |',
        '|---|---:|---:|---:|',
    ]
    for key, title, direction in metrics:
        a, b = [r['summary'][v][key] for v in ['antes', 'despues']]
        lines.append(f'| {title} ({direction.lower()}) | {a:.2f}% | {b:.2f}% | {b-a:+.2f} |')
    a,b=r['summary']['antes'],r['summary']['despues']
    if b['pitch_correct_50c_pct'] < a['pitch_correct_50c_pct'] and b['false_voiced_pct'] < a['false_voiced_pct']:
        lines += ['', '**Interpretación:** el filtro actual produce menos notas falsas, pero también pierde aciertos y omite más voz. En este conjunto no hay una mejora general de la detección: el coste en notas válidas debe considerarse junto con la reducción de falsas detecciones.', '',
                  'El siguiente ajuste debería estudiar cuándo aplicar el filtro de periodicidad de forma menos estricta. Si se usan estas pistas para diseñarlo, pasarán a ser datos de desarrollo; la comprobación final deberá reservar canciones distintas y mantener las pruebas de ruido y mezcla musical.']
    lines += ['', '![Comparación antes/después](comparacion.png)', '',
        '“Tono correcto” significa estar a menos de medio semitono (50 cents) de la referencia cuando hay voz. Las notas omitidas cuentan como fallos. Las falsas notas se calculan sobre los instantes sin voz; por eso estos porcentajes no deben sumarse. El error de octava usa una distancia de 1.200 ± 50 cents y se divide por todos los instantes con voz.', '',
        'Los porcentajes principales agrupan todos los instantes de referencia: las pistas largas pesan más. Como comprobación, el promedio que da el mismo peso a cada pista es '
        f"{r['summary']['antes']['macro_pitch_correct_50c_pct']:.2f}% → {r['summary']['despues']['macro_pitch_correct_50c_pct']:.2f}% de tono correcto.", '',
        '## Desglose por etiqueta original', '',
        '| Etiqueta | Tono correcto anterior | Tono correcto mejorado | Falsas notas anterior | Falsas notas mejorado |',
        '|---|---:|---:|---:|---:|']
    for label, group in r['by_instrument'].items():
        a,b=group['antes'],group['despues']
        lines.append(f"| {label} | {a['pitch_correct_50c_pct']:.2f}% | {b['pitch_correct_50c_pct']:.2f}% | {a['false_voiced_pct']:.2f}% | {b['false_voiced_pct']:.2f}% |")
    changes = sorted(r['per_track'], key=lambda p: p['metrics']['despues']['pitch_correct_50c_pct']-p['metrics']['antes']['pitch_correct_50c_pct'])
    better=sum(p['metrics']['despues']['pitch_correct_50c_pct']>p['metrics']['antes']['pitch_correct_50c_pct'] for p in changes)
    worse=sum(p['metrics']['despues']['pitch_correct_50c_pct']<p['metrics']['antes']['pitch_correct_50c_pct'] for p in changes)
    lines += ['', f'El tono correcto subió en {better} pistas, bajó en {worse} y quedó igual en {60-better-worse}.', '',
        '### Cinco pistas con el cambio menos favorable', '',
        '| Pista | Anterior | Mejorado | Cambio |', '|---|---:|---:|---:|']
    for p in changes[:5]:
        a,b=[p['metrics'][v]['pitch_correct_50c_pct'] for v in ['antes','despues']]
        lines.append(f"| {p['track']} | {a:.2f}% | {b:.2f}% | {b-a:+.2f} pp |")
    voiced=r['summary']['antes']['counts']['voiced']
    lines += ['', '## Método y límites', '',
        '- Se descargó el archivo oficial completo y se verificó su MD5; también se verificaron los 60 audios y sus 60 referencias contra el índice de mirdata.',
        '- Se comparó el YIN anterior con el YIN mejorado, usando ventanas de 0,24 s, actualizaciones de 0,10 s y la política real de aceptación de saltos de la interfaz nueva. Se mantuvieron los parámetros del algoritmo; este dataset no se usó para reajustarlos.',
        '- Se procesó cada audio completo, con silencios incluidos. La simulación usa voz aislada y no estima un piso de ruido del micrófono. No reproduce hardware, colas ni pérdidas de audio de una sesión real.',
        '- La referencia empieza en 0 s y avanza 128/44.100 s. Las predicciones se alinean al instante más cercano con tolerancia de medio salto de análisis (1.024/44.100/2 s); no se interpolan huecos sin notas.',
        '- Esta prueba evalúa únicamente YIN en vivo con la interfaz nueva. No mide pYIN de canciones guardadas ni la configuración de la interfaz clásica.',
        '- MDB-stem-synth contiene voces resintetizadas a partir de grabaciones. Permite una referencia de frecuencia conocida, pero no sustituye una prueba con micrófono y voces naturales, ni demuestra que funcione mejor sobre voz mezclada con música.',
        f"- Referencia fuera del rango nominal C2–C6: {r['reference_below_C2']} instantes por debajo y {r['reference_above_C6']} por encima, de {voiced} instantes con voz ({100*(r['reference_below_C2']+r['reference_above_C6'])/voiced:.3f}%). No se excluyeron del cálculo.", '',
        '## Reproducibilidad y fuentes', '',
        '- [Archivo oficial y licencia CC BY-NC 4.0](https://zenodo.org/records/1481172).',
        '- [Descripción del dataset y publicación](https://synthdatasets.weebly.com/mdb-stem-synth.html).',
        '- [Índice de mirdata](https://zenodo.org/records/14042058).',
        '- [Metadatos MedleyDB fijados a una revisión](https://github.com/marl/medleydb/tree/537bb7bad0601fc58e4fff8404f71658b86ef60e/medleydb/data/Metadata).',
        '- `protocolo.json`: versiones, parámetros y hashes de código. `resultados.json`: métricas agregadas y por pista. `predicciones/`: referencia y predicciones alineadas. `data/mdb_stem_synth/manifest.json`: inventario de las 230 pistas y selección vocal.', '',
        'Para reproducir desde la raíz del proyecto: `python scripts/preparar_mdb.py`, `python scripts/evaluar_mdb.py` y `python scripts/informe_mdb.py`.', '',
        'El código de producción no se modificó durante esta evaluación.', '',
    ]
    (OUT/'informe.md').write_text('\n'.join(lines), encoding='utf-8')
    print(OUT/'informe.md')


if __name__ == '__main__':
    main()
