"""Validacion externa en muestra de MIR-1K, parametros congelados, reanudable."""
from pathlib import Path
import hashlib
import importlib.metadata
import json
import sys
import time
import numpy as np
import librosa
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from audio import pitch
from scripts.evaluar_vocadito import align, counts, percentages, check_evaluator
from scripts.comparar_live_vocadito import load_before, ui_policy, simulate

DATA = ROOT / 'data/mir1k_muestra'
OUT = ROOT / 'output/mir1k_evaluacion'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mixture(voice, music, db):
    rv = float(np.sqrt(np.mean(voice.astype(float)**2)))
    rm = float(np.sqrt(np.mean(music.astype(float)**2)))
    assert rv > 0 and rm > 0
    coefficient = rv / (rm * 10**(db/20))
    y = voice + coefficient * music
    gain = min(1., .99 / max(float(np.max(abs(y))), 1e-12))
    actual_db = float(20*np.log10(rv/(coefficient*rm)))
    assert abs(actual_db-db) < 1e-6
    return y*gain, {'music_coefficient': coefficient, 'common_gain': gain, 'sar_db': actual_db}


def main():
    check_evaluator()
    manifest = json.loads((DATA / 'manifest.json').read_text(encoding='utf-8'))
    assert len(manifest['selected_tracks']) == 95
    assert len(set(manifest['selected_tracks'])) == 95
    before = load_before()
    config, accept = ui_policy()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'tracks').mkdir(exist_ok=True)
    (OUT / 'predicciones').mkdir(exist_ok=True)
    signature = {
        'pitch_sha256': digest(ROOT / 'audio/pitch.py'),
        'before_sha256': digest(ROOT / 'output/vocadito_mejoras/antes/pitch.py'),
        'ui_sha256': digest(ROOT / 'desktop_live.py'),
        'script_sha256': digest(Path(__file__)), 'manifest_sha256': digest(DATA / 'manifest.json'),
        'sample_rate': 44100, 'start_s': .02, 'hop_s': .02,
        'config_live': pitch.FILTRO_TIEMPO_REAL, 'config_offline': pitch.FILTRO_SUAVE,
        'desktop_config': config, 'backend': 'WORLD' if pitch.pw is not None else 'pYIN',
        'versions': {p: importlib.metadata.version(p) for p in ['librosa','numpy','soundfile']},
        'python': sys.version, 'scenarios': ['voz_sola', 'musica_10dB', 'musica_0dB'],
    }
    run_path = OUT / 'protocolo.json'
    if run_path.exists():
        assert json.loads(run_path.read_text(encoding='utf-8')) == signature, 'Cambio de protocolo; use otra carpeta para evitar mezclar resultados.'
    else:
        run_path.write_text(json.dumps(signature, indent=2), encoding='utf-8')
    # Verifica los bytes antes de inferir, no solo al descargar.
    for f in manifest['files']:
        assert digest(DATA / f['path']) == f['sha256'], f['path']
    warm = .1*np.sin(2*np.pi*220*np.arange(44100)/44100)
    pitch._extraer_pitch_base(warm, 44100)
    pitch.extraer_pitch_ligero_desde_audio(warm[:16758], 44100)
    before.extraer_pitch_ligero_desde_audio(warm[:16758], 44100)
    rows = []
    for i, name in enumerate(manifest['selected_tracks'], 1):
        cache = OUT / 'tracks' / (name + '.json')
        if cache.exists():
            rows.append(json.loads(cache.read_text(encoding='utf-8')))
            print(f'{i}/95 {name}: recuperado', flush=True)
            continue
        stereo, native_sr = sf.read(DATA / 'MIR-1K/Wavfile' / (name+'.wav'), dtype='float32')
        assert stereo.ndim == 2 and stereo.shape[1] == 2 and native_sr == 16000
        midi = np.loadtxt(DATA / 'MIR-1K/PitchLabel' / (name+'.pv'))
        assert midi.ndim == 1 and np.isfinite(midi).all() and np.all(midi >= 0)
        rt = .02 + np.arange(len(midi)) * .02
        duration = len(stereo) / native_sr
        assert -.0001 <= duration - rt[-1] <= .061, (name, duration, rt[-1])
        ref = np.zeros(len(midi))
        ref[midi > 0] = 440 * 2 ** ((midi[midi > 0] - 69)/12)
        audio = librosa.resample(stereo.T, orig_sr=native_sr, target_sr=44100).T
        music, voice = audio[:, 0], audio[:, 1]
        scenarios = {'voz_sola': voice}
        mix_info = {}
        for db in [10, 0]:
            key = f'musica_{db}dB'
            scenarios[key], mix_info[key] = mixture(voice, music, db)
        predictions = {'time': rt, 'reference': ref}
        row = {'track': name, 'singer': name.split('_')[0], 'duration_s': duration,
               'native_sr': native_sr, 'mix_info': mix_info, 'metrics': {}, 'timing': {}}
        tic = time.perf_counter()
        t, f = pitch._extraer_pitch_base(voice, 44100)
        predictions['pyin_base_voz'] = align(t, f, rt, np.median(np.diff(t))/2)
        tf, ff = pitch._filtrar_pitch(t, f.copy(), voice, 44100)
        predictions['pyin_final_voz'] = align(tf, ff, rt, np.median(np.diff(t))/2)
        row['offline_seconds'] = time.perf_counter()-tic
        for condition, signal in scenarios.items():
            for label, mod in [('antes', before), ('despues', pitch)]:
                key = condition+'_'+label
                ts, fs, durations = simulate(signal, 44100, mod.extraer_pitch_ligero_desde_audio,
                    config['LIVE_PITCH_INTERVAL'], config['LIVE_PITCH_CHUNK'], accept)
                predictions[key] = align(ts, fs, rt, 1024/44100/2)
                row['timing'][key] = {'median_ms': float(np.median(durations)*1000),
                                      'p95_ms': float(np.percentile(durations,95)*1000)}
        for key, est in predictions.items():
            if key in ['time','reference']:
                continue
            assert np.isfinite(est).all()
            c, err = counts(ref, est)
            row['metrics'][key] = {**percentages(c), 'counts': c,
                                  'median_abs_cents_both_voiced': float(np.median(err)) if len(err) else None}
        np.savez_compressed(OUT / 'predicciones' / (name+'.npz'), **predictions)
        cache.write_text(json.dumps(row, indent=2), encoding='utf-8')
        rows.append(row)
        print(f'{i}/95 {name}: pYIN={row["metrics"]["pyin_final_voz"]["pitch_correct_50c_pct"]:.1f}% '
              f'live={row["metrics"]["voz_sola_despues"]["pitch_correct_50c_pct"]:.1f}%', flush=True)
    def summarize(subset):
        result = {}
        for key in subset[0]['metrics']:
            c = {k: sum(r['metrics'][key]['counts'][k] for r in subset) for k in subset[0]['metrics'][key]['counts']}
            result[key] = {**percentages(c), 'counts': c,
                'macro_pitch_correct_50c_pct': float(np.mean([r['metrics'][key]['pitch_correct_50c_pct'] for r in subset]))}
        return result
    summary = {'protocol': signature, 'tracks': len(rows), 'singers': len(manifest['singers']),
               'duration_s': sum(r['duration_s'] for r in rows), 'summary': summarize(rows),
               'by_singer': {s: summarize([r for r in rows if r['singer']==s]) for s in manifest['singers']},
               'per_track': rows}
    (OUT / 'resultados.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print('Evaluacion completa: 95/95.', flush=True)


if __name__ == '__main__':
    main()
