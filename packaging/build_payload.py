"""Run with the project's Python 3.10 and its site-packages on PYTHONPATH."""
from pathlib import Path
import importlib.metadata as metadata
import json
import shutil
import sys
from packaging.requirements import Requirement

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'packaging' / 'payload'
DEST.mkdir(parents=True, exist_ok=True)
IGNORE = shutil.ignore_patterns('__pycache__', '*.pyc', 'site-packages')


def runtime(base, target):
    target.mkdir(parents=True, exist_ok=True)
    for name in ('python.exe', 'pythonw.exe', 'python3.dll', 'LICENSE.txt'):
        shutil.copy2(base / name, target / name)
    for file in list(base.glob('python3*.dll')) + list(base.glob('vcruntime*.dll')):
        shutil.copy2(file, target / file.name)
    for name in ('DLLs', 'Lib'):
        shutil.copytree(base / name, target / name, dirs_exist_ok=True, ignore=IGNORE)


runtime(Path(sys.base_prefix), DEST / 'runtime/audio')
youtube_base = Path((ROOT / '.youtube-env/pyvenv.cfg').read_text().split('home = ', 1)[1].splitlines()[0])
runtime(youtube_base, DEST / 'runtime/youtube')
shutil.copytree(ROOT / '.youtube-env/Lib/site-packages', DEST / 'runtime/youtube/Lib/site-packages',
                dirs_exist_ok=True, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))

# Follow dependency metadata instead of copying unrelated development packages.
pending = ['librosa', 'sounddevice', 'soundfile', 'pywebview', 'demucs', 'pyworld',
           'dtw-python', 'setuptools']
seen = set()
manifest = []
site = DEST / 'runtime/audio/Lib/site-packages'
for name in pending:
    dist = metadata.distribution(name)
    canonical = dist.metadata['Name'].lower().replace('_', '-')
    if canonical in seen:
        continue
    seen.add(canonical)
    manifest.append({'name': canonical, 'version': dist.version})
    for dependency in dist.requires or []:
        requirement = Requirement(dependency)
        if requirement.marker is None or requirement.marker.evaluate({'extra': ''}):
            pending.append(requirement.name)
    for file in dist.files or []:
        if '..' in file.parts or '__pycache__' in file.parts or str(file).endswith('.pyc'):
            continue
        source = Path(dist.locate_file(file))
        if source.is_file():
            target = site / file
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

for folder in ('audio', 'ui_live'):
    shutil.copytree(ROOT / folder, DEST / folder, dirs_exist_ok=True, ignore=IGNORE)
for name in ('desktop_live.py', 'Guia de Karaoke Studio.html', 'requirements-youtube.txt'):
    shutil.copy2(ROOT / name, DEST / name)
shutil.copy2(ROOT / 'packaging/launch.py', DEST / 'launch.py')
shutil.copy2(ROOT / 'packaging/instalar_youtube.bat', DEST / 'instalar_youtube.bat')
shutil.copy2(ROOT / 'packaging/NODE-LICENSE.txt', DEST / 'NODE-LICENSE.txt')
(DEST / 'tools').mkdir(exist_ok=True)
shutil.copy2(shutil.which('node'), DEST / 'tools/node.exe')
ffmpeg = next((ROOT / '.youtube-env/Lib/site-packages/imageio_ffmpeg/binaries').glob('ffmpeg*.exe'))
shutil.copy2(ffmpeg, DEST / 'tools/ffmpeg.exe')
checkpoint = Path.home() / '.cache/torch/hub/checkpoints/955717e8-8726e21a.th'
target = DEST / 'models/hub/checkpoints'
target.mkdir(parents=True, exist_ok=True)
shutil.copy2(checkpoint, target / checkpoint.name)
(DEST / 'DEPENDENCIAS.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
# Demucs 4 normalizes in place after expanding mono to two shared channels.
# Copy-on-subtraction keeps mono files usable with the packaged Torch version.
demucs_cli = site / 'demucs/separate.py'
source = demucs_cli.read_text(encoding='utf-8')
assert 'wav -= ref.mean()' in source
demucs_cli.write_text(source.replace('wav -= ref.mean()', 'wav = wav - ref.mean()'), encoding='utf-8')
assert not any((DEST / name).exists() for name in ('canciones', 'grabaciones', 'output', 'data', 'docs'))
print('Payload listo:', DEST, flush=True)
print('Paquetes:', len(manifest), flush=True)
