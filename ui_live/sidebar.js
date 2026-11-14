(() => {
  const paths={
    library:'M4 4h5v16H4z M11 4h4v16h-4z M17 5l3-1 3 15-3 1z',
    practice:'M9 5a3 3 0 0 1 6 0v7a3 3 0 0 1-6 0z M6 11v1a6 6 0 0 0 12 0v-1 M12 18v4 M8 22h8',
    result:'M4 20V11h4v9 M10 20V4h4v16 M16 20v-7h4v7',
    history:'M4 9a8 8 0 1 1 0 7 M4 3v6h6 M12 7v5l3 2',
    diagnostics:'M2 12h4l3-7 5 14 3-7h5',
    settings:'M4 6h16 M4 12h16 M4 18h16 M8 3v6 M16 9v6 M10 15v6',
    guide:'M12 6Q8 3 3 5v14q5-2 9 1 4-3 9-1V5q-5-2-9 1v14'
  };
  document.querySelectorAll('.app-nav .nav-item').forEach(button=>{
    const label=button.textContent.trim();button.setAttribute('aria-label',label);button.title=label;
    const icon=document.createElementNS('http://www.w3.org/2000/svg','svg');
    icon.setAttribute('viewBox','0 0 24 24');icon.setAttribute('aria-hidden','true');icon.classList.add('nav-icon');
    const path=document.createElementNS('http://www.w3.org/2000/svg','path');path.setAttribute('d',paths[button.dataset.viewTarget || button.id]||paths.library);icon.append(path);
    const text=document.createElement('span');text.className='nav-label';text.textContent=label;
    button.replaceChildren(icon,text);
  });
  const toggle=document.createElement('button');toggle.type='button';toggle.className='button sidebar-toggle';
  document.body.append(toggle);
  let collapsed=false;
  try {collapsed=localStorage.getItem('karaoke-sidebar-collapsed')==='true';}catch(_){}
  function render(){
    document.body.classList.toggle('sidebar-collapsed',collapsed);
    toggle.textContent=collapsed?'›':'‹';
    toggle.title=collapsed?'Expandir menú':'Contraer menú';toggle.setAttribute('aria-label',toggle.title);
    toggle.setAttribute('aria-expanded',String(!collapsed));
  }
  toggle.onclick=()=>{collapsed=!collapsed;render();try{localStorage.setItem('karaoke-sidebar-collapsed',String(collapsed));}catch(_){};renderChart();};
  render();
})();
