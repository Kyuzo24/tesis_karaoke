(() => {
  const el = id => document.getElementById(id);
  let songId = null, generation = 0, lastKey = '', lastLyrics = null;
  const status = text => {el('lyricsStatus').textContent=text;};
  // Keep configuration out of the performance layout, including when the chart moves.
  document.body.append(el('lyricsSettings'));
  el('lyricsConfigure').onclick=()=>el('lyricsSettings').showModal();
  el('libraryLyricsButton').onclick=()=>{render(); el('lyricsSettings').showModal();};
  el('lyricsClose').onclick=()=>el('lyricsSettings').close();
  function activeIndex(lines, time) {
    let lo=0, hi=lines.length;
    while(lo<hi) {const mid=(lo+hi)>>1; if(lines[mid].time<=time) lo=mid+1; else hi=mid;}
    return lo-1;
  }
  function render() {
    const song=currentSong();
    el('libraryLyricsButton').disabled=!song?.id;
    if(songId!==song?.id) {
      songId=song?.id; generation++; lastKey='';
      el('lyricsSettings').close();
      el('lyricsTitle').value=song?.title || '';
      el('lyricsArtist').value=song?.artist==='Sin artista' ? '' : song?.artist || '';
      el('lyricsOffset').value=song?.lyrics?.offset_ms || 0;
      el('lyricsResults').replaceChildren(); status('');
      el('lyricsSearch').disabled=false;
    }
    const lyrics=song?.lyrics, lines=lyrics?.lines || [];
    // Recording uses the instrumental clock. Saved playback uses its compensated time.
    const correction=state.playing ? 0 : (window.feedbackUI?.analysis?.()?.desfase_ms || 0)/1000;
    const index=activeIndex(lines,state.current-correction-(lyrics?.offset_ms || 0)/1000);
    const key=JSON.stringify([songId,index,lyrics?.offset_ms]);
    el('lyricsDisplay').hidden=!el('lyricsVisible').checked;
    el('lyricsSaveOffset').disabled=!lyrics;
    if(key===lastKey && lyrics===lastLyrics) return;
    lastKey=key; lastLyrics=lyrics;
    el('lyricsCurrent').textContent=!lines.length ? 'Añade una letra sincronizada para cantar.' : index<0 ? '♪' : lines[index].text || '♪';
    el('lyricsNext').textContent=lines[index+1]?.text || '';
    el('lyricsSource').textContent=lyrics ? `Fuente: ${lyrics.source}` : '';
  }
  async function save(song, text, offset, source) {
    const response=await window.pywebview.api.save_lyrics(song.id,text,offset,source);
    if(!response.ok) throw new Error(response.error);
    // The result belongs to the original song, even if selection changed during I/O.
    const target=songs.find(s=>s.id===song.id);
    if(target) target.lyrics=response.lyrics;
    renderSongs();
    updateLibrarySummary();
    if(currentSong()?.id===song.id) {
      lastKey=''; render(); status('Letra guardada.');
      el('lyricsResults').replaceChildren();
      el('lyricsSettings').close();
    }
  }
  el('lyricsSearch').onclick=async () => {
    const song=currentSong(), token=++generation;
    if(!song || !window.pywebview?.api) return;
    el('lyricsSearch').disabled=true; status('Buscando…'); el('lyricsResults').replaceChildren();
    try {
      const response=await window.pywebview.api.search_lyrics(el('lyricsTitle').value,el('lyricsArtist').value);
      if(token!==generation || currentSong()?.id!==song.id) return;
      if(!response.ok) throw new Error(response.error);
      status(response.results.length ? 'Elige la versión que corresponda a tu grabación.' : 'No hay letras sincronizadas para esta búsqueda. Puedes importar un archivo LRC.');
      response.results.forEach(result => {
        const button=document.createElement('button'); button.type='button';
        const duration=Number(result.duration);
        button.textContent=`${result.title} — ${result.artist} · ${result.album || 'Sin álbum'} · ${Number.isFinite(duration)?Math.round(duration)+' s':'duración desconocida'} (tu audio: ${Math.round(song.duration)} s)`;
        button.onclick=async () => {
          if(currentSong()?.id!==song.id) return;
          button.disabled=true;
          try {await save(song,result.lrc,0,`LRCLIB #${result.id}`); if(currentSong()?.id===song.id) el('lyricsOffset').value=0;}
          catch(e) {if(currentSong()?.id===song.id) status(e.message);}
          finally {button.disabled=false;}
        };
        el('lyricsResults').append(button);
      });
    } catch(e) {if(token===generation) status(e.message);}
    finally {if(token===generation) el('lyricsSearch').disabled=false;}
  };
  el('lyricsFile').onchange=async event => {
    const song=currentSong(), file=event.target.files[0];
    if(!song || !file) return;
    try {
      if(file.size>500000) throw new Error('El archivo supera 500 KB.');
      await save(song,await file.text(),0,'Archivo LRC');
      if(currentSong()?.id===song.id) el('lyricsOffset').value=0;
    } catch(e) {if(currentSong()?.id===song.id) status(e.message);}
    finally {event.target.value='';}
  };
  el('lyricsSaveOffset').onclick=async () => {
    const song=currentSong(); if(!song?.lyrics) return;
    try {await save(song,song.lyrics.lrc,Number(el('lyricsOffset').value),song.lyrics.source);}
    catch(e) {if(currentSong()?.id===song.id) status(e.message);}
  };
  el('lyricsVisible').onchange=render;
  window.lyricsUI={render,activeIndex}; render();
})();
