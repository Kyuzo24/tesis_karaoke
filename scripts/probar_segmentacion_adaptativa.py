"""Subdivide únicamente bloques largos usando las pausas ya medidas."""
import json
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/segmentacion_pausas'


def adaptar(comparaciones, limite, inicial=.4, secundarios=(.3, .2, .1)):
    base = comparaciones[str(inicial)]['segmentos']
    segmentos = [dict(s, umbral_s=inicial) for s in base]
    for umbral in secundarios:
        referencia = comparaciones[str(umbral)]['segmentos']
        pausas = [(a['fin_s'], b['inicio_s']) for a, b in zip(referencia, referencia[1:])]

        def dividir(s):
            inicio, fin = s['inicio_s'], s['fin_s']
            if fin-inicio <= limite:
                return [s]
            candidatas = [(a, b) for a, b in pausas if a-inicio >= 1 and fin-b >= 1]
            if not candidatas:
                return [s]
            # Escoge una pausa central; vuelve a revisar solo los hijos largos.
            a, b = min(candidatas, key=lambda p: max(p[0]-inicio, fin-p[1]))
            return dividir(dict(inicio_s=inicio, fin_s=a, umbral_s=umbral)) + dividir(
                dict(inicio_s=b, fin_s=fin, umbral_s=umbral))

        segmentos = [hijo for s in segmentos for hijo in dividir(s)]
    assert all(s['fin_s']-s['inicio_s'] >= 1 or any(
        s['inicio_s'] == b['inicio_s'] and s['fin_s'] == b['fin_s'] for b in base
    ) for s in segmentos)
    assert all(a['fin_s'] < b['inicio_s'] for a, b in zip(segmentos, segmentos[1:]))
    assert all(any(b['inicio_s'] <= s['inicio_s'] < s['fin_s'] <= b['fin_s'] for b in base) for s in segmentos)
    duraciones = [s['fin_s']-s['inicio_s'] for s in segmentos]
    return dict(cantidad=len(segmentos), mediana_s=median(duraciones), maxima_s=max(duraciones),
                mayores_limite=sum(d > limite for d in duraciones),
                menores_1s=sum(d < 1 for d in duraciones), segmentos=segmentos)


def main():
    fuente = json.loads((OUT/'resultados.json').read_text(encoding='utf-8'))
    resultados = []
    for cancion in fuente['canciones']:
        comparaciones = cancion['comparaciones']['-35']
        resultados.append(dict(id=cancion['id'], titulo=cancion['titulo'],
            audio_sha256=cancion['audio_sha256'], pitch_sha256=cancion['pitch_sha256'],
            cantidad_original=comparaciones['0.4']['cantidad'],
            pruebas={str(limite): adaptar(comparaciones, limite) for limite in [10, 15, 20]}))
    metodo = ('Base: pausas de 0,4 s. Solo en bloques mayores al límite, buscar pausas de '
              '0,3, luego 0,2 y luego 0,1 s. En cada etapa elegir una pausa central y repetir '
              'solo en hijos largos, evitando crear hijos menores de 1 s. Energía y pitch '
              'sin cambios (−35 dB). Si no hay pausa válida, conservar el bloque largo. '
              'Los límites son objetivos, no duraciones máximas garantizadas. No cambia la aplicación.')
    (OUT/'adaptativa.json').write_text(json.dumps(dict(metodo=metodo, canciones=resultados),
        ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    lines = ['# Prueba de segmentación adaptativa', '', metodo, '',
        '| Canción (ID) | Original | Límite objetivo | Segmentos | Mediana | Máximo | Sobre el límite |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for r in resultados:
        for limite, p in r['pruebas'].items():
            lines.append(f"| {r['titulo']} ({r['id']}) | {r['cantidad_original']} | {limite} s | "
                f"{p['cantidad']} | {p['mediana_s']:.2f} s | {p['maxima_s']:.2f} s | {p['mayores_limite']} |")
            print(r['id'], limite, {k:v for k,v in p.items() if k != 'segmentos'})
    lines += ['', 'Pausas estimadas, no verificadas por escucha. Detalles y tiempos en adaptativa.json.',
              'Reproducir: python scripts/probar_segmentacion_pausas.py y luego python scripts/probar_segmentacion_adaptativa.py.', '']
    (OUT/'adaptativa.md').write_text('\n'.join(lines), encoding='utf-8')


if __name__ == '__main__':
    main()
