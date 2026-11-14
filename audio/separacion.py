import os
import subprocess
import sys
import re

import librosa
import soundfile as sf


def _venv_site_packages():
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(raiz, "venv", "Lib", "site-packages")


def _entorno_subproceso():
    env = os.environ.copy()
    site_packages = _venv_site_packages()
    if os.path.exists(site_packages):
        pythonpath = env.get("PYTHONPATH", "")
        rutas = [site_packages]
        if pythonpath:
            rutas.append(pythonpath)
        env["PYTHONPATH"] = os.pathsep.join(rutas)
    return env


def _comando_python_demucs():
    if os.environ.get('KARAOKE_INSTALLED') == '1':
        return [os.path.join(os.path.dirname(sys.executable), 'python.exe'), '-m', 'demucs']
    if os.path.exists(_venv_site_packages()):
        return ["py", "-3.10", "-m", "demucs"]
    return [sys.executable, "-m", "demucs"]


def rutas_demucs(ruta_audio, output_dir="output"):
    nombre = os.path.splitext(os.path.basename(ruta_audio))[0]
    base_path = os.path.join(output_dir, "htdemucs", nombre)
    return {
        "base": base_path,
        "vocals": os.path.join(base_path, "vocals.wav"),
        "drums": os.path.join(base_path, "drums.wav"),
        "bass": os.path.join(base_path, "bass.wav"),
        "other": os.path.join(base_path, "other.wav"),
        "instrumental": os.path.join(base_path, "instrumental.wav"),
    }


def separar_voz(ruta_audio, forzar_separacion=False, progreso_callback=None):
    """
    Si ya existe vocals.wav y no se fuerza, lo reutiliza.
    Si no, ejecuta Demucs.
    """
    output_dir = "output"
    paths = rutas_demucs(ruta_audio, output_dir)
    vocals_path = paths["vocals"]

    if os.path.exists(vocals_path) and not forzar_separacion:
        print("Usando separacion ya existente")
        return vocals_path

    print("Separando audio con Demucs...")
    if progreso_callback:
        progreso_callback('Separando voz y acompañamiento…')
    opciones = {}
    if os.name == 'nt':
        opciones['creationflags'] = subprocess.CREATE_NO_WINDOW
    proceso = subprocess.Popen(
        _comando_python_demucs() + ["-o", output_dir, ruta_audio],
        env=_entorno_subproceso(),
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding='utf-8', errors='replace', **opciones,
    )
    recientes = []
    with proceso:
        for linea in proceso.stdout:
            recientes.append(linea.strip())
            recientes = recientes[-20:]
            progreso = progreso_demucs(linea)
            if progreso and progreso_callback:
                progreso_callback(progreso)
        codigo = proceso.wait()
    if codigo:
        raise RuntimeError('Falló la separación de audio: ' + '\n'.join(recientes)[-2000:])

    return vocals_path


def progreso_demucs(linea):
    """Read tqdm's actual percentage; ETA applies only to separation."""
    match = re.search(r'(\d{1,3})%\|.*?\[([^\]]+)\]', linea)
    if not match:
        return None
    percent = min(100, int(match[1]))
    timing = match[2].split(',')[0]
    remaining = timing.split('<', 1)[1] if '<' in timing else '?'
    return f'Separando voz y acompañamiento: {percent}% · Restante estimado: {remaining}'


def preparar_pistas(ruta_audio, forzar_separacion=False, progreso_callback=None):
    vocals_path = separar_voz(ruta_audio, forzar_separacion=forzar_separacion, progreso_callback=progreso_callback)
    paths = rutas_demucs(ruta_audio)

    if os.path.exists(paths["instrumental"]) and not forzar_separacion:
        return vocals_path, paths["instrumental"]

    stems = [paths["drums"], paths["bass"], paths["other"]]
    if not all(os.path.exists(stem) for stem in stems):
        raise FileNotFoundError("Faltan pistas instrumentales generadas por Demucs.")

    mezclas = []
    if progreso_callback:
        progreso_callback('Preparando la pista instrumental…')
    sr_objetivo = None
    for stem in stems:
        y, sr = librosa.load(stem, sr=sr_objetivo, mono=False)
        if sr_objetivo is None:
            sr_objetivo = sr
        mezclas.append(y)

    instrumental = sum(mezclas)
    sf.write(paths["instrumental"], instrumental.T, sr_objetivo)
    return vocals_path, paths["instrumental"]
