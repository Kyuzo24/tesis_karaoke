import csv
import json
import os
import shutil
import uuid
from datetime import datetime

from audio.guardar import guardar_csv
from audio.pitch import extraer_pitch
from audio.separacion import preparar_pistas


CATALOGO_DIR = "canciones"
GRABACIONES_DIR = "grabaciones"


def asegurar_directorios():
    os.makedirs(CATALOGO_DIR, exist_ok=True)
    os.makedirs(GRABACIONES_DIR, exist_ok=True)


def _slug(texto):
    limpio = "".join(c.lower() if c.isalnum() else "_" for c in texto.strip())
    partes = [p for p in limpio.split("_") if p]
    return "_".join(partes) or "cancion"


def _metadata_path(cancion_id):
    return os.path.join(CATALOGO_DIR, cancion_id, "metadata.json")


def guardar_metadata(metadata):
    with open(_metadata_path(metadata["id"]), "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)


def cargar_canciones():
    asegurar_directorios()
    canciones = []
    for nombre in os.listdir(CATALOGO_DIR):
        metadata_path = _metadata_path(nombre)
        if os.path.exists(metadata_path):
            with open(metadata_path, "r", encoding="utf-8") as f:
                canciones.append(json.load(f))
    return sorted(canciones, key=lambda item: item.get("titulo", "").lower())


def cargar_cancion(cancion_id):
    with open(_metadata_path(cancion_id), "r", encoding="utf-8") as f:
        return json.load(f)


def eliminar_cancion(cancion_id):
    asegurar_directorios()
    metadata = cargar_cancion(cancion_id)

    carpeta = os.path.join(CATALOGO_DIR, cancion_id)
    demucs_dir = ""
    original = metadata.get("original") or ""
    if original:
        nombre_original = os.path.splitext(os.path.basename(original))[0]
        demucs_dir = os.path.join("output", "htdemucs", nombre_original)

    grabaciones_dir = os.path.join(GRABACIONES_DIR, cancion_id)

    for ruta in [carpeta, demucs_dir, grabaciones_dir]:
        if ruta and os.path.exists(ruta):
            shutil.rmtree(ruta)


def editar_cancion(cancion_id, titulo, artista=""):
    metadata = cargar_cancion(cancion_id)
    metadata["titulo"] = titulo
    metadata["artista"] = artista
    guardar_metadata(metadata)
    _actualizar_tomas_cancion(cancion_id, titulo, artista)
    return metadata


def _actualizar_tomas_cancion(cancion_id, titulo, artista=""):
    grabaciones_dir = os.path.join(GRABACIONES_DIR, cancion_id)
    if not os.path.isdir(grabaciones_dir):
        return

    for nombre in os.listdir(grabaciones_dir):
        if not nombre.endswith("_toma.json"):
            continue
        ruta = os.path.join(grabaciones_dir, nombre)
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                toma = json.load(f)
            toma["song_title"] = titulo
            toma["artist"] = artista or "Sin artista"
            with open(ruta, "w", encoding="utf-8") as f:
                json.dump(toma, f, indent=2, ensure_ascii=False)
        except (OSError, json.JSONDecodeError):
            continue


def agregar_cancion(ruta_audio, titulo, artista="", forzar=False, progreso_callback=None, fuente=None):
    asegurar_directorios()
    cancion_id = f"{_slug(titulo)}_{uuid.uuid4().hex[:8]}"
    carpeta = os.path.join(CATALOGO_DIR, cancion_id)
    os.makedirs(carpeta, exist_ok=True)

    extension = os.path.splitext(ruta_audio)[1].lower() or ".wav"
    original_path = os.path.join(carpeta, f"{cancion_id}{extension}")
    shutil.copy2(ruta_audio, original_path)

    metadata = {
        "id": cancion_id,
        "titulo": titulo,
        "artista": artista,
        "original": original_path,
        "vocals": "",
        "instrumental": "",
        "pitch_referencia": os.path.join(carpeta, "ref_pitch.csv"),
        "creada_en": datetime.now().isoformat(timespec="seconds"),
        "preparada": False,
    }
    if fuente:
        metadata['fuente'] = dict(fuente)
    guardar_metadata(metadata)
    return preparar_cancion(cancion_id, forzar=forzar, progreso_callback=progreso_callback)


def preparar_cancion(cancion_id, forzar=False, progreso_callback=None):
    metadata = cargar_cancion(cancion_id)
    vocals_path, instrumental_path = preparar_pistas(
        metadata["original"],
        forzar_separacion=forzar,
        progreso_callback=progreso_callback,
    )

    if forzar or not os.path.exists(metadata["pitch_referencia"]):
        if progreso_callback:
            progreso_callback('Detectando las notas de referencia…')
        tiempos, frecuencias = extraer_pitch(vocals_path)
        guardar_csv(metadata["pitch_referencia"], tiempos, frecuencias)

    metadata["vocals"] = vocals_path
    metadata["instrumental"] = instrumental_path
    metadata["preparada"] = True
    guardar_metadata(metadata)
    return metadata


def regenerar_pitch_referencia(cancion_id, forzar_separacion=False, progreso_callback=None):
    metadata = cargar_cancion(cancion_id)
    vocals_path = metadata.get("vocals") or ""

    if forzar_separacion or not os.path.exists(vocals_path):
        vocals_path, instrumental_path = preparar_pistas(
            metadata["original"],
            forzar_separacion=forzar_separacion,
            progreso_callback=progreso_callback,
        )
        metadata["vocals"] = vocals_path
        metadata["instrumental"] = instrumental_path

    if progreso_callback:
        progreso_callback('Detectando las notas de referencia…')
    tiempos, frecuencias = extraer_pitch(metadata["vocals"])
    guardar_csv(metadata["pitch_referencia"], tiempos, frecuencias)
    metadata["preparada"] = True
    guardar_metadata(metadata)
    return metadata


def leer_pitch_csv(ruta_csv):
    tiempos = []
    frecuencias = []
    with open(ruta_csv, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tiempos.append(float(row["tiempo"]))
            frecuencias.append(float(row["frecuencia"]))
    return tiempos, frecuencias


def carpeta_grabaciones(cancion_id):
    ruta = os.path.join(GRABACIONES_DIR, cancion_id)
    os.makedirs(ruta, exist_ok=True)
    return ruta
