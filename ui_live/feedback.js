/* Backend compartido; todo texto externo se inserta como texto, nunca como HTML. */
(() => {
  const el = (tag, text, cls) => { const n = document.createElement(tag); if (text != null) n.textContent = text; if (cls) n.className = cls; return n; };
  const api = () => window.pywebview?.api;
  const root = el('section', null, 'feedback-panel');
  root.id = 'feedbackPanel';
  root.setAttribute('aria-label', 'Análisis por fragmentos');
  let identity = '', revision = 0, detailRevision = 0, data = null, fragment = null;
  let summaryBox, detailBox, fragmentList;
  let audioEnd = null;
  const button = (label, run) => { const b = el('button', label, 'button'); b.type = 'button'; b.onclick = run; return b; };
  const pct = v => v == null ? 'Sin datos' : `${v.toFixed(1)}%`;
  const time = v => `${Math.floor(v / 60).toString().padStart(2, '0')}:${(v % 60).toFixed(1).padStart(4, '0')}`;
  function stats(parent, m, musical) {
    if (musical) {
      const n = musical.metricas; const row = el('div', null, 'feedback-stats');
      [['Notas revisadas', `${n.notas_comparadas} / ${n.notas_referencia}`], ['Notas muy cercanas', pct(n.porcentaje_50)], ['Notas cercanas', pct(n.porcentaje_100)]].forEach(([name,value]) => { const card = el('div',name,'feedback-stat');card.append(el('strong',value));row.append(card); });
      parent.append(row);
      const d=el('details');d.append(el('summary','Ver mediciones detalladas'));
      d.append(el('p','Notas muy cercanas: diferencia de hasta 50 cents (medio semitono). Notas cercanas: hasta 100 cents (un semitono), incluidas las muy cercanas. Ambos porcentajes se calculan solo sobre las notas que se pudieron comparar.','feedback-note'));
      d.append(el('p', `Cobertura de notas: ${pct(n.cobertura_notas_pct)}. Diferencia mediana de entradas después de compensar: ${n.diferencia_inicio_mediana_ms == null ? 'sin datos' : n.diferencia_inicio_mediana_ms.toFixed(0)+' ms'}. Positivo indica entrada posterior; no es una calificación de ritmo.`, 'feedback-note'));
      stats(d,m); parent.append(d); return;
    }
    const row = el('div', null, 'feedback-stats');
    [['Cobertura comparable', pct(m.cobertura_comparable_pct)], ['Dentro de ±50 cents', pct(m.porcentaje_dentro_tolerancia)], ['Tiempo comparable', `${m.comparable_s.toFixed(1)} s`]].forEach(([name, value]) => {
      const card = el('div', name, 'feedback-stat'); card.append(el('strong', value)); row.append(card);
    }); parent.append(row);
  }
  function narrative(parent, response) {
    parent.replaceChildren();
    parent.append(el('span', 'Sobre tu interpretación', 'feedback-tag'));
    if (response.aviso) parent.append(el('p', response.aviso, 'feedback-note'));
    const c = response.contenido;
    parent.append(el('p', c.resumen));
    [['Aciertos', c.aciertos], ['Aspectos a revisar', c.aspectos_a_revisar], ['Para practicar', c.practica_sugerida]].forEach(([title, items]) => {
      if (!items.length) return;
      parent.append(el('h3', title)); const ul = el('ul');
      items.forEach(item => { const li = el('li', item.texto); li.title = `Evidencia: ${item.evidencia_ids.join(', ')}`; ul.append(li); }); parent.append(ul);
    });
    const d = el('details'); d.append(el('summary', 'Qué puede decirte este análisis'));
    c.limitaciones.forEach(text => d.append(el('p', text, 'feedback-note'))); parent.append(d);
  }
  async function explain(target, fid, expectedRevision, expectedDetail) {
    const songId = currentSong()?.id, takeId = selectedTake()?.id;
    const pending = el('p', 'Preparando explicación…', 'feedback-note'); target.append(pending);
    try {
      const r = await api().explain_take(songId, takeId, fid);
      if (revision !== expectedRevision || (fid && detailRevision !== expectedDetail)) return;
      if (!r.ok) throw new Error(r.error);
      narrative(target, r);

    } catch (error) {
      if (revision !== expectedRevision || (fid && detailRevision !== expectedDetail)) return;
      pending.remove(); target.append(el('p', error.message || 'No se pudo generar la explicación.', 'feedback-note'));
      target.append(button('Reintentar', () => { target.replaceChildren(); explain(target, fid, expectedRevision, expectedDetail); }));
    }
  }
  async function play(f) {
    if (state.playing || state.catalogWorking) return;
    pauseTakePlayback();
    loadTakeAudio(selectedTake());
    const offset = (data.desfase_ms || 0) / 1000;
    audioEnd = Math.max(0, f.fin_s + offset);
    try {
      voiceAudio.currentTime = Math.max(0, f.inicio_s + offset);
      state.current = voiceAudio.currentTime;
      state.viewStart = f.inicio_s;
      await toggleTakePlayback();
      renderChart();
    } catch (_) { audioEnd = null; }
  }
  voiceAudio.addEventListener('timeupdate', () => {
    if (audioEnd !== null && voiceAudio.currentTime >= audioEnd) {
      audioEnd = null; pauseTakePlayback();
    }
  });
  document.getElementById('takePlayButton').addEventListener('click', () => { audioEnd = null; });
  document.getElementById('takeStopButton').addEventListener('click', () => { audioEnd = null; });
  function openFragment(f) {
    fragment = f; detailRevision += 1;
    fragmentList.querySelectorAll('button').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.id === f.id)));
    detailBox.replaceChildren(el('h3', `Fragmento ${Number(f.id.slice(1))} · ${time(f.inicio_s)}–${time(f.fin_s)}`));
    const actions = el('div', null, 'feedback-actions');
    actions.append(button('Escuchar mi fragmento', () => play(f)), button('Detener audio', () => { audioEnd = null; pauseTakePlayback(); }));
    detailBox.append(actions); stats(detailBox, f.metricas, f.musical);
    const copy = el('div', null, 'feedback-copy'); detailBox.append(copy);
    const details = el('details'); details.append(el('summary', 'Ver mediciones de las notas'));
    (f.musical?.notas || []).forEach(n => details.append(el('p', `${time(n.referencia.inicio_s)}–${time(n.referencia.fin_s)} · ${n.usuario ? `${n.error_cents.toFixed(0)} cents · entrada ${n.diferencia_inicio_ms.toFixed(0)} ms · duración ${n.diferencia_duracion_ms.toFixed(0)} ms` : 'Sin correspondencia fiable'}`, 'feedback-note')));
    detailBox.append(details);
    explain(copy, f.id, revision, detailRevision);
  }
  function render() {
    root.replaceChildren(el('div', 'Tu interpretación', 'feedback-kicker'), el('h2', 'Análisis por fragmentos'));
    root.append(el('p', 'Elige una parte de la canción para escucharla y ver qué puedes practicar. Si las voces no coinciden en el tiempo, revisa el ajuste de tiempo.', 'feedback-note'));
    stats(root, data.metricas, data.musical);
    alignmentControls();
    const legacy = el('details'); legacy.append(el('summary','Indicadores históricos (otro método)'));
    const old = selectedTake()?.metrics || {}; legacy.append(el('p', `DTW: ${pct(old.porcentaje_50)} dentro de medio semitono; ${pct(old.porcentaje_100)} dentro de un semitono. Reordena la correspondencia temporal y excluye diferencias grandes; no equivale al análisis por notas.`, 'feedback-note')); root.append(legacy);
    summaryBox = el('div', null, 'feedback-copy'); root.append(summaryBox); narrative(summaryBox, data.explicacion);
    summaryBox.classList.add('review-summary');
    Array.from(root.children).forEach(child => {if(child!==summaryBox) child.classList.add('review-technical');});
    const layout = el('div', null, 'feedback-layout'); fragmentList = el('div', null, 'feedback-list');
    fragmentList.setAttribute('aria-label', 'Fragmentos de la toma'); detailBox = el('div', null, 'feedback-copy');
    detailBox.append(el('h3', 'Revisa una parte de tu interpretación'), el('p', 'Elige un fragmento para ver sus aciertos, diferencias detectadas y práctica sugerida.', 'feedback-note'));
    data.fragmentos.forEach(f => {
      const b = button(`Fragmento ${Number(f.id.slice(1))}`, () => openFragment(f)); b.className = 'feedback-fragment'; b.dataset.id = f.id;
      b.setAttribute('aria-pressed', 'false'); b.append(el('span', `${time(f.inicio_s)}–${time(f.fin_s)} · ${f.musical.metricas.notas_comparadas}/${f.musical.metricas.notas_referencia} notas comparadas`)); fragmentList.append(b);
    });
    if (!data.fragmentos.length) detailBox.replaceChildren(el('p', 'No hay fragmentos de referencia dentro de la duración grabada.'));
    layout.append(fragmentList, detailBox); root.append(layout);
  }
  function alignmentControls() {
    const alignment = data.alineacion;
    const names = {automatico:'automática', manual:'manual', desactivado:'desactivada'};
    const move = data.desfase_ms === 0 ? 'sin desplazamiento' : `${data.desfase_ms > 0 ? 'voz adelantada' : 'voz atrasada'} ${Math.abs(data.desfase_ms)} ms`;
    const qualifier = alignment.modo === 'automatico' && alignment.estado !== 'aplicado' ? ' · Sin corrección concluyente' : '';
    const box = el('details', null, 'feedback-alignment');
    box.append(el('summary', `Sincronización ${names[alignment.modo]} · ${move}${qualifier} · Modificar`));
    box.append(el('p', alignment.motivo, 'feedback-note'));
    box.append(el('p', 'Positivo: adelanta tu voz; negativo: atrasa tu voz. Se desplaza toda la toma sin estirar notas. Esto no mide la latencia del equipo ni demuestra una mejora al cantar.', 'feedback-note'));
    const label = el('label', 'Compensación (ms)'); const input = el('input');
    input.type = 'number'; input.min = '-2000'; input.max = '2000'; input.step = '5'; input.value = data.desfase_ms;
    label.append(input); box.append(label);
    const note = el('p', '', 'feedback-note'); note.setAttribute('role', 'status'); box.append(note);
    const songId = currentSong().id, takeId = selectedTake().id, token = revision;
    const apply = async mode => {
      if (mode === 'manual' && (!input.checkValidity() || input.value === '')) { input.reportValidity(); return; }
      note.textContent = 'Recalculando…';
      box.querySelectorAll('button').forEach(b => b.disabled = true);
      try {
        const r = await api().set_alignment(songId, takeId, mode === 'manual' ? Number(input.value) : 0, mode);
        if (token !== revision) return;
        if (!r.ok) throw new Error(r.error);
        audioEnd = null; pauseTakePlayback();
        await refresh(true);
      } catch (e) { if (token === revision) note.textContent = e.message || 'No se pudo aplicar el ajuste.'; }
      finally { box.querySelectorAll('button').forEach(b => b.disabled = false); }
    };
    box.append(button('Aplicar ajuste manual', () => apply('manual')),
               button('Volver al automático', () => apply('automatico')),
               button('Desactivar compensación', () => apply('desactivado')));
    root.append(box);
  }
  async function refresh(force = false) {
    const mount = document.getElementById(state.activeView === 'result' ? 'resultFeedbackMount' : state.activeView === 'history' ? 'historyFeedbackMount' : '');
    if (!mount) return;
    mount.append(root);
    const song = currentSong(), take = selectedTake(); const key = `${song?.id || ''}/${take?.id || ''}`;
    if (identity === key && !force) return;
    identity = key; const ticket = ++revision; detailRevision++; audioEnd = null; data = null; fragment = null;
    renderMetrics({}); renderChart();
    root.replaceChildren(el('h2', 'Análisis por fragmentos'));
    if (!take?.id || !api()?.get_feedback) { root.append(el('p', 'Selecciona una toma del historial o graba una interpretación.')); return; }
    root.append(el('p', 'Preparando métricas y fragmentos…', 'feedback-note'));
    try {
      const r = await api().get_feedback(song.id, take.id);
      if (ticket !== revision) return;
      if (!r.ok) throw new Error(r.error);
      data = r; render(); renderMetrics({}); renderChart();
    } catch (error) {
      if (ticket !== revision) return;
      root.replaceChildren(el('h2', 'Análisis por fragmentos'), el('p', error.message || 'No se pudo cargar el análisis.'));
      root.append(button('Volver a cargar', () => refresh(true)));
    }
  }
  // Durante un fragmento, la mezcla usa la misma compensación que el análisis.
  // Fuera de ese modo vuelve al ajuste independiente del mezclador.
  window.feedbackUI = { refresh, analysis: () => !state.playing && data && identity === `${currentSong()?.id || ''}/${selectedTake()?.id || ''}` ? data : null, playbackOffset: () => audioEnd !== null && data ? -data.desfase_ms : null };
  window.addEventListener('pywebviewready', () => refresh());
  refresh();
})();

(() => {
  const panel = document.getElementById('preparationProgress');
  let timer = null, generation = 0;
  window.preparationUI = {
    start() {
      this.stop(); const current = ++generation, since = Date.now();
      panel.classList.remove('hidden');
      document.getElementById('preparationMessage').textContent = 'Preparando canción…';
      panel.querySelector('progress').removeAttribute('value');
      const poll = async () => {
        if (current !== generation) return;
        try {
          const r = await window.pywebview.api.get_preparation_state();
          if (current !== generation) return;
          document.getElementById('preparationMessage').textContent = r.message;
          const bar=panel.querySelector('progress'); bar.max=100;
          if(Number.isFinite(r.percent)) bar.value=r.percent; else bar.removeAttribute('value');
          document.getElementById('preparationElapsed').textContent = `${Math.floor((Date.now()-since)/1000)} s transcurridos · Puedes seguir navegando. Mantén abierta la aplicación.`;
        } catch (_) { /* Mantener barra mientras la operación principal sigue en curso. */ }
        if (current === generation) timer = setTimeout(poll, 700);
      }; poll();
    },
    stop() { generation++; clearTimeout(timer); timer = null; panel.classList.add('hidden'); }
  };
})();
