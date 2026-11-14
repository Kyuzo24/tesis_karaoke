// Prueba de interfaz con datos reales y puente de escritorio simulado; sin llamadas de pago.
const {chromium} = require('playwright');
const fs = require('fs');
const path = require('path');
const {pathToFileURL} = require('url');
(async () => {
  const root = path.resolve(__dirname, '..');
  const fixture = JSON.parse(fs.readFileSync(path.join(root, 'output/prueba_interfaz/fixture.json'), 'utf8'));
  const browser = await chromium.launch({headless:true, executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
  const page = await browser.newPage({viewport:{width:1280,height:900}});
  const errors = []; page.on('pageerror', e => errors.push(e.message));
  await page.addInitScript(f => {
    window._fixture = f; window._explanations = 0;
    window.pywebview = {api:{
      get_songs: async () => f.songs, get_takes: async () => f.takes,
      get_status: async () => ({input_device:'Prueba',output_device:'Prueba'}),
      get_feedback: async () => ({ok:true,...f.panel}),
      explain_take: async (_s,_t,fid) => {
        window._explanations++;
        if(window._delayExplanation) await new Promise(r=>setTimeout(r,500));
        return {ok:true,...(fid?f.fragment:f.summary)};
      },
      get_preparation_state: async () => ({status:'adding',message:'Separando voz y acompañamiento: 19% · Restante estimado: 07:02',percent:19}),
      set_alignment: async (_s,_t,ms,mode) => {
        f.panel.desfase_ms=mode==='manual'?ms:mode==='automatico'?240:0;
        f.panel.alineacion={modo:mode,estado:mode==='automatico'?'aplicado':mode,motivo:'Estado de prueba.'};
        return {ok:true};
      }
    }};
  }, fixture);
  await page.goto(pathToFileURL(path.join(root,'ui_live/index.html')).href);
  await page.waitForFunction(() => document.querySelectorAll('#songList .song-card').length > 0);
  if(await page.locator('body').getAttribute('data-view')!=='library') throw new Error('No inicia en Biblioteca');
  await page.locator('#libraryLyricsButton').click();
  await page.locator('#lyricsSettings').waitFor({state:'visible'});
  await page.locator('#lyricsClose').click();
  await page.getByRole('button',{name:'Resultado',exact:true}).click();
  await page.locator('[data-review="fragments"]').click();
  await page.waitForSelector('.feedback-fragment');
  await page.waitForFunction(() => document.querySelector('#metricTight').textContent === window._fixture.panel.musical.metricas.porcentaje_50.toFixed(1)+'%');
  if(!(await page.locator('#visualOffset').isDisabled())) throw new Error('El gráfico permite una alineación independiente');
  const consistent = await page.evaluate(() => currentReferenceBlocks().length === window._fixture.panel.musical.notas.length && window.feedbackUI.analysis().desfase_ms === window._fixture.panel.desfase_ms);
  if(!consistent) throw new Error('Gráfico y métricas usan datos diferentes');
  await page.locator('[data-review="chart"]').click();
  await page.evaluate(() => {state.current=40; renderChart();});
  await page.locator('#chartShell').screenshot({path:path.join(root,'output/prueba_interfaz/notas_grafico.png')});
  await page.locator('[data-review="fragments"]').click();
  await page.locator('.feedback-fragment').first().click();
  await page.waitForFunction(() => document.querySelectorAll('.feedback-copy .feedback-tag').length >= 2);
  await page.getByRole('button',{name:'Escuchar mi fragmento',exact:true}).click();
  await page.waitForFunction(() => state.takePlaying);
  if(await page.evaluate(() => window.feedbackUI.playbackOffset() !== -window._fixture.panel.desfase_ms)) throw new Error('La escucha no usa la compensación del análisis');
  await page.getByRole('button',{name:'Detener audio',exact:true}).click();
  if(await page.evaluate(() => state.takePlaying)) throw new Error('No se detuvo la reproducción');
  if(await page.evaluate(() => window.feedbackUI.playbackOffset() !== null)) throw new Error('No se restauró el mezclador');
  await page.locator('#feedbackPanel').screenshot({path:path.join(root,'output/prueba_interfaz/fragmentos.png')});
  await page.locator('[data-review="technical"]').click();
  await page.locator('.feedback-alignment summary').click();
  await page.locator('.feedback-alignment input').fill('280');
  await page.getByRole('button',{name:'Aplicar ajuste manual',exact:true}).click();
  await page.waitForFunction(() => document.querySelector('.feedback-alignment summary').textContent.includes('manual · voz adelantada 280 ms'));
  await page.locator('.feedback-alignment summary').click();
  await page.getByRole('button',{name:'Desactivar compensación',exact:true}).click();
  await page.waitForFunction(() => document.querySelector('.feedback-alignment summary').textContent.includes('desactivada · sin desplazamiento'));
  await page.locator('.feedback-alignment summary').click();
  await page.getByRole('button',{name:'Volver al automático',exact:true}).click();
  await page.waitForFunction(() => document.querySelector('.feedback-alignment summary').textContent.includes('automática · voz adelantada 240 ms'));
  // Una respuesta tardía no debe restaurar el detalle de una toma anterior.
  await page.locator('[data-review="fragments"]').click();
  await page.evaluate(() => {window._delayExplanation=true;});
  await page.locator('.feedback-fragment').first().click();
  await page.evaluate(() => selectTake(1));
  await page.waitForTimeout(650);
  if(await page.locator('.feedback-fragment[aria-pressed="true"]').count()) throw new Error('Detalle obsoleto después de cambiar de toma');
  await page.evaluate(() => window.preparationUI.start());
  await page.waitForFunction(() => document.querySelector('#preparationMessage').textContent.includes('Separando'));
  if(await page.locator('#preparationProgress progress').getAttribute('value')!=='19') throw new Error('No muestra progreso real');
  await page.evaluate(()=>{state.catalogWorking=true;state.backgroundPreparing=true;renderSongs();renderTakes();updateTakePlayer();});
  if(await page.locator('#songList .song-card:disabled').count()) throw new Error('Biblioteca bloqueada durante preparación');
  await page.evaluate(()=>{state.catalogWorking=false;state.backgroundPreparing=false;renderSongs();renderTakes();updateTakePlayer();});
  await page.locator('#preparationProgress').screenshot({path:path.join(root,'output/prueba_interfaz/carga.png')});
  await page.evaluate(() => window.preparationUI.stop());
  if(await page.locator('#preparationProgress').isVisible()) throw new Error('Barra de carga no se ocultó');
  await page.getByRole('button',{name:'Ajustes',exact:true}).click();
  await page.getByRole('heading',{name:'Retroalimentación local',exact:true}).waitFor();
  if(await page.locator('#llmKey, #llmProvider, #llmServer').count()) throw new Error('Quedan controles de IA');
  await page.evaluate(() => {
    state.playing=true; state.current=4;
    currentSong().lyrics={source:'Prueba local',offset_ms:0,lines:[{time:5,text:'Primera frase de prueba'},{time:8,text:'Segunda frase de prueba'},{time:10,text:''}]};
    window.lyricsUI.render();
    if(document.getElementById('lyricsCurrent').textContent!=='♪') throw new Error('Letra antes de su tiempo');
    state.current=5; window.lyricsUI.render();
    if(document.getElementById('lyricsCurrent').textContent!=='Primera frase de prueba') throw new Error('No avanzó la letra');
    currentSong().lyrics.offset_ms=1000; window.lyricsUI.render();
    if(document.getElementById('lyricsCurrent').textContent!=='♪') throw new Error('Signo incorrecto del ajuste de letra');
    state.current=11; window.lyricsUI.render();
    if(document.getElementById('lyricsCurrent').textContent!=='♪') throw new Error('No se respetó la pausa LRC');
    state.current=9; window.lyricsUI.render();
    if(document.getElementById('lyricsCurrent').textContent!=='Segunda frase de prueba') throw new Error('La letra no retrocede al buscar');
    state.playing=false;
  });
  await page.getByRole('button',{name:'Resultado',exact:true}).click();
  await page.getByRole('button',{name:'Practicar',exact:true}).first().click();
  await page.locator('#lyricsPanel').screenshot({path:path.join(root,'output/prueba_interfaz/letra.png')});
  // A delayed bridge response must not scroll the live chart beyond known audio.
  await page.evaluate(() => {
    state.selectedTakeIndex=-1; state.playing=true; state.detail=false; state.overview=false;
    state.backendCurrent=20; state.backendPollAt=1000;
    const delayed=liveDisplayTime(16000);
    if(Math.abs(delayed-20.3)>0.001) throw new Error('El reloj extrapola sin límite');
    applyBackendState({current:NaN});
    if(state.backendCurrent!==20) throw new Error('Se aceptó un reloj inválido');
    // Controlled reference and input let us assert that both SVG layers survive a stall.
    songs[state.selectedIndex]={...currentSong(),duration:60,points:[[19,60],[19.1,60],[20,60],[20.1,60]]};
    state.userPoints=[[19,60],[19.1,60],[20,60],[20.1,60]];
    state.visualOffsetMs=0; state.current=delayed;
    renderChart();
    if(!els.referenceBlockLayer.querySelector('path')?.getAttribute('d') || !els.userPath.getAttribute('d')) throw new Error('Capas vacías tras retraso');
    applyBackendState({current:21});
    state.current=liveDisplayTime(state.backendPollAt);
    if(state.current!==21) throw new Error('El reloj no recuperó el tiempo confirmado');
    renderChart();
    state.playing=false;
  });
  if(errors.length) throw new Error(errors.join('\n'));
  await page.setViewportSize({width:1366,height:768});
  await page.getByRole('button',{name:'Practicar',exact:true}).first().click();
  await page.evaluate(()=>{state.current=20; renderChart(); window.scrollTo(0,0);});
  await page.locator('#lyricsConfigure').click();
  if(!await page.locator('#lyricsSettings').isVisible()) throw new Error('No abre la configuración');
  await page.evaluate(()=>{
    window.pywebview.api.save_lyrics=async()=>({ok:true,lyrics:{source:'Prueba local',offset_ms:0,lrc:'[00:00]Una frase de prueba',lines:[{time:0,text:'Una frase de prueba para cantar'},{time:30,text:'La siguiente línea aparece aquí'}]}});
    document.getElementById('lyricsResults').textContent='Resultado temporal';
  });
  await page.locator('#lyricsSaveOffset').click();
  await page.waitForFunction(()=>!document.getElementById('lyricsSettings').open);
  if(await page.locator('#lyricsSettings').isVisible()) throw new Error('La configuración no se oculta');
  if(await page.locator('#lyricsResults').textContent()) throw new Error('Resultados antiguos tras guardar');
  const bounds=await page.locator('#stopButton').boundingBox();
  const chartBounds=await page.locator('#chartShell').boundingBox();
  if(chartBounds.height<450 || chartBounds.y+chartBounds.height>768) throw new Error('Altura del gráfico incorrecta');
  if(bounds.y+bounds.height>768) throw new Error('Controles fuera de la pantalla: '+JSON.stringify(bounds));
  await page.screenshot({path:path.join(root,'output/prueba_interfaz/practica_compacta.png')});
  await page.getByRole('button',{name:'Resultado',exact:true}).click();
  await page.locator('button[data-review="summary"]').click();
  if(await page.locator('#chartShell').isVisible()) throw new Error('Resumen muestra gráfico ocultable');
  await page.screenshot({path:path.join(root,'output/prueba_interfaz/resumen_vistas.png')});
  await page.getByRole('button',{name:'Historial',exact:true}).click();
  await page.locator('button[data-review="chart"]').click();
  if(!await page.locator('#takePlayer').isVisible()) throw new Error('Historial sin reproductor');
  if(await page.locator('#lyricsPanel').isVisible()) throw new Error('Letra invade evaluación');
  await page.screenshot({path:path.join(root,'output/prueba_interfaz/historial_vistas.png')});
  await page.evaluate(()=>{
    let collections=[];
    window.pywebview.api.library_info=async()=>({ok:true,collections,stats:{}});
    window.pywebview.api.change_collection=async(action,id,name,song,included)=>{
      if(action==='create') collections.push({id:'test',name,songs:[]});
      if(action==='membership') collections[0].songs=included?[song]:[];
      if(action==='delete') collections=[];
      return {ok:true,collections};
    };
  });
  await page.getByRole('button',{name:'Biblioteca',exact:true}).click();
  await page.locator('#libraryFolders').click();
  await page.locator('#collectionCreate').click();
  await page.getByRole('textbox',{name:'Nombre de la colección'}).fill('Práctica semanal');
  await page.getByRole('button',{name:'Crear',exact:true}).click();
  await page.waitForSelector('.collection-card');
  await page.locator('#songCollections').click();
  await page.locator('.collection-dialog input[type=checkbox]').check();
  await page.waitForFunction(()=>document.querySelector('.collection-card button').textContent.includes('1 canción'));
  await page.locator('.collection-dialog').getByRole('button',{name:'Salir',exact:true}).click();
  await page.locator('.collection-card button').first().click();
  if(await page.locator('#songList .song-card').count()!==1) throw new Error('Colección no filtra canciones');
  if(await page.locator('#collectionGrid').isVisible()) throw new Error('Carpetas visibles dentro de colección');
  if(await page.locator('#collectionTitle').textContent()!=='Práctica semanal') throw new Error('Falta nombre de colección');
  await page.locator('#librarySort').selectOption('count');
  await page.screenshot({path:path.join(root,'output/prueba_interfaz/colecciones.png')});
  await page.locator('#collectionBack').click();
  if(await page.locator('#librarySort').isVisible()) throw new Error('Orden de canciones visible en carpetas');
  page.once('dialog',d=>d.accept());
  await page.getByRole('button',{name:'Eliminar colección Práctica semanal',exact:true}).click();
  await page.waitForFunction(()=>!document.querySelector('.collection-card'));
  await page.locator('#libraryAll').click();
  if(!await page.locator('#songList .song-card').count()) throw new Error('Eliminar colección eliminó canciones');
  await page.getByRole('button',{name:'Contraer menú',exact:true}).click();
  await page.waitForTimeout(320);
  if(!await page.locator('.side-nav').isVisible()) throw new Error('Menú contraído desaparece');
  if(await page.locator('.side-nav .nav-icon').count()!==6) throw new Error('Faltan iconos');
  await page.locator('.app-nav').getByRole('button',{name:'Historial',exact:true}).click();
  if(await page.locator('body').getAttribute('data-view')!=='history') throw new Error('Iconos no navegan');
  await page.screenshot({path:path.join(root,'output/prueba_interfaz/menu_iconos.png')});
  await page.getByRole('button',{name:'Expandir menú',exact:true}).click();
  await browser.close();
  console.log('OK: resumen, fragmentos, desfase, cambio de toma, barra de carga y ajustes; sin errores JS.');
})().catch(e=>{console.error(e);process.exit(1);});

