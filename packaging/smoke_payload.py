"""Validate only the packaged files, with disposable user data."""
import os
from pathlib import Path
import sys
import tempfile
import time
import threading
from contextlib import contextmanager

sys.argv[0] = str(Path(__file__).resolve())

@contextmanager
def isolated_folder():
    original = Path.cwd()
    with tempfile.TemporaryDirectory(prefix='karaoke-installer-test-') as folder:
        try:
            yield folder
        finally:
            os.chdir(original)

root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root))
os.environ['PATH'] = str(root / 'tools') + os.pathsep + os.environ['PATH']
os.environ['KARAOKE_INSTALLED'] = '1'
os.environ['TORCH_HOME'] = str(root / 'models')
with isolated_folder() as folder:
    profile = Path(folder) / 'windows-profile'
    previous = profile / 'Karaoke Studio' / 'tutorial-visto'
    previous.parent.mkdir(parents=True)
    previous.touch()
    os.environ['LOCALAPPDATA'] = str(profile)
    os.environ['KARAOKE_DATA_DIR'] = folder
    os.environ['NUMBA_CACHE_DIR'] = str(Path(folder) / 'cache')
    os.chdir(folder)
    import desktop_live
    from audio import catalogo
    from audio.separacion import _comando_python_demucs
    assert Path(desktop_live.__file__).parent == root
    assert catalogo.cargar_canciones() == []
    assert _comando_python_demucs()[0] == sys.executable
    print('PASS runtime aislado y biblioteca vacia', flush=True)
    if '--audio' in sys.argv:
        import numpy as np
        import soundfile as sf
        source = Path(folder) / 'prueba.wav'
        sr = 44100
        signal = .05 * np.sin(2 * np.pi * 440 * np.arange(sr) / sr)
        sf.write(source, signal, sr)
        song = catalogo.agregar_cancion(str(source), 'Prueba sintetica', progreso_callback=print)
        assert song['preparada']
        assert Path(song['instrumental']).is_file()
        assert Path(song['pitch_referencia']).is_file()
        print('PASS Demucs, modelo incluido y preparacion completa', flush=True)
    else:
        import webview
        backend = desktop_live.LiveBackend()
        assert not backend.tutorial_seen(), 'Installed app inherited development preferences'
        assert backend._guide_preferences._marker.parent == Path(folder) / 'Preferencias'
        window = webview.create_window('Verificacion del instalador', (root / 'ui_live/index.html').as_uri(), js_api=backend)
        def check():
            for _ in range(200):
                if window.evaluate_js('window.tutorial?.active === true'):
                    assert backend.get_songs() == []
                    print('PASS interfaz y tutorial con biblioteca vacia', flush=True)
                    window.destroy()
                    return
                time.sleep(.1)
            os._exit(2)
        watchdog = threading.Timer(50, lambda: os._exit(3))
        watchdog.daemon = True
        watchdog.start()
        webview.start(check, gui='edgechromium')
        watchdog.cancel()
