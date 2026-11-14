(() => {
  const box = document.getElementById('hideGuide');
  const notice = document.getElementById('guideNotice');
  document.getElementById('guideLibrary').onclick = () => setActiveView('library');
  let connected = false;
  async function initialize() {
    const api = window.pywebview?.api;
    if (connected || !api?.guide_hidden) return;
    connected = true;
    try {
      box.checked = await api.guide_hidden();
      box.disabled = false;
      const seen = await api.tutorial_seen();
      if (!seen && window.tutorial.start()) {
        await api.mark_tutorial_seen();
      } else if (!box.checked && state.activeView === 'library') {
        setActiveView('guide');
      }
    } catch {
      notice.textContent = 'No se pudo leer la preferencia de inicio.';
    }
    box.onchange = async () => {
      const requested = box.checked;
      box.disabled = true;
      try {
        box.checked = await api.set_guide_hidden(requested);
        notice.textContent = 'Preferencia guardada.';
      } catch {
        box.checked = !requested;
        notice.textContent = 'No se pudo guardar el cambio.';
      } finally {
        box.disabled = false;
      }
    };
  }
  window.addEventListener('pywebviewready', initialize);
  initialize();
})();
