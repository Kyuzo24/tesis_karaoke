(() => {
  const steps = [
    {
      view: 'library', target: '.song-browser', title: 'Elige una canción',
      text: 'Puedes pulsar Agregar canción y buscar un tema, o seleccionar uno que ya esté preparado. El recorrido continuará cuando tengas una canción lista seleccionada.',
      done: () => !state.catalogWorking && Boolean(currentSong()?.prepared)
    },
    {
      view: 'settings', target: '#audioInput', title: 'El sonido que te acomode',
      text: 'Puedes elegir el micrófono y la salida de audio en esta pantalla. Si los dispositivos actuales te sirven, pulsa Continuar.',
      next: 'Continuar'
    },
    {
      view: 'library', target: '#libraryPracticeButton', title: 'Abre tu canción',
      text: 'Pulsa Practicar para abrir la canción seleccionada. También puedes elegir otra canción de la biblioteca antes de continuar.',
      done: () => state.activeView === 'practice'
    },
    {
      view: 'practice', target: '#startButton', title: 'Cuando quieras, canta',
      text: 'Pulsa Cantar para iniciar tu toma. La aplicación mide primero el ruido ambiente. Esperar en silencio esos instantes ayuda a detectar tu voz.',
      done: () => state.playing
    },
    {
      view: 'practice', target: '#stopButton', title: 'Canta a tu ritmo',
      text: 'Puedes cantar hasta el final o pulsar Detener cuando prefieras. Los bloques del gráfico muestran la referencia y el trazo muestra tu voz. El recorrido continuará cuando esté listo el resultado.',
      done: () => !state.playing && state.sessionStatus === 'finished'
    },
    {
      view: 'result', target: '#takePlayButton', title: 'Escucha tu toma',
      text: 'Pulsa Reproducir toma para escucharla. Puedes explorar el gráfico y los fragmentos de tu interpretación. Cuando quieras seguir el recorrido, pulsa Continuar.',
      next: 'Continuar'
    },
    {
      view: 'result', target: '[data-view-target="history"]', title: 'Encuentra tus grabaciones',
      text: 'Pulsa Historial para ver las tomas guardadas de esta canción. Allí puedes volver a escucharlas, renombrarlas o marcar tus favoritas.',
      done: () => state.activeView === 'history'
    },
    {
      view: 'history', target: '[data-view-target="guide"]', title: 'La ayuda queda a mano',
      text: 'Puedes abrir Guía de uso para consultar las pestañas o repetir este recorrido. También puedes terminar aquí y seguir explorando.',
      done: () => state.activeView === 'guide',
      next: 'Terminar'
    }
  ];
  const overlay = document.createElement('div');
  overlay.className = 'tutorial-overlay';
  overlay.hidden = true;
  overlay.innerHTML = `
    <svg class="tutorial-shade" aria-hidden="true"><path fill="rgba(0,0,0,.65)" fill-rule="evenodd"></path></svg>
    <div class="tutorial-ring" aria-hidden="true"></div>
    <section class="tutorial-card" role="region" aria-label="Tutorial práctico">
      <div aria-live="polite" aria-atomic="true">
        <span class="tutorial-count"></span><h2></h2><p></p>
      </div>
      <div class="tutorial-actions">
        <button class="button" type="button" data-exit>Salir del tutorial</button>
        <button class="button button-primary" type="button" data-next>Saltar paso</button>
      </div>
    </section>`;
  document.body.append(overlay);
  const card = overlay.querySelector('.tutorial-card');
  const ring = overlay.querySelector('.tutorial-ring');
  const path = overlay.querySelector('path');
  const next = overlay.querySelector('[data-next]');
  let index = 0;
  let timer = null;
  let active = false;
  let message = '';

  function position() {
    if (!active || overlay.hidden) return;
    const target = document.querySelector(steps[index].target);
    const rect = target?.getBoundingClientRect();
    const width = window.innerWidth;
    const height = window.innerHeight;
    const visible = rect && rect.width > 0 && rect.height > 0 &&
      rect.bottom > 0 && rect.top < height;
    ring.hidden = !visible;
    const left = visible ? Math.max(4, rect.left - 6) : 12;
    const top = visible ? Math.max(4, rect.top - 6) : 12;
    const right = visible ? Math.min(width - 4, rect.right + 6) : 12;
    const bottom = visible ? Math.min(height - 4, rect.bottom + 6) : 12;
    path.setAttribute('d', `M0 0H${width}V${height}H0Z` +
      (visible ? ` M${left} ${top}H${right}V${bottom}H${left}Z` : ''));
    // While singing, leave the graph and controls fully visible.
    path.style.opacity = state.playing ? '0' : '1';
    Object.assign(ring.style, {left: left + 'px', top: top + 'px',
      width: (right - left) + 'px', height: (bottom - top) + 'px'});
    const cardWidth = card.offsetWidth;
    const cardHeight = card.offsetHeight;
    let x = left;
    let y = bottom + 12;
    if (y + cardHeight > height - 12) {
      y = top - cardHeight - 12;
      if (y < 12) {
        y = top;
        x = right + 12 + cardWidth <= width ? right + 12 : left - cardWidth - 12;
      }
    }
    // Large sections get a card beside them when space permits.
    if (right - left > width / 2 && left >= cardWidth + 24) {
      x = left - cardWidth - 12;
      y = top;
    }
    card.style.left = Math.max(12, Math.min(x, width - cardWidth - 12)) + 'px';
    card.style.top = Math.max(12, Math.min(y, height - cardHeight - 12)) + 'px';
  }

  function showStep() {
    const step = steps[index];
    setActiveView(step.view);
    overlay.querySelector('.tutorial-count').textContent = `Paso ${index + 1} de ${steps.length}`;
    overlay.querySelector('h2').textContent = step.title;
    message = '';
    next.textContent = step.next || 'Saltar paso';
    document.querySelector(step.target)?.scrollIntoView({block: 'center', behavior: 'instant'});
    refresh();
  }

  function finish() {
    active = false;
    overlay.hidden = true;
    clearInterval(timer);
    timer = null;
    // Closing the tutorial leaves the user's current activity in place.
  }

  function advance() {
    if (index === steps.length - 1) return finish();
    index++;
    if (index === 4 && !state.playing) index++; // Skipping singing also skips waiting for a recording.
    showStep();
  }

  function refresh() {
    if (!active) return;
    // Native dialogs and the metadata form keep their own focus and instructions.
    const modal = document.querySelector('dialog[open], .modal-backdrop:not(.hidden)');
    overlay.hidden = Boolean(modal);
    if (modal) return;
    if (index === 4 && !state.playing && state.sessionStatus === 'error') {
      index = 3;
      showStep();
      return;
    }
    if (steps[index].done?.()) {
      advance();
      return;
    }
    next.disabled = state.playing || state.catalogWorking;
    let text = steps[index].text;
    if (state.catalogWorking) text = 'La canción se está preparando. Puedes seguir usando la aplicación. Cuando termine, selecciona la canción que quieras cantar.';
    else if (index === 4 && ['stopping', 'comparing'].includes(state.sessionStatus)) {
      text = 'Tu grabación se está procesando. El resultado aparecerá cuando termine el análisis.';
    } else if (index === 3 && !currentSong()?.prepared) {
      text = 'Para cantar, vuelve a Biblioteca y selecciona una canción preparada. También puedes saltar este paso para conocer las demás pantallas.';
    }
    if (text !== message) {
      overlay.querySelector('p').textContent = text;
      message = text;
    }
    position();
  }
  next.onclick = advance;
  overlay.querySelector('[data-exit]').onclick = finish;
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && active && !overlay.hidden) finish();
  });
  window.addEventListener('resize', position);
  window.addEventListener('scroll', position, true);
  new ResizeObserver(position).observe(card);
  window.tutorial = {
    get active() { return active; },
    start() {
      if (active) return true;
      if (state.playing || state.catalogWorking || document.querySelector('dialog[open], .modal-backdrop:not(.hidden)')) {
        document.getElementById('guideNotice').textContent = 'Puedes abrir el recorrido al terminar la tarea actual.';
        return false;
      }
      active = true;
      index = 0;
      document.getElementById('libraryAll').click();
      overlay.hidden = false;
      showStep();
      timer = setInterval(refresh, 250);
      return true;
    }
  };
  document.getElementById('repeatTutorial').onclick = () => window.tutorial.start();
})();
