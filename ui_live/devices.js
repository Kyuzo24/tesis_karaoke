(() => {
  const el=id=>document.getElementById(id);
  let busy=false;
  async function refresh(rescan=false) {
    if(busy || state.playing || !window.pywebview?.api?.audio_devices) return;
    busy=true;
    try {
      const r=await window.pywebview.api.audio_devices(rescan);
      if(!r.ok) throw new Error(r.error);
      ['audioInput','audioOutput'].forEach((id,index)=>{
        const select=el(id); select.replaceChildren();

        r.devices.filter(d=>index===0?d.input:d.output).forEach(d=>select.add(new Option(d.name,d.id)));
        select.value=String(r.selected[index]);
        if(select.selectedIndex<0 && select.options.length) select.selectedIndex=0;
        select.disabled=!select.options.length;
      });
      el('audioDeviceStatus').textContent='';
      await loadBackendStatus();
    } catch(e) {el('audioDeviceStatus').textContent=e.message;}
    finally {busy=false;}
  }
  async function apply() {
    if(busy) return;
    if(state.playing) {el('audioDeviceStatus').textContent='Detén la grabación antes de cambiar dispositivos.';return;}
    busy=true;
    try {
      const r=await window.pywebview.api.select_audio_devices(Number(el('audioInput').value),Number(el('audioOutput').value));
      if(!r.ok) throw new Error(r.error);
      el('audioDeviceStatus').textContent='Dispositivos aplicados para la próxima grabación.';
      await loadBackendStatus();
    } catch(e) {el('audioDeviceStatus').textContent=e.message;}
    finally {busy=false;}
  }
  el('audioInput').onchange=apply;
  el('audioOutput').onchange=apply;
  setInterval(()=>{if(state.activeView==='settings' && document.activeElement?.tagName!=='SELECT') refresh(true);},5000);
  window.addEventListener('pywebviewready',()=>refresh());
  navigator.mediaDevices?.addEventListener('devicechange',()=>refresh(true));
  document.querySelector('[data-view-target=settings]').addEventListener('click',()=>refresh(true));
  refresh();
})();

