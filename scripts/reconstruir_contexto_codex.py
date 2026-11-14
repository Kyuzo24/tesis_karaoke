"""Reconstituye los historiales grandes respaldados por partes en Git."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1] / 'docs' / 'contexto_codex'
index = json.loads((root / 'indice.json').read_text(encoding='utf-8'))
for entry in index['files']:
    if not entry.get('parts'):
        continue
    target = root / entry['path']
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        if digest == entry['sha256']:
            print('Ya verificado:', entry['path'])
            continue
        raise SystemExit('Ya existe una copia diferente: ' + str(target))
    digest = hashlib.sha256()
    temp = target.with_suffix(target.suffix + '.restaurando')
    with temp.open('wb') as out:
        for part in entry['parts']:
            data = (root / part['path']).read_bytes()
            if hashlib.sha256(data).hexdigest() != part['sha256']:
                raise SystemExit('Parte danada: ' + part['path'])
            out.write(data)
            digest.update(data)
    if digest.hexdigest() != entry['sha256'] or temp.stat().st_size != entry['size']:
        raise SystemExit('No coincide el archivo reconstruido: ' + entry['path'])
    temp.replace(target)
    print('Reconstruido y verificado:', entry['path'])
