import threading
import unittest
from unittest.mock import MagicMock, patch

from audio import youtube
from desktop_live import LiveBackend

VIDEO = 'DTi8wZ1a1TA'


class YouTubeTests(unittest.TestCase):
    def test_rejects_urls_and_invalid_ids_before_launching_worker(self):
        with patch.object(youtube, '_ejecutar') as worker:
            for value in ('', '../file', 'https://youtube.com/watch?v=' + VIDEO):
                with self.assertRaises(ValueError):
                    youtube.descargar_audio(value, 'unused')
            worker.assert_not_called()

    def test_search_only_returns_available_songs_and_preserves_metadata(self):
        entry = dict(videoId=VIDEO, resultType='song', title='Canción', duration_seconds=60,
                     artists=[{'name': 'Artista'}], album={'name': 'Álbum'})
        factory = MagicMock()
        factory.return_value.search.return_value = [
            entry, entry, dict(entry, videoId='12345678901', resultType='video'),
            dict(entry, videoId='12345678902', duration_seconds=1201),
            dict(entry, videoId='12345678903', isAvailable=False), None]
        results = youtube._buscar('canción', factory)
        self.assertEqual([v['id'] for v in results], [VIDEO])
        self.assertEqual(results[0]['artist'], 'Artista')
        self.assertEqual(results[0]['album'], 'Álbum')
        factory.return_value.search.assert_called_once_with('canción', filter='songs', limit=20)

    def setUp(self):
        self.backend = LiveBackend.__new__(LiveBackend)
        self.backend._lock = threading.Lock()
        self.backend._estado = self.backend._estado_inicial()
        self.backend._cancion_para_ui = lambda song: song

    def test_busy_backend_does_not_download(self):
        self.backend._estado['status'] = 'recording'
        with patch.object(youtube, 'descargar_audio') as download:
            self.assertFalse(self.backend.add_song_from_youtube(VIDEO, 'Test')['ok'])
            download.assert_not_called()
        self.assertEqual(self.backend._estado['status'], 'recording')

    def test_existing_song_is_reused_without_download(self):
        song = dict(id='song', preparada=True, fuente=dict(provider='youtube', video_id=VIDEO))
        with patch('desktop_live.cargar_canciones', return_value=[song]), \
             patch.object(youtube, 'descargar_audio') as download:
            result = self.backend.add_song_from_youtube(VIDEO, 'Test')
            download.assert_not_called()
        self.assertTrue(result['reused'])
        self.assertEqual(self.backend._estado['status'], 'idle')

    def test_failed_preparation_can_retry_without_redownloading(self):
        song = dict(id='song', preparada=False, fuente=dict(provider='youtube', video_id=VIDEO))
        with patch('desktop_live.cargar_canciones', return_value=[song]), \
             patch('desktop_live.preparar_cancion', return_value=dict(song, preparada=True)) as prepare, \
             patch.object(youtube, 'descargar_audio') as download:
            result = self.backend.add_song_from_youtube(VIDEO, 'Test')
            prepare.assert_called_once()
            download.assert_not_called()
        self.assertTrue(result['ok'])

    def test_import_passes_source_to_catalog_and_cleans_temporary_files(self):
        from pathlib import Path
        folders = []
        source = dict(provider='youtube', video_id=VIDEO)
        def download(video, folder, callback):
            folders.append(folder)
            path = Path(folder) / 'audio.wav'
            path.write_bytes(b'test')
            return dict(path=str(path), source=source)
        with patch('desktop_live.cargar_canciones', return_value=[]), \
             patch.object(youtube, 'descargar_audio', side_effect=download), \
             patch('desktop_live.agregar_cancion', return_value={'id': 'new'}) as add:
            result = self.backend.add_song_from_youtube(VIDEO, 'Test')
        self.assertTrue(result['ok'])
        self.assertEqual(add.call_args.kwargs['fuente'], source)
        self.assertFalse(Path(folders[0]).exists())

    def test_download_failure_releases_backend_for_retry(self):
        with patch('desktop_live.cargar_canciones', return_value=[]), \
             patch.object(youtube, 'descargar_audio', side_effect=RuntimeError('Sin conexión')), \
             patch('desktop_live.logging.exception'):
            result = self.backend.add_song_from_youtube(VIDEO, 'Test')
        self.assertFalse(result['ok'])
        self.assertIn('Sin conexión', result['error'])
        self.assertFalse(self.backend._tarea_en_curso())


if __name__ == '__main__':
    unittest.main()
