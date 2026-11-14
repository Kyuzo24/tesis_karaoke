(() => {
  const watched=new WeakSet();
  function watchLists() {
    document.querySelectorAll('.take-list,.feedback-list').forEach(list=>{
      if(watched.has(list)) return;
      watched.add(list);
      const edges=()=>{
        list.classList.toggle('has-content-above',list.scrollTop>2);
        list.classList.toggle('has-content-below',list.scrollHeight-list.clientHeight-list.scrollTop>2);
      };
      list.addEventListener('scroll',edges,{passive:true});
      new ResizeObserver(edges).observe(list);
      new MutationObserver(edges).observe(list,{childList:true,subtree:true});
      edges();
    });
  }
  const toolbar=document.createElement('nav'); toolbar.className='review-tabs'; toolbar.setAttribute('aria-label','Vistas de la toma');
  const caption=document.createElement('p'); caption.className='review-caption';
  let current='summary';
  const choices=[['summary','Resumen'],['chart','Gráfico y audio'],['fragments','Fragmentos'],['technical','Ajuste de tiempo y detalles']];
  for(const [key,label] of choices) {
    const b=document.createElement('button'); b.type='button'; b.className='button'; b.textContent=label; b.dataset.review=key;
    b.onclick=()=>{current=key; update(); renderChart();}; toolbar.append(b);
  }
  function update() {
    document.body.dataset.review=current;
    toolbar.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.review===current)));
    const take=selectedTake();
    caption.textContent=take ? `Toma seleccionada: ${take.name || take.createdAt || 'Sin nombre'} · ${formatTime(take.duration)}` : 'Selecciona una toma en el historial o graba una interpretación.';
  }
  function mount() {
    watchLists();
    if(!['result','history'].includes(state.activeView)) return;
    const parent=document.querySelector(state.activeView==='history' ? '.history-detail' : '[data-view-panel="result"]');
    if(toolbar.parentElement!==parent) {parent.prepend(caption); parent.prepend(toolbar);}
    update();
  }
  window.reviewUI={mount}; mount();
})();
