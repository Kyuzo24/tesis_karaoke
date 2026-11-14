"""Colecciones independientes del audio; escrituras atómicas."""
import json
import os
import tempfile
import threading
import uuid
from pathlib import Path
from datetime import datetime
from audio import catalogo

_lock = threading.RLock()


def _path():
    return Path(catalogo.CATALOGO_DIR) / 'colecciones.json'


def leer():
    if not _path().exists():
        return []
    return json.loads(_path().read_text(encoding='utf-8'))


def cambiar(accion, collection_id='', nombre='', song_id='', included=True):
    with _lock:
        items = leer()
        if accion == 'create':
            nombre = str(nombre).strip()
            if not nombre or len(nombre)>80:
                raise ValueError('Usa un nombre de 1 a 80 caracteres.')
            if any(c['name'].casefold()==nombre.casefold() for c in items):
                raise ValueError('Ya existe una colección con ese nombre.')
            items.append(dict(id=uuid.uuid4().hex, name=nombre, songs=[]))
        elif accion in ('delete','membership'):
            target = next((c for c in items if c['id']==collection_id), None)
            if target is None:
                raise ValueError('La colección ya no existe.')
            if accion == 'delete':
                items.remove(target)
            else:
                catalogo.cargar_cancion(song_id)
                target['songs'] = [s for s in target['songs'] if s!=song_id]
                if included:
                    target['songs'].append(song_id)
        else:
            raise ValueError('Operación desconocida.')
        _path().parent.mkdir(exist_ok=True, parents=True)
        with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=_path().parent,delete=False) as f:
            temp=f.name
            json.dump(items,f,ensure_ascii=False)
        try:
            os.replace(temp,_path())
        finally:
            if os.path.exists(temp): os.unlink(temp)
        return items


def informacion():
    stats={}
    for song in catalogo.cargar_canciones():
        recordings=list((Path(catalogo.GRABACIONES_DIR)/song['id']).glob('*.wav'))
        dates=[]
        for wav in recordings:
            try:
                date=datetime.strptime(wav.stem.removeprefix('usuario_'),'%Y%m%d_%H%M%S').isoformat()
            except ValueError:
                date=datetime.fromtimestamp(wav.stat().st_mtime).isoformat()
            dates.append(date)
        stats[song['id']]=dict(added=song.get('creada_en',''),count=len(recordings),last=max(dates,default=''))
    return dict(collections=leer(),stats=stats)
