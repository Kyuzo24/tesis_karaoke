"""Inventario vocal completo; descarga oficial reanudable por rangos y MD5."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter
import hashlib
import json
import shutil
import tarfile
import time
import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/mdb_stem_synth'
REV = '537bb7bad0601fc58e4fff8404f71658b86ef60e'
URL = 'https://zenodo.org/records/1481172/files/MDB-stem-synth.tar.gz?download=1'
SIZE = 1845117819
MD5 = '31c1f6b4888e5fd108af91c69789a809'


def md5(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'md5').hexdigest()


def metadata(song):
    path = DATA / 'metadata' / (song + '_METADATA.yaml')
    if not path.exists():
        r = requests.get(f'https://raw.githubusercontent.com/marl/medleydb/{REV}/medleydb/data/Metadata/{path.name}', timeout=40)
        r.raise_for_status()
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(r.content)
    return song, yaml.safe_load(path.read_text(encoding='utf-8'))


def part(start, end):
    path = DATA / 'parts' / f'{start}-{end}.part'
    if path.exists() and path.stat().st_size == end-start+1:
        return path
    for attempt in range(4):
        try:
            with requests.get(URL, headers={'Range': f'bytes={start}-{end}'}, stream=True, timeout=(30,90)) as r:
                r.raise_for_status()
                assert r.status_code == 206 and r.headers['Content-Range'] == f'bytes {start}-{end}/{SIZE}'
                with path.open('wb') as f:
                    for chunk in r.iter_content(1024*1024):
                        f.write(chunk)
            assert path.stat().st_size == end-start+1
            return path
        except Exception:
            if attempt == 3:
                raise
            time.sleep(3)


def main():
    index = json.loads((DATA / 'index.json').read_text())['tracks']
    assert len(index) == 230
    songs = sorted({name.rsplit('_STEM_',1)[0] for name in index})
    with ThreadPoolExecutor(max_workers=6) as pool:
        metas = dict(pool.map(metadata, songs))
    inventory = []
    for name, paths in sorted(index.items()):
        song, stem = name.rsplit('_STEM_',1)
        inst = metas[song]['stems']['S'+stem]['instrument']
        labels = inst if isinstance(inst,list) else [inst]
        vocal = any('singer' in s or 'vocal' in s for s in labels)
        inventory.append({'track':name,'song':song,'instrument':inst,'vocal':vocal,**paths})
    selected = [x for x in inventory if x['vocal']]
    manifest = {'total_tracks':230, 'vocal_tracks':len(selected),'selection':'Todas las pistas con singer o vocal en la etiqueta instrument de MedleyDB.',
                'metadata_revision':REV,'archive_url':URL,'archive_md5':MD5,
                'index_md5':md5(DATA/'index.json'), 'inventory':inventory,'selected':selected}
    (DATA/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print('Inventario completo:',len(selected),'pistas vocales de 230;',Counter(str(x['instrument']) for x in selected),flush=True)
    archive = DATA/'MDB-stem-synth.tar.gz'
    if not archive.exists() or archive.stat().st_size != SIZE:
        prefix = DATA/'archive.prefix'
        if archive.exists() and not prefix.exists():
            archive.rename(prefix)
        offset = prefix.stat().st_size if prefix.exists() else 0
        (DATA/'parts').mkdir(exist_ok=True)
        ranges = [(start,min(start+32*1024*1024-1,SIZE-1)) for start in range(offset,SIZE,32*1024*1024)]
        done = 0
        with ThreadPoolExecutor(max_workers=8) as pool:
            for future in as_completed([pool.submit(part,*r) for r in ranges]):
                future.result(); done+=1
                print(f'Descarga: {done}/{len(ranges)} bloques completos',flush=True)
        with archive.open('wb') as f:
            if prefix.exists():
                with prefix.open('rb') as src:
                    shutil.copyfileobj(src,f)
            for start,end in ranges:
                with (DATA/'parts'/f'{start}-{end}.part').open('rb') as src:
                    shutil.copyfileobj(src,f)
    assert md5(archive) == MD5, 'Checksum del archivo oficial incorrecto'
    print('Archivo completo y MD5 oficial verificado.',flush=True)
    # Solo datos vocales y sus etiquetas; no extrae rutas ni enlaces del tar.
    wanted = {Path(x[k][0]).name:(x[k][0],x[k][1]) for x in selected for k in ['audio','f0']}
    found = set()
    with tarfile.open(archive,'r|gz') as tar:
        for member in tar:
            name=Path(member.name).name
            if name not in wanted or not member.isfile():
                continue
            rel,expected = wanted[name]
            dst=DATA/rel
            dst.parent.mkdir(exist_ok=True)
            with tar.extractfile(member) as src, dst.open('wb') as f:
                shutil.copyfileobj(src,f)
            assert md5(dst)==expected, name
            found.add(name)
    assert len(found)==len(wanted), (len(found),len(wanted))
    print(f'Listo: {len(selected)} audios vocales completos y sus etiquetas verificadas.',flush=True)


if __name__=='__main__':
    main()
