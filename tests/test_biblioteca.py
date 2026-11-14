import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from audio import biblioteca


class BibliotecaTests(unittest.TestCase):
    def test_membership_multiple_collections_delete_keeps_song(self):
        with tempfile.TemporaryDirectory() as root, patch('audio.catalogo.CATALOGO_DIR', root):
            song=Path(root)/'song';song.mkdir()
            (song/'metadata.json').write_text(json.dumps({'id':'song'}))
            a=biblioteca.cambiar('create',nombre='Favoritas')[0]['id']
            b=biblioteca.cambiar('create',nombre='Práctica')[1]['id']
            biblioteca.cambiar('membership',a,song_id='song')
            biblioteca.cambiar('membership',b,song_id='song')
            self.assertTrue(all(c['songs']==['song'] for c in biblioteca.leer()))
            biblioteca.cambiar('delete',a)
            self.assertTrue((song/'metadata.json').exists())
            self.assertEqual(biblioteca.leer()[0]['songs'],['song'])
            biblioteca.cambiar('membership',b,song_id='song',included=False)
            self.assertEqual(biblioteca.leer()[0]['songs'],[])
            with self.assertRaises(ValueError): biblioteca.cambiar('create',nombre='práctica')

    def test_counts_and_dates(self):
        with tempfile.TemporaryDirectory() as root, patch('audio.catalogo.GRABACIONES_DIR',root), patch('audio.catalogo.cargar_canciones',return_value=[{'id':'s','creada_en':'2026-01-01'}]), patch.object(biblioteca,'leer',return_value=[]):
            folder=Path(root)/'s';folder.mkdir()
            for date in ['20260102_120000','20260103_120000']:
                (folder/f'usuario_{date}.wav').touch()
            stats=biblioteca.informacion()['stats']['s']
            self.assertEqual(stats['count'],2)
            self.assertEqual(stats['last'],'2026-01-03T12:00:00')
