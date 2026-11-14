import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import soundfile as sf
from audio.segmentacion import segmentar_referencia
from audio.retroalimentacion import generar_retroalimentacion, preparar_contexto_modelo


class SegmentTests(unittest.TestCase):
    def test_pauses_split_and_voiced_soft_notes_remain(self):
        sr = 1000
        y = np.ones(4000)*.2
        y[1000:1300] = 0
        y[2000:2500] = .001
        t = np.arange(2., 2.5, .01)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'ref.wav'
            sf.write(path, y, sr, subtype='FLOAT')
            segments = segmentar_referencia(path, t, np.full(len(t), 440.))
        self.assertEqual(segments, [dict(inicio_s=0., fin_s=1.), dict(inicio_s=1.3, fin_s=4.)])

    def test_short_pause_only_splits_long_blocks(self):
        sr = 1000
        y = np.ones(20000)*.2
        y[10000:10060] = 0
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'ref.wav'
            sf.write(path, y, sr, subtype='FLOAT')
            segments = segmentar_referencia(path, [], [])
            self.assertEqual(len(segments), 2)
            sf.write(path, y[:14000], sr, subtype='FLOAT')
            self.assertEqual(len(segmentar_referencia(path, [], [])), 1)

    def test_long_continuous_voice_is_not_forced_apart(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'ref.wav'
            sf.write(path, np.ones(30000)*.2, 1000)
            self.assertEqual(segmentar_referencia(path, [], []), [dict(inicio_s=0., fin_s=30.)])
            sf.write(path, np.zeros(30000), 1000)
            self.assertEqual(segmentar_referencia(path, [], []), [])

    def test_clip_to_take_and_never_include_excluded_pause(self):
        t = np.arange(0, 10, .01)
        f = np.full(len(t), 440.)
        r = generar_retroalimentacion(t, f, t, f, 7, segmentos=[
            dict(inicio_s=1, fin_s=3), dict(inicio_s=5, fin_s=10)])
        self.assertEqual([(f['inicio_s'], f['fin_s']) for f in r['fragmentos']], [(1., 3.), (5., 7.)])
        self.assertAlmostEqual(r['resumen_metricas']['duracion_s'], 4.)
        self.assertAlmostEqual(r['metodo']['segmentacion']['duracion_fuera_fragmentos_s'], 3.)
        empty = generar_retroalimentacion(t, f, t, f, 7, segmentos=[])
        self.assertEqual(empty['fragmentos'], [])
        with self.assertRaises(ValueError):
            generar_retroalimentacion(t, f, t, f, 7, segmentos=[dict(inicio_s=1, fin_s=4), dict(inicio_s=3, fin_s=5)])

    def test_events_localize_and_do_not_bridge_missing_detection(self):
        t = np.arange(0, 5, .01)
        ref = np.full(len(t), 440.)
        usr = ref.copy()
        usr[(t >= 1) & (t < 2)] *= 2**(-150/1200)
        usr[(t >= 2) & (t < 3)] = 0
        usr[(t >= 3) & (t < 4)] *= 2**(-150/1200)
        usr[t >= 4] *= 2
        r = generar_retroalimentacion(t, ref, t, usr, 5, segmentos=[dict(inicio_s=0, fin_s=5)])
        events = r['fragmentos'][0]['eventos']
        self.assertEqual([e['tipo'] for e in events], ['afinacion_cercana', 'desviacion_grave',
            'sin_deteccion_usuario', 'desviacion_grave', 'discrepancia_grande'])
        for i, e in enumerate(events):
            self.assertAlmostEqual(e['inicio_s'], i)
            self.assertAlmostEqual(e['fin_s'], i+1)
        self.assertEqual(events[-1]['categoria'], 'limitacion')
        ctx = preparar_contexto_modelo(r, 'f0001')
        self.assertEqual(len(ctx['analisis_fragmentos']), 1)
        with self.assertRaises(ValueError):
            preparar_contexto_modelo(r, 'f9999')

    def test_pipeline_uses_reference_segments(self):
        from audio import karaoke
        t = np.arange(0, 4, .01)
        f = np.full(len(t), 440.)
        with tempfile.TemporaryDirectory() as folder:
            voice = Path(folder)/'ref.wav'
            take = Path(folder)/'take.wav'
            y = np.ones(4000)*.2
            y[1000:1300] = 0
            sf.write(voice, y, 1000)
            sf.write(take, np.ones(4000)*.2, 1000)
            f[(t >= .98) & (t <= 1.32)] = 0
            with patch.object(karaoke, 'leer_pitch_csv', return_value=(t, f)), \
                 patch.object(karaoke, 'extraer_pitch', return_value=(t, f)), \
                 patch.object(karaoke, 'comparar', return_value={}):
                r = karaoke.comparar_grabacion(dict(vocals=str(voice), pitch_referencia='unused'), str(take))
            self.assertEqual(len(r['retroalimentacion']['fragmentos']), 2)
            self.assertEqual(r['retroalimentacion']['metodo']['segmentacion']['tipo'], 'pausas_referencia')


if __name__ == '__main__':
    unittest.main()
