"""Benchmark reproducible del detector existente; no ajusta sus parametros.

python scripts/evaluar_vocadito.py
Dataset v3: https://zenodo.org/records/5578807
"""
from pathlib import Path
import argparse
import hashlib
import importlib.metadata
import json
import platform
import sys
import time

import numpy as np
import librosa
import soundfile as sf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from audio import pitch

MODES = ('base', 'filtrado', 'final', 'yin_stream')


def align(t, f, target, tolerance):
    """Vecino mas cercano acotado: nunca une silencios entre puntos validos."""
    out = np.zeros(len(target))
    if not len(t):
        return out
    assert len(t) == len(f) and np.all(np.diff(t) > 0)
    right = np.clip(np.searchsorted(t, target), 0, len(t) - 1)
    left = np.maximum(right - 1, 0)
    idx = np.where(abs(t[left] - target) <= abs(t[right] - target), left, right)
    valid = abs(t[idx] - target) <= tolerance + 1e-9
    out[valid] = f[idx[valid]]
    return out


def counts(ref, est):
    rv, ev = ref > 0, est > 0
    both = rv & ev
    cents = 1200 * np.log2(est[both] / ref[both])
    good = abs(cents) <= 50
    octaves = abs(abs(cents) - 1200) <= 50
    return {
        'frames': len(ref), 'voiced': int(rv.sum()), 'unvoiced': int((~rv).sum()),
        'both_voiced': int(both.sum()), 'correct_pitch': int(good.sum()),
        'missed': int((rv & ~ev).sum()), 'false_voiced': int((~rv & ev).sum()),
        'correct_unvoiced': int((~rv & ~ev).sum()),
        'octave_errors': int(octaves.sum()),
    }, abs(cents)


def percentages(c):
    def pct(n, d):
        return 100 * n / d if d else None
    return {
        'pitch_correct_50c_pct': pct(c['correct_pitch'], c['voiced']),
        'missed_voiced_pct': pct(c['missed'], c['voiced']),
        'false_voiced_pct': pct(c['false_voiced'], c['unvoiced']),
        'octave_error_pct': pct(c['octave_errors'], c['voiced']),
        'overall_accuracy_pct': pct(c['correct_pitch'] + c['correct_unvoiced'], c['frames']),
    }


def stream(y, sr):
    """Simula worker: ventana 380 ms, llamadas 60 ms, solo puntos nuevos.

    Sin hardware/cola, sin ruido de calibracion y sin descarte de llamadas.
    Se conservan tiempos reales de disponibilidad para estimar retraso.
    """
    ts, fs, delays, calls = [], [], [], []
    last = 0.0
    for end in np.arange(0.06, len(y) / sr, 0.06):
        start = max(0.0, end - 0.38)
        chunk = y[int(start * sr):int(end * sr)]
        tic = time.perf_counter()
        t, f = pitch.extraer_pitch_ligero_desde_audio(chunk, sr, offset_t=start, ruido_base=None)
        elapsed = time.perf_counter() - tic
        calls.append(elapsed)
        new = t > last
        if np.any(new):
            ts.extend(t[new]); fs.extend(f[new])
            delays.extend(end - t[new] + elapsed)
            last = float(t[new].max())
    return np.asarray(ts), np.asarray(fs), np.asarray(calls), np.asarray(delays)


def check_evaluator():
    # Un hueco no se interpola como una nota sostenida.
    assert np.array_equal(align(np.array([0., .02]), np.array([440., 440.]),
                               np.array([0., .01, .02]), .004), [440., 0., 440.])
    c, _ = counts(np.array([440., 440., 440., 0., 0.]),
                  np.array([440., 880., 0., 440., 0.]))
    assert c['correct_pitch'] == c['missed'] == c['octave_errors'] == c['false_voiced'] == 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', type=Path, default=ROOT / 'data/vocadito_benchmark')
    parser.add_argument('--output', type=Path, default=ROOT / 'output/vocadito_benchmark')
    parser.add_argument('--limit', type=int)
    args = parser.parse_args()
    check_evaluator()
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'predicciones').mkdir(exist_ok=True)
    archive = args.data / 'vocadito.zip'
    checksum = hashlib.md5(archive.read_bytes()).hexdigest()
    assert checksum == 'dea40fd18f14d899643c4ba221b33a46', 'Dataset no coincide con v3'
    files = sorted((args.data / 'Audio').glob('*.wav'), key=lambda p: int(p.stem.split('_')[-1]))
    assert len(files) == 40, f'Se esperaban 40 audios, hay {len(files)}'
    files = files[:args.limit] if args.limit else files
    # Warmup excluido de tiempos; tambien registra el coste de arranque.
    tic = time.perf_counter()
    warm = .1 * np.sin(2 * np.pi * 220 * np.arange(44100) / 44100)
    pitch._extraer_pitch_base(warm, 44100)
    pitch.extraer_pitch_ligero_desde_audio(warm[:16758], 44100)
    warmup = time.perf_counter() - tic
    all_counts = {m: [] for m in MODES}
    all_cents = {m: [] for m in MODES}
    rows, call_times, delays, base_times, audio_seconds = [], [], [], [], 0.
    for n, path in enumerate(files, 1):
        y, sr = sf.read(path, dtype='float32')
        assert y.ndim == 1 and sr == 44100
        duration = len(y) / sr
        audio_seconds += duration
        reference = np.loadtxt(args.data / 'Annotations/F0' / (path.stem + '_f0.csv'), delimiter=',')
        rt, rf = reference.T
        assert np.all(np.diff(rt) > 0) and np.all(rf >= 0)
        tic = time.perf_counter()
        t, f = pitch._extraer_pitch_base(y, sr)
        base_elapsed = time.perf_counter() - tic
        base_times.append(base_elapsed)
        tf, ff = pitch._filtrar_pitch(t, f.copy(), y, sr, corregir_octavas=False)
        tc, fc = pitch._corregir_octavas_por_registro(tf, ff.copy())
        hop = float(np.median(np.diff(t)))
        predictions = {
            'base': align(t, f, rt, hop / 2),
            'filtrado': align(tf, ff, rt, hop / 2),
            'final': align(tc, fc, rt, hop / 2),
        }
        st, sfreq, calls, delay = stream(y, sr)
        predictions['yin_stream'] = align(st, sfreq, rt, 1024 / sr / 2)
        call_times.extend(calls); delays.extend(delay)
        row = {'track': path.stem, 'duration_s': duration, 'base_processing_s': base_elapsed, 'metrics': {}}
        for mode, est in predictions.items():
            c, error = counts(rf, est)
            all_counts[mode].append(c); all_cents[mode].append(error)
            row['metrics'][mode] = {**percentages(c), 'counts': c,
                'median_abs_cents_both_voiced': float(np.median(error)) if len(error) else None}
        rows.append(row)
        np.savez_compressed(args.output / 'predicciones' / (path.stem + '.npz'),
                            time=rt, reference=rf, **predictions)
        print(f'{n}/{len(files)} {path.stem}: final={row["metrics"]["final"]["pitch_correct_50c_pct"]:.1f}% '
              f'live={row["metrics"]["yin_stream"]["pitch_correct_50c_pct"]:.1f}%', flush=True)
    summary = {}
    for mode in MODES:
        pooled = {key: sum(c[key] for c in all_counts[mode]) for key in all_counts[mode][0]}
        errors = np.concatenate(all_cents[mode])
        summary[mode] = {**percentages(pooled), 'counts': pooled,
            'macro_pitch_correct_50c_pct': float(np.mean([r['metrics'][mode]['pitch_correct_50c_pct'] for r in rows])),
            'median_abs_cents_both_voiced': float(np.median(errors)),
            'p90_abs_cents_both_voiced': float(np.percentile(errors, 90))}
    report = {
        'dataset_url': 'https://zenodo.org/records/5578807', 'dataset_md5': checksum,
        'tracks': len(files), 'duration_s': audio_seconds,
        'python': sys.version, 'platform': platform.platform(),
        'versions': {p: importlib.metadata.version(p) for p in ['librosa', 'numpy', 'soundfile', 'matplotlib']},
        'backend': 'WORLD' if pitch.pw is not None else 'pYIN',
        'pitch_sha256': hashlib.sha256((ROOT / 'audio/pitch.py').read_bytes()).hexdigest(),
        'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'config_offline': pitch.FILTRO_SUAVE, 'config_live': pitch.FILTRO_TIEMPO_REAL,
        'warmup_s': warmup, 'base_processing_s': sum(base_times),
        'base_realtime_factor': sum(base_times) / audio_seconds,
        'live_call_median_ms': float(np.median(call_times) * 1000),
        'live_call_p95_ms': float(np.percentile(call_times, 95) * 1000),
        'live_call_over_60ms_pct': float(np.mean(np.array(call_times) > .06) * 100),
        'live_availability_delay_median_ms': float(np.median(delays) * 1000),
        'live_availability_delay_p95_ms': float(np.percentile(delays, 95) * 1000),
        'summary': summary, 'per_track': rows,
    }
    (args.output / 'resultados.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    labels = ['pYIN base', 'Filtros', 'Salida final', 'YIN en bloques']
    fig, ax = plt.subplots(figsize=(9, 4.5), layout='constrained')
    vals = [summary[m]['pitch_correct_50c_pct'] for m in MODES]
    bars = ax.bar(labels, vals, color=['#526c91', '#c18340', '#477b61', '#8764a5'])
    ax.bar_label(bars, fmt='%.1f%%', padding=3)
    ax.set(ylim=(0, 100), ylabel='Aciertos / frames de referencia con F0 (%)',
           title=f'Vocadito: {len(files)} grabaciones, tolerancia de 50 cents')
    fig.savefig(args.output / 'resumen.png', dpi=160); plt.close(fig)
    # Peor caso final y mayor perdida producida por filtros, sin seleccion manual.
    worst = min(rows, key=lambda r: r['metrics']['final']['pitch_correct_50c_pct'])
    loss = min(rows, key=lambda r: r['metrics']['final']['pitch_correct_50c_pct'] - r['metrics']['base']['pitch_correct_50c_pct'])
    chosen = list(dict.fromkeys([worst['track'], loss['track']]))
    for track in chosen:
        data = np.load(args.output / 'predicciones' / (track + '.npz'))
        fig, axes = plt.subplots(3, 1, figsize=(12, 8), sharex=True, layout='constrained')
        for ax, mode in zip(axes, ['base', 'final', 'yin_stream']):
            for key, label, color in [('reference', 'Referencia', '#333333'), (mode, mode, '#c55940')]:
                hz = data[key]; midi = np.full(len(hz), np.nan); v = hz > 0
                midi[v] = 69 + 12 * np.log2(hz[v] / 440)
                ax.plot(data['time'], midi, '.', ms=1.5, label=label, color=color)
            ax.set_ylabel('Altura MIDI'); ax.legend(loc='upper right'); ax.grid(alpha=.2)
        axes[0].set_title(track + ': referencia y estimacion (huecos = ausencia de F0)')
        axes[-1].set_xlabel('Tiempo (s)')
        fig.savefig(args.output / (track + '.png'), dpi=140); plt.close(fig)
    print(json.dumps({k: v for k, v in report.items() if k not in ['per_track', 'summary']}, indent=2))


if __name__ == '__main__':
    main()
