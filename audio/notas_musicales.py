"""Notas estables y correspondencias temporales uno a uno, sin DTW ni ajuste de altura."""
import numpy as np
from audio.retroalimentacion import _serie, _muestrear

VERSION = '1.0.0'
PARAMETROS = dict(paso_s=.01, mediana_s=.05, cambio_semitonos=.8,
                  persistencia_cambio_s=.10, minimo_nota_s=.12, recorte_borde_s=.04,
                  dispersion_maxima_cents=150., maximo_diferencia_inicio_s=.25,
                  solapamiento_minimo=.25)


def detectar_notas(t, f, inicio, fin, prefijo):
    """No cuantiza la altura. Mediana del núcleo; cambios persistentes separan notas."""
    tr, fr, _ = _serie(t, f, fin)
    times = np.arange(inicio, fin, .01)
    hz = _muestrear(tr, fr, times+.005, .025)
    midi = np.full(len(times), np.nan)
    good = hz > 0
    midi[good] = 69+12*np.log2(hz[good]/440)
    # La mediana no atraviesa huecos: cada racha se procesa por separado.
    boundaries = np.flatnonzero(np.diff(np.r_[False, good, False].astype(int)))
    notes = []
    def emit(start, end):
        duration = min(fin, inicio+end*.01)-(inicio+start*.01)
        if duration < .12-1e-8:
            return
        trim = min(4, max(1, (end-start)//5))
        core = midi[start+trim:end-trim]
        if len(core) < 6:
            return
        spread = float(np.percentile(core,90)-np.percentile(core,10))*100
        if spread > 150:
            return
        notes.append(dict(id=f'{prefijo}{len(notes)+1:05d}', inicio_s=float(times[start]),
                          fin_s=float(min(fin,inicio+end*.01)), midi=float(np.median(core)),
                          dispersion_cents=spread, nucleo_s=len(core)*.01))
    for lo, hi in zip(boundaries[::2], boundaries[1::2]):
        segment = midi[lo:hi]
        smooth = np.median(np.lib.stride_tricks.sliding_window_view(np.pad(segment,(2,2),mode='edge'),5),axis=1)
        start, pending = int(lo), None
        for k, value in enumerate(smooth):
            i = int(lo+k)
            anchor = float(np.median(midi[start:min(i+1,start+20)]))
            if abs(value-anchor) >= .8:
                if pending is None:
                    pending = i
                if i-pending+1 >= 10:
                    emit(start,pending)
                    start, pending = pending, None
            else:
                pending = None
        emit(start, pending if pending is not None else int(hi))
    return notes


def emparejar(ref, usr):
    """Orden monótono, sin reutilizar notas; el coste NO utiliza la afinación."""
    n,m=len(ref),len(usr)
    dp=np.zeros((n+1,m+1)); choice=np.zeros((n+1,m+1),dtype=np.uint8)
    for i,r in enumerate(ref,1):
        for j,u in enumerate(usr,1):
            if dp[i-1,j] >= dp[i,j-1]:
                dp[i,j]=dp[i-1,j]; choice[i,j]=1
            else:
                dp[i,j]=dp[i,j-1]; choice[i,j]=2
            delta=abs(u['inicio_s']-r['inicio_s'])
            overlap=max(0.,min(r['fin_s'],u['fin_s'])-max(r['inicio_s'],u['inicio_s']))
            support=overlap/min(r['fin_s']-r['inicio_s'],u['fin_s']-u['inicio_s'])
            if delta <= .25+1e-8 and support >= .25:
                score=dp[i-1,j-1]+1+support-.5*delta/.25
                if score > dp[i,j]:
                    dp[i,j]=score; choice[i,j]=3
    pairs=[]; i,j=n,m
    while i and j:
        if choice[i,j]==3:
            pairs.append((ref[i-1],usr[j-1]));i-=1;j-=1
        elif choice[i,j]==1: i-=1
        else: j-=1
    return pairs[::-1]


def resumir(notas):
    paired=[n for n in notas if n['usuario'] is not None]
    errors=np.array([n['error_cents'] for n in paired])
    def pct(condition):
        return float(np.mean(condition)*100) if len(errors) else None
    return dict(notas_referencia=len(notas), notas_comparadas=len(paired),
                notas_sin_correspondencia=len(notas)-len(paired),
                cobertura_notas_pct=100*len(paired)/len(notas) if notas else None,
                porcentaje_50=pct(abs(errors)<=50+1e-8), porcentaje_100=pct(abs(errors)<=100+1e-8),
                error_mediano_cents=float(np.median(errors)) if len(errors) else None,
                diferencia_inicio_mediana_ms=float(np.median([n['diferencia_inicio_ms'] for n in paired])) if paired else None)


def analizar_notas(tr,fr,tu,fu,fragmentos):
    all_notes=[]; fragments={}; extras=[]
    for fragment in fragmentos:
        a,b,fid=fragment['inicio_s'],fragment['fin_s'],fragment['id']
        # Cortes definidos por referencia: no se emparejan notas entre frases distintas.
        ref=detectar_notas(tr,fr,a,b,f'r_{fid}_')
        usr=detectar_notas(tu,fu,a,b,f'u_{fid}_')
        # Limita memoria por bloques largos: partición temporal para candidatos,
        # conservando el orden y sin reutilizar usuarios.
        pairs=[]; used=set(); last_start=float("-inf")
        for start in range(0,len(ref),100):
            batch=ref[start:start+100]
            candidates=[u for u in usr if u['id'] not in used and u['inicio_s'] > last_start and batch[0]['inicio_s']-.25 <= u['inicio_s'] <= batch[-1]['inicio_s']+.25]
            found=emparejar(batch,candidates);pairs.extend(found);used.update(u['id'] for _,u in found)
            if found: last_start=found[-1][1]['inicio_s']
        matches={r['id']:u for r,u in pairs}
        notes=[]
        for r in ref:
            u=matches.get(r['id']); error=100*(u['midi']-r['midi']) if u else None
            notes.append(dict(id=r['id'], fragmento_id=fid, referencia=r, usuario=u,
                              error_cents=error, diferencia_inicio_ms=1000*(u['inicio_s']-r['inicio_s']) if u else None,
                              diferencia_duracion_ms=1000*((u['fin_s']-u['inicio_s'])-(r['fin_s']-r['inicio_s'])) if u else None,
                              clase='sin_correspondencia' if u is None else 'cerca' if abs(error)<=50+1e-8 else 'margen' if abs(error)<=100+1e-8 else 'fuera'))
        unmatched=[dict(u,fragmento_id=fid) for u in usr if u['id'] not in used]
        fragments[fid]=dict(metricas=resumir(notes), notas=notes, usuario_sin_correspondencia=unmatched)
        all_notes.extend(notes);extras.extend(unmatched)
    return dict(version=VERSION, parametros=PARAMETROS, metricas=resumir(all_notes), notas=all_notes,
                usuario_sin_correspondencia=extras),fragments
