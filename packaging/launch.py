"""Installed entry point. All personal data belongs to the Windows user."""
import os
from pathlib import Path
import sys
import traceback

ROOT = Path(__file__).resolve().parent
DATA = Path(os.environ.get('KARAOKE_DATA_DIR') or
            Path(os.environ['LOCALAPPDATA']) / 'Karaoke Studio' / 'Datos')
DATA.mkdir(parents=True, exist_ok=True)
os.environ['KARAOKE_DATA_DIR'] = str(DATA)
os.environ['KARAOKE_INSTALLED'] = '1'
os.environ['TORCH_HOME'] = str(ROOT / 'models')
os.environ['PATH'] = str(ROOT / 'tools') + os.pathsep + os.environ.get('PATH', '')
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['NUMBA_CACHE_DIR'] = str(DATA / 'cache')
os.chdir(DATA)
log = open(DATA / 'inicio.log', 'a', encoding='utf-8', buffering=1)
sys.stdout = log
sys.stderr = log
try:
    from desktop_live import main
    main()
except Exception:
    traceback.print_exc()
    import ctypes
    ctypes.windll.user32.MessageBoxW(
        None, 'No se pudo abrir Karaoke Studio. El detalle está en ' + str(DATA / 'inicio.log'),
        'Karaoke Studio', 0x10)
    raise
