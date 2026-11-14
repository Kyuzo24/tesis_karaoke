import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from audio.letras import parsear_lrc, guardar, cargar


class LetrasTests(unittest.TestCase):
    def test_timestamps_repetidos_y_fracciones(self):
        lines = parsear_lrc('[ar:Prueba]\n[00:12.5][01:02.050]Una línea\n[00:13.00]')
        self.assertEqual([l['time'] for l in lines], [12.5, 13, 62.05])
        self.assertEqual(lines[1]['text'], '')

    def test_offset_y_lineas_simultaneas(self):
        lines = parsear_lrc('[offset:500]\n[00:02.00]A\n[00:02.00]B')
        self.assertEqual(lines, [{'time': 1.5, 'text': 'A\nB'}])

    def test_rechaza_sin_tiempos(self):
        with self.assertRaises(ValueError):
            parsear_lrc('Letra sin sincronizar')

    def test_guardado_local_y_ajuste(self):
        with tempfile.TemporaryDirectory() as root, patch('audio.catalogo.CATALOGO_DIR', root):
            Path(root, 'prueba').mkdir()
            song = {'id': 'prueba'}
            saved = guardar(song, '[00:01]Prueba', 250)
            self.assertEqual(cargar(song), saved)
            with self.assertRaises(ValueError):
                guardar(song, '[00:01]Prueba', float('nan'))
            self.assertEqual(cargar(song), saved)
