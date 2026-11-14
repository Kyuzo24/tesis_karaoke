"""Genera el informe legible a partir de resultados.json, sin repetir inferencia."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/vocadito_benchmark'
data = json.loads((OUT / 'resultados.json').read_text(encoding='utf-8'))
worst_live = min(data['per_track'], key=lambda r: r['metrics']['yin_stream']['pitch_correct_50c_pct'])
example = np.load(OUT / 'predicciones' / (worst_live['track'] + '.npz'))
fig, ax = plt.subplots(figsize=(12, 4), layout='constrained')
for key, label, color in [('reference', 'Referencia', '#333333'), ('yin_stream', 'YIN en vivo', '#c55940')]:
    values = example[key]
    midi = np.full(len(values), np.nan)
    voiced = values > 0
    midi[voiced] = 69 + 12 * np.log2(values[voiced] / 440)
    ax.plot(example['time'], midi, '.', ms=2, label=label, color=color)
ax.set(title='Menor precisión de YIN en vivo: ' + worst_live['track'], xlabel='Tiempo (s)', ylabel='Altura MIDI')
ax.legend(); ax.grid(alpha=.2)
fig.savefig(OUT / 'peor_caso_yin.png', dpi=150)
plt.close(fig)
names = {'base': 'pYIN sin filtros', 'filtrado': 'pYIN con filtros',
         'final': 'pYIN salida final', 'yin_stream': 'YIN en ventanas del modo en vivo'}
lines = [
    '# Evaluación inicial del detector con Vocadito', '',
    f"Se evaluaron **{data['tracks']} grabaciones** ({data['duration_s']/60:.2f} minutos) "
    'sin ajustar ni modificar el detector. Se usó Vocadito v3, con audio mono a 44.100 Hz.', '',
    '[Dataset y anotaciones oficiales](https://zenodo.org/records/5578807). '
    f"MD5 verificado: `{data['dataset_md5']}`.", '',
    '## Resultados', '',
    'Porcentajes agrupados por frame, no promedio de porcentajes por canción. '
    'Las omisiones cuentan como fallos en la precisión de F0.', '',
    '| Ruta | F0 correcta ±50 cents | F0 omitida | Falsos positivos sin F0 | Error de ±1 octava | Exactitud global |',
    '|---|---:|---:|---:|---:|---:|',
]
for mode, name in names.items():
    m = data['summary'][mode]
    keys = ['pitch_correct_50c_pct', 'missed_voiced_pct', 'false_voiced_pct',
            'octave_error_pct', 'overall_accuracy_pct']
    lines.append('| ' + name + ' | ' + ' | '.join(f'{m[k]:.2f}%' for k in keys) + ' |')
lines += [
    '', '![Comparación de precisión](resumen.png)', '',
    '## Hallazgo principal', '',
    'En `audio/pitch.py`, las llamadas a `librosa.pyin` de `_extraer_pitch_base` '
    'y `extraer_pitch_crudo` omiten `sr=sr`. Librosa usa por defecto 22.050 Hz, '
    'pero el audio de esta prueba tiene 44.100 Hz. Esto provoca un desplazamiento '
    'sistemático de frecuencia. Un control independiente con una sinusoide de 440 Hz '
    'a 44.100 Hz produjo aproximadamente 220 Hz en la ruta actual. '
    'La misma llamada con `sr=sr` explícito devolvió 440 Hz. '
    'El control reproducible está en `scripts/diagnostico_sr_pyin.py` y sus valores '
    'en `diagnostico_sr.json`; no equivale a evaluar la corrección sobre todo Vocadito.', '',
    'La ruta YIN ligera sí proporciona `sr=sr`. El fallo anterior no se atribuye '
    'a WORLD: ese backend no está instalado en el Python usado y no fue evaluado.', '',
    'Recomendación inmediata: pasar explícitamente `sr=sr` en ambas llamadas a pYIN '
    'y repetir esta misma evaluación antes de ajustar umbrales o cambiar de algoritmo. '
    'El detector se conservó intacto para registrar una línea base.', '',
    '## Qué significan las métricas', '',
    '- **F0 correcta ±50 cents:** frames con referencia tonal en que se emitió una '
    'F0 a una distancia máxima de 50 cents; denominador: todos los frames con F0 de referencia.',
    '- **F0 omitida:** referencia con F0 y estimación ausente; denominador: frames con F0 de referencia.',
    '- **Falsos positivos sin F0:** se estima F0 donde la referencia marca 0; '
    'denominador: frames sin F0 de referencia. Incluye consonantes y otros segmentos no tonales, no solo silencio.',
    '- **Error de ±1 octava:** distancia a +1200 o −1200 cents de como máximo 50 cents; '
    'denominador: frames con F0 de referencia. No incluye errores de dos octavas.',
    '- **Exactitud global:** F0 correcta en frames tonales más ausencia correcta en frames '
    'no tonales, dividido por todos los frames.',
    '- La mediana del error en cents del JSON considera únicamente frames donde ambos '
    'tienen F0; no reemplaza las métricas que penalizan omisiones.', '',
    '## Protocolo y límites', '',
    '1. Se conservaron frecuencia de muestreo, amplitud y parámetros actuales; sin normalización '
    'de volumen, reducción de ruido ni ajuste con las etiquetas.',
    '2. Las estimaciones se llevaron a los tiempos de referencia mediante vecino más cercano, '
    'con distancia máxima de medio hop de estimación. Los huecos quedan en cero; no se '
    'interpoló una nota a través de regiones rechazadas. Se evaluaron todos los frames anotados, '
    'incluidos los bordes sin predicción.',
    '3. La simulación en vivo llama al detector cada 60 ms sobre los últimos 380 ms, '
    'con la regla del worker que conserva solamente puntos posteriores al último emitido. '
    'No usa micrófono, reproducción, cola de tareas ni calibración ambiental; '
    '`ruido_base=None`. Por ello no mide latencia acústica total ni robustez al acompañamiento.',
    '4. Los filtros se evaluaron sobre una copia de la misma salida base; la corrección '
    'de octavas se aplicó como una etapa adicional.',
    '5. Se comprobó el evaluador con casos de frecuencia correcta, omisión, falsa detección, '
    'error de octava y huecos temporales.',
    '6. Es una evaluación descriptiva de las 40 grabaciones, sin entrenamiento ni selección '
    'de parámetros. Si se ajustan parámetros usando estos resultados, hará falta reservar '
    'cantantes o utilizar otro dataset para una prueba independiente.',
    '7. Las referencias de Vocadito fueron creadas con asistencia de pYIN y revisión humana; '
    'no son mediciones fisiológicas independientes. Son de canto solo, sin acompañamiento.', '',
    '## Tiempos', '',
    f"- Extracción base total: {data['base_processing_s']:.2f} s; "
    f"factor tiempo de procesamiento/audio: {data['base_realtime_factor']:.3f}.",
    f"- Arranque y calentamiento excluido: {data['warmup_s']:.2f} s.",
    f"- Llamada YIN: mediana {data['live_call_median_ms']:.2f} ms; "
    f"percentil 95 {data['live_call_p95_ms']:.2f} ms.",
    f"- Llamadas que superan 60 ms: {data['live_call_over_60ms_pct']:.2f}%.",
    f"- Retraso simulado entre centro del frame emitido y disponibilidad: mediana "
    f"{data['live_availability_delay_median_ms']:.2f} ms; "
    f"percentil 95 {data['live_availability_delay_p95_ms']:.2f} ms. "
    'No incluye hardware, colas ni renderizado; los percentiles se calculan sobre puntos emitidos.', '',
    '## Reproducción', '',
    'El entorno `venv` existente apunta a Python 3.10 y no pudo arrancar. '
    'Se utilizó el Python 3.14 disponible, con versiones registradas en `resultados.json`.', '',
    '```powershell', 'python scripts/evaluar_vocadito.py', 'python scripts/diagnostico_sr_pyin.py',
    'python scripts/informe_vocadito.py', '```', '',
    'La carpeta `data/vocadito_benchmark` debe contener el ZIP oficial v3 y sus carpetas '
    '`Audio` y `Annotations` extraídas. El evaluador valida su checksum y los 40 WAV. '
    'Los resultados guardan las versiones, parámetros y SHA-256 del detector y evaluador. '
    'Las predicciones alineadas están en `predicciones/*.npz`.', '',
    '## Resultados por grabación', '',
    '| Grabación | pYIN base: F0 correcta | pYIN final: F0 correcta | YIN en vivo: F0 correcta |',
    '|---|---:|---:|---:|',
]
for row in data['per_track']:
    vals = [row['metrics'][m]['pitch_correct_50c_pct'] for m in ['base', 'final', 'yin_stream']]
    lines.append('| ' + row['track'] + ' | ' + ' | '.join(f'{v:.2f}%' for v in vals) + ' |')
lines += ['', '## Ejemplos de contornos', '',
          'Selección automática: menor precisión de la salida final y mayor pérdida '
          'entre salida base y final; si coinciden, se muestra una sola grabación.', '']
for path in sorted(OUT.glob('vocadito_*.png')):
    lines += [f'![{path.stem}]({path.name})', '']
lines += ['También se muestra la grabación con menor precisión de YIN en vivo: '
          f"**{worst_live['track']}**, "
          f"{worst_live['metrics']['yin_stream']['pitch_correct_50c_pct']:.2f}%.", '',
          '![Peor caso de YIN en vivo](peor_caso_yin.png)', '']
(OUT / 'informe.md').write_text('\n'.join(lines), encoding='utf-8')
print(OUT / 'informe.md')
