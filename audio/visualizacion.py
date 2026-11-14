import numpy as np

from audio.metricas import hz_to_midi


NOMBRES_NOTAS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def midi_to_nota(midi):
    midi = int(round(midi))
    nombre = NOMBRES_NOTAS[midi % 12]
    octava = midi // 12 - 1
    return f"{nombre}{octava}"


def _insertar_cortes_por_silencio(tiempos, valores, max_gap=0.25):
    tiempos = list(tiempos)
    valores = list(valores)
    if len(tiempos) < 2:
        return tiempos, valores

    t_plot = [tiempos[0]]
    v_plot = [valores[0]]
    for i in range(1, len(tiempos)):
        if tiempos[i] - tiempos[i - 1] > max_gap:
            t_plot.append(np.nan)
            v_plot.append(np.nan)
        t_plot.append(tiempos[i])
        v_plot.append(valores[i])
    return t_plot, v_plot


def configurar_grafico_notas(ax, t_ref, f_ref, t_usr, f_usr):
    ax.clear()

    y_ref = hz_to_midi(f_ref)
    y_usr = hz_to_midi(f_usr)
    t_ref_plot, y_ref_plot = _insertar_cortes_por_silencio(t_ref, y_ref)
    t_usr_plot, y_usr_plot = _insertar_cortes_por_silencio(t_usr, y_usr)

    ax.plot(t_ref_plot, y_ref_plot, label="Esperado", color="#1f77b4", linewidth=1.8)
    ax.plot(t_usr_plot, y_usr_plot, label="Obtenido", color="#d62728", linewidth=1.5, alpha=0.9)

    _configurar_ejes_notas(ax, [(t_ref, y_ref), (t_usr, y_usr)], "Comparacion visual de afinacion")
    ax.legend(loc="upper right")


def configurar_grafico_esperado(ax, t_ref, f_ref, cursor_t=0, ventana=18, t_usr=None, f_usr=None):
    ax.clear()

    y_ref = hz_to_midi(f_ref)
    t_ref_plot, y_ref_plot = _insertar_cortes_por_silencio(t_ref, y_ref)
    ax.plot(t_ref_plot, y_ref_plot, label="Esperado", color="#1f77b4", linewidth=1.8)
    if t_usr is not None and f_usr is not None and len(t_usr):
        y_usr = hz_to_midi(f_usr)
        t_usr_plot, y_usr_plot = _insertar_cortes_por_silencio(t_usr, y_usr)
        usuario = ax.plot(
            t_usr_plot,
            y_usr_plot,
            label="Usuario",
            color="#d62728",
            linewidth=1.6,
            alpha=0.95,
        )[0]

    cursor = ax.axvline(cursor_t, color="#111111", linewidth=1.5, alpha=0.85)
    cursor.set_label("_cursor_karaoke")

    _configurar_ejes_notas(
        ax,
        [
            (t_ref, y_ref),
            ([] if t_usr is None else t_usr, hz_to_midi([] if f_usr is None else f_usr)),
        ],
        "Notas esperadas",
        ventana,
        cursor_t,
    )
    ax.legend(loc="upper right")


def actualizar_ventana_cursor(ax, cursor_t, ventana=18):
    for linea in ax.lines:
        if linea.get_label() == "_cursor_karaoke":
            linea.set_xdata([cursor_t, cursor_t])
            break
    else:
        linea = ax.axvline(cursor_t, color="#111111", linewidth=1.5, alpha=0.85)
        linea.set_label("_cursor_karaoke")

    _ajustar_vista_tiempo_real(ax, cursor_t, ventana)


def actualizar_usuario_tiempo_real(ax, t_usr, f_usr, cursor_t, ventana=18):
    inicio = max(0, cursor_t - ventana * 0.45)
    fin = inicio + ventana * 1.1
    t_usr = np.asarray(t_usr, dtype=float)
    f_usr = np.asarray(f_usr, dtype=float)
    mask_visible = (t_usr >= inicio) & (t_usr <= fin)
    t_visible = t_usr[mask_visible]
    y_usr = hz_to_midi(f_usr[mask_visible])
    t_usr_plot, y_usr_plot = _insertar_cortes_por_silencio(t_visible, y_usr)

    creada = False
    for linea in ax.lines:
        if linea.get_label() == "Usuario":
            linea.set_xdata(t_usr_plot)
            linea.set_ydata(y_usr_plot)
            break
    else:
        creada = True
        ax.plot(
            t_usr_plot,
            y_usr_plot,
            label="Usuario",
            color="#d62728",
            linewidth=1.6,
            alpha=0.95,
        )

    _ajustar_vista_tiempo_real(ax, cursor_t, ventana)
    if creada:
        ax.legend(loc="upper right")


def aplicar_vista_detalle(ax, x_inicio, ventana, y_centro, rango_notas):
    ax.set_xlim(x_inicio, x_inicio + ventana)

    y_min = int(np.floor(y_centro - rango_notas / 2))
    y_max = int(np.ceil(y_centro + rango_notas / 2))
    ticks = np.arange(y_min, y_max + 1)
    ax.set_yticks(ticks)
    ax.set_yticklabels([midi_to_nota(tick) for tick in ticks])
    ax.set_ylim(y_min, y_max)
    ax.grid(axis="y", color="#d8d8d8", linewidth=0.8)
    ax.grid(axis="x", color="#eeeeee", linewidth=0.6)


def rango_midi_grafico(*series_frecuencias):
    valores = []
    for frecuencias in series_frecuencias:
        midi = hz_to_midi(frecuencias)
        midi = midi[~np.isnan(midi)]
        if len(midi):
            valores.append(midi)

    if not valores:
        return 48, 72

    todos = np.concatenate(valores)
    return float(np.floor(np.min(todos)) - 1), float(np.ceil(np.max(todos)) + 1)


def configurar_grafico_diagnostico(figura, diagnostico):
    figura.clear()

    usuario = diagnostico.get("usuario")
    if usuario:
        axes = figura.subplots(2, 1, sharex=False)
        _graficar_diagnostico_archivo(axes[0], diagnostico["referencia"], "Referencia")
        _graficar_diagnostico_archivo(axes[1], usuario, "Usuario")
    else:
        axes = [figura.add_subplot(111)]
        _graficar_diagnostico_archivo(axes[0], diagnostico["referencia"], "Referencia")

    figura.tight_layout()


def _graficar_diagnostico_archivo(ax, datos, titulo):
    ax.clear()
    y_crudo = hz_to_midi(datos["f_crudo"])
    y_filtrado = hz_to_midi(datos["f_filtrado"])
    y_corregido = hz_to_midi(datos.get("f_corregido", []))
    t_crudo, y_crudo_plot = _insertar_cortes_por_silencio(datos["t_crudo"], y_crudo)
    t_filtrado, y_filtrado_plot = _insertar_cortes_por_silencio(
        datos["t_filtrado"],
        y_filtrado,
    )
    t_corregido, y_corregido_plot = _insertar_cortes_por_silencio(
        datos.get("t_corregido", []),
        y_corregido,
    )

    ax.plot(t_crudo, y_crudo_plot, label="Crudo", color="#9a9a9a", linewidth=1.0, alpha=0.55)
    ax.plot(t_filtrado, y_filtrado_plot, label="Filtrado", color="#1f77b4", linewidth=1.5)
    if len(t_corregido):
        ax.plot(t_corregido, y_corregido_plot, label="Corregido", color="#2ca02c", linewidth=1.3)

    series = [y_crudo[~np.isnan(y_crudo)], y_filtrado[~np.isnan(y_filtrado)], y_corregido[~np.isnan(y_corregido)]]
    series_validas = [serie for serie in series if len(serie)]
    if not series_validas:
        ax.text(0.5, 0.5, "No hay pitch detectado", ha="center", va="center")
        ax.set_axis_off()
        return

    valores = np.concatenate(series_validas)
    if len(valores) == 0:
        ax.text(0.5, 0.5, "No hay pitch detectado", ha="center", va="center")
        ax.set_axis_off()
        return

    y_min = int(np.floor(np.min(valores))) - 1
    y_max = int(np.ceil(np.max(valores))) + 1
    ticks = np.arange(y_min, y_max + 1)
    ax.set_yticks(ticks)
    ax.set_yticklabels([midi_to_nota(tick) for tick in ticks])
    ax.set_ylim(y_min, y_max)
    ax.grid(axis="y", color="#d8d8d8", linewidth=0.8)
    ax.grid(axis="x", color="#eeeeee", linewidth=0.6)
    ax.set_ylabel("Nota")
    ax.set_title(f"{titulo}: crudo vs filtrado")
    ax.legend(loc="upper right")


def _configurar_ejes_notas(ax, series, titulo, ventana=None, cursor_t=0):
    if ventana is not None:
        inicio_x = max(0, cursor_t - ventana * 0.35)
        fin_x = inicio_x + ventana
        visibles = []
        for tiempos, serie in series:
            tiempos = np.asarray(tiempos, dtype=float)
            serie = np.asarray(serie, dtype=float)
            if len(tiempos) != len(serie):
                continue
            mask = (tiempos >= inicio_x) & (tiempos <= fin_x)
            visibles.append(serie[mask])
        series_midi = visibles
    else:
        series_midi = [np.asarray(serie, dtype=float) for _tiempos, serie in series]

    series_validas = [serie[~np.isnan(serie)] for serie in series_midi if len(serie)]
    series_validas = [serie for serie in series_validas if len(serie)]
    if not series_validas:
        ax.text(0.5, 0.5, "No hay pitch suficiente para graficar", ha="center", va="center")
        ax.set_axis_off()
        return

    valores = np.concatenate(series_validas)
    if len(valores) == 0:
        ax.text(0.5, 0.5, "No hay pitch suficiente para graficar", ha="center", va="center")
        ax.set_axis_off()
        return

    y_min = int(np.floor(np.min(valores))) - 1
    y_max = int(np.ceil(np.max(valores))) + 1
    ticks = np.arange(y_min, y_max + 1)
    ax.set_yticks(ticks)
    ax.set_yticklabels([midi_to_nota(tick) for tick in ticks])
    ax.set_ylim(y_min, y_max)
    ax.grid(axis="y", color="#d8d8d8", linewidth=0.8)
    ax.grid(axis="x", color="#eeeeee", linewidth=0.6)
    ax.set_xlabel("Tiempo (s)")
    ax.set_ylabel("Nota")
    ax.set_title(titulo)

    if ventana is not None:
        inicio = max(0, cursor_t - ventana * 0.35)
        ax.set_xlim(inicio, inicio + ventana)


def _ajustar_vista_tiempo_real(ax, cursor_t, ventana):
    inicio = max(0, cursor_t - ventana * 0.35)
    fin = inicio + ventana
    ax.set_xlim(inicio, fin)

    valores_visibles = []
    for linea in ax.lines:
        label = linea.get_label()
        if label == "_cursor_karaoke":
            continue
        x = np.asarray(linea.get_xdata(), dtype=float)
        y = np.asarray(linea.get_ydata(), dtype=float)
        if len(x) != len(y):
            continue
        mask = (x >= inicio) & (x <= fin) & ~np.isnan(y)
        if np.any(mask):
            valores_visibles.append(y[mask])

    if not valores_visibles:
        return

    valores = np.concatenate(valores_visibles)
    centro = np.median(valores)
    y_min = int(np.floor(min(np.min(valores), centro - 6))) - 1
    y_max = int(np.ceil(max(np.max(valores), centro + 6))) + 1
    ticks = np.arange(y_min, y_max + 1)
    ax.set_yticks(ticks)
    ax.set_yticklabels([midi_to_nota(tick) for tick in ticks])
    ax.set_ylim(y_min, y_max)


def configurar_grafico_musical(ax, musical):
    """Mismos núcleos y clases que el informe y la interfaz web."""
    ax.clear(); labels=set(); points=[]
    def draw(note,color,label,width):
        ax.hlines(note['midi'],note['inicio_s'],note['fin_s'],color=color,linewidth=width,
                  label=label if label not in labels else '_nolegend_')
        labels.add(label);points.append(([note['inicio_s'],note['fin_s']],[note['midi'],note['midi']]))
    colors={'cerca':('#21966c','Hasta 50 cents'),'margen':('#d49a00','Hasta 100 cents'),'fuera':('#cf4545','Más de 100 cents')}
    for pair in musical['notas']:
        draw(pair['referencia'],'#aaaaaa','Referencia',7)
        if pair['usuario']:
            color,label=colors[pair['clase']];draw(pair['usuario'],color,label,3)
    for note in musical['usuario_sin_correspondencia']:
        draw(note,'#777777','Sin correspondencia',3)
    _configurar_ejes_notas(ax,points,'Afinación por notas estables · Sin calificación global')
    if labels: ax.legend(loc='upper right',fontsize=8)
