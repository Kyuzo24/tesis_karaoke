"""Compara volumen manteniendo las reglas temporales de la prueba anterior."""
import json
import probar_segmentacion_pausas as medicion
from probar_segmentacion_adaptativa import adaptar


def main():
    # Salida independiente para conservar las pruebas anteriores.
    medicion.OUT = medicion.ROOT / 'output/segmentacion_volumen'
    medicion.NIVELES_DB = [-35, -30, -25, -20, -15]
    medicion.main()
    fuente = json.loads((medicion.OUT/'resultados.json').read_text(encoding='utf-8'))
    resultados = []
    for c in fuente['canciones']:
        pruebas = {}
        for nivel in medicion.NIVELES_DB:
            comp = c['comparaciones'][str(nivel)]
            p = adaptar(comp, 15, .2, (.05,))
            p['duracion_conservada_s'] = sum(s['fin_s']-s['inicio_s'] for s in p['segmentos'])
            pruebas[str(nivel)] = p
            print(c['id'], nivel, {k:v for k,v in p.items() if k != 'segmentos'})
        resultados.append(dict(id=c['id'], titulo=c['titulo'], audio_sha256=c['audio_sha256'],
                               pitch_sha256=c['pitch_sha256'], pruebas=pruebas))
    metodo = ('Volumen relativo al percentil 95 del RMS de cada voz separada; valores menos negativos '
              'admiten más energía como silencio. Siempre se exige también ausencia de pitch. '
              'Base: pausas de 0,2 s; subdividir bloques >15 s con pausas de 0,05 s '
              '(60 ms efectivos por resolución de 20 ms), sin crear hijos <1 s. '
              'Los fragmentos cortos de la división inicial se conservan. El nivel de volumen '
              'se aplica a toda la canción en cada variante. No cambia el backend.')
    (medicion.OUT/'adaptativa.json').write_text(json.dumps(dict(metodo=metodo,canciones=resultados),
        ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    lines = ['# Comparación del umbral de volumen', '', metodo, '',
             '| Canción (ID) | Nivel | Segmentos | Mediana | Máximo | >15 s | <1 s | Duración conservada |',
             '|---|---:|---:|---:|---:|---:|---:|---:|']
    for r in resultados:
        for nivel, p in r['pruebas'].items():
            lines.append(f"| {r['titulo']} ({r['id']}) | {nivel} dB | {p['cantidad']} | "
                f"{p['mediana_s']:.2f} s | {p['maxima_s']:.2f} s | {p['mayores_limite']} | "
                f"{p['menores_1s']} | {p['duracion_conservada_s']:.2f} s |")
    lines += ['', 'Más segmentos no implica mejores frases. Pausas estimadas, sin validación por escucha. '
              'Al elevar el umbral pueden excluirse partes suaves si el detector tampoco registra pitch.',
              '', 'Tiempos exactos en adaptativa.json; mediciones originales en resultados.json.',
              'Reproducir: python scripts/probar_umbral_volumen.py.', '']
    (medicion.OUT/'informe.md').write_text('\n'.join(lines), encoding='utf-8')


if __name__ == '__main__':
    main()
