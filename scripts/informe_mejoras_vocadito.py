"""Informe antes/despues con resultados reales, sin repetir la inferencia."""
from pathlib import Path
import hashlib
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/vocadito_mejoras'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


old = read(ROOT / 'output/vocadito_benchmark/resultados.json')
new = read(OUT / 'evaluacion/resultados.json')
live = read(OUT / 'comparacion_live.json')
dev = read(OUT / 'desarrollo_live.json')
assert old['tracks'] == new['tracks'] == live['tracks'] == 40
assert old['pitch_sha256'] == live['before_sha256']
assert new['pitch_sha256'] == live['pitch_sha256'] == hashlib.sha256((ROOT / 'audio/pitch.py').read_bytes()).hexdigest()
assert live['summary']['all']['clasica_antes']['counts'] == old['summary']['yin_stream']['counts']
assert live['summary']['all']['clasica_despues']['counts'] == new['summary']['yin_stream']['counts']
assert float(dev['selected_threshold']) == new['config_live']['min_periodicidad']
dev_singers = {r['singer'] for r in live['per_track'] if r['split'] == 'development'}
val_singers = {r['singer'] for r in live['per_track'] if r['split'] == 'validation'}
assert not dev_singers & val_singers
development_n = sum(r['split'] == 'development' for r in live['per_track'])
validation_n = 40 - development_n

metrics = [('pitch_correct_50c_pct', 'Aciertos de F0'), ('false_voiced_pct', 'Falsas detecciones sin F0'),
           ('missed_voiced_pct', 'F0 omitida'), ('octave_error_pct', 'Errores de una octava'),
           ('overall_accuracy_pct', 'Exactitud global')]
comparisons = {
    'Análisis final pYIN': (old['summary']['final'], new['summary']['final']),
    'En vivo: interfaz clásica': (live['summary']['all']['clasica_antes'], live['summary']['all']['clasica_despues']),
    'En vivo: interfaz nueva': (live['summary']['all']['desktop_antes'], live['summary']['all']['desktop_despues']),
}

fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), layout='constrained')
positions = np.arange(3)
for ax, (key, title) in zip(axes, metrics[:2]):
    for i, (label, color) in enumerate([('Antes', '#7f8b99'), ('Después', '#278471')]):
        values = [pair[i][key] for pair in comparisons.values()]
        bars = ax.bar(positions + (i - .5) * .35, values, width=.35, label=label, color=color)
        ax.bar_label(bars, fmt='%.1f', padding=3, fontsize=9)
    ax.set_xticks(positions, ['pYIN final', 'YIN clásica', 'YIN nueva'])
    ax.set(title=title, ylabel='%', ylim=(0, 108)); ax.legend(loc='upper left')
fig.suptitle('Vocadito: comparación de las mismas 40 grabaciones')
fig.savefig(OUT / 'comparacion.png', dpi=160); plt.close(fig)

lines = [
    '# Mejoras del detector y nueva prueba con Vocadito', '',
    f"Se repitió la evaluación sobre **40 grabaciones, {new['duration_s']/60:.2f} minutos**. "
    'Las métricas se calculan sobre todos los frames anotados; las notas omitidas cuentan como errores.', '',
    '## Cambios aplicados', '',
    '- Se agregó `sr=sr` a las dos llamadas a pYIN del detector compartido. '
    'El audio ya no se interpreta con la frecuencia de muestreo predeterminada equivocada.',
    '- YIN ahora comprueba la periodicidad del candidato: compara cada ventana con una copia '
    'desplazada un período, resta la componente continua y normaliza por energía. '
    'La comprobación no depende del volumen absoluto ni representa una probabilidad.',
    '- Se rechazan candidatos cuya similitud es menor que **0,7**. El relleno de huecos '
    'no puede reintroducir una nota rechazada por falta de periodicidad.',
    '- Se mantuvieron los umbrales de volumen, la corrección de octavas y los parámetros '
    'propios de cada interfaz. Los cambios del detector benefician a ambas.', '',
    '## Resultados en todo Vocadito', '',
    '| Ruta | Medida | Antes | Después |', '|---|---|---:|---:|',
]
for name, pair in comparisons.items():
    for key, label in metrics:
        lines.append(f'| {name} | {label} | {pair[0][key]:.2f}% | {pair[1][key]:.2f}% |')
lines += ['', '![Comparación](comparacion.png)', '',
          'Una falsa detección es emitir F0 donde la referencia indica que no hay F0; '
          'incluye consonantes y sonidos no tonales, además de pausas. '
          'Su denominador son los frames sin F0. El denominador de aciertos, omisiones '
          'y errores de octava son los frames con F0 de referencia. '
          'El acierto admite ±50 cents (medio semitono). La exactitud global incluye '
          'también los frames sin F0 correctamente rechazados.', '',
          '## Ajuste y comprobación por cantantes', '',
          f'El umbral se eligió con **{development_n} grabaciones de {len(dev_singers)} cantantes (S1 a S8)**. '
          'Se compararon únicamente 0,6, 0,7 y 0,8. El criterio fue reducir falsas '
          'detecciones sin perder más de 2 puntos porcentuales de acierto ni aumentar '
          'las omisiones más de 2 puntos respecto al original, en ambas interfaces. '
          'Primero se exploró la interfaz nueva y luego se comprobó el mismo criterio '
          'en ambas; 0,8 no superó las restricciones de la clásica. Se fijó 0,7 antes '
          'de evaluar los cantantes restantes.', '',
          f'Comprobación interna: **{validation_n} grabaciones de {len(val_singers)} cantantes diferentes**, '
          'sin volver a cambiar el umbral tras ver sus resultados.', '',
          '| Configuración | Medida | Antes | Después |', '|---|---|---:|---:|']
for prefix, title in [('clasica', 'Clásica'), ('desktop', 'Nueva')]:
    before = live['summary']['validation'][prefix + '_antes']
    after = live['summary']['validation'][prefix + '_despues']
    for key, label in metrics:
        lines.append(f'| {title} | {label} | {before[key]:.2f}% | {after[key]:.2f}% |')
lines += ['', 'Vocadito ya se inspeccionó en la evaluación inicial. Esta separación limita '
          'el ajuste directo a los mismos cantantes, pero **no es una validación externa '
          'ni una prueba ciega nueva**. Falta comprobar generalización con otro dataset '
          'y con micrófono, ruido y acompañamiento.', '',
          '## Condiciones de la prueba', '',
          '- Misma alineación que la evaluación inicial: vecino más cercano hasta medio hop, '
          'sin interpolar frecuencias a través de huecos.',
          '- Interfaz clásica: ventanas de 380 ms y llamadas cada 60 ms.',
          '- Interfaz nueva: ventanas de 240 ms y llamadas cada 100 ms, incluyendo su filtro '
          'de saltos. El simulador extrae las constantes y el método real '
          '`_aceptar_punto_usuario` de `desktop_live.py`, sin arrancar la GUI.',
          '- Ambas simulaciones reproducen la regla del worker que solo emite tiempos '
          'posteriores al último punto entregado. No incluyen hardware, colas, '
          'calibración de ruido ni renderizado.',
          '- Se usó Python 3.14 y pYIN; WORLD no está disponible en ese entorno y no se evaluó. '
          'Los resultados no prueban el arranque de las interfaces con el antiguo Python 3.10.',
          '- Las referencias de Vocadito tienen asistencia de pYIN y revisión humana. '
          'No son mediciones fisiológicas independientes.', '',
          '## Tiempo de procesamiento en vivo', '',
          '| Configuración | Mediana por llamada | Percentil 95 |', '|---|---:|---:|']
for key, timing in live['timing_ms'].items():
    lines.append(f"| {key} | {timing['median']:.2f} ms | {timing['p95']:.2f} ms |")
lines += ['', 'Mediciones con calentamiento previo; incluyen detección y selección de puntos '
          'de la simulación. No son la latencia de extremo a extremo del karaoke.', '',
          '## Verificación y reproducción', '',
          '- Seis pruebas automáticas: frecuencias de muestreo y entrada por archivo; '
          'silencio/ruido; tonos suaves/fuertes; armónicos/vibrato; huecos rechazados; '
          'ruta de respaldo ante fallo de YIN.',
          '- Se conservó una copia del detector anterior en `antes/pitch.py`; los resultados '
          'incluyen hashes del detector, del simulador y de la interfaz. '
          'La línea base original permanece en `output/vocadito_benchmark`.', '',
          '```powershell', 'python -m unittest discover -s tests -p test_pitch.py -v',
          'python scripts/comparar_live_vocadito.py --development',
          'python scripts/evaluar_vocadito.py --output output/vocadito_mejoras/evaluacion',
          'python scripts/comparar_live_vocadito.py', 'python scripts/informe_mejoras_vocadito.py', '```', '',
          'Los archivos del catálogo y las grabaciones personales no se reprocesaron. '
          '**Las referencias ya guardadas no cambian automáticamente**: para aplicar la '
          'corrección a una canción previamente analizada con pYIN, usar Reprocesar en '
          'la aplicación. Los resultados antiguos de tomas tampoco se recalculan solos.', '',
          '## Detalle de pYIN después de corregir el muestreo', '',
          '| Etapa | Aciertos de F0 | Falsas detecciones sin F0 | F0 omitida |', '|---|---:|---:|---:|']
for mode in ['base', 'filtrado', 'final']:
    m = new['summary'][mode]
    lines.append(f"| {mode} | {m['pitch_correct_50c_pct']:.2f}% | {m['false_voiced_pct']:.2f}% | {m['missed_voiced_pct']:.2f}% |")

# Ejemplo determinado por la mayor reduccion de falsas detecciones en UI nueva.
example = max(live['per_track'], key=lambda r: r['metrics']['desktop_antes']['false_voiced_pct'] - r['metrics']['desktop_despues']['false_voiced_pct'])
name = example['track']
p = np.load(OUT / 'live_predicciones' / (name + '.npz'))
fig, axes = plt.subplots(2, 1, figsize=(12, 6), sharex=True, layout='constrained')
for ax, key in zip(axes, ['desktop_antes', 'desktop_despues']):
    for mode, label, color in [('reference', 'Referencia', '#333333'), (key, key, '#c65c43')]:
        hz = p[mode]; valid = hz > 0; midi = np.full(len(hz), np.nan)
        midi[valid] = 69 + 12 * np.log2(hz[valid] / 440)
        ax.plot(p['time'], midi, '.', ms=1.8, label=label, color=color)
    ax.set_ylabel('Altura MIDI'); ax.legend(loc='upper right'); ax.grid(alpha=.2)
axes[0].set_title(name + ': interfaz nueva, antes y después')
axes[-1].set_xlabel('Tiempo (s)')
fig.savefig(OUT / 'ejemplo_live.png', dpi=150); plt.close(fig)
lines += ['', '## Ejemplo de reducción de falsas detecciones', '',
          f'Seleccionado automáticamente por la mayor reducción en la interfaz nueva: {name}.', '',
          '![Ejemplo](ejemplo_live.png)', '', '## Resultados por grabación (interfaz nueva)', '',
          '| Grabación | Grupo | Aciertos antes | Aciertos después | Falsos antes | Falsos después |',
          '|---|---|---:|---:|---:|---:|']
for row in live['per_track']:
    a, b = row['metrics']['desktop_antes'], row['metrics']['desktop_despues']
    lines.append(f"| {row['track']} | {row['split']} | {a['pitch_correct_50c_pct']:.2f}% | "
                 f"{b['pitch_correct_50c_pct']:.2f}% | {a['false_voiced_pct']:.2f}% | {b['false_voiced_pct']:.2f}% |")
(OUT / 'informe.md').write_text('\n'.join(lines), encoding='utf-8')
print(OUT / 'informe.md')
