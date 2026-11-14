"""Exporta datos para pruebas locales de UI, sin red; guarda compensaciones y explicaciones derivadas."""
import json
from pathlib import Path
import sys
import types
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
# Las conversiones de datos no necesitan inicializar una ventana pywebview.
try:
    import webview
except ImportError:
    sys.modules['webview'] = types.ModuleType('webview')
from desktop_live import LiveBackend
from audio.catalogo import cargar_cancion
from audio.tomas import listar_tomas
from audio.explicaciones import panel, explicar

backend = LiveBackend.__new__(LiveBackend)
song = cargar_cancion(sys.argv[1] if len(sys.argv)>1 else 'fdsofdisj_9425509d')
takes = listar_tomas(song)
if len(sys.argv)>2:
    takes.sort(key=lambda t:t['id'] != sys.argv[2])
takes=takes[:2]
data = panel(song, takes[0]['id'])
fid = data['fragmentos'][0]['id'] if data['fragmentos'] else None
out = ROOT/'output/prueba_interfaz'
out.mkdir(exist_ok=True)
fixture = dict(songs=[backend._cancion_para_ui(song)], takes=[backend._toma_para_ui(song, t) for t in takes],
    panel=data, summary=explicar(song,takes[0]['id']), fragment=explicar(song,takes[0]['id'],fid))
(out/'fixture.json').write_text(json.dumps(fixture,ensure_ascii=False),encoding='utf-8')
print('Fixture local generado sin llamadas de IA.')
