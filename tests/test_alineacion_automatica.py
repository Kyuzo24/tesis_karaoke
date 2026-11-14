"""Desfases conocidos, rechazo de ambigüedad y persistencia de controles."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from audio import alineacion as a


def melody():
    t = np.arange(0, 30, .01)
    rng = np.random.default_rng(21)
    notes = 220*2**(rng.integers(0, 14, 60)/12)
    return t, notes[np.minimum((t/.5).astype(int), 59)]


class AutomaticAlignmentTests(unittest.TestCase):
    def test_known_positive_negative_and_fractional_offsets(self):
        t, f = melody()
        for lag in (.28, -.32, .135, -.475):
            with self.subTest(lag=lag):
                r = a.sugerir_desfase(t, f, t+lag, f)
                self.assertTrue(r['disponible'], r)
                self.assertLessEqual(abs(r['desfase_ms']-lag*1000), 20)
                self.assertGreaterEqual(r['acuerdo_ventanas'], 2/3)

    def test_zero_shift_does_not_move_a_correct_recording(self):
        t, f = melody()
        r = a.sugerir_desfase(t, f, t, f)
        self.assertFalse(r['disponible']); self.assertEqual(r['estado'], 'sin_cambio')

    def test_sustained_short_and_empty_inputs_are_rejected(self):
        t, f = melody()
        for tr, fr, tu, fu in [(t, np.full(len(t),440), t+.3, np.full(len(t),440)),
                              (t[:300], f[:300], t[:300]+.3, f[:300]), ([], [], [], [])]:
            self.assertFalse(a.sugerir_desfase(tr, fr, tu, fu)['disponible'])

    def test_periodic_melody_has_ambiguous_alternatives(self):
        t = np.arange(0,30,.01)
        f = np.where((t % .8) < .4,220.,440.)
        r = a.sugerir_desfase(t, f, t+.28, f)
        self.assertFalse(r['disponible'], r)
        self.assertEqual(r['estado'], 'ambiguo')

    def test_different_offsets_are_not_corrected_per_fragment(self):
        t, f = melody()
        shifts = np.where(t < 10, .28, np.where(t < 20, -.4, .8))
        r = a.sugerir_desfase(t, f, t+shifts, f)
        self.assertFalse(r['disponible'], r)

    def test_search_boundary_is_rejected(self):
        t, f = melody()
        r = a.sugerir_desfase(t, f, t+1.99, f)
        self.assertFalse(r['disponible']); self.assertEqual(r['estado'], 'limite')

    def test_auto_cache_manual_zero_disabled_and_restore(self):
        t, f = melody()
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)/'take.wav'; p.touch()
            first = a.resolver_ajuste(p,t,f,t+.28,f)
            self.assertEqual(first['desfase_s'], .28)
            with patch.object(a, 'sugerir_desfase', side_effect=AssertionError('No repetir cálculo')):
                self.assertEqual(a.resolver_ajuste(p,t,f,t+.28,f), first)
                a.guardar_ajuste(p, 0)
                state = a.resolver_ajuste(p,t,f,t+.28,f)
                self.assertEqual(state['modo'], 'manual'); self.assertEqual(state['desfase_s'],0)
                a.guardar_ajuste(p, 0, 'desactivado')
                self.assertEqual(a.resolver_ajuste(p,t,f,t+.28,f)['modo'],'desactivado')
            a.guardar_ajuste(p, 0, 'automatico')
            self.assertEqual(a.resolver_ajuste(p,t,f,t+.28,f)['desfase_s'],.28)
            self.assertAlmostEqual(a.resolver_ajuste(p,t,f,t+.4,f)['desfase_s'],.4,places=2)

    def test_legacy_manual_is_preserved_and_invalid_values_are_ignored(self):
        t, f = melody()
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)/'take.wav'; p.touch()
            a.ruta_ajuste(p).write_text(json.dumps(dict(desfase_s=.17, origen='ajuste_usuario')))
            self.assertEqual(a.resolver_ajuste(p,t,f,t+.28,f)['desfase_s'],.17)
            for value in ['NaN', 'Infinity', '2001']:
                with self.assertRaises(ValueError): a.guardar_ajuste(p, value)
            a.ruta_ajuste(p).write_text('null')
            self.assertEqual(a.leer_ajuste(p),0)

    def test_readonly_cache_does_not_prevent_analysis(self):
        t, f = melody()
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)/'take.wav'; p.touch()
            with patch.object(a, '_guardar', side_effect=PermissionError('Solo lectura')):
                state = a.resolver_ajuste(p,t,f,t+.28,f)
            self.assertEqual(state['estado'], 'aplicado')
            self.assertIn('No pudo guardarse', state['motivo'])

    def test_capture_edges_are_excluded_and_latency_is_not_claimed(self):
        t = np.arange(0,5,.01); f = np.full(len(t),440.)
        for lag in (.28, -.28):
            state = dict(modo='manual', estado='manual', desfase_s=lag, motivo='Manual')
            r = a.analizar_alineado(t,f,t+lag,f,5,None,state)
            self.assertAlmostEqual(r['resumen_metricas']['referencia_detectada_s'],4.72,places=2)
            self.assertAlmostEqual(r['resumen_metricas']['porcentaje_dentro_tolerancia'],100)
            self.assertIsNone(r['metodo']['latencia_estimada_s'])
            self.assertEqual(r['metodo']['sincronizacion'],'ajuste_manual')
            self.assertAlmostEqual(r['metodo']['extremos_no_capturados_s'],.28)


if __name__ == '__main__':
    unittest.main()
