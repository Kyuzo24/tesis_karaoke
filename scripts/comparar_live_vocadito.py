"""Comparacion del detector anterior y nuevo, con ambas configuraciones de UI.

--development selecciona un umbral solo usando cantantes S1 a S8.
Sin esa opcion evalua todos los audios sin seleccionar parametros.
La particion restante es una comprobacion interna: Vocadito ya se inspecciono
en la evaluacion inicial y no se presenta como un test externo independiente.
"""
import argparse
import ast
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time
from types import SimpleNamespace

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from audio import pitch
from scripts.evaluar_vocadito import align, counts, percentages

OUT = ROOT / 'output/vocadito_mejoras'
DATA = ROOT / 'data/vocadito_benchmark'
DEVELOPMENT = {f'S{i}' for i in range(1, 9)}


def load_before():
    path = OUT / 'antes/pitch.py'
    spec = importlib.util.spec_from_file_location('pitch_before', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def ui_policy():
    # Extrae del codigo real solo las constantes y el filtro de puntos.
    # No importa la GUI, no abre dispositivos ni crea hilos.
    tree = ast.parse((ROOT / 'desktop_live.py').read_text(encoding='utf-8'))
    constants = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.startswith('LIVE_'):
                    constants[target.id] = ast.literal_eval(node.value)
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'LiveBackend')
    method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == '_aceptar_punto_usuario')
    scope = dict(constants)
    exec(compile(ast.Module(body=[method], type_ignores=[]), 'desktop_live_policy', 'exec'), scope)
    return constants, scope['_aceptar_punto_usuario']


def simulate(y, sr, detector, interval, window, accept=None):
    ts, fs, elapsed = [], [], []
    last = 0.
    state = SimpleNamespace(_ultimo_punto_usuario=None)
    for end in np.arange(interval, len(y) / sr, interval):
        start = max(0., end - window)
        tic = time.perf_counter()
        t, f = detector(y[int(start * sr):int(end * sr)], sr, offset_t=start, ruido_base=None)
        new = t > last
        if np.any(new):
            last = float(t[new].max())
            for ti, fi in zip(t[new], f[new]):
                if accept is None or accept(state, [float(ti), float(69 + 12 * np.log2(fi / 440))]):
                    ts.append(ti); fs.append(fi)
        elapsed.append(time.perf_counter() - tic)
    return np.asarray(ts), np.asarray(fs), elapsed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--development', action='store_true')
    args = parser.parse_args()
    before = load_before()
    config, accept = ui_policy()
    metadata = list(csv.DictReader((DATA / 'vocadito_metadata.csv').open(encoding='utf-8')))
    if args.development:
        metadata = [r for r in metadata if r['singer_id'] in DEVELOPMENT]
    variants = ['antes', '0.6', '0.7', '0.8'] if args.development else ['antes', 'despues']
    profiles = ['clasica', 'desktop']
    rows = []
    timings = {}
    warm = .1 * np.sin(2 * np.pi * 220 * np.arange(16758) / 44100)
    before.extraer_pitch_ligero_desde_audio(warm, 44100)
    pitch.extraer_pitch_ligero_desde_audio(warm, 44100)
    pred_dir = OUT / 'live_predicciones'
    if not args.development:
        pred_dir.mkdir(parents=True, exist_ok=True)
    for n, row in enumerate(metadata, 1):
        name = 'vocadito_' + row['track_id']
        y, sr = sf.read(DATA / 'Audio' / (name + '.wav'), dtype='float32')
        rt, ref = np.loadtxt(DATA / 'Annotations/F0' / (name + '_f0.csv'), delimiter=',').T
        preds = {'time': rt, 'reference': ref}
        result = {'track': name, 'singer': row['singer_id'],
                  'split': 'development' if row['singer_id'] in DEVELOPMENT else 'validation', 'metrics': {}}
        for profile in profiles:
            interval, window, policy = (.06, .38, None) if profile == 'clasica' else (
                config['LIVE_PITCH_INTERVAL'], config['LIVE_PITCH_CHUNK'], accept)
            for variant in variants:
                module = before if variant == 'antes' else pitch
                if args.development and variant != 'antes':
                    module.FILTRO_TIEMPO_REAL['min_periodicidad'] = float(variant)
                t, f, durations = simulate(y, sr, module.extraer_pitch_ligero_desde_audio, interval, window, policy)
                est = align(t, f, rt, 1024 / sr / 2)
                key = profile + '_' + variant
                c, _ = counts(ref, est)
                preds[key] = est
                result['metrics'][key] = {**percentages(c), 'counts': c}
                timings.setdefault(key, []).extend(durations)
        rows.append(result)
        if not args.development:
            np.savez_compressed(pred_dir / (name + '.npz'), **preds)
        print(f'{n}/{len(metadata)} {name}', flush=True)
    totals = {}
    for group in ['all', 'development', 'validation']:
        subset = [r for r in rows if group == 'all' or r['split'] == group]
        if not subset:
            continue
        totals[group] = {}
        for key in subset[0]['metrics']:
            pooled = {field: sum(r['metrics'][key]['counts'][field] for r in subset)
                      for field in subset[0]['metrics'][key]['counts']}
            totals[group][key] = {**percentages(pooled), 'counts': pooled}
    summary = {'development_singers': sorted(DEVELOPMENT), 'tracks': len(rows),
               'desktop_config': config, 'config_live': dict(pitch.FILTRO_TIEMPO_REAL),
               'pitch_sha256': hashlib.sha256((ROOT / 'audio/pitch.py').read_bytes()).hexdigest(),
               'before_sha256': hashlib.sha256((OUT / 'antes/pitch.py').read_bytes()).hexdigest(),
               'ui_sha256': hashlib.sha256((ROOT / 'desktop_live.py').read_bytes()).hexdigest(),
               'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               'summary': totals, 'per_track': rows,
               'timing_ms': {k: {'median': float(np.median(v)*1000), 'p95': float(np.percentile(v,95)*1000)}
                             for k, v in timings.items()}}
    if args.development:
        # Objetivo fijado antes de mirar los resultados: reducir falsos positivos
        # sin perder mas de 2 puntos de acierto ni aumentar omisiones mas de 2 puntos.
        eligible = [v for v in variants[1:]
                    if all(totals['all'][p + '_' + v]['pitch_correct_50c_pct'] >= totals['all'][p + '_antes']['pitch_correct_50c_pct'] - 2
                           and totals['all'][p + '_' + v]['missed_voiced_pct'] <= totals['all'][p + '_antes']['missed_voiced_pct'] + 2
                           for p in profiles)]
        summary['selected_threshold'] = min(eligible, key=lambda v: sum(totals['all'][p + '_' + v]['false_voiced_pct'] for p in profiles)) if eligible else None
    name = 'desarrollo_live.json' if args.development else 'comparacion_live.json'
    (OUT / name).write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'summary': totals, 'selected_threshold': summary.get('selected_threshold')}, indent=2))


if __name__ == '__main__':
    main()
