"""Explicaciones auditables de notas; sin juicios de técnica ni calificación global."""
def redactar(musical, metodo):
    m=musical['metricas']; notes=musical['notas']; paired=[n for n in notes if n['usuario']]
    n,total=m['notas_comparadas'],m['notas_referencia']
    enough=n>=3 and (m['cobertura_notas_pct'] or 0)>=40
    if not n:
        summary='No pudimos comparar tu voz con la canción en esta parte. Escucha la toma antes de sacar conclusiones sobre cómo cantaste.'
    elif not enough:
        summary='Solo pudimos revisar una pequeña parte de tu voz. Encontrarás observaciones sobre esos momentos, pero no bastan para valorar toda la interpretación.'
    else:
        close=m['porcentaje_50']
        summary=('En la mayoría de las notas que pudimos revisar, tu voz estuvo muy cerca de la canción.' if close>=80 else
                 'En buena parte de las notas que pudimos revisar, tu voz se acercó a la canción. Hay algunos momentos para repasar.' if close>=50 else
                 'En las notas que pudimos revisar aparecen varias diferencias con la canción. Escucha los momentos señalados y practícalos poco a poco.')
        if m['cobertura_notas_pct']<80:
            summary+=' No pudimos revisar toda tu voz; estas observaciones se refieren solo a las partes comparadas.'
    limits=['El sistema ajusta el tiempo de la comparación cuando encuentra un desfase claro. Puedes revisarlo en el ajuste de tiempo.',
            'Se revisan las notas que se mantienen lo suficiente para reconocerlas. Los cambios entre notas pueden quedar fuera.',
            'Si una nota no se pudo comparar, no significa que la hayas cantado mal o que no la hayas cantado.',
            'Varias notas iguales seguidas pueden reconocerse como una sola si no hay una pausa clara.',
            'Esta revisión se centra en la afinación. No valora tu técnica vocal, tu expresividad ni tu ritmo.']
    if m['notas_sin_correspondencia']:
        limits.append('Hay partes en las que no pudimos relacionar con seguridad tu voz con la canción. Escúchalas para completar la revisión.')
    result=dict(resumen=summary,aciertos=[],aspectos_a_revisar=[],practica_sugerida=[],limitaciones=limits)
    evidence=[]; audit=[dict(regla='notas_resumen',version='2.1.0',valores=m,evidencia_ids=[x['id'] for x in notes])]
    for note in notes:
        error=note['error_cents']
        category=('limitacion' if error is None or abs(error)>=600 else 'fortaleza' if abs(error)<=50+1e-8 else 'aspecto_por_mejorar')
        action='comprobar_correspondencia' if category=='limitacion' else 'comparar_altura' if category=='aspecto_por_mejorar' else None
        evidence.append(dict(id=note['id'],categoria=category,accion_sugerida={'id':action} if action else None))
    def where(note):
        r=note['referencia'];return f"{int(r['inicio_s']//60)}:{r['inicio_s']%60:04.1f}–{int(r['fin_s']//60)}:{r['fin_s']%60:04.1f}"
    def add(key,note,text,action=None):
        item=dict(texto=text,evidencia_ids=[note['id']])
        if action: item['accion_id']=action
        result[key].append(item)
        audit.append(dict(regla='nota_'+key,version='2.1.0',evidencia_ids=[note['id']],valores=note,accion_id=action))
    strengths=sorted([x for x in paired if abs(x['error_cents'])<=50+1e-8],key=lambda x:-(x['referencia']['fin_s']-x['referencia']['inicio_s']))
    if strengths:
        x=strengths[0];add('aciertos',x,where(x)+': mantuviste una nota muy cercana a la de la canción. Vuelve a escuchar este momento para reconocer lo que te salió bien.')
    issues=sorted([x for x in paired if 50+1e-8<abs(x['error_cents'])<600],key=lambda x:-abs(x['error_cents']))
    chosen=[]
    for x in issues:
        direction='grave' if x['error_cents']<0 else 'aguda'
        if direction in chosen: continue
        chosen.append(direction)
        add('aspectos_a_revisar',x,where(x)+f": tu voz sonó más {direction} que la nota de la canción. Escucha ambas para reconocer la diferencia.")
        if len(chosen)==2:break
    big=[x for x in paired if abs(x['error_cents'])>=600]
    if big:
        x=big[0]
        limits.append(where(x)+': las voces parecen muy distintas. Primero comprueba que se estén comparando en el mismo momento; podría ser un problema del análisis.')
        add('practica_sugerida',x,'Escucha ambas voces en '+where(x)+' y comprueba que suenen al mismo tiempo antes de intentar corregir tu voz.','comprobar_correspondencia')
    elif issues and enough:
        x=issues[0]
        add('practica_sugerida',x,'Escucha la nota de la canción en '+where(x)+', haz una pausa e intenta repetirla. Después canta la frase completa.','comparar_altura')
    elif m['notas_sin_correspondencia'] and not enough:
        x=next(x for x in notes if x['usuario'] is None)
        add('practica_sugerida',x,'Escucha tu grabación en '+where(x)+' y comprueba que esté a tiempo con la canción antes de evaluar la afinación.','comprobar_correspondencia')
    return result,audit,evidence
