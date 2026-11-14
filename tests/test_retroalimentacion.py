import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import soundfile as sf

from audio.retroalimentacion import generar_retroalimentacion, preparar_contexto_modelo


def serie(duration=10, cents=0):
    t = np.arange(0, duration, .01)
    return t, np.full(len(t), 440.), np.full(len(t), 440 * 2 ** (cents / 1200))


class FeedbackTests(unittest.TestCase):
    def test_in_tune_has_supported_strength_and_exact_coverage(self):
        t, ref, usr = serie()
        r = generar_retroalimentacion(t, ref, t, usr, 10)
        m = r['resumen_metricas']
        self.assertAlmostEqual(m['comparable_s'], 10)
        self.assertAlmostEqual(m['porcentaje_dentro_tolerancia'], 100)
        self.assertEqual(r['calidad']['suficiencia_evidencia'], 'suficiente')
        self.assertEqual({h['tipo'] for h in r['hallazgos']}, {'afinacion_cercana'})
        json.dumps(r, allow_nan=False)

    def test_signed_errors_are_localized_in_recording_time(self):
        t, ref, usr = serie()
        usr[t < 5] *= 2 ** (-150 / 1200)
        usr[t >= 5] *= 2 ** (150 / 1200)
        r = generar_retroalimentacion(t, ref, t, usr, 10)
        self.assertEqual([h['tipo'] for h in r['hallazgos']], ['tendencia_grave', 'tendencia_aguda'])
        self.assertEqual([(h['inicio_s'], h['fin_s']) for h in r['hallazgos']], [(0., 5.), (5., 10.)])
        self.assertAlmostEqual(r['resumen_metricas']['error_absoluto_medio_cents'], 150)

    def test_missing_detection_is_not_bad_singing_or_a_strength(self):
        t, ref, usr = serie(5)
        keep = t < .3
        r = generar_retroalimentacion(t, ref, t[keep], usr[keep], 5)
        self.assertEqual(r['hallazgos'][0]['tipo'], 'deteccion_insuficiente')
        self.assertEqual(r['seleccion']['aspectos_por_mejorar'], [])
        self.assertEqual(r['seleccion']['fortalezas'], [])
        self.assertLess(r['resumen_metricas']['cobertura_comparable_pct'], 10)
        self.assertEqual(r['resumen_metricas']['porcentaje_dentro_tolerancia'], 100)

    def test_reference_gaps_are_not_interpolated(self):
        t, ref, usr = serie(10)
        keep = (t < 1) | (t > 9)
        r = generar_retroalimentacion(t[keep], ref[keep], t, usr, 10)
        self.assertLess(r['resumen_metricas']['referencia_detectada_s'], 2.1)
        self.assertGreater(r['resumen_metricas']['usuario_sin_referencia_detectada_s'], 7.9)

    def test_one_octave_is_not_silently_discarded(self):
        t, ref, usr = serie(5, 1200)
        r = generar_retroalimentacion(t, ref, t, usr, 5)
        self.assertAlmostEqual(r['resumen_metricas']['error_absoluto_medio_cents'], 1200)
        self.assertEqual(r['hallazgos'][0]['tipo'], 'discrepancia_grande')
        self.assertEqual(r['seleccion']['aspectos_por_mejorar'], [])

    def test_empty_zero_and_invalid_inputs_are_explicit(self):
        for duration in [0, 5]:
            r = generar_retroalimentacion([], [], [], [], duration)
            self.assertIsNone(r['resumen_metricas']['porcentaje_dentro_tolerancia'])
            self.assertEqual(r['calidad']['suficiencia_evidencia'], 'referencia_insuficiente')
            json.dumps(preparar_contexto_modelo(r), allow_nan=False)
        r = generar_retroalimentacion([0, 0, np.nan, -1, 3], [440, 0, 440, 440, np.inf], [], [], 5)
        self.assertEqual(r['calidad']['entrada_referencia']['puntos_descartados'], 3)
        self.assertEqual(r['calidad']['entrada_referencia']['tiempos_duplicados'], 1)
        self.assertEqual(r['resumen_metricas']['referencia_detectada_s'], 0)
        with self.assertRaises(ValueError):
            generar_retroalimentacion([0, 1], [440], [], [], 2)
        with self.assertRaises(ValueError):
            generar_retroalimentacion([], [], [], [], float('nan'))

    def test_duration_and_sampling_density_do_not_inflate_coverage(self):
        t, ref, usr = serie(5.013)
        a = generar_retroalimentacion(t, ref, t, usr, 5.013)
        b = generar_retroalimentacion(t[::2], ref[::2], t[::2], usr[::2], 5.013)
        for r in [a, b]:
            self.assertAlmostEqual(r['resumen_metricas']['duracion_s'], 5.013)
            self.assertAlmostEqual(sum(f['metricas']['duracion_s'] for f in r['fragmentos']), 5.013)
            self.assertAlmostEqual(r['resumen_metricas']['cobertura_comparable_pct'], 100)
            self.assertLessEqual(r['resumen_metricas']['comparable_s'], 5.013 + 1e-9)

    def test_context_has_bounded_selection_and_evidence_ids(self):
        t, ref, usr = serie(60, -100)
        r = generar_retroalimentacion(t, ref, t, usr, 60)
        context = preparar_contexto_modelo(r)
        self.assertEqual(len(context['hallazgos_seleccionados']), 3)
        self.assertEqual(context['hallazgos_no_incluidos'], 9)
        for h in context['hallazgos_seleccionados']:
            fragment = next(f for f in r['fragmentos'] if f['id'] == h['fragmento_id'])
            for key, value in h['evidencia'].items():
                self.assertEqual(value, fragment['metricas'][key])
        self.assertNotIn('grafico', context)
        self.assertNotIn('fragmentos', context)
        json.dumps(context, allow_nan=False)

    def test_noise_without_reference_does_not_become_a_singing_error(self):
        t, _, usr = serie(5)
        r = generar_retroalimentacion([], [], t, usr, 5)
        self.assertEqual(r['hallazgos'][0]['tipo'], 'referencia_insuficiente')
        self.assertIsNone(r['resumen_metricas']['porcentaje_dentro_tolerancia'])

    def test_partial_coverage_does_not_produce_a_vocal_judgement(self):
        t, ref, usr = serie(5, -150)
        keep = t < 3.5
        r = generar_retroalimentacion(t, ref, t[keep], usr[keep], 5)
        self.assertEqual(r['hallazgos'][0]['tipo'], 'cobertura_parcial')
        self.assertEqual(r['seleccion']['aspectos_por_mejorar'], [])

    def test_temporal_mismatch_is_not_hidden_by_dtw(self):
        t, ref, usr = serie(5)
        keep = t < 1
        r = generar_retroalimentacion(t[keep], ref[keep], t[keep] + 3, usr[keep], 5)
        self.assertEqual(r['resumen_metricas']['comparable_s'], 0)
        self.assertEqual(r['hallazgos'][0]['tipo'], 'deteccion_insuficiente')
        self.assertFalse(r['metodo']['dtw'])


class FeedbackIntegrationTests(unittest.TestCase):
    def test_new_recording_applies_auto_before_feedback_and_preserves_raw_graph(self):
        from audio import karaoke, tomas
        t = np.arange(0, 15, .02)
        notes = np.array([220,330,440,247,392,294,494,262,349,440,294,220,392,262,330])
        f = notes[np.minimum(t.astype(int), 14)]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'take.wav'
            sf.write(path, np.zeros(16000), 1000)
            with patch.object(karaoke, 'leer_pitch_csv', return_value=(t,f)), \
                 patch.object(karaoke, 'extraer_pitch', return_value=(t+.28,f)), \
                 patch.object(karaoke, 'comparar', return_value={'error_prom':123.}):
                result = karaoke.comparar_grabacion({'pitch_referencia':'unused.csv'},str(path))
            report = result['retroalimentacion']
            self.assertEqual(report['metodo']['sincronizacion'],'ajuste_automatico')
            self.assertAlmostEqual(report['metodo']['compensacion_temporal_s'],.28)
            self.assertGreater(report['resumen_metricas']['porcentaje_dentro_tolerancia'],99)
            self.assertAlmostEqual(result['grafico']['t_usr'][0],.28)
            stored = path.with_name('take_resultado.json'); before = stored.read_bytes()
            with patch.object(tomas,'_buscar_toma',return_value={'voice_path':str(path),'result_path':str(stored)}):
                reread = tomas.obtener_contexto_retroalimentacion({},'take')
            self.assertEqual(reread['metodo']['sincronizacion'],'ajuste_automatico')
            self.assertEqual(before,stored.read_bytes())

    def test_comparison_persists_feedback_without_changing_legacy_metrics(self):
        from audio import karaoke
        t, ref, usr = serie(1)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'take.wav'
            sf.write(path, np.zeros(44100), 44100)
            with patch.object(karaoke, 'leer_pitch_csv', return_value=(t, ref)), \
                 patch.object(karaoke, 'extraer_pitch', return_value=(t, usr)), \
                 patch.object(karaoke, 'comparar', return_value={'error_prom': 123., 'tendencia': 'grave'}):
                result = karaoke.comparar_grabacion({'pitch_referencia': 'unused.csv'}, str(path))
            saved = json.loads(path.with_name('take_resultado.json').read_text(encoding='utf-8'))
            self.assertEqual(saved, result)
            self.assertEqual(saved['error_prom'], 123.)
            self.assertIn('grafico', saved)
            self.assertEqual(saved['retroalimentacion']['resumen_metricas']['error_absoluto_medio_cents'], 0.)

    def test_existing_take_can_be_read_without_reanalysis_or_file_mutation(self):
        from audio import tomas
        t, ref, usr = serie(1)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'take.wav'
            result_path = Path(folder) / 'take_resultado.json'
            sf.write(path, np.zeros(44100), 44100)
            result_path.write_text(json.dumps({'grafico': {'t_ref': t.tolist(), 'f_ref': ref.tolist(),
                                                          't_usr': t.tolist(), 'f_usr': usr.tolist()}}), encoding='utf-8')
            original = result_path.read_bytes()
            with patch.object(tomas, '_buscar_toma', return_value={'result_path': str(result_path), 'voice_path': str(path)}):
                result = tomas.obtener_contexto_retroalimentacion({'id': 'test'}, 'take')
            self.assertEqual(result_path.read_bytes(), original)
            self.assertEqual(result['version'], '3.0.0')
            self.assertEqual(result['resumen_metricas']['porcentaje_dentro_tolerancia'], 100)


if __name__ == '__main__':
    unittest.main()
