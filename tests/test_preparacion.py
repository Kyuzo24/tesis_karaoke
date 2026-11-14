import unittest
from unittest.mock import patch

from audio.separacion import separar_voz, progreso_demucs
from audio import catalogo


class PreparationTests(unittest.TestCase):
    def test_phase_is_reported_before_demucs_and_failure_propagates(self):
        phases = []
        with patch('audio.separacion.os.path.exists', return_value=False), \
             patch('audio.separacion.subprocess.Popen', side_effect=RuntimeError('fallo')):
            with self.assertRaises(RuntimeError):
                separar_voz('song.wav', progreso_callback=phases.append)
        self.assertEqual(phases, ['Separando voz y acompañamiento…'])

    def test_real_progress_and_eta(self):
        self.assertEqual(progreso_demucs('19%|### | 52.65/280.8 [01:37<07:02, 1.85s/seconds]'),
                         'Separando voz y acompañamiento: 19% · Restante estimado: 07:02')
        self.assertIsNone(progreso_demucs('Loading model'))

    def test_catalog_reports_pitch_phase_and_preserves_callback(self):
        phases = []
        metadata = dict(original='song.wav', pitch_referencia='pitch.csv')
        with patch.object(catalogo, 'cargar_cancion', return_value=metadata), \
             patch.object(catalogo, 'preparar_pistas', return_value=('vocals.wav', 'track.wav')) as preparation, \
             patch.object(catalogo.os.path, 'exists', return_value=False), \
             patch.object(catalogo, 'extraer_pitch', return_value=([], [])), \
             patch.object(catalogo, 'guardar_csv'), patch.object(catalogo, 'guardar_metadata'):
            catalogo.preparar_cancion('song', progreso_callback=phases.append)
        self.assertEqual(phases, ['Detectando las notas de referencia…'])
        self.assertEqual(preparation.call_args.kwargs['progreso_callback'], phases.append)


if __name__ == '__main__':
    unittest.main()
