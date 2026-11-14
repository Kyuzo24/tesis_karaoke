"""Configuración elegida para revisión manual, sin modificar el catálogo."""
import json
import probar_segmentacion_pausas as medicion
from probar_segmentacion_adaptativa import adaptar

NIVEL_DB = -15
PAUSA_S = .2
PAUSA_INTERNA_S = .05
LIMITE_S = 15


def tiempo(segundos):
    minutos, segundos = divmod(segundos, 60)
    return f'{int(minutos):02d}:{segundos:05.2f}'


def main():
    # Reutiliza las mediciones ya realizadas; no repite la canción duplicada.
    fuente = json.loads((medicion.ROOT/'output/segmentacion_volumen/resultados.json').read_text(encoding='utf-8'))
    out = medicion.ROOT/'output/segmentacion_revision'
    out.mkdir(parents=True, exist_ok=True)
    config = dict(nivel_db=NIVEL_DB, pausa_s=PAUSA_S, pausa_interna_s=PAUSA_INTERNA_S,
                  limite_objetivo_s=LIMITE_S, forzar_cortes=False,
                  ids_excluidos=sorted(medicion.IDS_EXCLUIDOS))
    canciones = []
    lines = ['# Segmentos para revisión manual', '',
        'Configuración elegida: −15 dB relativos al RMS P95 de la voz separada y ausencia de pitch. '
        'Pausas de 0,2 s; dentro de segmentos >15 s, pausas de 0,05 s (60 ms efectivos). '
        'No se fuerzan cortes adicionales. Se conserva una sola carga de Reik. '
        'Esta configuración pertenece a la prueba; todavía no sustituye los bloques de 5 s del backend.', '']
    for c in fuente['canciones']:
        if c['id'] in medicion.IDS_EXCLUIDOS:
            continue
        resultado = adaptar(c['comparaciones'][str(NIVEL_DB)], LIMITE_S, PAUSA_S, (PAUSA_INTERNA_S,))
        canciones.append(dict(id=c['id'], titulo=c['titulo'], audio_sha256=c['audio_sha256'],
                              pitch_sha256=c['pitch_sha256'], **resultado))
        lines += [f"## {c['titulo']} — {resultado['cantidad']} segmentos", '',
                  '| Segmento | Inicio | Fin | Duración |', '|---:|---:|---:|---:|']
        for i, s in enumerate(resultado['segmentos'], 1):
            lines.append(f"| {i} | {tiempo(s['inicio_s'])} | {tiempo(s['fin_s'])} | {s['fin_s']-s['inicio_s']:.2f} s |")
        lines.append('')
        print(c['id'], resultado['cantidad'])
    (out/'segmentos.json').write_text(json.dumps(dict(configuracion=config, canciones=canciones),
        ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    (out/'revision.md').write_text('\n'.join(lines), encoding='utf-8')


if __name__ == '__main__':
    main()
