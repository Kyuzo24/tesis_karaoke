"""Letras LRC locales; la red solo se usa al buscar explícitamente."""
import json
import os
import re
import tempfile
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

STAMP = re.compile(r"\[(\d+):([0-5]\d)(?:[.:](\d{1,3}))?\]")


def parsear_lrc(texto):
    if not isinstance(texto, str) or len(texto) > 500_000:
        raise ValueError('La letra es demasiado grande o no es texto.')
    offset = re.findall(r'\[offset:([+-]?\d+)\]', texto, re.I)
    offset = int(offset[-1]) / 1000 if offset else 0
    lineas = []
    for linea in texto.splitlines():
        marcas = list(STAMP.finditer(linea))
        if not marcas:
            continue
        contenido = linea[marcas[-1].end():].strip()
        for marca in marcas:
            minutos, segundos, fraccion = marca.groups()
            tiempo = int(minutos) * 60 + int(segundos) + float('0.' + (fraccion or '0'))
            lineas.append({'time': max(0, tiempo - offset), 'text': contenido})
    lineas.sort(key=lambda l: l['time'])
    agrupadas = []
    for linea in lineas:
        if agrupadas and agrupadas[-1]['time'] == linea['time']:
            if linea['text'] and linea['text'] not in agrupadas[-1]['text'].split('\n'):
                agrupadas[-1]['text'] += ('\n' if agrupadas[-1]['text'] else '') + linea['text']
        else:
            agrupadas.append(linea)
    if not agrupadas:
        raise ValueError('No hay tiempos LRC válidos. Usa líneas como [00:23.50]Texto.')
    return agrupadas


def _ruta(cancion):
    from audio.catalogo import CATALOGO_DIR
    return Path(CATALOGO_DIR) / cancion['id'] / 'letra.json'


def cargar(cancion):
    try:
        return json.loads(_ruta(cancion).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None


def guardar(cancion, texto, desfase_ms=0, fuente='Archivo LRC'):
    desfase = float(desfase_ms)
    if not -30000 <= desfase <= 30000:
        raise ValueError('El ajuste debe estar entre -30000 y 30000 ms.')
    datos = dict(lrc=texto, lines=parsear_lrc(texto), offset_ms=desfase, source=str(fuente)[:200])
    ruta = _ruta(cancion)
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=ruta.parent, delete=False) as f:
        temporal = f.name
        json.dump(datos, f, ensure_ascii=False)
    try:
        os.replace(temporal, ruta)
    finally:
        if os.path.exists(temporal):
            os.unlink(temporal)
    return datos


def buscar(titulo, artista):
    if not str(titulo).strip():
        raise ValueError('Escribe el título de la canción.')
    query = urlencode({'track_name': str(titulo)[:200], 'artist_name': str(artista)[:200]})
    request = Request('https://lrclib.net/api/search?' + query,
                      headers={'User-Agent': 'KaraokeStudio/1.0', 'Accept': 'application/json'})
    with urlopen(request, timeout=12) as respuesta:
        raw = respuesta.read(4_000_001)
    if len(raw) > 4_000_000:
        raise ValueError('La respuesta de LRCLIB es demasiado grande.')
    registros = json.loads(raw)
    resultados = []
    for r in registros:
        if not r.get('syncedLyrics'):
            continue
        try:
            parsear_lrc(r['syncedLyrics'])
        except ValueError:
            continue
        resultados.append(dict(id=r['id'], title=r.get('trackName'), artist=r.get('artistName'),
                               album=r.get('albumName'), duration=r.get('duration'), lrc=r['syncedLyrics']))
    return resultados[:20]
