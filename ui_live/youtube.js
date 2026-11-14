/* Search results are untrusted: render all provider text with textContent. */
(() => {
  const dialog = document.createElement('dialog');
  dialog.className = 'song-modal youtube-dialog';
  dialog.setAttribute('aria-labelledby', 'youtubeTitle');
  dialog.innerHTML = `
    <div class="modal-head"><div><div class="section-label">Biblioteca</div>
    <h2 id="youtubeTitle">Agregar canción</h2></div>
    <button type="button" class="button" data-close aria-label="Cerrar">×</button></div>
    <form><label class="modal-field" for="youtubeQuery"><span>Buscar en YouTube Music</span>
    <input id="youtubeQuery" type="search" placeholder="Nombre de canción y artista" required minlength="2" maxlength="200" autocomplete="off"></label>
    <button class="button button-primary" type="submit">Buscar</button></form>
    <p class="youtube-status" role="status" aria-live="polite"></p>
    <div class="youtube-results"></div>
    <p class="youtube-hint">La preparación puede tardar varios minutos. Las canciones listas se guardan para tus próximas sesiones. Importa contenido propio o que tengas permiso para utilizar.</p>
    <div class="modal-actions"><button type="button" class="button" data-file>Elegir archivo local</button>
    <button type="button" class="button" data-close>Cancelar</button></div>`;
  const style = document.createElement('style');
  style.textContent = `
    .youtube-dialog {width:min(680px,90vw);max-height:85vh;overflow:auto;padding:24px;}
    .youtube-dialog:not([open]) {display:none;}
    .youtube-dialog::backdrop {background:rgba(0,0,0,.7);}
    .youtube-dialog form {display:flex;align-items:end;gap:12px;}
    .youtube-dialog .modal-field {flex:1;min-width:0;}
    .youtube-results {display:grid;gap:10px;}
    .youtube-result {display:flex;align-items:center;justify-content:space-between;gap:16px;border:1px solid var(--line-strong);border-radius:10px;padding:12px;}
    .youtube-result strong,.youtube-result small {display:block;overflow-wrap:anywhere;}
    .youtube-result small,.youtube-hint {color:var(--muted);}
    .youtube-hint {font-size:13px;line-height:1.5;}
    .youtube-status {min-height:24px;}
    @media(max-width:500px){.youtube-result{align-items:start;flex-direction:column;}}
  `;
  document.head.append(style);
  document.body.append(dialog);
  const form = dialog.querySelector('form');
  const query = dialog.querySelector('input');
  const submit = form.querySelector('button');
  const status = dialog.querySelector('.youtube-status');
  const results = dialog.querySelector('.youtube-results');
  let finish = null;
  let generation = 0;
  function close(result) {
    generation++;
    const resolve = finish;
    finish = null;
    dialog.close();
    resolve?.(result);
  }
  dialog.querySelectorAll('[data-close]').forEach(b => b.onclick = () => close({cancelled:true}));
  dialog.addEventListener('cancel', event => {event.preventDefault(); close({cancelled:true});});
  dialog.querySelector('[data-file]').onclick = () => close({local:true});
  form.onsubmit = async event => {
    event.preventDefault();
    const request = ++generation;
    submit.disabled = true;
    results.replaceChildren();
    status.textContent = 'Buscando canciones…';
    try {
      const response = await window.pywebview.api.search_youtube(query.value.trim());
      if (!finish || request !== generation) return;
      if (!response.ok) throw new Error(response.error || 'No se pudo completar la búsqueda.');
      status.textContent = response.results.length
        ? 'Selecciona una canción. Se muestran canciones de hasta 20 minutos.'
        : 'No encontramos canciones disponibles. Prueba con otro título o artista.';
      response.results.forEach(item => {
        const row = document.createElement('div'); row.className = 'youtube-result';
        const info = document.createElement('div');
        const title = document.createElement('strong'); title.textContent = item.title;
        const meta = document.createElement('small');
        const seconds = Math.round(item.duration || 0);
        meta.textContent = [item.artist || 'Artista sin nombre', item.album,
          seconds ? Math.floor(seconds/60)+':'+String(seconds%60).padStart(2,'0') : 'Duración no disponible'].filter(Boolean).join(' · ');
        info.append(title, meta);
        const button = document.createElement('button');button.type = 'button';button.className = 'button';button.textContent = 'Seleccionar';
        button.onclick = () => close({ok:true,video_id:item.id,filename:item.title,
          suggested_title:item.title,suggested_artist:item.artist || ''});
        row.append(info,button);results.append(row);
      });
    } catch (error) {
      if (finish && request === generation) status.textContent = error.message || String(error);
    } finally {
      if (request === generation) submit.disabled = false;
    }
  };
  window.chooseSongSource = async () => {
    const selected = await new Promise(resolve => {
      finish = resolve;generation++;submit.disabled = false;
      status.textContent = '';results.replaceChildren();query.value = '';
      dialog.showModal();query.focus();
    });
    return selected.local ? window.pywebview.api.select_audio_file() : selected;
  };
})();
