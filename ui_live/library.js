(() => {
  const el=id=>document.getElementById(id);
  let collections=[],stats={},mode='songs',folder=null,sort='alpha',request=0;
  const notice=text=>el('libraryNotice').textContent=text;
  async function refresh() {
    if(!window.pywebview?.api?.library_info) return;
    const ticket=++request;
    try {
      const r=await window.pywebview.api.library_info();
      if(ticket!==request) return;
      if(!r.ok) throw new Error(r.error);
      collections=r.collections;stats=r.stats;renderSongs();
    } catch(e) {notice(e.message);}
  }
  async function change(action,id='',name='',song='',included=true) {
    ++request;
    const r=await window.pywebview.api.change_collection(action,id,name,song,included);
    if(!r.ok) throw new Error(r.error);
    collections=r.collections;renderSongs();
  }
  function entries() {
    const collection=collections.find(c=>c.id===folder);
    return songs.map((song,index)=>({song,index})).filter(({song})=>mode!=='folders' || !collection || collection.songs.includes(song.id)).sort((a,b)=>{
      const sa=stats[a.song.id]||{},sb=stats[b.song.id]||{};
      let delta=sort==='count' ? (sb.count||0)-(sa.count||0) : sort==='alpha' ? 0 : String(sb[sort]||'').localeCompare(String(sa[sort]||''));
      return delta || a.song.title.localeCompare(b.song.title,'es',{sensitivity:'base'}) || a.song.id.localeCompare(b.song.id);
    });
  }
  const dialog=document.createElement('dialog'); dialog.className='collection-dialog';document.body.append(dialog);
  function open(title) {
    dialog.replaceChildren();const h=document.createElement('h2');h.textContent=title;dialog.append(h);
    const close=document.createElement('button');close.type='button';close.className='button collection-exit';close.textContent='Salir';close.onclick=()=>dialog.close();dialog.append(close);
    dialog.showModal();
  }
  function render() {
    collections.sort((a,b)=>a.name.localeCompare(b.name,'es',{sensitivity:'base'}) || a.id.localeCompare(b.id));
    const current=collections.find(c=>c.id===folder);
    if(!current) folder=null;
    const inside=mode==='folders' && Boolean(current);
    el('addButton').hidden=mode==='folders';
    document.body.classList.toggle('inside-collection',inside);
    document.body.classList.toggle('collection-selection',inside && current.songs.includes(currentSong()?.id));
    el('collectionAddSongs').hidden=!inside;
    el('collectionRemoveSong').hidden=!inside;
    el('collectionRemoveSong').disabled=!inside || !current?.songs.includes(currentSong()?.id);
    el('collectionHeading').hidden=!inside;
    el('collectionTitle').textContent=inside?current.name:'';
    el('libraryAll').hidden=inside;
    el('libraryFolders').hidden=inside;
    el('librarySort').closest('label').hidden=mode==='folders'&&!inside;
    el('songCollections').disabled=!currentSong() || state.playing;
    el('libraryAll').setAttribute('aria-pressed',String(mode==='songs'));
    el('libraryFolders').setAttribute('aria-pressed',String(mode==='folders'));
    el('collectionToolbar').hidden=mode!=='folders'||inside;
    el('collectionHint').textContent=current ? current.name : 'Elige una colección. Una canción puede estar en varias.';
    el('songList').hidden=mode==='folders'&&!folder;
    const grid=el('collectionGrid');grid.replaceChildren();grid.hidden=mode!=='folders'||inside;
    if(mode!=='folders'||inside) return;
    if(!collections.length) grid.textContent='Crea tu primera colección para organizar la biblioteca.';
    collections.forEach(c=>{
      const card=document.createElement('div');card.className='collection-card';
      const b=document.createElement('button');b.className='button';b.type='button';
      const count=songs.filter(s=>c.songs.includes(s.id)).length;
      b.textContent=`▣ ${c.name} · ${count} ${count===1?'canción':'canciones'}`;
      b.setAttribute('aria-pressed',String(folder===c.id));b.onclick=()=>{
        folder=c.id;
        if(!c.songs.includes(currentSong()?.id)) {const index=songs.findIndex(s=>c.songs.includes(s.id));if(index>=0) selectSong(index);}
        renderSongs();window.scrollTo(0,0);el('collectionBack').focus({preventScroll:true});
      };
      const del=document.createElement('button');del.className='button';del.type='button';del.textContent='Eliminar';del.setAttribute('aria-label',`Eliminar colección ${c.name}`);
      del.onclick=async()=>{if(!confirm(`¿Eliminar la colección «${c.name}»? Las canciones se conservarán.`)) return;del.disabled=true;try{await change('delete',c.id);}catch(e){notice(e.message);del.disabled=false;}};
      card.append(b,del);grid.append(card);
    });
  }
  el('libraryAll').onclick=()=>{mode='songs';folder=null;renderSongs();};
  el('libraryFolders').onclick=()=>{mode='folders';folder=null;renderSongs();refresh();};
  el('collectionBack').onclick=()=>{const previous=folder;folder=null;renderSongs();window.scrollTo(0,0);el('libraryFolders').focus({preventScroll:true});};
  const addSongs=document.createElement('button');addSongs.id='collectionAddSongs';addSongs.type='button';addSongs.className='button button-primary';addSongs.textContent='Añadir canciones';
  el('libraryAll').parentElement.prepend(addSongs);
  const removeSong=document.createElement('button');removeSong.id='collectionRemoveSong';removeSong.type='button';removeSong.className='button button-danger';removeSong.textContent='Quitar de esta colección';
  el('songCollections').after(removeSong);
  addSongs.onclick=()=>{
    const id=folder,collection=collections.find(c=>c.id===id);if(!collection) return;
    open(`Canciones de ${collection.name}`);
    const hint=document.createElement('p');hint.textContent='Marca las canciones que quieras incluir. Desmarcarlas solo las quita de esta colección.';dialog.append(hint);
    const message=document.createElement('p');message.setAttribute('role','status');dialog.append(message);
    [...songs].sort((a,b)=>a.title.localeCompare(b.title,'es',{sensitivity:'base'})).forEach(song=>{
      const label=document.createElement('label'),input=document.createElement('input');input.type='checkbox';input.checked=collection.songs.includes(song.id);
      label.append(input,document.createTextNode(`${song.title} — ${song.artist}`));dialog.append(label);
      input.onchange=async()=>{
        const wanted=input.checked;dialog.querySelectorAll('input').forEach(i=>i.disabled=true);
        try{await change('membership',id,'',song.id,wanted);message.textContent='Colección actualizada.';}
        catch(e){input.checked=!wanted;message.textContent=e.message;}
        finally{dialog.querySelectorAll('input').forEach(i=>i.disabled=false);}
      };
    });
    if(!songs.length) message.textContent='Primero añade canciones desde la vista Canciones de la Biblioteca.';
  };
  removeSong.onclick=async()=>{
    const id=folder,song=currentSong();if(!id||!song) return;
    removeSong.disabled=true;
    try{await change('membership',id,'',song.id,false);notice(`«${song.title}» se quitó de la colección. Sigue en tu Biblioteca.`);}
    catch(e){notice(e.message);render();}
  };
  el('librarySort').onchange=e=>{sort=e.target.value;renderSongs();};
  el('collectionCreate').onclick=()=>{
    open('Nueva colección');const form=document.createElement('form');const input=document.createElement('input');input.required=true;input.maxLength=80;input.placeholder='Nombre de la colección';input.setAttribute('aria-label','Nombre de la colección');
    const submit=document.createElement('button');submit.className='button';submit.textContent='Crear';const error=document.createElement('p');error.setAttribute('role','status');form.append(input,submit,error);dialog.append(form);input.focus();
    form.onsubmit=async e=>{e.preventDefault();submit.disabled=true;try{await change('create','',input.value);dialog.close();}catch(e){error.textContent=e.message;}finally{submit.disabled=false;}};
    const cancel=dialog.querySelector('button');cancel.textContent='Cancelar';cancel.classList.remove('collection-exit');cancel.classList.add('button-danger');form.append(cancel);
  };
  el('songCollections').onclick=async()=>{
    await refresh();const song=currentSong();if(!song) return;open(`Colecciones de ${song.title}`);
    if(!collections.length) {const p=document.createElement('p');p.textContent='Crea una colección desde la pestaña Colecciones.';dialog.append(p);}
    collections.forEach(c=>{
      const label=document.createElement('label'),input=document.createElement('input');input.type='checkbox';input.checked=c.songs.includes(song.id);label.append(input,document.createTextNode(c.name));dialog.append(label);
      input.onchange=async()=>{const wanted=input.checked;dialog.querySelectorAll('input').forEach(i=>i.disabled=true);try{await change('membership',c.id,'',song.id,wanted);}catch(e){input.checked=!wanted;notice(e.message);}finally{dialog.querySelectorAll('input').forEach(i=>i.disabled=false);}};
    });
  };
  document.querySelector('[data-view-target=library]').addEventListener('click',refresh);
  window.addEventListener('pywebviewready',refresh);
  window.libraryUI={render,entries};refresh();renderSongs();
})();
