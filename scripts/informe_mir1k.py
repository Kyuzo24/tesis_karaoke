"""Informe de la evaluacion externa, con graficas y comparacion antes/despues."""
from pathlib import Path
import hashlib
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/mir1k_evaluacion'
d = json.loads((OUT / 'resultados.json').read_text(encoding='utf-8'))
manifest = json.loads((ROOT / 'data/mir1k_muestra/manifest.json').read_text(encoding='utf-8'))
assert d['tracks'] == 95 and d['singers'] == 19
assert len(list((OUT / 'tracks').glob('*.json'))) == 95
assert len(list((OUT / 'predicciones').glob('*.npz'))) == 95
assert hashlib.sha256((ROOT / 'audio/pitch.py').read_bytes()).hexdigest() == d['protocol']['pitch_sha256']
conditions = [('voz_sola', 'Voz sola'), ('musica_10dB', 'Voz 10 dB sobre la música'), ('musica_0dB', 'Voz y música al mismo nivel')]
metrics = [('pitch_correct_50c_pct', 'Aciertos de F0'), ('false_voiced_pct', 'Falsas detecciones sin F0'),
           ('missed_voiced_pct', 'F0 omitida'), ('octave_error_pct', 'Errores de una octava'),
           ('overall_accuracy_pct', 'Exactitud global')]
lines = ['# Evaluación externa con MIR-1K', '',
         f"Se evaluaron **95 de los 1.000 fragmentos**, de **19 cantantes**, "
         f"con una duración total de **{d['duration_s']/60:.2f} minutos**. "
         'No se modificó el detector ni se ajustaron parámetros con MIR-1K.', '',
         '## Diseño de la prueba', '',
         '- Cinco fragmentos por cantante. Selección por orden SHA-256 con prefijo fijo, '
         'priorizando canciones diferentes antes de completar los cinco. La lista exacta '
         'está en `data/mir1k_muestra/manifest.json` y se fijó antes de inferir.',
         '- Audio estéreo original a 16 kHz: acompañamiento izquierdo y voz derecha. '
         'Se remuestrearon ambos canales a 44,1 kHz para reproducir las ventanas en muestras '
         'del modo en vivo de la aplicación; eso no añade información al audio original.',
         '- Etiquetas MIDI convertidas a Hz, conservando 0 como ausencia de F0. '
         'Primer centro a 20 ms y paso de 20 ms; se comprobó que su duración corresponde al audio.',
         '- Interfaz nueva: ventanas de 240 ms, llamadas cada 100 ms y su filtro real de saltos. '
         'Se aplican los mismos tiempos y reglas al detector anterior y al mejorado.',
         '- Tres condiciones sobre exactamente los mismos fragmentos: voz sola; mezcla con '
         'voz 10 dB por encima del acompañamiento; mezcla a 0 dB. Las relaciones se fijan '
         'mediante RMS de cada clip completo. Si una mezcla supera 0,99 de pico, se reduce '
         'voz y acompañamiento por el mismo factor para evitar saturación.',
         '- La prueba de mezclas introduce acompañamiento directamente en el detector '
         'monofónico. No ejecuta separación de fuentes, micrófono ni calibración ambiental. '
         'Es una prueba de interferencia musical, no de toda la cadena de karaoke.', '',
         '## Resultados del modo en vivo — interfaz nueva', '',
         '| Condición | Medida | Anterior | Mejorado |', '|---|---|---:|---:|']
for key, title in conditions:
    a, b = d['summary'][key+'_antes'], d['summary'][key+'_despues']
    for metric, label in metrics:
        lines.append(f'| {title} | {label} | {a[metric]:.2f}% | {b[metric]:.2f}% |')
lines += ['', 'Los aciertos admiten ±50 cents (medio semitono) y cuentan las omisiones '
          'como errores. El denominador de aciertos, omisiones y errores de octava son '
          'los frames con F0 de referencia. Las falsas detecciones se calculan sobre '
          'los frames sin F0; incluyen consonantes y pausas. La exactitud global incluye '
          'tanto notas acertadas como ausencia de F0 correctamente detectada. '
          'Los porcentajes principales se agrupan por frames; también se guardan '
          'promedios por clip y resultados por cantante.', '',
          '![Comparación por condición](comparacion.png)', '',
          '## Análisis posterior con pYIN — solo voz', '',
          '| Etapa actual | Aciertos | Falsas detecciones sin F0 | Omisiones | Exactitud global |',
          '|---|---:|---:|---:|---:|']
for key, label in [('pyin_base_voz','Sin filtros posteriores'),('pyin_final_voz','Salida final con filtros')]:
    m=d['summary'][key]
    lines.append(f"| {label} | {m['pitch_correct_50c_pct']:.2f}% | {m['false_voiced_pct']:.2f}% | "
                 f"{m['missed_voiced_pct']:.2f}% | {m['overall_accuracy_pct']:.2f}% |")
lines += ['', 'pYIN se evaluó con la corrección de frecuencia de muestreo ya aplicada. '
          'La comparación anterior/mejorado de la tabla principal corresponde a YIN en vivo. '
          'WORLD no está instalado en el entorno utilizado y no fue evaluado.', '',
          '## Interpretación y límites', '',
          f"Con voz sola, los aciertos del modo en vivo pasan de "
          f"{d['summary']['voz_sola_antes']['pitch_correct_50c_pct']:.2f}% a "
          f"{d['summary']['voz_sola_despues']['pitch_correct_50c_pct']:.2f}%, y las falsas detecciones "
          f"bajan de {d['summary']['voz_sola_antes']['false_voiced_pct']:.2f}% a "
          f"{d['summary']['voz_sola_despues']['false_voiced_pct']:.2f}%. "
          'La mejora observada en Vocadito se mantiene en esta muestra externa.', '',
          'Con música al mismo nivel que la voz, el filtro nuevo reduce falsas detecciones '
          'pero también descarta muchas notas verdaderas: '
          f"los aciertos caen de {d['summary']['musica_0dB_antes']['pitch_correct_50c_pct']:.2f}% a "
          f"{d['summary']['musica_0dB_despues']['pitch_correct_50c_pct']:.2f}% y las omisiones alcanzan "
          f"{d['summary']['musica_0dB_despues']['missed_voiced_pct']:.2f}%. "
          'No debe describirse esto como una mejora de seguimiento de la voz. '
          'El problema prioritario en esa condición es separar o reducir la interferencia '
          'del acompañamiento antes de estimar una única F0.', '',
          'En pYIN, los filtros posteriores reducen falsas detecciones, pero también '
          f"bajan los aciertos de {d['summary']['pyin_base_voz']['pitch_correct_50c_pct']:.2f}% a "
          f"{d['summary']['pyin_final_voz']['pitch_correct_50c_pct']:.2f}%. "
          'Conviene estudiar por separado ese compromiso en otro experimento; '
          'no se reajustó el filtro durante esta evaluación.', '',
          'Esta muestra permite comprobar transferencia a otros cantantes y grabaciones '
          'sin ajustar de nuevo el algoritmo. No equivale a evaluar todo MIR-1K ni garantiza '
          'el rendimiento en cualquier micrófono o estilo de canto. '
          'Los resultados con mezcla miden la capacidad de seguir la voz cuando compite '
          'con instrumentos: rechazar ruido no garantiza distinguir una voz de otro sonido musical tonal.', '',
          'Las cifras de Vocadito y MIR-1K no deben compararse como si fueran la misma prueba: '
          'cambian voces, grabación, anotaciones y granularidad temporal. '
          'Para atribuir una mejora al cambio de código, comparar anterior y mejorado '
          'sobre la misma condición de MIR-1K.', '',
          '## Procedencia y reproducibilidad', '',
          '[Descripción y protocolo temporal por el autor en MIREX](https://music-ir.org/mirex/wiki/2009:Audio_Melody_Extraction). '
          '[Copia pública utilizada](https://huggingface.co/datasets/AnhP/Mir-1k-use-DJCM-training/tree/d6b7565ab4d85c0fa752eeb3ac63618c94620edd/MIR-1K).', '',
          'El servidor original no respondió durante la preparación. Se utilizó un mirror '
          'de terceros fijado a una revisión concreta. Los 190 archivos se verificaron '
          'contra los hashes publicados de esa revisión (SHA-256 LFS o hash de objeto Git); '
          'esto comprueba integridad respecto al mirror, no autentica los archivos con el autor original. '
          'El readme de ese mirror describe MIREX09, otra colección; se usó la especificación '
          'MIR-1K del autor y se comprobó que las 95 parejas audio/etiquetas coinciden en duración.', '',
          f"Revisión del mirror: `{manifest['revision']}`. Detector: `{d['protocol']['pitch_sha256']}`.", '',
          'Se guardan predicciones, métricas por fragmento y protocolo con versiones y hashes. '
          'El evaluador guarda cada fragmento al terminar y puede reanudar una interrupción '
          'sin repetir los ya evaluados; rechaza reutilizar esos resultados si cambia el protocolo.', '',
          '```powershell', 'python scripts/preparar_mir1k.py', 'python scripts/evaluar_mir1k.py',
          'python scripts/informe_mir1k.py', '```', '',
          '## Resultados por cantante — voz sola, interfaz nueva', '',
          '| Cantante | Aciertos anterior | Aciertos mejorado | Falsas anterior | Falsas mejorado |',
          '|---|---:|---:|---:|---:|']
for singer, values in d['by_singer'].items():
    a,b=values['voz_sola_antes'],values['voz_sola_despues']
    lines.append(f"| {singer} | {a['pitch_correct_50c_pct']:.2f}% | {b['pitch_correct_50c_pct']:.2f}% | "
                 f"{a['false_voiced_pct']:.2f}% | {b['false_voiced_pct']:.2f}% |")
fig,axes=plt.subplots(1,2,figsize=(12,5),layout='constrained')
x=np.arange(3)
for ax,(metric,title) in zip(axes,metrics[:2]):
    for i,(suffix,label,color) in enumerate([('antes','Anterior','#8995a1'),('despues','Mejorado','#257d6d')]):
        vals=[d['summary'][key+'_'+suffix][metric] for key,_ in conditions]
        bars=ax.bar(x+(i-.5)*.36,vals,.36,label=label,color=color)
        ax.bar_label(bars,fmt='%.1f',padding=3,fontsize=9)
    ax.set_xticks(x,['Voz sola','Música más baja\n(+10 dB)','Mismo nivel\n(0 dB)'])
    ax.set(title=title,ylabel='%',ylim=(0,115))
    ax.legend(loc='upper center',ncol=2,frameon=False)
fig.suptitle('MIR-1K: 95 fragmentos, 19 cantantes — interfaz nueva')
fig.savefig(OUT/'comparacion.png',dpi=150);plt.close(fig)
(OUT/'informe.md').write_text('\n'.join(lines),encoding='utf-8')
print(OUT/'informe.md')
