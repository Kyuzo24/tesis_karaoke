"""YouTube search/import isolated from the application's Python/audio environment.

The worker runs in .youtube-env (Python 3.11+) and emits JSON lines only.
No credentials, browser cookies or restricted-content workarounds are used.
"""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading

ROOT = Path(__file__).resolve().parents[1]
MAX_SECONDS = 1200
MAX_BYTES = 100 * 1024 * 1024


def validar_id(video_id):
    value = str(video_id or '')
    if not re.fullmatch(r'[A-Za-z0-9_-]{11}', value):
        raise ValueError('Selecciona un resultado válido de YouTube.')
    return value


def _ejecutar(action, value, destination='', progreso_callback=None):
    executable = ROOT / '.youtube-env' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    bundled = ROOT / 'runtime' / 'youtube' / 'python.exe'
    if bundled.is_file():
        executable = bundled
    if not executable.is_file():
        raise RuntimeError('Falta instalar el componente de YouTube. Ejecuta instalar_youtube.bat.')
    env = os.environ.copy()
    env.pop('PYTHONPATH', None)
    env.pop('PYTHONHOME', None)
    env['PYTHONIOENCODING'] = 'utf-8'
    flags = {'creationflags': subprocess.CREATE_NO_WINDOW} if os.name == 'nt' else {}
    process = subprocess.Popen(
        [str(executable), str(Path(__file__).resolve()), action, value, str(destination)],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
        encoding='utf-8', errors='replace', env=env, **flags,
    )
    timed_out = threading.Event()
    def expire():
        timed_out.set()
        process.kill()
    timer = threading.Timer(90 if action == 'search' else 900, expire)
    timer.start()
    result = None
    try:
        for line in process.stdout:
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if 'progress' in event and progreso_callback:
                progreso_callback(event['progress'])
            if 'result' in event:
                result = event['result']
            if 'error' in event:
                raise RuntimeError(event['error'])
        process.wait()
        if timed_out.is_set():
            raise RuntimeError('YouTube tardó demasiado en responder. Intenta nuevamente.')
        if process.returncode or result is None:
            raise RuntimeError('No se pudo completar la operación con YouTube. Revisa tu conexión e intenta nuevamente.')
        return result
    finally:
        timer.cancel()
        if process.poll() is None:
            process.kill()
        process.wait()
        process.stdout.close()


def buscar_videos(query):
    query = str(query or '').strip()
    if not 2 <= len(query) <= 200:
        raise ValueError('Escribe entre 2 y 200 caracteres para buscar una canción.')
    return _ejecutar('search', query)


def descargar_audio(video_id, destination, progreso_callback=None):
    return _ejecutar('download', validar_id(video_id), destination, progreso_callback)


class _Logger:
    def debug(self, message):
        pass
    def warning(self, message):
        pass
    def error(self, message):
        pass


def _options():
    options = dict(quiet=True, no_warnings=True, logger=_Logger(), noplaylist=True,
                   socket_timeout=20, retries=2, extractor_retries=2, cachedir=False)
    node = shutil.which('node')
    if node:
        options['js_runtimes'] = {'node': {'path': node}}
    return options


def _resumen(entry):
    if not entry or not re.fullmatch(r'[A-Za-z0-9_-]{11}', str(entry.get('id', ''))):
        return None
    duration = entry.get('duration')
    if entry.get('live_status') in ('is_live', 'is_upcoming', 'post_live') or entry.get('is_live'):
        return None
    if duration is not None and (duration <= 0 or duration > MAX_SECONDS):
        return None
    return dict(id=entry['id'], title=entry.get('title') or 'Sin título',
                channel=entry.get('channel') or entry.get('uploader') or '',
                duration=duration, url='https://www.youtube.com/watch?v=' + entry['id'])


def _buscar(query, factory):
    # English response labels are parsed reliably; song titles keep their original language.
    client = factory(language='en')
    entries = client.search(query, filter='songs', limit=20)
    results, seen = [], set()
    for entry in entries or []:
        if not entry or entry.get('resultType') != 'song' or entry.get('isAvailable') is False:
            continue
        artists = ', '.join(artist['name'] for artist in entry.get('artists') or [] if artist.get('name'))
        item = _resumen(dict(id=entry.get('videoId'), title=entry.get('title'),
                             channel=artists, duration=entry.get('duration_seconds')))
        if item and item['id'] not in seen:
            item['artist'] = artists
            item['album'] = (entry.get('album') or {}).get('name', '')
            results.append(item)
            seen.add(item['id'])
    return results


def _descargar(video_id, destination, factory, emit):
    import imageio_ffmpeg
    video_id = validar_id(video_id)
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    url = 'https://www.youtube.com/watch?v=' + video_id
    last_percent = [-1]
    def progress(data):
        downloaded = data.get('downloaded_bytes') or 0
        if downloaded > MAX_BYTES:
            raise ValueError('El audio supera el límite de 100 MB.')
        if data.get('status') == 'downloading':
            total = data.get('total_bytes') or data.get('total_bytes_estimate')
            percent = min(100, int(downloaded * 100 / total)) if total else 0
            if percent != last_percent[0]:
                emit({'progress': f'Descargando audio: {percent}%'})
                last_percent[0] = percent
    options = {**_options(), 'format': 'bestaudio/best', 'max_filesize': MAX_BYTES,
               'outtmpl': str(destination / 'source.%(ext)s'), 'progress_hooks': [progress]}
    with factory(options) as ydl:
        info = ydl.extract_info(url, download=False)
        if not _resumen(info) or not info.get('duration'):
            raise ValueError('Selecciona un video de duración conocida, de hasta 20 minutos y que no esté en directo.')
        emit({'progress': 'Descargando audio…'})
        ydl.process_info(info)
        source = Path(ydl.prepare_filename(info)).resolve()
    if source.parent != destination or not source.is_file():
        raise ValueError('No se obtuvo un archivo de audio completo.')
    if source.stat().st_size > MAX_BYTES:
        raise ValueError('El audio supera el límite de 100 MB.')
    emit({'progress': 'Convirtiendo audio para preparar la canción…'})
    output = destination / 'audio.wav'
    flags = {'creationflags': subprocess.CREATE_NO_WINDOW} if os.name == 'nt' else {}
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-nostdin', '-y', '-i', str(source),
                    '-vn', '-ac', '2', '-ar', '44100', '-c:a', 'pcm_s16le', str(output)],
                   stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True, timeout=120, **flags)
    if not output.is_file() or output.stat().st_size <= 44:
        raise ValueError('El audio descargado está vacío.')
    return dict(path=str(output), source=dict(provider='youtube', video_id=video_id,
                url=url, title=info.get('title', ''), channel=info.get('channel') or info.get('uploader', '')))


def _main():
    def emit(event):
        print(json.dumps(event, ensure_ascii=False), flush=True)
    try:
        action, value = sys.argv[1:3]
        if action == 'search':
            from ytmusicapi import YTMusic
            result = _buscar(value, YTMusic)
        elif action == 'download':
            from yt_dlp import YoutubeDL
            result = _descargar(value, sys.argv[3], YoutubeDL, emit)
        else:
            raise ValueError('Operación no válida.')
        emit({'result': result})
    except ValueError as exc:
        emit({'error': str(exc)})
    except Exception:
        emit({'error': 'No se pudo obtener el contenido de YouTube. Comprueba tu conexión. '
              'El video podría no estar disponible o requerir acceso restringido. '
              'Si persiste, actualiza el componente con instalar_youtube.bat.'})


if __name__ == '__main__':
    _main()
