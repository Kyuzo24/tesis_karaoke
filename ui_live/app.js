let songs = [];
let takes = [];
let backendReady = false;
let backendLoading = false;
const PATH_GAP_BREAK_SECONDS = 0.65;
const BACKEND_POLL_MS = 90;
// Interpolate briefly between updates, never run away from confirmed audio time.
const LIVE_MAX_EXTRAPOLATION_SECONDS = 0.3;
const NOTE_STALE_SECONDS = 0.45;
const LIVE_RENDER_MS = 50;
const LIVE_MAX_POINTS = 3500;
const LIVE_KEEP_SECONDS = 90;
const PLOT_LEFT = 70;
const PLOT_RIGHT = 1150;
const PLOT_TOP = 56;
const PLOT_BOTTOM = 486;
const PLAYHEAD_VIEW_RATIO = 0.65;
const REFERENCE_BLOCK_HALF_STEPS = 0.45;
const USER_BLOCK_HALF_STEPS = 0.46;
const USER_GOOD_CENTS = 50;
const USER_NEAR_CENTS = 100;
const REFERENCE_TIME_TOLERANCE_SECONDS = 0.45;
const USER_BLOCK_GAP_SECONDS = 0.28;
const PITCH_LINE_JUMP_BREAK_STEPS = 5;

const state = {
  selectedIndex: 0,
  selectedTakeIndex: -1,
  activeView: "library",
  noteNotation: "es",
  theme: "dark",
  pendingSongFile: null,
  playing: false,
  takePlaying: false,
  catalogWorking: false,
  backgroundPreparing: false,
  reprocessing: false,
  diagnosticLoading: false,
  detail: false,
  overview: false,
  current: 0,
  viewStart: 0,
  viewWindow: 12,
  yMin: 57,
  yMax: 72,
  userPoints: [],
  referenceDiagnostic: null,
  referenceDiagnosticError: "",
  animationId: null,
  takeAnimationId: null,
  pollId: null,
  pollingBackend: false,
  sessionStatus: "idle",
  backendCurrent: 0,
  backendPollAt: null,
  lastChartPaintAt: 0,
  lastUserPitchAt: null,
  currentNoteMidi: null,
  voiceMuted: false,
  trackMuted: false,
  syncOffsetMs: 0,
  visualOffsetMs: 0,
  gridYMin: null,
  gridYMax: null
};

const els = {
  navButtons: Array.from(document.querySelectorAll("[data-view-target]")),
  viewPanels: Array.from(document.querySelectorAll("[data-view-panel]")),
  chartModule: document.getElementById("chartModule"),
  takePlayer: document.getElementById("takePlayer"),
  moduleDock: document.getElementById("moduleDock"),
  practiceChartMount: document.getElementById("practiceChartMount"),
  resultChartMount: document.getElementById("resultChartMount"),
  historyChartMount: document.getElementById("historyChartMount"),
  resultPlayerMount: document.getElementById("resultPlayerMount"),
  historyPlayerMount: document.getElementById("historyPlayerMount"),
  selectedSongMini: document.getElementById("selectedSongMini"),
  selectedSongMiniMeta: document.getElementById("selectedSongMiniMeta"),
  librarySongTitle: document.getElementById("librarySongTitle"),
  librarySongMeta: document.getElementById("librarySongMeta"),
  libraryPracticeButton: document.getElementById("libraryPracticeButton"),
  songList: document.getElementById("songList"),
  takeList: document.getElementById("takeList"),
  artistLabel: document.getElementById("artistLabel"),
  songTitle: document.getElementById("songTitle"),
  notationToggleButton: document.getElementById("notationToggleButton"),
  songModal: document.getElementById("songModal"),
  songModalForm: document.getElementById("songModalForm"),
  songModalEyebrow: document.getElementById("songModalEyebrow"),
  songModalTitle: document.getElementById("songModalTitle"),
  songModalFileName: document.getElementById("songModalFileName"),
  songTitleInput: document.getElementById("songTitleInput"),
  songArtistInput: document.getElementById("songArtistInput"),
  songModalError: document.getElementById("songModalError"),
  songModalCancel: document.getElementById("songModalCancel"),
  songModalCancelX: document.getElementById("songModalCancelX"),
  songModalSubmit: document.getElementById("songModalSubmit"),
  statusDot: document.getElementById("statusDot"),
  statusLabel: document.getElementById("statusLabel"),
  currentTime: document.getElementById("currentTime"),
  durationTime: document.getElementById("durationTime"),
  currentNote: document.getElementById("currentNote"),
  averageError: document.getElementById("averageError"),
  chartShell: document.getElementById("chartShell"),
  noteRuler: document.getElementById("noteRuler"),
  gridLayer: document.getElementById("gridLayer"),
  referenceBlockLayer: document.getElementById("referenceBlockLayer"),
  referencePath: document.getElementById("referencePath"),
  userBlockLayer: document.getElementById("userBlockLayer"),
  userSegmentLayer: document.getElementById("userSegmentLayer"),
  userPath: document.getElementById("userPath"),
  cursorLine: document.getElementById("cursorLine"),
  timelineFill: document.getElementById("timelineFill"),
  visualOffset: document.getElementById("visualOffset"),
  visualOffsetLabel: document.getElementById("visualOffsetLabel"),
  visualAutoAlignButton: document.getElementById("visualAutoAlignButton"),
  visualOffsetResetButton: document.getElementById("visualOffsetResetButton"),
  addButton: document.getElementById("addButton"),
  startButton: document.getElementById("startButton"),
  stopButton: document.getElementById("stopButton"),
  detailButton: document.getElementById("detailButton"),
  fullButton: document.getElementById("fullButton"),
  selectedTakeLabel: document.getElementById("selectedTakeLabel"),
  takeTimeLabel: document.getElementById("takeTimeLabel"),
  takePlayButton: document.getElementById("takePlayButton"),
  takeStopButton: document.getElementById("takeStopButton"),
  takeRenameButton: document.getElementById("takeRenameButton"),
  takeFavoriteButton: document.getElementById("takeFavoriteButton"),
  takeDeleteButton: document.getElementById("takeDeleteButton"),
  voiceMuteButton: document.getElementById("voiceMuteButton"),
  trackMuteButton: document.getElementById("trackMuteButton"),
  voiceVolume: document.getElementById("voiceVolume"),
  trackVolume: document.getElementById("trackVolume"),
  syncOffset: document.getElementById("syncOffset"),
  syncOffsetLabel: document.getElementById("syncOffsetLabel"),
  detailX: document.getElementById("detailX"),
  detailY: document.getElementById("detailY"),
  notationSelect: document.getElementById("notationSelect"),
  themeToggleButton: document.getElementById("themeToggleButton"),
  metricTight: document.getElementById("metricTight"),
  metricLoose: document.getElementById("metricLoose"),
  metricTrend: document.getElementById("metricTrend"),
  metricPoints: document.getElementById("metricPoints"),
  metricTightNote: document.getElementById("metricTightNote"),
  metricLooseNote: document.getElementById("metricLooseNote"),
  metricTrendNote: document.getElementById("metricTrendNote"),
  metricPointsNote: document.getElementById("metricPointsNote"),
  inputDeviceLabel: document.getElementById("inputDeviceLabel"),
  outputDeviceLabel: document.getElementById("outputDeviceLabel"),
  noiseLabel: document.getElementById("noiseLabel"),
  rejectLabel: document.getElementById("rejectLabel"),
  referenceDiagnosticButton: document.getElementById("referenceDiagnosticButton"),
  diagnosticStatus: document.getElementById("diagnosticStatus"),
  diagnosticRawCount: document.getElementById("diagnosticRawCount"),
  diagnosticFilteredCount: document.getElementById("diagnosticFilteredCount"),
  diagnosticCorrectedCount: document.getElementById("diagnosticCorrectedCount"),
  diagnosticOctaveCount: document.getElementById("diagnosticOctaveCount"),
  diagnosticGridLayer: document.getElementById("diagnosticGridLayer"),
  diagnosticRawPath: document.getElementById("diagnosticRawPath"),
  diagnosticFilteredPath: document.getElementById("diagnosticFilteredPath"),
  diagnosticCorrectedPath: document.getElementById("diagnosticCorrectedPath"),
  diagnosticEmpty: document.getElementById("diagnosticEmpty"),
  genericModal: document.getElementById("genericModal"),
  genericModalForm: document.getElementById("genericModalForm"),
  genericModalEyebrow: document.getElementById("genericModalEyebrow"),
  genericModalTitle: document.getElementById("genericModalTitle"),
  genericModalMessage: document.getElementById("genericModalMessage"),
  genericModalInputRow: document.getElementById("genericModalInputRow"),
  genericModalInputLabel: document.getElementById("genericModalInputLabel"),
  genericModalInput: document.getElementById("genericModalInput"),
  genericModalError: document.getElementById("genericModalError"),
  genericModalCancel: document.getElementById("genericModalCancel"),
  genericModalCancelX: document.getElementById("genericModalCancelX"),
  genericModalSubmit: document.getElementById("genericModalSubmit")
};

const voiceAudio = new Audio();
const trackAudio = new Audio();
voiceAudio.preload = "auto";
trackAudio.preload = "auto";

const referenceBlockCache = {
  source: null,
  blocks: []
};

const referencePointCache = {
  source: null,
  points: []
};

const viewMeta = {
  guide: {title: "Guía de uso", eyebrow: "Karaoke Studio"},
  library: {
    title: "Biblioteca",
    eyebrow: "Canciones"
  },
  practice: {
    title: "Practicar",
    eyebrow: "Referencia y voz"
  },
  result: {
    title: "Resultado",
    eyebrow: "Ultima toma"
  },
  history: {
    title: "Historial",
    eyebrow: "Tomas guardadas"
  },
  diagnostics: {
    title: "Diagnostico",
    eyebrow: "Referencia vocal"
  },
  settings: {
    title: "Ajustes",
    eyebrow: "Audio y deteccion"
  }
};

function loadNotationPreference() {
  let saved = "es";
  try {
    saved = window.localStorage.getItem("karaoke_note_notation") || "es";
  } catch (_error) {
    saved = "es";
  }

  state.noteNotation = saved === "en" ? "en" : "es";
  updateNotationControls();
}

function notationLabel() {
  return state.noteNotation === "en" ? "Notas: C, D, E ⇄" : "Notas: Do, Re, Mi ⇄";
}

function updateNotationControls() {
  els.notationSelect.value = state.noteNotation;
  els.notationToggleButton.textContent = notationLabel();
  const next = state.noteNotation === "en" ? "Do, Re, Mi" : "C, D, E";
  els.notationToggleButton.title = `Cambiar los nombres de las notas a ${next}`;
  els.notationToggleButton.setAttribute('aria-label', `${notationLabel().replace(' ⇄','')}. Cambiar a ${next}`);
}

function setNoteNotation(notation, persist = true) {
  const next = notation === "en" ? "en" : "es";
  if (state.noteNotation === next) {
    updateNotationControls();
    return;
  }

  state.noteNotation = next;
  if (persist) {
    try {
      window.localStorage.setItem("karaoke_note_notation", state.noteNotation);
    } catch (_error) {
      // Local files can run without localStorage in some embedded browsers.
    }
  }

  state.gridYMin = null;
  state.gridYMax = null;
  updateNotationControls();
  updateCurrentNoteLabel();
  renderChart();
  renderReferenceDiagnostic();
}

function saveNotationPreference() {
  setNoteNotation(els.notationSelect.value);
}

function toggleNoteNotation() {
  setNoteNotation(state.noteNotation === "en" ? "es" : "en");
}

function loadThemePreference() {
  let saved = "dark";
  try {
    saved = window.localStorage.getItem("karaoke_theme") || "dark";
  } catch (_error) {
    saved = "dark";
  }

  setTheme(saved === "light" ? "light" : "dark", false);
}

function updateThemeControls() {
  const isLight = state.theme === "light";
  document.body.dataset.theme = state.theme;
  els.themeToggleButton.textContent = isLight ? "Tema claro" : "Tema oscuro";
  els.themeToggleButton.title = isLight ? "Cambiar a tema oscuro" : "Cambiar a tema claro";
}

function setTheme(theme, persist = true) {
  state.theme = theme === "light" ? "light" : "dark";
  if (persist) {
    try {
      window.localStorage.setItem("karaoke_theme", state.theme);
    } catch (_error) {
      // Local files can run without localStorage in some embedded browsers.
    }
  }
  updateThemeControls();
}

function toggleTheme() {
  setTheme(state.theme === "light" ? "dark" : "light");
}

function loadVisualOffsetPreference() {
  let saved = 0;
  try {
    saved = Number(window.localStorage.getItem("karaoke_visual_offset_ms") || 0);
  } catch (_error) {
    saved = 0;
  }
  setVisualOffset(saved, false);
}

function setVisualOffset(value, persist = true) {
  const min = Number(els.visualOffset.min || -700);
  const max = Number(els.visualOffset.max || 700);
  const next = Math.max(min, Math.min(max, Math.round(Number(value || 0))));
  state.visualOffsetMs = next;
  els.visualOffset.value = String(next);
  updateVisualOffsetLabel();

  if (persist) {
    try {
      window.localStorage.setItem("karaoke_visual_offset_ms", String(next));
    } catch (_error) {
      // Local files can run without localStorage in some embedded browsers.
    }
  }
}

function updateVisualOffsetLabel() {
  const value = state.visualOffsetMs;
  const sign = value > 0 ? "+" : "";
  els.visualOffsetLabel.textContent = `${sign}${value} ms`;
}

function updateCurrentNoteLabel() {
  if (state.currentNoteMidi == null) {
    els.currentNote.textContent = "--";
    return;
  }
  els.currentNote.textContent = noteName(state.currentNoteMidi);
}

function resetReferenceBlockCache() {
  referenceBlockCache.source = null;
  referenceBlockCache.blocks = [];
  referencePointCache.source = null;
  referencePointCache.points = [];
}

function resetReferenceDiagnostic() {
  state.referenceDiagnostic = null;
  state.referenceDiagnosticError = "";
  state.diagnosticLoading = false;
  renderReferenceDiagnostic();
}

function setActiveView(view) {
  if (!viewMeta[view]) return;

  const reviewViews = ["result", "history"];
  if (state.takePlaying && !reviewViews.includes(view)) {
    pauseTakePlayback();
  }

  state.activeView = view;
  if (reviewViews.includes(view) && state.selectedTakeIndex < 0 && takes.length) {
    state.selectedTakeIndex = 0;
    loadSelectedTakeIntoChart();
    loadTakeAudio(selectedTake());
    renderTakes();
  }

  document.body.dataset.view = view;
  els.navButtons.forEach((button) => {
    button.classList.toggle("is-active", button.dataset.viewTarget === view);
  });
  els.viewPanels.forEach((panel) => {
    panel.classList.toggle("is-active", panel.dataset.viewPanel === view);
  });

  mountSharedModules();
  updateTopbar();
  renderChart();
  updateTakePlayer();
}

function mountSharedModules() {
  const chartTargets = {
    practice: els.practiceChartMount,
    result: els.resultChartMount,
    history: els.historyChartMount
  };
  const chartTarget = chartTargets[state.activeView] || els.moduleDock;
  if (chartTarget && els.chartModule.parentElement !== chartTarget) {
    chartTarget.appendChild(els.chartModule);
  }

  const playerTargets = {
    result: els.resultPlayerMount,
    history: els.historyPlayerMount
  };
  const playerTarget = playerTargets[state.activeView] || els.moduleDock;
  if (playerTarget && els.takePlayer.parentElement !== playerTarget) {
    playerTarget.appendChild(els.takePlayer);
  }
}

function updateTopbar() {
  const song = currentSong();
  const meta = viewMeta[state.activeView] || viewMeta.practice;
  els.artistLabel.textContent = meta.eyebrow;

  if (state.activeView === "practice" && song) {
    els.artistLabel.textContent = song.artist;
    els.songTitle.textContent = song.title;
    return;
  }

  if ((state.activeView === "result" || state.activeView === "history") && song) {
    els.artistLabel.textContent = `${song.artist} / ${song.title}`;
  }

  els.songTitle.textContent = meta.title;
}

function updateLibrarySummary() {
  const song = currentSong();
  if (!song) {
    els.selectedSongMini.textContent = "Sin canciones";
    els.selectedSongMiniMeta.textContent = "Catalogo vacio";
    els.librarySongTitle.textContent = "Sin cancion seleccionada";
    els.librarySongMeta.textContent = "Agrega una cancion para comenzar.";
    els.libraryPracticeButton.disabled = true;
    return;
  }

  els.selectedSongMini.textContent = song.title;
  els.selectedSongMiniMeta.textContent = `${song.artist} / ${formatTime(song.duration)}`;
  els.librarySongTitle.textContent = song.title;
  els.librarySongMeta.textContent = `${song.artist} / ${formatTime(song.duration)} / ${song.prepared ? "Lista" : "Sin procesar"} / ${song.lyrics?.lines?.length ? "Con letra" : "Sin letra"}`;
  els.libraryPracticeButton.disabled = !backendReady || state.catalogWorking || !song.prepared || !song.id;
}

function normalizeBackendSongs(backendSongs) {
  if (!Array.isArray(backendSongs)) return [];
  return backendSongs.map((song) => ({
    id: song.id,
    title: song.title || "Sin titulo",
    artist: song.artist || "Sin artista",
    duration: Number(song.duration || 0),
    prepared: Boolean(song.prepared),
    lyrics: song.lyrics || null,
    points: Array.isArray(song.points) ? song.points : []
  }));
}

function normalizeBackendTakes(backendTakes) {
  if (!Array.isArray(backendTakes)) return [];
  return backendTakes.map((take) => ({
    id: take.id,
    songId: take.song_id,
    name: take.name || "",
    favorite: Boolean(take.favorite),
    createdAt: take.created_at || "",
    duration: Number(take.duration || 0),
    voiceUrl: take.voice_url || "",
    instrumentalUrl: take.instrumental_url || "",
    metrics: take.metrics || {},
    pointsRef: Array.isArray(take.points_ref) ? take.points_ref : [],
    pointsUser: Array.isArray(take.points_user) ? take.points_user : [],
    previewRef: Array.isArray(take.preview_ref) ? take.preview_ref : [],
    previewUser: Array.isArray(take.preview_user) ? take.preview_user : []
  }));
}

function hasBackendApi() {
  return Boolean(window.pywebview?.api?.get_songs);
}

async function loadBackendSongs() {
  if (!hasBackendApi()) return false;
  if (backendLoading) return false;

  backendLoading = true;
  backendReady = true;
  setStatus("Cargando catalogo", false);
  try {
    await loadBackendStatus();
    songs = normalizeBackendSongs(await window.pywebview.api.get_songs());
    state.selectedIndex = 0;
    state.selectedTakeIndex = -1;
    state.current = 0;
    state.userPoints = [];
    state.referenceDiagnostic = null;
    state.referenceDiagnosticError = "";
    resetReferenceBlockCache();
    renderSongs();
    if (!songs.length && state.activeView !== "guide" && !window.tutorial?.active) {
      setActiveView("library");
    }
    await loadTakesForCurrentSong();
    updateSongLabels();
    renderChart();
    return true;
  } catch (error) {
    backendReady = false;
    setStatus(`Error: ${error}`, false);
    return false;
  } finally {
    backendLoading = false;
  }
}

async function loadTakesForCurrentSong(selectLatest = false) {
  const song = currentSong();
  takes = [];
  state.selectedTakeIndex = -1;
  resetReferenceBlockCache();
  stopTakePlayback();
  renderTakes();
  updateTakePlayer();

  if (!backendReady || !song?.id || !window.pywebview?.api?.get_takes) {
    return;
  }

  try {
    const response = await window.pywebview.api.get_takes(song.id);
    if(currentSong()?.id!==song.id) return;
    if (response && response.ok === false) {
      throw new Error(response.error || "No se pudieron cargar las tomas.");
    }
    takes = normalizeBackendTakes(response);
    if (selectLatest && takes.length) {
      state.selectedTakeIndex = 0;
      loadSelectedTakeIntoChart();
    }
    renderTakes();
    updateTakePlayer();
  } catch (error) {
    setStatus(`Error: ${String(error.message || error)}`, false);
  }
}

async function loadBackendStatus() {
  if (!window.pywebview?.api?.get_status) return;

  const status = await window.pywebview.api.get_status();
  els.inputDeviceLabel.textContent = status.input_device || "No detectado";
  els.outputDeviceLabel.textContent = status.output_device || "No detectado";
}

function connectBackend(attempt = 0) {
  if (backendReady || backendLoading) return;

  if (hasBackendApi()) {
    loadBackendSongs();
    return;
  }

  if (attempt < 60) {
    window.setTimeout(() => connectBackend(attempt + 1), 100);
    return;
  }

  backendReady = false;
  songs = [];
  els.inputDeviceLabel.textContent = "Backend no conectado";
  els.outputDeviceLabel.textContent = "Backend no conectado";
  renderSongs();
  updateSongLabels();
  setStatus("Abre la app con iniciar_live.bat", false);
}

function renderSongs() {
  window.libraryUI?.render();
  els.songList.innerHTML = "";

  if (!songs.length) {
    els.songList.innerHTML = `
      <div class="empty-state">
        ${backendReady ? "No hay canciones cargadas en el catalogo." : "Conectando con el backend Python..."}
      </div>
    `;
    return;
  }

  const entries=window.libraryUI ? window.libraryUI.entries() : songs.map((song,index)=>({song,index}));
  if(!entries.length) els.songList.textContent='Esta colección todavía no tiene canciones.';
  entries.forEach(({song, index}) => {
    const button = document.createElement("button");
    button.className = `song-card${index === state.selectedIndex ? " is-active" : ""}`;
    button.type = "button";
    button.disabled = state.playing || (state.catalogWorking && !state.backgroundPreparing);
    button.innerHTML = `
      <div class="song-title">${escapeHtml(song.title)}</div>
      <div class="song-artist">${escapeHtml(song.artist)}</div>
      <div class="song-meta">
        <span>${formatTime(song.duration)}</span>
        <span>${song.prepared ? "Lista" : "Sin procesar"}</span>
        <span>${song.lyrics?.lines?.length ? "♫ Con letra" : "Sin letra"}</span>
      </div>
    `;
    button.addEventListener("click", () => selectSong(index));
    const row=document.createElement('div');row.className='song-row';
    const actions=document.createElement('div');actions.className='song-row-actions';
    for(const [symbol,label,run] of [['✎','Editar',editSelectedSong],['↻','Reprocesar',reprocessSelectedSong],['⌫','Eliminar',deleteSelectedSong]]) {
      const action=document.createElement('button');action.type='button';action.className='button song-action';
      action.textContent=symbol;action.title=`${label} canción`;action.setAttribute('aria-label',`${label} ${song.title}`);
      action.disabled=state.playing||state.catalogWorking;
      if(label==='Eliminar') action.classList.add('song-action-danger');
      action.onclick=()=>{selectSong(index);run();};actions.append(action);
    }
    row.append(button,actions);els.songList.appendChild(row);
  });
}

function renderTakes() {
  els.takeList.innerHTML = "";

  if (!currentSong()) {
    els.takeList.innerHTML = `<div class="empty-state">Selecciona una cancion.</div>`;
    return;
  }

  if (!takes.length) {
    els.takeList.innerHTML = `<div class="empty-state">Aun no hay tomas guardadas.</div>`;
    return;
  }

  takes.forEach((take, index) => {
    const button = document.createElement("button");
    button.className = `take-card${index === state.selectedTakeIndex ? " is-active" : ""}`;
    button.type = "button";
    button.disabled = state.playing || (state.catalogWorking && !state.backgroundPreparing);
    const displayName = takeDisplayName(take);
    const dateLabel = formatTakeDate(take.createdAt);
    button.innerHTML = `
      <div class="take-card-head">
        <strong>${escapeHtml(displayName)}</strong>
        <span>${formatTime(take.duration)}</span>
      </div>
      <div class="take-card-meta">
        <span>${escapeHtml(dateLabel)}</span>
        ${take.favorite ? `<span class="take-favorite-badge">Favorita</span>` : ""}
      </div>
      ${takePreviewSvg(take)}
      <div class="take-card-note">${takeShortSummary(take.metrics)}</div>
    `;
    button.addEventListener("click", () => selectTake(index));
    els.takeList.appendChild(button);
  });
}

function takeDisplayName(take) {
  return take?.name?.trim() || formatTakeDate(take?.createdAt);
}

function takePreviewSvg(take) {
  const domain = previewMidiDomain([...take.previewRef, ...take.previewUser]);
  const refPath = previewPath(take.previewRef, take.duration, domain);
  const userPath = previewPath(take.previewUser, take.duration, domain);
  return `
    <svg class="take-preview" viewBox="0 0 220 54" aria-hidden="true">
      <path class="take-preview-ref" d="${refPath}"></path>
      <path class="take-preview-user" d="${userPath}"></path>
    </svg>
  `;
}

function previewMidiDomain(points) {
  if (!points?.length) return "";

  const midiValues = points.map(([, midi]) => midi).filter((midi) => Number.isFinite(midi));
  if (!midiValues.length) return null;

  return {
    minMidi: Math.min(...midiValues) - 1,
    maxMidi: Math.max(...midiValues) + 1
  };
}

function previewPath(points, duration, domain) {
  if (!points?.length || !domain) return "";

  const { minMidi, maxMidi } = domain;
  const span = Math.max(1, maxMidi - minMidi);
  const safeDuration = Math.max(1, duration || points[points.length - 1]?.[0] || 1);

  return points.map(([time, midi], index) => {
    const previous = points[index - 1];
    const startsSegment = !previous || time - previous[0] > PATH_GAP_BREAK_SECONDS;
    const x = (time / safeDuration) * 220;
    const y = 48 - ((midi - minMidi) / span) * 42;
    return `${startsSegment ? "M" : "L"} ${x.toFixed(1)} ${y.toFixed(1)}`;
  }).join(" ");
}

async function loadReferenceDiagnostics() {
  const song = currentSong();
  if (!song || state.playing || state.catalogWorking || state.diagnosticLoading) return;
  const songId = song.id;

  if (!backendReady || !window.pywebview?.api?.get_reference_diagnostics) {
    setStatus("Backend no conectado", false);
    return;
  }

  state.diagnosticLoading = true;
  state.referenceDiagnosticError = "";
  renderReferenceDiagnostic();
  setStatus("Analizando referencia", true);

  try {
    const response = await window.pywebview.api.get_reference_diagnostics(songId);
    if (currentSong()?.id !== songId) return;
    if (!response.ok) {
      throw new Error(response.error || "No se pudo diagnosticar la referencia.");
    }
    state.referenceDiagnostic = response.diagnostic || null;
    state.referenceDiagnosticError = "";
    renderReferenceDiagnostic();
    setStatus("Diagnostico listo", false);
  } catch (error) {
    state.referenceDiagnostic = null;
    state.referenceDiagnosticError = String(error.message || error);
    setStatus(`Error: ${state.referenceDiagnosticError}`, false);
  } finally {
    state.diagnosticLoading = false;
    renderReferenceDiagnostic();
  }
}

function renderReferenceDiagnostic() {
  if (!els.referenceDiagnosticButton) return;

  const song = currentSong();
  els.referenceDiagnosticButton.disabled = !backendReady || state.playing || state.catalogWorking || state.diagnosticLoading || !song?.prepared;

  if (state.diagnosticLoading) {
    els.diagnosticStatus.textContent = "Analizando la voz separada...";
    return;
  }

  const diagnostic = state.referenceDiagnostic;
  if (!diagnostic || state.referenceDiagnosticError) {
    els.diagnosticRawCount.textContent = "--";
    els.diagnosticFilteredCount.textContent = "--";
    els.diagnosticCorrectedCount.textContent = "--";
    els.diagnosticOctaveCount.textContent = "--";
    els.diagnosticRawPath.setAttribute("d", "");
    els.diagnosticFilteredPath.setAttribute("d", "");
    els.diagnosticCorrectedPath.setAttribute("d", "");
    els.diagnosticGridLayer.innerHTML = "";
    els.diagnosticEmpty.classList.remove("is-hidden");
    els.diagnosticStatus.textContent = state.referenceDiagnosticError || "Analiza la referencia para revisar que notas se pierden o se corrigen.";
    return;
  }

  els.diagnosticRawCount.textContent = formatCount(diagnostic.raw_count);
  els.diagnosticFilteredCount.textContent = formatCount(diagnostic.filtered_count);
  els.diagnosticCorrectedCount.textContent = formatCount(diagnostic.corrected_count);
  els.diagnosticOctaveCount.textContent = formatCount(diagnostic.octave_corrections);
  els.diagnosticStatus.textContent = `${Number(diagnostic.retention || 0).toFixed(0)}% de puntos crudos quedaron tras el filtrado.`;
  els.diagnosticEmpty.classList.add("is-hidden");

  const domain = diagnosticChartDomain(diagnostic);
  renderDiagnosticGrid(domain);
  els.diagnosticRawPath.setAttribute("d", diagnosticPitchPath(diagnostic.points_raw, domain, 0.24));
  els.diagnosticFilteredPath.setAttribute("d", diagnosticPitchPath(diagnostic.points_filtered, domain, PATH_GAP_BREAK_SECONDS));
  els.diagnosticCorrectedPath.setAttribute("d", diagnosticPitchPath(diagnostic.points_corrected, domain, PATH_GAP_BREAK_SECONDS));
}

function formatCount(value) {
  const number = Number(value || 0);
  return number.toLocaleString("es-CL");
}

function diagnosticChartDomain(diagnostic) {
  const preferredPoints = [
    ...(diagnostic.points_filtered || []),
    ...(diagnostic.points_corrected || [])
  ].filter(([, midi]) => Number.isFinite(midi));
  const allPoints = preferredPoints.length ? preferredPoints : (diagnostic.points_raw || []).filter(([, midi]) => Number.isFinite(midi));
  const times = allPoints.map(([time]) => Number(time || 0));
  const notes = allPoints.map(([, midi]) => midi);
  const noteCenter = notes.length ? median(notes) : 60;

  return {
    xMin: 0,
    xMax: Math.max(1, Math.max(...times, currentSong()?.duration || 1)),
    yMin: notes.length ? Math.floor(Math.min(percentile(notes, 0.01), noteCenter - 7)) - 1 : 48,
    yMax: notes.length ? Math.ceil(Math.max(percentile(notes, 0.99), noteCenter + 7)) + 1 : 72
  };
}

function diagnosticX(time, domain) {
  return 64 + ((time - domain.xMin) / (domain.xMax - domain.xMin)) * 1096;
}

function diagnosticY(midi, domain) {
  return 386 - ((midi - domain.yMin) / Math.max(1, domain.yMax - domain.yMin)) * 326;
}

function renderDiagnosticGrid(domain) {
  els.diagnosticGridLayer.innerHTML = "";
  const labelStep = domain.yMax - domain.yMin > 24 ? 2 : 1;
  for (let midi = Math.ceil(domain.yMin); midi <= Math.floor(domain.yMax); midi += 1) {
    const y = diagnosticY(midi, domain);
    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("class", "diagnostic-grid-line");
    line.setAttribute("x1", "64");
    line.setAttribute("x2", "1160");
    line.setAttribute("y1", y.toFixed(1));
    line.setAttribute("y2", y.toFixed(1));
    els.diagnosticGridLayer.appendChild(line);

    if (Math.abs(midi) % labelStep !== 0) continue;
    const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
    label.setAttribute("class", "diagnostic-note-label");
    label.setAttribute("x", "16");
    label.setAttribute("y", (y + 4).toFixed(1));
    label.textContent = noteName(midi);
    els.diagnosticGridLayer.appendChild(label);
  }
}

function diagnosticPitchPath(points, domain, gapBreak) {
  if (!Array.isArray(points) || !points.length) return "";

  const commands = [];
  points.forEach(([time, midi], index) => {
    if (!Number.isFinite(time) || !Number.isFinite(midi)) return;
    const previous = points[index - 1];
    const startsSegment = !previous ||
      time - previous[0] > gapBreak ||
      Math.abs(midi - previous[1]) > PITCH_LINE_JUMP_BREAK_STEPS;
    commands.push(`${startsSegment ? "M" : "L"} ${diagnosticX(time, domain).toFixed(1)} ${diagnosticY(midi, domain).toFixed(1)}`);
  });
  return commands.join(" ");
}

function takeShortSummary(metrics) {
  return 'Ver afinación y cobertura por notas';
}

function formatTakeDate(value) {
  if (!value) return "Toma guardada";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("es-CL", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  });
}

function selectSong(index) {
  if (state.playing || (state.catalogWorking && !state.backgroundPreparing)) return;
  stopTakePlayback();
  state.selectedIndex = index;
  state.selectedTakeIndex = -1;
  state.current = 0;
  state.backendCurrent = 0;
  state.viewStart = 0;
  state.detail = false;
  state.overview = false;
  state.userPoints = [];
  state.lastUserPitchAt = null;
  state.gridYMin = null;
  state.gridYMax = null;
  resetReferenceBlockCache();
  resetReferenceDiagnostic();
  updateSongLabels();
  renderSongs();
  renderChart();
  loadTakesForCurrentSong();
}

function updateSongLabels() {
  const song = currentSong();
  resetMetrics();
  els.chartShell.classList.remove("is-detail");
  els.fullButton.classList.add("hidden");
  els.detailButton.classList.remove("hidden");
  els.detailButton.disabled = true;
  els.stopButton.disabled = true;
  updateCatalogButtons();

  if (!song) {
    els.durationTime.textContent = "0:00";
    els.currentTime.textContent = "0:00";
    els.startButton.disabled = true;
    updateCatalogButtons();
    updateTopbar();
    updateLibrarySummary();
    setStatus(backendReady ? "Agrega una cancion para comenzar" : "Conectando backend", false);
    updateChartModeButtons();
    return;
  }

  els.durationTime.textContent = formatTime(song.duration);
  els.currentTime.textContent = formatTime(state.current);
  els.startButton.disabled = !backendReady || state.catalogWorking || !song.prepared || !song.id;
  updateCatalogButtons();
  updateTopbar();
  updateLibrarySummary();
  setStatus(song.prepared ? "Listo" : "Sin procesar", false);
  updateChartModeButtons();
}

function updateCatalogButtons() {
  const song = currentSong();
  const busy = state.playing || state.catalogWorking;
  els.addButton.disabled = !backendReady || busy;
  els.libraryPracticeButton.disabled = !backendReady || busy || !song?.prepared || !song?.id;
  renderReferenceDiagnostic();
}

function currentSong() {
  return songs[state.selectedIndex] || null;
}

function selectedTake() {
  return takes[state.selectedTakeIndex] || null;
}

function referencePoints() {
  const musical = window.feedbackUI?.analysis?.()?.musical;
  if (musical) return musical.notas.flatMap(n => [[n.referencia.inicio_s,n.referencia.midi],[n.referencia.fin_s,n.referencia.midi]]);
  const source = selectedTake()?.pointsRef || currentSong()?.points || [];
  if (referencePointCache.source !== source) {
    referencePointCache.source = source;
    referencePointCache.points = normalizeRegisterOctaves(source);
  }
  return referencePointCache.points;
}

function userPointsForChart() {
  return selectedTake()?.pointsUser || state.userPoints;
}

function hasReferenceForChart() {
  return Boolean(referencePoints().length);
}

function canUseChartModes() {
  const song = currentSong();
  return Boolean(song?.id && song?.prepared && hasReferenceForChart());
}

function updateChartModeButtons() {
  const canUseModes = canUseChartModes() && !state.playing && !state.catalogWorking;
  els.chartShell.classList.toggle("is-detail", state.detail);
  els.detailButton.classList.toggle("hidden", state.detail);
  els.detailButton.disabled = !canUseModes;
  els.fullButton.classList.toggle("hidden", !canUseModes);
  els.fullButton.disabled = !canUseModes;

  if (state.overview) {
    els.fullButton.textContent = "Ver seguimiento";
  } else if (state.detail && userPointsForChart().length) {
    els.fullButton.textContent = "Ver desempeno completo";
  } else {
    els.fullButton.textContent = "Ver cancion completa";
  }
}

function selectTake(index) {
  if (state.playing || (state.catalogWorking && !state.backgroundPreparing)) return;
  stopTakePlayback();
  state.selectedTakeIndex = index;
  loadSelectedTakeIntoChart();
  loadTakeAudio(selectedTake());
  renderTakes();
  updateTakePlayer();
  renderChart();
}

function loadSelectedTakeIntoChart() {
  const take = selectedTake();
  if (!take) return;

  state.current = 0;
  state.backendCurrent = 0;
  state.viewStart = 0;
  state.detail = false;
  state.overview = false;
  state.gridYMin = null;
  state.gridYMax = null;
  state.userPoints = take.pointsUser || [];
  resetReferenceBlockCache();
  els.chartShell.classList.remove("is-detail");
  els.detailButton.classList.remove("hidden");
  els.fullButton.classList.add("hidden");
  els.detailButton.disabled = !state.userPoints.length;
  updateChartModeButtons();
  renderMetrics(take.metrics || {});
}

function resetMetrics() {
  state.currentNoteMidi = null;
  els.currentNote.textContent = "--";
  els.averageError.textContent = "--";
  els.metricTight.textContent = "--";
  els.metricLoose.textContent = "--";
  els.metricTrend.textContent = "--";
  els.metricPoints.textContent = "--";
  els.metricTightNote.textContent = "--";
  els.metricLooseNote.textContent = "--";
  els.metricTrendNote.textContent = "--";
  els.metricPointsNote.textContent = "--";
  els.noiseLabel.textContent = "--";
  els.rejectLabel.textContent = "--";
}

function clearCurrentTake() {
  if (state.takePlaying) stopTakePlayback(false);
  state.selectedTakeIndex = -1;
  state.current = 0;
  state.backendCurrent = 0;
  state.viewStart = 0;
  state.detail = false;
  state.overview = false;
  state.userPoints = [];
  state.lastUserPitchAt = null;
  state.gridYMin = null;
  state.gridYMax = null;
  resetReferenceBlockCache();
  els.chartShell.classList.remove("is-detail");
  els.detailButton.classList.remove("hidden");
  els.fullButton.classList.add("hidden");
  els.detailButton.disabled = true;
  updateChartModeButtons();
  resetMetrics();
}

function setStatus(text, recording) {
  els.statusLabel.textContent = text;
  els.statusDot.classList.toggle("is-recording", Boolean(recording));
}

function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function formatTime(seconds) {
  const safe = Math.max(0, Number(seconds || 0));
  const minutes = Math.floor(safe / 60);
  const rest = Math.floor(safe % 60).toString().padStart(2, "0");
  return `${minutes}:${rest}`;
}

function noteName(midi) {
  const spanishNames = ["Do", "Do#", "Re", "Re#", "Mi", "Fa", "Fa#", "Sol", "Sol#", "La", "La#", "Si"];
  const englishNames = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
  const names = state.noteNotation === "en" ? englishNames : spanishNames;
  const rounded = Math.round(midi);
  return `${names[((rounded % 12) + 12) % 12]}${Math.floor(rounded / 12) - 1}`;
}

function visibleDomain() {
  const duration = Math.max(state.viewWindow, currentDuration() || state.viewWindow);

  if (state.overview) {
    return {
      xMin: 0,
      xMax: duration
    };
  }

  if (state.detail) {
    return {
      xMin: state.viewStart,
      xMax: state.viewStart + state.viewWindow
    };
  }

  const xMin = Math.max(
    0,
    Math.min(duration - state.viewWindow, state.current - state.viewWindow * PLAYHEAD_VIEW_RATIO)
  );
  return {
    xMin,
    xMax: xMin + state.viewWindow
  };
}

function currentDuration() {
  return selectedTake()?.duration || currentSong()?.duration || 0;
}

function xScale(time) {
  const domain = visibleDomain();
  return PLOT_LEFT + ((time - domain.xMin) / (domain.xMax - domain.xMin)) * (PLOT_RIGHT - PLOT_LEFT);
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function cursorXForDomain(domain) {
  const span = Math.max(0.001, domain.xMax - domain.xMin);
  const cursorTime = state.current - (window.feedbackUI?.analysis?.()?.desfase_ms || 0)/1000;
  const rawX = PLOT_LEFT + ((cursorTime - domain.xMin) / span) * (PLOT_RIGHT - PLOT_LEFT);
  return clamp(rawX, PLOT_LEFT, PLOT_RIGHT);
}

function yScale(midi) {
  return PLOT_BOTTOM - ((midi - state.yMin) / (state.yMax - state.yMin)) * (PLOT_BOTTOM - PLOT_TOP);
}

function updateYDomain() {
  if (state.detail) {
    const center = Number(els.detailY.value || 64);
    state.yMin = center - 7;
    state.yMax = center + 7;
    return;
  }

  const domain = visibleDomain();
  const referenceValues = [];
  const userValues = [];
  referencePoints().forEach(([time, midi]) => {
    if (Number.isFinite(time) && Number.isFinite(midi) && time >= domain.xMin - 0.5 && time <= domain.xMax + 0.5) referenceValues.push(midi);
  });
  // Long sustained notes can cross the window with both endpoints outside it.
  currentReferenceBlocks().forEach(block => {
    if (Number.isFinite(block.note) && block.end >= domain.xMin && block.start <= domain.xMax) referenceValues.push(block.note);
  });
  visibleShiftedUserPoints(domain, 0).forEach(([time, midi]) => {
    if (time >= domain.xMin && time <= domain.xMax) userValues.push(midi);
  });

  const values = referenceValues.length ? referenceValues : userValues;
  const center = values.length ? median(values) : 64;
  let min = values.length ? Math.min(percentile(values, 0.02), center - 5) : center - 5;
  let max = values.length ? Math.max(percentile(values, 0.98), center + 5) : center + 5;

  if (referenceValues.length && userValues.length) {
    const usableUserValues = userValues.filter((midi) => midi >= min - 5 && midi <= max + 5);
    if (usableUserValues.length) {
      min = Math.min(min, percentile(usableUserValues, 0.05));
      max = Math.max(max, percentile(usableUserValues, 0.95));
    }
  }

  state.yMin = Math.floor(min) - 1;
  state.yMax = Math.ceil(max) + 1;
}

function median(values) {
  const sorted = [...values].sort((a, b) => a - b);
  return sorted[Math.floor(sorted.length / 2)];
}

function percentile(values, ratio) {
  if (!values.length) return 0;
  const sorted = [...values].sort((a, b) => a - b);
  const index = Math.max(0, Math.min(sorted.length - 1, Math.round((sorted.length - 1) * ratio)));
  return sorted[index];
}

function finitePitchPoints(points) {
  return (points || [])
    .filter(([time, midi]) => Number.isFinite(time) && Number.isFinite(midi))
    .sort((a, b) => a[0] - b[0]);
}

function normalizeRegisterOctaves(points) {
  const cleanPoints = finitePitchPoints(points);
  if (cleanPoints.length < 30) return cleanPoints;

  const corrected = cleanPoints.map(([time, midi]) => [time, midi]);
  const values = cleanPoints.map(([, midi]) => midi);
  const highOctaveThreshold = Math.max(70.5, percentile(values, 0.9) + 4);
  const segments = pitchContinuitySegments(cleanPoints);

  segments.forEach((segment, index) => {
    if (segment.median < highOctaveThreshold || segment.duration > 0.9) return;
    const neighbors = neighboringSegmentMedians(segments, index, 1.5)
      .filter((note) => note < highOctaveThreshold);
    if (!neighbors.length) return;

    const currentScore = median(neighbors.map((note) => Math.abs(note - segment.median)));
    const octaveDownScore = median(neighbors.map((note) => Math.abs(note - (segment.median - 12))));
    if (currentScore >= 8 && octaveDownScore <= 5.5 && octaveDownScore + 2 < currentScore) {
      for (let i = segment.start; i < segment.end; i += 1) {
        if (corrected[i][1] >= highOctaveThreshold) corrected[i][1] -= 12;
      }
    }
  });

  return removeErraticReferenceSegments(corrected);
}

function pitchContinuitySegments(points, maxGap = 0.18, maxJump = 4.5) {
  if (!points.length) return [];

  const segments = [];
  let start = 0;
  for (let i = 1; i < points.length; i += 1) {
    const gap = points[i][0] - points[i - 1][0];
    const jump = Math.abs(points[i][1] - points[i - 1][1]);
    if (gap > maxGap || jump > maxJump) {
      segments.push(describePitchSegment(points, start, i));
      start = i;
    }
  }
  segments.push(describePitchSegment(points, start, points.length));
  return segments.filter(Boolean);
}

function describePitchSegment(points, start, end) {
  if (end <= start) return null;
  const values = points.slice(start, end).map(([, midi]) => midi);
  return {
    start,
    end,
    median: median(values),
    duration: Math.max(0, points[end - 1][0] - points[start][0]),
    startTime: points[start][0],
    endTime: points[end - 1][0]
  };
}

function neighboringSegmentMedians(segments, index, maxDistance = 1) {
  const segment = segments[index];
  const neighbors = [];

  for (let i = index - 1; i >= Math.max(0, index - 3); i -= 1) {
    const distance = Math.max(0, segment.startTime - segments[i].endTime);
    if (distance > maxDistance) break;
    neighbors.push(segments[i].median);
  }

  for (let i = index + 1; i <= Math.min(segments.length - 1, index + 3); i += 1) {
    const distance = Math.max(0, segments[i].startTime - segment.endTime);
    if (distance > maxDistance) break;
    neighbors.push(segments[i].median);
  }

  return neighbors;
}

function removeErraticReferenceSegments(points) {
  if (points.length < 30) return points;

  const values = points.map(([, midi]) => midi);
  const highOctaveThreshold = Math.max(70.5, percentile(values, 0.9) + 4);
  const segments = pitchContinuitySegments(points);
  const keep = new Array(points.length).fill(true);

  segments.forEach((segment, index) => {
    const neighbors = neighboringSegmentMedians(segments, index, 1.5);
    const neighborDistance = neighbors.length
      ? median(neighbors.map((note) => Math.abs(note - segment.median)))
      : 99;
    const veryHighAndShort = segment.median >= highOctaveThreshold + 5 && segment.duration <= 0.45 && neighborDistance >= 7;
    const tinyHighBlip = segment.median >= highOctaveThreshold && segment.duration <= 0.06 && neighborDistance >= 5;

    if (!veryHighAndShort && !tinyHighBlip) return;
    for (let i = segment.start; i < segment.end; i += 1) {
      keep[i] = false;
    }
  });

  return points.filter((_point, index) => keep[index]);
}

function lowerBoundPitch(points, targetTime) {
  let low = 0;
  let high = points.length;
  while (low < high) {
    const mid = Math.floor((low + high) / 2);
    if ((points[mid]?.[0] ?? 0) < targetTime) {
      low = mid + 1;
    } else {
      high = mid;
    }
  }
  return low;
}

function visibleShiftedUserPoints(domain, padding = 0.4) {
  const rawPoints = userPointsForChart();
  const analysis = window.feedbackUI?.analysis?.();
  const offset = analysis ? -analysis.desfase_ms / 1000 : state.visualOffsetMs / 1000;
  const rawMin = domain.xMin - padding - offset;
  const rawMax = domain.xMax + padding - offset;
  const startIndex = lowerBoundPitch(rawPoints, rawMin);
  const visible = [];

  for (let i = startIndex; i < rawPoints.length; i += 1) {
    const [time, midi] = rawPoints[i];
    if (time > rawMax) break;
    if (!Number.isFinite(time) || !Number.isFinite(midi)) continue;
    visible.push([time + offset, midi]);
  }

  return visible;
}

function trimLiveUserPoints() {
  if (!state.playing || state.userPoints.length <= LIVE_MAX_POINTS) return;
  const cutoff = Math.max(0, state.current - LIVE_KEEP_SECONDS);
  const startIndex = lowerBoundPitch(state.userPoints, cutoff);
  state.userPoints = state.userPoints.slice(startIndex);
}

function referenceBlocksFromPoints(points) {
  return noteBlocksFromPitchPoints(finitePitchPoints(points), {
    gapBreak: PATH_GAP_BREAK_SECONDS,
    maxTail: 0.18,
    mergeGap: 0.12,
    minDuration: 0.055,
    smoothRadius: 4
  });
}

function userBlocksFromPoints(points) {
  return noteBlocksFromPitchPoints(points, {
    gapBreak: USER_BLOCK_GAP_SECONDS,
    maxTail: 0.12,
    mergeGap: 0.12,
    minDuration: 0.018,
    smoothRadius: 1
  });
}

function currentReferenceBlocks() {
  const musical = window.feedbackUI?.analysis?.()?.musical;
  if (musical) return musical.notas.map(n => ({start:n.referencia.inicio_s,end:n.referencia.fin_s,note:n.referencia.midi,midi:n.referencia.midi}));
  const source = referencePoints();
  if (referenceBlockCache.source !== source) {
    referenceBlockCache.source = source;
    referenceBlockCache.blocks = referenceBlocksFromPoints(source);
  }
  return referenceBlockCache.blocks;
}

function noteBlocksFromPitchPoints(points, options) {
  const cleanPoints = points.filter(([time, midi]) => Number.isFinite(time) && Number.isFinite(midi));
  if (!cleanPoints.length) return [];

  const deltas = [];
  for (let i = 1; i < cleanPoints.length; i += 1) {
    const delta = cleanPoints[i][0] - cleanPoints[i - 1][0];
    if (delta > 0 && delta <= 0.4) deltas.push(delta);
  }

  const tail = Math.min(options.maxTail, deltas.length ? median(deltas) : options.maxTail);
  const blocks = [];
  let current = null;
  let previous = null;

  cleanPoints.forEach(([time, midi], index) => {
    const note = smoothedNoteAt(cleanPoints, index, options.smoothRadius);
    if (!current) {
      current = createNoteBlock(time, time + tail, note, midi);
      previous = { time, note };
      return;
    }

    const gap = time - previous.time;
    if (gap > options.gapBreak) {
      current.end = previous.time + tail;
      blocks.push(finalizeNoteBlock(current));
      current = createNoteBlock(time, time + tail, note, midi);
    } else if (note !== current.note) {
      const boundary = (previous.time + time) / 2;
      current.end = boundary;
      blocks.push(finalizeNoteBlock(current));
      current = createNoteBlock(boundary, time + tail, note, midi);
    } else {
      current.end = time + tail;
      current.midiSum += midi;
      current.weight += 1;
    }

    previous = { time, note };
  });

  if (current) blocks.push(finalizeNoteBlock(current));
  return mergeNoteBlocks(blocks, options.mergeGap, options.minDuration);
}

function smoothedNoteAt(points, index, radius) {
  const values = [];
  for (let i = Math.max(0, index - radius); i <= Math.min(points.length - 1, index + radius); i += 1) {
    values.push(points[i][1]);
  }
  return Math.round(median(values));
}

function createNoteBlock(start, end, note, midi) {
  return {
    start,
    end,
    note,
    midiSum: midi,
    weight: 1
  };
}

function finalizeNoteBlock(block) {
  const weight = Math.max(1, block.weight || 1);
  return {
    start: block.start,
    end: block.end,
    note: block.note,
    midi: block.midiSum / weight,
    weight
  };
}

function mergeNoteBlocks(blocks, maxGap, minDuration) {
  const merged = [];
  blocks.forEach((block) => {
    if (block.end - block.start < minDuration) return;

    const previous = merged[merged.length - 1];
    if (previous && previous.note === block.note && block.start - previous.end <= maxGap) {
      const totalWeight = (previous.weight || 1) + (block.weight || 1);
      previous.midi = ((previous.midi || previous.note) * (previous.weight || 1) + (block.midi || block.note) * (block.weight || 1)) / totalWeight;
      previous.weight = totalWeight;
      previous.end = Math.max(previous.end, block.end);
      return;
    }

    merged.push({ ...block });
  });
  return merged;
}

function buildReferenceBlockPath(blocks) {
  return buildNoteBlockPath(blocks, REFERENCE_BLOCK_HALF_STEPS);
}

function buildNoteBlockPath(blocks, halfSteps) {
  const domain = visibleDomain();
  const commands = [];

  blocks.forEach((block) => {
    if (block.end < domain.xMin || block.start > domain.xMax) return;
    if (block.note < state.yMin - 1 || block.note > state.yMax + 1) return;

    const start = Math.max(domain.xMin, block.start);
    const end = Math.min(domain.xMax, block.end);
    if (end <= start) return;

    const x1 = xScale(start);
    const x2 = xScale(end);
    const y1 = yScale(block.note + halfSteps);
    const y2 = yScale(block.note - halfSteps);
    commands.push(`M ${x1.toFixed(1)} ${y1.toFixed(1)} H ${x2.toFixed(1)} V ${y2.toFixed(1)} H ${x1.toFixed(1)} Z`);
  });

  return commands.join(" ");
}

function accuracyClass(cents) {
  if (cents == null) return "unknown";
  if (cents <= USER_GOOD_CENTS) return "good";
  if (cents <= USER_NEAR_CENTS) return "near";
  return "far";
}

function blockDistanceToTime(block, time) {
  if (time < block.start) return block.start - time;
  if (time > block.end) return time - block.end;
  return 0;
}

function nearestReferenceBlock(referenceBlocks, time, startIndex) {
  let best = null;
  const from = Math.max(0, startIndex - 4);
  const to = Math.min(referenceBlocks.length - 1, startIndex + 4);
  for (let index = from; index <= to; index += 1) {
    const block = referenceBlocks[index];
    if (!block) continue;
    const distance = blockDistanceToTime(block, time);
    if (distance > REFERENCE_TIME_TOLERANCE_SECONDS) continue;
    if (!best || distance < best.distance) {
      best = { block, distance };
    }
  }
  return best?.block || null;
}

function renderUserAccuracy(referenceBlocks) {
  const domain = visibleDomain();
  const points = visibleShiftedUserPoints(domain, 0.45);
  const userBlocks = userBlocksFromPoints(points);
  const blocksByClass = {
    good: [],
    near: [],
    far: [],
    unknown: []
  };
  const lineCommands = [];
  let blockIndex = 0;

  for (let i = 1; i < points.length; i += 1) {
    const [t1, m1] = points[i - 1];
    const [t2, m2] = points[i];
    if (t2 < domain.xMin - 0.4 || t1 > domain.xMax + 0.4) continue;
    if (t2 - t1 > PATH_GAP_BREAK_SECONDS) continue;
    if (Math.abs(m2 - m1) > PITCH_LINE_JUMP_BREAK_STEPS) continue;

    lineCommands.push(`M ${xScale(t1).toFixed(1)} ${yScale(m1).toFixed(1)} L ${xScale(t2).toFixed(1)} ${yScale(m2).toFixed(1)}`);
  }

  const musical = window.feedbackUI?.analysis?.()?.musical;
  if (musical) {
    const classes = {cerca:'good', margen:'near', fuera:'far'};
    musical.notas.filter(n => n.usuario).forEach(n => {
      const u=n.usuario;blocksByClass[classes[n.clase]].push({start:u.inicio_s,end:u.fin_s,note:u.midi,midi:u.midi});
    });
    musical.usuario_sin_correspondencia.forEach(u => blocksByClass.unknown.push({start:u.inicio_s,end:u.fin_s,note:u.midi,midi:u.midi}));
  }
  if (!musical && selectedTake() && !state.playing) blocksByClass.unknown.push(...userBlocks);
  (musical || (selectedTake() && !state.playing) ? [] : userBlocks).forEach((block) => {
    const midpoint = (block.start + block.end) / 2;
    while (
      blockIndex < referenceBlocks.length &&
      referenceBlocks[blockIndex].end < midpoint - REFERENCE_TIME_TOLERANCE_SECONDS
    ) {
      blockIndex += 1;
    }
    const expected = nearestReferenceBlock(referenceBlocks, midpoint, blockIndex);
    const cents = expected ? Math.abs(((block.midi || block.note) - expected.note) * 100) : null;
    const className = accuracyClass(cents);
    blocksByClass[className].push(block);
  });

  els.userBlockLayer.innerHTML = Object.entries(blocksByClass)
    .filter(([, blocks]) => blocks.length)
    .map(([className, blocks]) => `<path class="user-note-blocks user-${className}" d="${buildNoteBlockPath(blocks, USER_BLOCK_HALF_STEPS)}"></path>`)
    .join("");
  els.userSegmentLayer.innerHTML = "";
  els.userPath.setAttribute("d", lineCommands.join(" "));
}

function alignmentScore(offsetMs) {
  const referenceBlocks = currentReferenceBlocks();
  const rawPoints = finitePitchPoints(userPointsForChart());
  if (!referenceBlocks.length || rawPoints.length < 4) return Number.NEGATIVE_INFINITY;

  const step = Math.max(1, Math.floor(rawPoints.length / 900));
  let blockIndex = 0;
  let matched = 0;
  let score = 0;

  for (let i = 0; i < rawPoints.length; i += step) {
    const [rawTime, midi] = rawPoints[i];
    const time = rawTime + offsetMs / 1000;
    while (
      blockIndex < referenceBlocks.length &&
      referenceBlocks[blockIndex].end < time - REFERENCE_TIME_TOLERANCE_SECONDS
    ) {
      blockIndex += 1;
    }

    const expected = nearestReferenceBlock(referenceBlocks, time, blockIndex);
    if (!expected) continue;

    const cents = Math.abs((midi - expected.note) * 100);
    matched += 1;
    if (cents <= USER_GOOD_CENTS) {
      score += 2;
    } else if (cents <= USER_NEAR_CENTS) {
      score += 1;
    } else {
      score += 0.15;
    }
  }

  if (matched < 8) return Number.NEGATIVE_INFINITY;
  return score / matched + Math.min(0.4, matched / rawPoints.length);
}

function autoAlignVisualOffset() {
  if (!currentReferenceBlocks().length || !userPointsForChart().length) return;

  let bestOffset = state.visualOffsetMs;
  let bestScore = Number.NEGATIVE_INFINITY;

  for (let offset = -700; offset <= 700; offset += 10) {
    const score = alignmentScore(offset);
    if (score > bestScore) {
      bestScore = score;
      bestOffset = offset;
    }
  }

  setVisualOffset(bestOffset);
  renderChart();
}

function noteRulerStep() {
  const first = Math.ceil(state.yMin);
  const last = Math.floor(state.yMax);
  const noteCount = Math.max(1, last - first + 1);
  const pixelsPerNote = (PLOT_BOTTOM - PLOT_TOP) / noteCount;
  if (pixelsPerNote >= 22) return 1;
  if (pixelsPerNote >= 13) return 2;
  if (pixelsPerNote >= 9) return 3;
  return 4;
}

function renderNoteRulerLabel(midi, y) {
  const group = document.createElementNS("http://www.w3.org/2000/svg", "g");
  const background = document.createElementNS("http://www.w3.org/2000/svg", "rect");
  const label = document.createElementNS("http://www.w3.org/2000/svg", "text");

  background.setAttribute("class", "note-ruler-label-bg");
  background.setAttribute("x", "2");
  background.setAttribute("y", (y - 13).toFixed(1));
  background.setAttribute("width", "58");
  background.setAttribute("height", "26");
  background.setAttribute("rx", "2");

  label.setAttribute("class", "note-ruler-label");
  label.setAttribute("x", "31");
  label.setAttribute("y", y.toFixed(1));
  label.setAttribute("text-anchor", "middle");
  label.setAttribute("dominant-baseline", "middle");
  label.textContent = noteName(midi);

  group.appendChild(background);
  group.appendChild(label);
  els.gridLayer.appendChild(group);
}

function updateDetailYBounds(preferredCenter = null) {
  const values = [
    ...referencePoints().map(([, midi]) => midi),
    ...userPointsForChart().map(([, midi]) => midi)
  ].filter((midi) => Number.isFinite(midi));

  let min = 0;
  let max = 100;
  if (values.length) {
    min = Math.max(0, Math.floor(Math.min(...values) - 4));
    max = Math.min(127, Math.ceil(Math.max(...values) + 4));
  }

  if (max - min < 16) {
    const center = (min + max) / 2;
    min = Math.max(0, Math.floor(center - 8));
    max = Math.min(127, Math.ceil(center + 8));
  }

  els.detailY.min = String(min);
  els.detailY.max = String(max);
  if (preferredCenter != null) {
    els.detailY.value = String(clamp(preferredCenter, min, max));
  }
}

function renderGrid() {
  if (state.gridYMin === state.yMin && state.gridYMax === state.yMax) {
    return;
  }

  state.gridYMin = state.yMin;
  state.gridYMax = state.yMax;
  els.gridLayer.innerHTML = "";
  els.noteRuler.innerHTML = "";

  const firstMidi = Math.ceil(state.yMin);
  const labelStep = noteRulerStep();

  for (let midi = firstMidi; midi <= Math.floor(state.yMax); midi += 1) {
    const y = yScale(midi);
    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("class", "grid-line");
    line.setAttribute("x1", String(PLOT_LEFT));
    line.setAttribute("x2", String(PLOT_RIGHT));
    line.setAttribute("y1", y);
    line.setAttribute("y2", y);
    els.gridLayer.appendChild(line);

    if ((midi - firstMidi) % labelStep === 0) {
      renderNoteRulerLabel(midi, y);
    }
  }
}

function renderChart() {
  window.reviewUI?.mount();
  window.lyricsUI?.render();
  const analysis = window.feedbackUI?.analysis?.();
  const saved = Boolean(selectedTake()) && !state.playing;
  [els.visualOffset, els.visualOffsetResetButton, els.visualAutoAlignButton].filter(Boolean).forEach(e => e.disabled=saved);
  document.getElementById('visualAlignmentHint').textContent = saved ? 'Alineación compartida con las métricas. Modifícala en Sincronización del análisis.' : 'Ajuste visual durante la práctica; no cambia las métricas.';
  if (analysis) {
    els.visualOffsetLabel.textContent = `${-analysis.desfase_ms} ms`;
    els.visualOffset.value = String(-analysis.desfase_ms);
  }
  else updateVisualOffsetLabel();
  updateYDomain();
  renderGrid();
  const domain = visibleDomain();
  const referenceBlocks = currentReferenceBlocks();
  els.referenceBlockLayer.innerHTML = `<path class="reference-blocks" d="${buildReferenceBlockPath(referenceBlocks)}"></path>`;
  els.referencePath.setAttribute("d", "");
  renderUserAccuracy(referenceBlocks);

  const cursorX = cursorXForDomain(domain);
  const cursorInside = state.current >= domain.xMin && state.current <= domain.xMax;
  els.cursorLine.setAttribute("x1", cursorX);
  els.cursorLine.setAttribute("x2", cursorX);
  els.cursorLine.setAttribute("y1", String(PLOT_TOP));
  els.cursorLine.setAttribute("y2", String(PLOT_BOTTOM));
  els.cursorLine.classList.toggle("is-outside-window", state.detail && !cursorInside);
  els.currentTime.textContent = formatTime(state.current);
  els.durationTime.textContent = formatTime(currentDuration());

  const duration = Math.max(1, currentDuration() || 1);
  els.timelineFill.style.width = `${Math.min(100, (state.current / duration) * 100)}%`;
  updateChartModeButtons();
  updateTakeTimeLabel();
}

function renderChartThrottled(force = false) {
  const now = performance.now();
  if (!force && now - state.lastChartPaintAt < LIVE_RENDER_MS) return;
  state.lastChartPaintAt = now;
  renderChart();
}

async function startPlayback() {
  const song = currentSong();
  if (!song || state.playing || state.catalogWorking) return;

  if (!backendReady) {
    setStatus("Backend no conectado", false);
    return;
  }

  stopTakePlayback();
  setActiveView("practice");
  state.selectedTakeIndex = -1;
  resetReferenceBlockCache();
  state.playing = true;
  state.detail = false;
  state.overview = false;
  state.current = 0;
  state.backendCurrent = 0;
  state.backendPollAt = performance.now();
  state.lastChartPaintAt = 0;
  state.sessionStatus = "calibrating";
  state.viewStart = 0;
  state.userPoints = [];
  state.lastUserPitchAt = null;
  state.gridYMin = null;
  state.gridYMax = null;
  resetMetrics();
  setStatus("Midiendo ruido", true);
  els.startButton.disabled = true;
  els.stopButton.disabled = false;
  updateCatalogButtons();
  els.detailButton.disabled = true;
  els.fullButton.classList.add("hidden");
  els.chartShell.classList.remove("is-detail");
  renderSongs();

  try {
    const response = await window.pywebview.api.start_session(song.id);
    if (!response.ok) {
      throw new Error(response.error || "No se pudo iniciar la sesion.");
    }
    if (response.state) applyBackendState(response.state);
    startPollingBackend();
    startAnimationLoop();
  } catch (error) {
    failSession(String(error.message || error));
  }
}

async function requestStopPlayback() {
  if (!state.playing) return;

  if (!backendReady) {
    failSession("Backend no conectado.");
    return;
  }

  els.stopButton.disabled = true;
  setStatus("Deteniendo", true);
  try {
    await window.pywebview.api.stop_session();
  } catch (error) {
    failSession(String(error.message || error));
  }
}

function updateTakePlayer() {
  window.feedbackUI?.refresh();
  const take = selectedTake();
  const enabled = Boolean(take?.voiceUrl);
  const canManage = Boolean(take?.id) && !state.playing && !state.catalogWorking;
  els.selectedTakeLabel.textContent = take ? takeDisplayName(take) : "Sin toma seleccionada";
  els.takePlayButton.disabled = !enabled || state.playing || (state.catalogWorking && !state.backgroundPreparing);
  els.takeStopButton.disabled = !enabled || state.playing;
  els.takeRenameButton.disabled = !canManage;
  els.takeFavoriteButton.disabled = !canManage;
  els.takeDeleteButton.disabled = !canManage;
  els.voiceMuteButton.disabled = !enabled;
  els.trackMuteButton.disabled = !enabled || !take?.instrumentalUrl;
  els.voiceVolume.disabled = !enabled;
  els.trackVolume.disabled = !enabled || !take?.instrumentalUrl;
  els.syncOffset.disabled = !enabled || !take?.instrumentalUrl;
  els.takePlayButton.textContent = state.takePlaying ? "Pausar toma" : "Reproducir toma";
  els.takeFavoriteButton.textContent = take?.favorite ? "Quitar favorita" : "Favorita";
  updateMixerButtons();
  updateTakeTimeLabel();
}

function loadTakeAudio(take) {
  if (!take) return;

  if (voiceAudio.src !== take.voiceUrl) {
    voiceAudio.src = take.voiceUrl;
    voiceAudio.currentTime = 0;
  }
  if (trackAudio.src !== take.instrumentalUrl) {
    trackAudio.src = take.instrumentalUrl || "";
    trackAudio.currentTime = 0;
  }
  applyMixer();
}

async function toggleTakePlayback() {
  const take = selectedTake();
  if (!take?.voiceUrl) return;

  loadTakeAudio(take);
  if (state.takePlaying) {
    pauseTakePlayback();
    return;
  }

  state.takePlaying = true;
  syncTrackToVoice(true);
  applyMixer();
  els.takePlayButton.textContent = "Pausar toma";

  try {
    const plays = [voiceAudio.play()];
    if (take.instrumentalUrl) plays.push(trackAudio.play());
    await Promise.all(plays);
    startTakePlaybackLoop();
  } catch (error) {
    voiceAudio.pause();
    trackAudio.pause();
    state.takePlaying = false;
    setStatus(`Error: ${String(error.message || error)}`, false);
    updateTakePlayer();
  }
}

function pauseTakePlayback() {
  voiceAudio.pause();
  trackAudio.pause();
  state.takePlaying = false;
  stopTakePlaybackLoop();
  updateTakePlayer();
}

function stopTakePlayback(reset = true) {
  voiceAudio.pause();
  trackAudio.pause();
  state.takePlaying = false;
  stopTakePlaybackLoop();

  if (reset) {
    try {
      voiceAudio.currentTime = 0;
      trackAudio.currentTime = Math.max(0, state.syncOffsetMs / 1000);
    } catch (_error) {
      // Some backends do not allow seeking before metadata is loaded.
    }
    state.current = 0;
  }

  updateTakePlayer();
  renderChart();
}

function startTakePlaybackLoop() {
  stopTakePlaybackLoop();
  state.takeAnimationId = requestAnimationFrame(takePlaybackLoop);
}

function stopTakePlaybackLoop() {
  if (state.takeAnimationId) {
    cancelAnimationFrame(state.takeAnimationId);
    state.takeAnimationId = null;
  }
}

function takePlaybackLoop() {
  if (!state.takePlaying) return;

  state.current = voiceAudio.currentTime || 0;
  syncTrackToVoice(false);
  renderChartThrottled();

  const duration = selectedTake()?.duration || voiceAudio.duration || 0;
  if (duration && state.current >= duration - 0.05) {
    stopTakePlayback(true);
    return;
  }

  state.takeAnimationId = requestAnimationFrame(takePlaybackLoop);
}

function syncTrackToVoice(force) {
  const take = selectedTake();
  if (!take?.instrumentalUrl || !trackAudio.src) return;

  const playbackOffset = window.feedbackUI?.playbackOffset?.() ?? state.syncOffsetMs;
  const target = Math.max(0, (voiceAudio.currentTime || 0) + playbackOffset / 1000);
  if (force || Math.abs((trackAudio.currentTime || 0) - target) > 0.08) {
    try {
      trackAudio.currentTime = target;
    } catch (_error) {
      // Metadata may still be loading; the next animation frame will retry.
    }
  }
}

function applyMixer() {
  voiceAudio.volume = Number(els.voiceVolume.value || 0) / 100;
  trackAudio.volume = Number(els.trackVolume.value || 0) / 100;
  voiceAudio.muted = state.voiceMuted;
  trackAudio.muted = state.trackMuted;
}

function updateMixerButtons() {
  els.voiceMuteButton.classList.toggle("is-muted", state.voiceMuted);
  els.trackMuteButton.classList.toggle("is-muted", state.trackMuted);
  els.voiceMuteButton.textContent = state.voiceMuted ? "Voz mute" : "Voz";
  els.trackMuteButton.textContent = state.trackMuted ? "Pista mute" : "Pista";
  els.syncOffsetLabel.textContent = `${state.syncOffsetMs} ms`;
}

function updateTakeTimeLabel() {
  const take = selectedTake();
  const duration = take?.duration || 0;
  els.takeTimeLabel.textContent = `${formatTime(state.current)} / ${formatTime(duration)}`;
}

function openSongMetadataModal(fileInfo) {
  return new Promise((resolve) => {
    let settled = false;
    const fallbackTitle = "Nueva canción";
    const suggestedTitle = String(fileInfo?.suggestedTitle || fileInfo?.suggested_title || "").trim();

    els.songModalEyebrow.textContent = "Biblioteca";
    els.songModalTitle.textContent = "Agregar canción";
    els.songModalFileName.textContent = fileInfo?.filename || "Audio seleccionado";
    els.songTitleInput.value = suggestedTitle || fallbackTitle;
    els.songArtistInput.value = fileInfo?.suggested_artist || "";
    els.songModalSubmit.textContent = "Agregar";
    els.songModalError.textContent = "";
    els.songModal.classList.remove("hidden");
    document.body.classList.add("modal-open");

    const cleanup = () => {
      els.songModalForm.removeEventListener("submit", handleSubmit);
      els.songModalCancel.removeEventListener("click", handleCancel);
      els.songModalCancelX.removeEventListener("click", handleCancel);
      els.songModal.removeEventListener("mousedown", handleBackdrop);
      window.removeEventListener("keydown", handleKeydown);
    };

    const close = (value) => {
      if (settled) return;
      settled = true;
      cleanup();
      els.songModal.classList.add("hidden");
      document.body.classList.remove("modal-open");
      resolve(value);
    };

    function handleSubmit(event) {
      event.preventDefault();
      const title = els.songTitleInput.value.trim();
      if (!title) {
        els.songModalError.textContent = "Ingresa un título para agregar la canción.";
        els.songTitleInput.focus();
        return;
      }

      close({
        title,
        artist: els.songArtistInput.value.trim()
      });
    }

    function handleCancel() {
      close(null);
    }

    function handleBackdrop(event) {
      if (event.target === els.songModal) close(null);
    }

    function handleKeydown(event) {
      if (event.key === "Escape") close(null);
    }

    els.songModalForm.addEventListener("submit", handleSubmit);
    els.songModalCancel.addEventListener("click", handleCancel);
    els.songModalCancelX.addEventListener("click", handleCancel);
    els.songModal.addEventListener("mousedown", handleBackdrop);
    window.addEventListener("keydown", handleKeydown);
    window.setTimeout(() => els.songTitleInput.focus(), 0);
  });
}

function openGenericModal(options) {
  return new Promise((resolve) => {
    let settled = false;
    const hasInput = Boolean(options.inputLabel);
    const danger = Boolean(options.danger);

    els.genericModalEyebrow.textContent = options.eyebrow || "Toma";
    els.genericModalTitle.textContent = options.title || "Gestionar toma";
    els.genericModalMessage.textContent = options.message || "";
    els.genericModalInputLabel.textContent = options.inputLabel || "";
    els.genericModalInput.value = options.inputValue || "";
    els.genericModalInputRow.classList.toggle("hidden", !hasInput);
    els.genericModalInput.required = Boolean(options.required);
    els.genericModalError.textContent = "";
    els.genericModalSubmit.textContent = options.confirmText || "Aceptar";
    els.genericModalSubmit.classList.toggle("button-primary", !danger);
    els.genericModalSubmit.classList.toggle("button-danger", danger);
    els.genericModal.classList.remove("hidden");
    document.body.classList.add("modal-open");

    const cleanup = () => {
      els.genericModalForm.removeEventListener("submit", handleSubmit);
      els.genericModalCancel.removeEventListener("click", handleCancel);
      els.genericModalCancelX.removeEventListener("click", handleCancel);
      els.genericModal.removeEventListener("mousedown", handleBackdrop);
      window.removeEventListener("keydown", handleKeydown);
    };

    const close = (value) => {
      if (settled) return;
      settled = true;
      cleanup();
      els.genericModal.classList.add("hidden");
      document.body.classList.remove("modal-open");
      resolve(value);
    };

    function handleSubmit(event) {
      event.preventDefault();
      if (!hasInput) {
        close(true);
        return;
      }

      const value = els.genericModalInput.value.trim();
      if (options.required && !value) {
        els.genericModalError.textContent = options.requiredMessage || "Completa este campo.";
        els.genericModalInput.focus();
        return;
      }
      close(value);
    }

    function handleCancel() {
      close(null);
    }

    function handleBackdrop(event) {
      if (event.target === els.genericModal) close(null);
    }

    function handleKeydown(event) {
      if (event.key === "Escape") close(null);
    }

    els.genericModalForm.addEventListener("submit", handleSubmit);
    els.genericModalCancel.addEventListener("click", handleCancel);
    els.genericModalCancelX.addEventListener("click", handleCancel);
    els.genericModal.addEventListener("mousedown", handleBackdrop);
    window.addEventListener("keydown", handleKeydown);

    if (hasInput) {
      window.setTimeout(() => {
        els.genericModalInput.focus();
        els.genericModalInput.select();
      }, 0);
    } else {
      window.setTimeout(() => els.genericModalSubmit.focus(), 0);
    }
  });
}

async function addSong() {
  if (state.playing || state.catalogWorking) return;

  if (!backendReady || !window.pywebview?.api?.select_audio_file || !window.pywebview?.api?.add_song_from_file) {
    setStatus("Backend no conectado", false);
    return;
  }

  state.catalogWorking = true;
  let finalStatus = null;
  let finalRecording = false;
  resetMetrics();
  updateCatalogButtons();
  renderSongs();
  setStatus("Busca una canción o elige un archivo", true);

  try {
    const selectedFile = window.chooseSongSource
      ? await window.chooseSongSource()
      : await window.pywebview.api.select_audio_file();
    if (selectedFile.cancelled) {
      finalStatus = "Agregar cancelado";
      return;
    }
    if (!selectedFile.ok) {
      throw new Error(selectedFile.error || "No se pudo seleccionar el archivo.");
    }

    setStatus("Completa los datos de la canción", false);
    const details = await openSongMetadataModal(selectedFile);
    if (!details) {
      finalStatus = "Agregar cancelado";
      return;
    }

    setStatus("Preparando canción", true);
    state.backgroundPreparing = true;
    renderSongs(); renderTakes(); updateTakePlayer();
    window.preparationUI?.start();
    const response = selectedFile.video_id
      ? await window.pywebview.api.add_song_from_youtube(selectedFile.video_id, details.title, details.artist)
      : await window.pywebview.api.add_song_from_file(selectedFile.path, details.title, details.artist);
    if (!response.ok) {
      throw new Error(response.error || "No se pudo agregar la canción.");
    }

    const added = normalizeBackendSongs([response.song])[0];
    if (added) {
      const previousId=currentSong()?.id;
      const existingIndex = songs.findIndex(song => song.id === added.id);
      if (existingIndex >= 0) songs[existingIndex] = added;
      else songs.push(added);
      songs.sort((a, b) => a.title.localeCompare(b.title));
      state.selectedIndex = Math.max(0, songs.findIndex((song) => song.id === (previousId || added.id)));
      if(!previousId) {takes=[]; clearCurrentTake(); renderChart(); renderTakes();}
    }
    finalStatus = `${response.reused ? 'Ya está en tu biblioteca' : 'Lista'}: ${added?.title || details.title}`;
  } catch (error) {
    finalStatus = `Error: ${String(error.message || error)}`;
  } finally {
    window.preparationUI?.stop();
    state.backgroundPreparing = false;
    state.catalogWorking = false;
    updateSongLabels();
    renderSongs();
    renderTakes(); updateTakePlayer();
    if (finalStatus) setStatus(finalStatus, finalRecording);
  }
}

async function editSelectedSong() {
  const song = currentSong();
  if (!song || state.playing || state.catalogWorking) return;

  if (!backendReady || !window.pywebview?.api?.edit_song) {
    setStatus("Backend no conectado", false);
    return;
  }

  const title = window.prompt("Nuevo titulo de la cancion", song.title);
  if (title == null) return;
  const cleanTitle = title.trim();
  if (!cleanTitle) {
    setStatus("El titulo no puede quedar vacio", false);
    return;
  }

  const currentArtist = song.artist === "Sin artista" ? "" : song.artist;
  const artist = window.prompt("Artista", currentArtist);
  if (artist == null) return;

  state.catalogWorking = true;
  let finalStatus = null;
  updateCatalogButtons();
  renderSongs();
  setStatus("Editando cancion", true);

  try {
    const response = await window.pywebview.api.edit_song(song.id, cleanTitle, artist.trim());
    if (!response.ok) {
      throw new Error(response.error || "No se pudo editar la cancion.");
    }

    songs = normalizeBackendSongs(response.songs || []);
    state.selectedIndex = Math.max(0, songs.findIndex((item) => item.id === song.id));
    await loadTakesForCurrentSong();
    renderSongs();
    updateSongLabels();
    renderChart();
    finalStatus = "Cancion actualizada";
  } catch (error) {
    finalStatus = `Error: ${String(error.message || error)}`;
  } finally {
    state.catalogWorking = false;
    updateSongLabels();
    renderSongs();
    if (finalStatus) setStatus(finalStatus, false);
  }
}

async function deleteSelectedSong() {
  const song = currentSong();
  if (!song || state.playing || state.catalogWorking) return;

  if (!backendReady || !window.pywebview?.api?.delete_song) {
    setStatus("Backend no conectado", false);
    return;
  }

  const confirmed = window.confirm(
    `Se eliminara "${song.title}" del catalogo, junto con sus archivos preparados y grabaciones.\n\nQuieres continuar?`
  );
  if (!confirmed) return;

  state.catalogWorking = true;
  let finalStatus = null;
  let finalRecording = false;
  updateCatalogButtons();
  renderSongs();
  setStatus("Eliminando cancion", true);

  try {
    const response = await window.pywebview.api.delete_song(song.id);
    if (!response.ok) {
      throw new Error(response.error || "No se pudo eliminar la cancion.");
    }
    songs = normalizeBackendSongs(response.songs || []);
    state.selectedIndex = Math.min(state.selectedIndex, Math.max(0, songs.length - 1));
    takes = [];
    clearCurrentTake();
    if (songs.length) {
      await loadTakesForCurrentSong();
    } else {
      renderTakes();
      updateTakePlayer();
      setActiveView("library");
    }
    renderChart();
    finalStatus = songs.length ? "Cancion eliminada" : "Catalogo vacio";
  } catch (error) {
    finalStatus = `Error: ${String(error.message || error)}`;
  } finally {
    state.catalogWorking = false;
    updateSongLabels();
    renderSongs();
    if (finalStatus) setStatus(finalStatus, finalRecording);
  }
}

function replaceSelectedTake(updatedTake) {
  const normalized = normalizeBackendTakes([updatedTake])[0];
  if (!normalized || state.selectedTakeIndex < 0) return;
  takes[state.selectedTakeIndex] = normalized;
  renderTakes();
  updateTakePlayer();
}

async function renameSelectedTake() {
  const song = currentSong();
  const take = selectedTake();
  if (!song?.id || !take?.id || state.playing || state.catalogWorking) return;

  if (!backendReady || !window.pywebview?.api?.edit_take) {
    setStatus("Backend no conectado", false);
    return;
  }

  const name = await openGenericModal({
    title: "Renombrar toma",
    message: "Asigna un nombre corto para reconocer esta grabación en el historial.",
    inputLabel: "Nombre de la toma",
    inputValue: take.name || takeDisplayName(take),
    confirmText: "Guardar",
    required: true,
    requiredMessage: "Ingresa un nombre para la toma."
  });
  if (name == null) return;

  stopTakePlayback(false);
  state.catalogWorking = true;
  updateCatalogButtons();
  updateTakePlayer();
  renderTakes();
  setStatus("Renombrando toma", true);

  try {
    const response = await window.pywebview.api.edit_take(song.id, take.id, name);
    if (!response.ok) {
      throw new Error(response.error || "No se pudo renombrar la toma.");
    }
    replaceSelectedTake(response.take);
    setStatus("Toma renombrada", false);
  } catch (error) {
    setStatus(`Error: ${String(error.message || error)}`, false);
  } finally {
    state.catalogWorking = false;
    updateCatalogButtons();
    updateTakePlayer();
    renderTakes();
  }
}

async function toggleSelectedTakeFavorite() {
  const song = currentSong();
  const take = selectedTake();
  if (!song?.id || !take?.id || state.playing || state.catalogWorking) return;

  if (!backendReady || !window.pywebview?.api?.set_take_favorite) {
    setStatus("Backend no conectado", false);
    return;
  }

  stopTakePlayback(false);
  state.catalogWorking = true;
  updateCatalogButtons();
  updateTakePlayer();
  renderTakes();
  setStatus(take.favorite ? "Quitando favorita" : "Marcando favorita", true);

  try {
    const response = await window.pywebview.api.set_take_favorite(song.id, take.id, !take.favorite);
    if (!response.ok) {
      throw new Error(response.error || "No se pudo actualizar la toma.");
    }
    replaceSelectedTake(response.take);
    setStatus(response.take?.favorite ? "Toma marcada como favorita" : "Toma quitada de favoritas", false);
  } catch (error) {
    setStatus(`Error: ${String(error.message || error)}`, false);
  } finally {
    state.catalogWorking = false;
    updateCatalogButtons();
    updateTakePlayer();
    renderTakes();
  }
}

async function deleteSelectedTake() {
  const song = currentSong();
  const take = selectedTake();
  if (!song?.id || !take?.id || state.playing || state.catalogWorking) return;

  if (!backendReady || !window.pywebview?.api?.delete_take) {
    setStatus("Backend no conectado", false);
    return;
  }

  const confirmed = await openGenericModal({
    title: "Eliminar toma",
    message: `Se eliminará "${takeDisplayName(take)}" junto con su audio y datos guardados. Esta acción no se puede deshacer.`,
    confirmText: "Eliminar toma",
    danger: true
  });
  if (!confirmed) return;

  const previousIndex = state.selectedTakeIndex;
  stopTakePlayback(false);
  state.catalogWorking = true;
  updateCatalogButtons();
  updateTakePlayer();
  renderTakes();
  setStatus("Eliminando toma", true);

  try {
    const response = await window.pywebview.api.delete_take(song.id, take.id);
    if (!response.ok) {
      throw new Error(response.error || "No se pudo eliminar la toma.");
    }

    takes = normalizeBackendTakes(response.takes || []);
    if (takes.length) {
      state.selectedTakeIndex = Math.min(previousIndex, takes.length - 1);
      loadSelectedTakeIntoChart();
    } else {
      clearCurrentTake();
    }
    renderTakes();
    updateTakePlayer();
    renderChart();
    setStatus(takes.length ? "Toma eliminada" : "Sin tomas guardadas", false);
  } catch (error) {
    setStatus(`Error: ${String(error.message || error)}`, false);
  } finally {
    state.catalogWorking = false;
    updateCatalogButtons();
    updateTakePlayer();
    renderTakes();
  }
}

async function reprocessSelectedSong() {
  const song = currentSong();
  if (!song || state.playing || state.catalogWorking) return;

  if (!backendReady || !window.pywebview?.api?.reprocess_song) {
    setStatus("Backend no conectado", false);
    return;
  }

  const confirmed = window.confirm(
    "Se volvera a recalcular la lectura de frecuencias de la voz ya separada. Puede tardar unos segundos.\n\nQuieres continuar?"
  );
  if (!confirmed) return;

  state.catalogWorking = true;
  state.reprocessing = true;
  els.startButton.disabled = true;
  updateCatalogButtons();
  els.detailButton.disabled = true;
  renderSongs();
  setStatus("Reprocesando referencia", true);
  window.preparationUI?.start();

  try {
    const response = await window.pywebview.api.reprocess_song(song.id);
    if (!response.ok) {
      throw new Error(response.error || "No se pudo reprocesar la cancion.");
    }

    const updated = normalizeBackendSongs([response.song])[0];
    if (updated) {
      songs[state.selectedIndex] = updated;
      clearCurrentTake();
      resetReferenceDiagnostic();
      renderChart();
    }
    setStatus("Referencia actualizada", false);
  } catch (error) {
    setStatus(`Error: ${String(error.message || error)}`, false);
  } finally {
    state.catalogWorking = false;
    state.reprocessing = false;
    window.preparationUI?.stop();
    els.startButton.disabled = !backendReady || !currentSong()?.prepared;
    updateCatalogButtons();
    renderSongs();
  }
}

function startPollingBackend() {
  stopPollingBackend();
  state.pollId = window.setInterval(pollBackendState, BACKEND_POLL_MS);
  pollBackendState();
}

function stopPollingBackend() {
  if (state.pollId) {
    window.clearInterval(state.pollId);
    state.pollId = null;
  }
  state.pollingBackend = false;
}

async function pollBackendState() {
  if (!backendReady || state.pollingBackend) return;

  state.pollingBackend = true;
  try {
    const session = await window.pywebview.api.get_session_state();
    applyBackendState(session);
  } catch (error) {
    failSession(String(error.message || error));
  } finally {
    state.pollingBackend = false;
  }
}

function applyBackendState(session) {
  if (session.status) {
    state.sessionStatus = session.status;
  }

  if (Array.isArray(session.pitch_points) && session.pitch_points.length) {
    state.userPoints.push(...session.pitch_points);
    trimLiveUserPoints();
    const last = state.userPoints[state.userPoints.length - 1];
    if (last) {
      state.lastUserPitchAt = last[0];
      state.currentNoteMidi = last[1];
      updateCurrentNoteLabel();
    }
  }

  if (Number.isFinite(session.current) && session.current >= 0) {
    state.backendCurrent = session.current;
    state.backendPollAt = performance.now();
    state.current = Math.max(state.current, session.current);
  }

  if (session.diagnostics) {
    updateLiveDiagnostics(session.diagnostics);
  }

  if (session.status === "calibrating") {
    setStatus("Midiendo ruido", true);
  } else if (session.status === "preparing") {
    setStatus("Preparando audio", true);
  } else if (session.status === "recording") {
    setStatus("Grabando", true);
  } else if (session.status === "stopping" || session.status === "comparing") {
    setStatus("Comparando", true);
    els.stopButton.disabled = true;
  } else if (session.status === "finished") {
    finishBackendSession(session.result);
  } else if (session.status === "error") {
    failSession(session.error || "Error desconocido en audio.");
  }
}

function updateLiveDiagnostics(diagnostics) {
  const noise = Number(diagnostics.noise_floor || 0);
  const rejected = Number(diagnostics.rejected_points || 0);
  const jumps = Number(diagnostics.rejected_jumps || 0);
  const pitchErrors = Number(diagnostics.pitch_errors || 0);
  els.noiseLabel.textContent = noise > 0 ? noise.toFixed(4) : "--";
  const jumpLabel = jumps === 1 ? "salto" : "saltos";
  const errorLabel = pitchErrors ? `, ${pitchErrors} err.` : "";
  els.rejectLabel.textContent = jumps > 0 ? `${rejected} (${jumps} ${jumpLabel}${errorLabel})` : `${rejected}${errorLabel}`;
}

function startAnimationLoop() {
  if (state.animationId) cancelAnimationFrame(state.animationId);
  state.animationId = requestAnimationFrame(loop);
}

function stopAnimationLoop() {
  if (state.animationId) {
    cancelAnimationFrame(state.animationId);
    state.animationId = null;
  }
}

function loop() {
  if (!state.playing) return;

  if (backendReady && state.sessionStatus === "recording") {
    state.current = liveDisplayTime(performance.now());
  } else if (backendReady) {
    state.current = state.backendCurrent;
  }

  if (
    state.sessionStatus === "recording" &&
    state.lastUserPitchAt != null &&
    state.current - state.lastUserPitchAt > NOTE_STALE_SECONDS
  ) {
    state.currentNoteMidi = null;
    els.currentNote.textContent = "--";
  }

  renderChartThrottled();
  state.animationId = requestAnimationFrame(loop);
}

function liveDisplayTime(now) {
  const elapsed = state.backendPollAt == null ? 0 : Math.max(0, (now - state.backendPollAt) / 1000);
  const confirmed = Number.isFinite(state.backendCurrent) ? state.backendCurrent : 0;
  const predicted = confirmed + Math.min(elapsed, LIVE_MAX_EXTRAPOLATION_SECONDS);
  const duration = currentSong()?.duration;
  return Number.isFinite(duration) && duration > 0 ? Math.min(duration, predicted) : predicted;
}

function finishBackendSession(result) {
  state.playing = false;
  state.sessionStatus = "finished";
  stopAnimationLoop();
  stopPollingBackend();

  if (result?.points_ref?.length) {
    currentSong().points = result.points_ref;
    resetReferenceBlockCache();
  }
  if (Array.isArray(result?.points_user)) {
    state.userPoints = result.points_user;
    const last = state.userPoints[state.userPoints.length - 1];
    if (last) state.current = last[0];
  }
  if (result?.take) {
    const savedTake = normalizeBackendTakes([result.take])[0];
    if (savedTake) {
      takes = [savedTake, ...takes.filter((take) => take.id !== savedTake.id)];
      state.selectedTakeIndex = 0;
      resetReferenceBlockCache();
      loadTakeAudio(savedTake);
    }
  }

  setStatus("Comparacion lista", false);
  els.startButton.disabled = !backendReady || !currentSong()?.prepared;
  els.stopButton.disabled = true;
  updateCatalogButtons();
  els.detailButton.disabled = !state.userPoints.length;
  updateChartModeButtons();
  renderSongs();
  renderTakes();
  updateTakePlayer();
  renderMetrics(result || {});
  renderChart();
  setActiveView("result");
}

function failSession(message) {
  state.playing = false;
  state.sessionStatus = "error";
  stopAnimationLoop();
  stopPollingBackend();
  setStatus(`Error: ${message}`, false);
  els.startButton.disabled = !backendReady || !currentSong()?.prepared;
  els.stopButton.disabled = true;
  updateCatalogButtons();
  els.detailButton.disabled = true;
  updateChartModeButtons();
  renderSongs();
}

function renderMetrics(result) {
  const m = window.feedbackUI?.analysis?.()?.musical?.metricas;
  const format = v => v == null ? '--' : `${v.toFixed(1)}%`;
  els.metricTight.textContent = format(m?.porcentaje_50);
  els.metricLoose.textContent = format(m?.porcentaje_100);
  els.metricTrend.textContent = format(m?.cobertura_notas_pct);
  els.metricPoints.textContent = m ? `${m.notas_comparadas} / ${m.notas_referencia}` : '--';
  els.metricTightNote.textContent = 'Proporción de notas revisadas muy cercanas a la canción.';
  els.metricLooseNote.textContent = 'Incluye las notas muy cercanas y las que se desviaron un poco.';
  els.metricTrendNote.textContent = 'Proporción de notas de la canción que pudimos revisar.';
  els.metricPointsNote.textContent = m ? `${m.notas_sin_correspondencia} no se pudieron comparar. Eso no significa que estén mal cantadas.` : 'Revisando tu interpretación…';
  els.averageError.textContent = m?.error_mediano_cents == null ? '--' : Math.abs(m.error_mediano_cents)<=50 ? 'Cerca' : m.error_mediano_cents<0 ? 'Más grave' : 'Más aguda';
}

function showDetail() {
  if (!canUseChartModes()) return;
  state.detail = true;
  state.overview = false;
  els.detailX.max = Math.max(0, currentDuration() - state.viewWindow);
  els.detailX.value = Math.max(0, Math.min(Number(els.detailX.max), state.current - state.viewWindow / 2));
  updateDetailYBounds(Math.round((state.yMin + state.yMax) / 2));
  state.viewStart = Number(els.detailX.value);
  renderChart();
}

function showOverview() {
  if (!canUseChartModes()) return;
  state.detail = false;
  state.overview = true;
  renderChart();
}

function showFollowView() {
  state.detail = false;
  state.overview = false;
  renderChart();
}

function toggleOverview() {
  if (state.overview) {
    showFollowView();
  } else {
    showOverview();
  }
}

els.startButton.addEventListener("click", startPlayback);
els.stopButton.addEventListener("click", requestStopPlayback);
els.addButton.addEventListener("click", addSong);
els.referenceDiagnosticButton.addEventListener("click", loadReferenceDiagnostics);
els.libraryPracticeButton.addEventListener("click", () => setActiveView("practice"));
els.navButtons.forEach((button) => {
  button.addEventListener("click", () => setActiveView(button.dataset.viewTarget));
});
els.takePlayButton.addEventListener("click", toggleTakePlayback);
els.takeStopButton.addEventListener("click", () => stopTakePlayback(true));
els.takeRenameButton.addEventListener("click", renameSelectedTake);
els.takeFavoriteButton.addEventListener("click", toggleSelectedTakeFavorite);
els.takeDeleteButton.addEventListener("click", deleteSelectedTake);
els.voiceMuteButton.addEventListener("click", () => {
  state.voiceMuted = !state.voiceMuted;
  applyMixer();
  updateMixerButtons();
});
els.trackMuteButton.addEventListener("click", () => {
  state.trackMuted = !state.trackMuted;
  applyMixer();
  updateMixerButtons();
});
els.voiceVolume.addEventListener("input", applyMixer);
els.trackVolume.addEventListener("input", applyMixer);
els.syncOffset.addEventListener("input", () => {
  state.syncOffsetMs = Number(els.syncOffset.value || 0);
  updateMixerButtons();
  syncTrackToVoice(true);
});
els.detailButton.addEventListener("click", showDetail);
els.fullButton.addEventListener("click", toggleOverview);
els.detailX.addEventListener("input", () => {
  state.viewStart = Number(els.detailX.value);
  renderChart();
});
els.detailY.addEventListener("input", renderChart);
els.notationSelect.addEventListener("change", saveNotationPreference);
els.notationToggleButton.addEventListener("click", toggleNoteNotation);
els.themeToggleButton.addEventListener("click", toggleTheme);
els.visualOffset.addEventListener("input", () => {
  setVisualOffset(Number(els.visualOffset.value || 0));
  renderChart();
});
els.visualOffsetResetButton.addEventListener("click", () => {
  setVisualOffset(0);
  renderChart();
});
els.visualAutoAlignButton.addEventListener("click", autoAlignVisualOffset);
voiceAudio.addEventListener("ended", () => stopTakePlayback(true));
trackAudio.addEventListener("ended", () => {
  if (voiceAudio.ended) stopTakePlayback(true);
});

loadNotationPreference();
loadThemePreference();
loadVisualOffsetPreference();
renderSongs();
renderTakes();
updateSongLabels();
mountSharedModules();
updateTakePlayer();
renderChart();
renderReferenceDiagnostic();

window.addEventListener("pywebviewready", loadBackendSongs);
connectBackend();
