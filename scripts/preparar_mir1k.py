"""Descarga una muestra fijada por cantante desde un mirror publico versionado."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/mir1k_muestra'
REPO = 'AnhP/Mir-1k-use-DJCM-training'
REV = 'd6b7565ab4d85c0fa752eeb3ac63618c94620edd'
BASE = 'https://huggingface.co'


def listing(folder):
    r = requests.get(f'{BASE}/api/datasets/{REPO}/tree/{REV}/MIR-1K/{folder}?limit=1000', timeout=40)
    r.raise_for_status()
    assert 'next' not in r.links, 'Listado incompleto'
    rows = r.json()
    assert len(rows) == 1000
    return rows


def rank(name):
    return hashlib.sha256(('mir1k-evaluacion-20260929:' + name).encode()).hexdigest()


def download(item):
    path = OUT / item['path']
    url = f'{BASE}/datasets/{REPO}/resolve/{REV}/' + item['path']
    if path.exists():
        content = path.read_bytes()
    else:
        r = requests.get(url, timeout=90)
        r.raise_for_status()
        content = r.content
    assert len(content) == item['size'], item['path']
    digest = hashlib.sha256(content).hexdigest()
    if 'lfs' in item:
        assert digest == item['lfs']['oid'], item['path']
    else:
        blob = b'blob ' + str(len(content)).encode() + b'\0' + content
        assert hashlib.sha1(blob).hexdigest() == item['oid'], item['path']
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return {'path': item['path'], 'sha256': digest, 'bytes': len(content), 'url': url}


def main():
    waves, labels = listing('Wavfile'), listing('PitchLabel')
    groups = defaultdict(list)
    for row in waves:
        groups[Path(row['path']).stem.split('_')[0]].append(row)
    assert len(groups) == 19
    selected = []
    for singer, rows in sorted(groups.items()):
        candidates = sorted(rows, key=lambda r: rank(r['path']))
        chosen, songs = [], set()
        for row in candidates:
            song = Path(row['path']).stem.rsplit('_', 1)[0]
            if song not in songs and len(chosen) < 5:
                chosen.append(row); songs.add(song)
        for row in candidates:
            if len(chosen) < 5 and row not in chosen:
                chosen.append(row)
        assert len(chosen) == 5
        selected.extend(chosen)
    label_map = {Path(x['path']).stem: x for x in labels}
    items = selected + [label_map[Path(x['path']).stem] for x in selected]
    results = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        for i, future in enumerate(as_completed([pool.submit(download, row) for row in items]), 1):
            results.append(future.result())
            if i % 20 == 0 or i == len(items):
                print(f'{i}/{len(items)} archivos descargados y verificados', flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {'repo': REPO, 'revision': REV, 'total_dataset_tracks': 1000,
                'selected_tracks': [Path(x['path']).stem for x in selected],
                'selection': '5 por cantante; orden SHA256 prefijado; primero canciones diferentes y luego completar',
                'selection_prefix': 'mir1k-evaluacion-20260929:', 'singers': sorted(groups),
                'files': sorted(results, key=lambda r: r['path']),
                'annotation_start_s': .02, 'annotation_hop_s': .02,
                'annotation_source': 'https://music-ir.org/mirex/wiki/2009:Audio_Melody_Extraction',
                'note': 'Mirror de terceros; hashes verificados contra su revision publicada. El readme del mirror describe MIREX09 y no corresponde a estos 1000 archivos; se usa el protocolo MIR-1K del autor y se valida duracion de etiquetas.'}
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print('Muestra lista: 95 fragmentos de 19 cantantes.', flush=True)


if __name__ == '__main__':
    main()
