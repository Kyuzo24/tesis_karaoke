"""Control sintetico de la causa del error; no modifica audio/pitch.py."""
from pathlib import Path
import json
import sys
import librosa
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from audio import pitch

sr = 44100
y = .1 * np.sin(2 * np.pi * 440 * np.arange(sr) / sr)
_, actual = pitch._extraer_pitch_base(y, sr)
corrected, _, _ = librosa.pyin(y, sr=sr, fmin=librosa.note_to_hz('C2'),
                              fmax=librosa.note_to_hz('C7'))
_, live = pitch.extraer_pitch_ligero_desde_audio(y[:int(sr * .38)], sr)
result = {
    'input_hz': 440, 'sample_rate': sr,
    'backend_actual': 'WORLD' if pitch.pw is not None else 'pYIN',
    'actual_median_hz': float(np.median(actual[actual > 0])),
    'pyin_explicit_sr_median_hz': float(np.nanmedian(corrected)),
    'yin_live_median_hz': float(np.median(live)),
    'scope': 'Control de un tono sintetico; no es una evaluacion de la correccion sobre Vocadito.',
}
assert abs(result['pyin_explicit_sr_median_hz'] - 440) < 2
out = ROOT / 'output/vocadito_benchmark/diagnostico_sr.json'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
