import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock
import urllib.error
import numpy as np

from audio import explicaciones as ex
from audio.alineacion import sugerir_desfase, guardar_ajuste, leer_ajuste
from audio.retroalimentacion import generar_retroalimentacion, preparar_contexto_modelo


def contexto():
    t = np.arange(0, 5, .01)
    f = np.full(len(t), 440.)
    return preparar_contexto_modelo(generar_retroalimentacion(t, f, t, f, 5))


class ExplanationTests(unittest.TestCase):
    def test_no_network_even_with_old_environment_or_cache(self):
        import os
        import urllib.request
        c = contexto()
        with tempfile.TemporaryDirectory() as folder:
            audio = Path(folder)/'take.wav'; audio.touch()
            ex.ruta_cache(audio).write_text('{"old": {"resumen": "texto externo"}}')
            with patch.dict(os.environ, {'KARAOKE_LLM_PROVIDER':'ollama', 'OPENAI_API_KEY':'secret'}), \
                 patch.object(ex, 'obtener_contexto_retroalimentacion', return_value=c), \
                 patch.object(ex, '_buscar_toma', return_value={'voice_path':str(audio)}), \
                 patch.object(urllib.request, 'urlopen', side_effect=AssertionError('No debe haber red')):
                r = ex.explicar({}, 'take')
                self.assertEqual(r['origen'], 'reglas')
                self.assertNotIn('texto externo', json.dumps(r))
                self.assertNotIn('secret', json.dumps(r))
                self.assertTrue(ex.explicar({}, 'take')['guardada'])
                c['metodo']['sincronizacion'] = 'ajuste_manual'
                self.assertFalse(ex.explicar({}, 'take')['guardada'])
                self.assertTrue(r['trazabilidad'])
                with self.assertRaises(ValueError): ex.configurar('ollama')

    def test_bad_evidence_category_action_and_cross_fragment_rejected(self):
        c = ex._contexto(contexto(), None)
        valid = ex.plantilla(c)
        bad = copy.deepcopy(valid); bad['aciertos'][0]['evidencia_ids'] = ['inventado']
        with self.assertRaises(ValueError): ex.validar(bad, c)
        bad = copy.deepcopy(valid); bad['aspectos_a_revisar'] = bad['aciertos']; bad['aciertos'] = []
        with self.assertRaises(ValueError): ex.validar(bad, c)
        bad = copy.deepcopy(valid); bad['practica_sugerida'] = [dict(texto='x', evidencia_ids=[c['evidencias'][0]['id']], accion_id='inventada')]
        with self.assertRaises(ValueError): ex.validar(bad, c)
        fc = ex._contexto(contexto(), 'f0001')
        with self.assertRaises(ValueError): ex.validar(valid, fc)

    def render(self, cents=0, coverage=1, duration=5, fragment=True):
        t = np.arange(0, duration, .01); ref = np.full(len(t), 440.)
        usr = ref*2**(cents/1200); usr[t >= duration*coverage] = 0
        report = generar_retroalimentacion(t, ref, t, usr, duration)
        c = preparar_contexto_modelo(report, 'f0001' if fragment else None)
        return ex.plantilla(ex._contexto(c, 'f0001' if fragment else None))

    def test_low_coverage_never_judges_singing(self):
        r = self.render(cents=-150, coverage=.1)
        self.assertEqual(r['aciertos'], []); self.assertEqual(r['aspectos_a_revisar'], [])
        self.assertTrue(all(p['accion_id'] != 'comparar_altura' for p in r['practica_sugerida']))
        self.assertIn('insuficiente', r['resumen'])

    def test_partial_evidence_scope_and_direction(self):
        r = self.render(cents=-150, coverage=.6)
        self.assertIn('parcial', r['resumen']); self.assertIn('más graves', r['resumen'])
        self.assertLessEqual(len(r['aspectos_a_revisar']), 2)
        self.assertEqual(len(r['practica_sugerida']), 1)
        self.assertIn('más grave', r['practica_sugerida'][0]['texto'])

    def test_large_discrepancy_prioritizes_correspondence(self):
        r = self.render(cents=1200)
        self.assertEqual(r['aspectos_a_revisar'], [])
        self.assertEqual(r['practica_sugerida'][0]['accion_id'], 'comprobar_correspondencia')
        self.assertNotIn('octava', json.dumps(r))

    def test_perfect_and_short_fragments_have_no_invented_practice(self):
        r = self.render()
        self.assertEqual(len(r['aciertos']), 1); self.assertEqual(r['practica_sugerida'], [])
        r = self.render(duration=.5)
        self.assertEqual(r['aciertos'], []); self.assertIn('insuficiente', r['resumen'])

    def test_exact_time_boundaries_are_not_rejected_by_float_roundoff(self):
        r = self.render(duration=1)
        self.assertIn('parcial', r['resumen'])
        self.assertNotIn('insuficiente', r['resumen'])
        r = self.render(duration=2)
        self.assertIn('mayor parte', r['resumen'])


class AlignmentTests(unittest.TestCase):
    def test_manual_adjustment_recalculates_saved_take_without_rewriting_result(self):
        from audio import tomas
        import soundfile as sf
        t = np.arange(0, 4, .01)
        f = np.where(t < 2, 440., 660.)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'take.wav'; result = Path(folder)/'take_resultado.json'
            sf.write(path, np.zeros(5000), 1000)
            original = json.dumps({'grafico': dict(t_ref=t.tolist(),f_ref=f.tolist(),t_usr=(t+.28).tolist(),f_usr=f.tolist())})
            result.write_text(original,encoding='utf-8')
            guardar_ajuste(path, 280)
            with patch.object(tomas, '_buscar_toma', return_value=dict(result_path=str(result), voice_path=str(path))), \
                 patch('audio.segmentacion.preparar_segmentacion', return_value=[dict(inicio_s=0.,fin_s=4.)]):
                context = tomas.obtener_contexto_retroalimentacion({}, 'take')
            self.assertEqual(context['metodo']['sincronizacion'], 'ajuste_manual')
            self.assertAlmostEqual(context['resumen_metricas']['porcentaje_dentro_tolerancia'], 100.)
            self.assertEqual(result.read_text(encoding='utf-8'), original)

    def test_known_shift_is_suggested_but_not_automatically_applied(self):
        t = np.arange(0, 15, .02)
        notes = np.array([220, 330, 440, 247, 392, 294, 494, 262, 349, 440, 294, 220, 392, 262, 330])
        f = notes[np.minimum(t.astype(int), len(notes)-1)]
        r = sugerir_desfase(t, f, t+.28, f)
        self.assertTrue(r['disponible']); self.assertEqual(r['desfase_ms'], 280)
        r = sugerir_desfase(t, np.full(len(t),440), t, np.full(len(t),440))
        self.assertFalse(r['disponible'])

    def test_manual_offset_persistence_and_bounds(self):
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder)/'take.wav')
            self.assertEqual(leer_ajuste(path), 0)
            guardar_ajuste(path, 240); self.assertAlmostEqual(leer_ajuste(path), .24)
            for value in [float('nan'), 2001, -2001]:
                with self.assertRaises(ValueError): guardar_ajuste(path, value)


if __name__ == '__main__':
    unittest.main()
