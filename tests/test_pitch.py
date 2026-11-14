"""Regresiones de frecuencia de muestreo y rechazo de senales no tonales."""
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np
import soundfile as sf
from audio import pitch


def tone(sr, hz=440, amplitude=.1, duration=.4):
    return amplitude * np.sin(2*np.pi*hz*np.arange(int(sr*duration))/sr)


class PitchTests(unittest.TestCase):
    def test_pyin_sample_rates_and_file_entrypoint(self):
        with patch.object(pitch, 'pw', None):
            for sr in [22050, 44100, 48000]:
                with self.subTest(sr=sr):
                    _, f = pitch._extraer_pitch_base(tone(sr), sr)
                    self.assertLess(abs(np.median(f[f > 0])-440), 2)
            with tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / 'tone.wav'
                sf.write(path, tone(44100), 44100, subtype='FLOAT')
                _, f = pitch.extraer_pitch_crudo(str(path))
                self.assertLess(abs(np.median(f)-440), 2)

    def test_live_silence_and_noise_are_not_notes(self):
        rng = np.random.default_rng(42)
        for y in [np.zeros(16758), rng.normal(0, .05, 16758)]:
            _, f = pitch.extraer_pitch_ligero_desde_audio(y, 44100)
            self.assertEqual(len(f), 0)

    def test_live_soft_and_loud_tones_keep_pitch(self):
        for amp in [.005, .1]:
            t, f = pitch.extraer_pitch_ligero_desde_audio(tone(44100, amplitude=amp), 44100, offset_t=2)
            self.assertGreater(len(f), 8)
            self.assertTrue(np.all(t >= 2))
            self.assertLess(abs(np.median(f)-440), 2)

    def test_rejected_periodicity_is_not_gap_filled(self):
        t = np.arange(9) * .025 + .05
        f = np.full(9, 440.)
        confidence = np.ones(9); confidence[4] = 0
        ts, _ = pitch._filtrar_pitch_tiempo_real(t, f, tone(44100), 44100, periodicidad=confidence)
        self.assertFalse(np.any(np.isclose(ts, t[4])))

    def test_live_harmonics_and_vibrato_keep_pitch(self):
        sr = 44100
        samples = np.arange(int(sr * .6)) / sr
        fundamental = 220 * 2 ** (25 * np.sin(2 * np.pi * 5 * samples) / 1200)
        phase = 2 * np.pi * np.cumsum(fundamental) / sr
        y = .06 * np.sin(phase) + .04 * np.sin(2 * phase) + .02 * np.sin(3 * phase)
        t, f = pitch.extraer_pitch_ligero_desde_audio(y, sr)
        self.assertGreater(len(f), 15)
        expected = np.interp(t, samples, fundamental)
        self.assertLess(np.median(abs(1200 * np.log2(f / expected))), 25)

    def test_fallback_rejects_noise(self):
        with patch.object(pitch.librosa, 'yin', side_effect=RuntimeError('forced fallback')):
            _, f = pitch.extraer_pitch_ligero_desde_audio(np.random.default_rng(7).normal(0, .05, 16758), 44100)
            self.assertEqual(len(f), 0)


class LearnedFilterTests(unittest.TestCase):
    def setUp(self):
        self.config_patch = patch.dict(pitch.FILTRO_TIEMPO_REAL, usar_filtro_aprendido=True)
        self.config_patch.start()
        self.addCleanup(self.config_patch.stop)

    def test_learned_filter_keeps_tones_at_live_sample_rates(self):
        from audio.filtro_aprendido import _cargar_modelo
        self.assertIsNotNone(_cargar_modelo())
        for sr in [22050, 44100, 48000]:
            for amp in [.005, .1]:
                with self.subTest(sr=sr, amplitude=amp):
                    t, f = pitch.extraer_pitch_ligero_desde_audio(tone(sr, amplitude=amp), sr, offset_t=2)
                    self.assertGreater(len(f), 3)
                    self.assertTrue(np.all(t >= 2))
                    self.assertLess(abs(np.median(f)-440), 2)

    def test_learned_filter_rejects_noise_even_with_fallback_detector(self):
        y = np.random.default_rng(42).normal(0, .05, 16758)
        self.assertEqual(len(pitch.extraer_pitch_ligero_desde_audio(y, 44100)[1]), 0)
        with patch.object(pitch.librosa, 'yin', side_effect=RuntimeError('forced fallback')):
            self.assertEqual(len(pitch.extraer_pitch_ligero_desde_audio(y, 44100)[1]), 0)

    def test_learned_filter_respects_microphone_noise_floor(self):
        _, f = pitch.extraer_pitch_ligero_desde_audio(tone(44100, amplitude=.005), 44100, ruido_base=.02)
        self.assertEqual(len(f), 0)

    def test_missing_model_preserves_previous_filter(self):
        from audio import filtro_aprendido
        y = tone(44100) + np.random.default_rng(6).normal(0, .02, 17640)
        with patch.dict(pitch.FILTRO_TIEMPO_REAL, usar_filtro_aprendido=False):
            expected = pitch.extraer_pitch_ligero_desde_audio(y, 44100)
        with patch.object(filtro_aprendido, '_cargar_modelo', return_value=None):
            actual = pitch.extraer_pitch_ligero_desde_audio(y, 44100)
        for a, b in zip(actual, expected):
            np.testing.assert_array_equal(a, b)

    def test_explicit_selection_does_not_modify_shared_defaults(self):
        y = tone(44100)
        with patch.dict(pitch.FILTRO_TIEMPO_REAL, usar_filtro_aprendido=False):
            with patch.object(pitch, 'aceptar_candidatos', return_value=None) as learned:
                pitch.extraer_pitch_ligero_desde_audio(y, 44100)
                learned.assert_not_called()
                pitch.extraer_pitch_ligero_desde_audio(y, 44100, usar_filtro_aprendido=True)
                learned.assert_called_once()
                self.assertFalse(pitch.FILTRO_TIEMPO_REAL['usar_filtro_aprendido'])

    def test_worker_passes_explicit_filter_selection(self):
        import queue
        import threading
        from audio import karaoke
        for enabled in [False, True]:
            q = queue.Queue()
            q.put((0., tone(44100)))
            stop = threading.Event()
            stop.set()
            with patch.object(karaoke, 'extraer_pitch_ligero_desde_audio',
                              return_value=(np.array([.1]), np.array([440.]), {})) as detector:
                received = []
                karaoke._worker_pitch_tiempo_real(q, stop, lambda t, f: received.extend(f),
                                                 None, 44100, .001, usar_filtro_aprendido=enabled)
                self.assertEqual(detector.call_args.kwargs['usar_filtro_aprendido'], enabled)
                self.assertEqual(received, [440.])
                self.assertEqual(q.unfinished_tasks, 0)


if __name__ == '__main__':
    unittest.main()
