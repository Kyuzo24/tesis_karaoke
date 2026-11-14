import os
import threading
import logging
import time
import json
import re
import tempfile
from pathlib import Path

import numpy as np
import sounddevice as sd
import soundfile as sf
import webview

from audio.catalogo import (
    agregar_cancion,
    cargar_cancion,
    cargar_canciones,
    editar_cancion,
    eliminar_cancion,
    leer_pitch_csv,
    regenerar_pitch_referencia,
    preparar_cancion,
)
from audio.karaoke import comparar_grabacion, diagnosticar_filtros, grabar_con_instrumental
from audio.metricas import hz_to_midi
from audio.pitch import extraer_pitch_ligero_desde_audio
from audio.tomas import actualizar_toma, eliminar_toma, guardar_toma, listar_tomas


LIVE_PITCH_INTERVAL = 0.10
LIVE_PITCH_CHUNK = 0.24
LIVE_MAX_JUMP_MIDI = 7
LIVE_JUMP_RESET_SECONDS = 0.55


class GuidePreferences:
    def __init__(self):
        profile = Path(os.environ.get('LOCALAPPDATA') or Path.home())
        if os.environ.get('KARAOKE_INSTALLED') == '1':
            data = Path(os.environ.get('KARAOKE_DATA_DIR') or profile / 'Karaoke Studio' / 'Datos')
            preferences = data / 'Preferencias'
        else:
            preferences = profile / 'Karaoke Studio'
        self._marker = preferences / 'ocultar-guia'

    def guide_hidden(self):
        return self._marker.is_file()

    def set_guide_hidden(self, hidden):
        if hidden:
            self._marker.parent.mkdir(parents=True, exist_ok=True)
            self._marker.touch()
        else:
            self._marker.unlink(missing_ok=True)
        return self.guide_hidden()


class LiveBackend:
    def tutorial_seen(self):
        return self._guide_preferences._marker.with_name('tutorial-visto').is_file()

    def mark_tutorial_seen(self):
        marker = self._guide_preferences._marker.with_name('tutorial-visto')
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.touch()
        return True

    def guide_hidden(self):
        return self._guide_preferences.guide_hidden()

    def set_guide_hidden(self, hidden):
        return self._guide_preferences.set_guide_hidden(hidden)

    def library_info(self):
        from audio.biblioteca import informacion
        try:
            return {'ok':True, **informacion()}
        except Exception as exc:
            return {'ok':False,'error':str(exc)}

    def change_collection(self, action, collection_id='', name='', song_id='', included=True):
        from audio.biblioteca import cambiar
        try:
            return {'ok':True,'collections':cambiar(action,collection_id,name,song_id,included)}
        except Exception as exc:
            return {'ok':False,'error':str(exc)}

    def audio_devices(self, refresh=False):
        with self._lock:
            if self._estado['status'] in ('calibrating', 'preparing', 'recording', 'stopping'):
                return {'ok': False, 'error': 'Detén la grabación antes de actualizar dispositivos.'}
            try:
                # PortAudio on Windows retains the device inventory until reinitialized.
                if refresh:
                    sd._terminate()
                    sd._initialize()
                    self._restore_audio_selection()
                hosts = sd.query_hostapis()
                devices = [dict(id=i, name=d['name'], host=hosts[d['hostapi']]['name'],
                                input=d['max_input_channels']>0, output=d['max_output_channels']>0)
                           for i,d in enumerate(sd.query_devices())]
                # Windows exposes the same endpoint via MME, DirectSound and WASAPI.
                # Prefer the active WASAPI inventory, avoiding duplicate/legacy entries.
                wasapi=[d for d in devices if d['host']=='Windows WASAPI']
                if wasapi:
                    devices=wasapi
                selected=list(sd.default.device)
                for direction in range(2):
                    kind='input' if direction==0 else 'output'
                    if not any(d['id']==selected[direction] for d in devices):
                        host=next((h for h in hosts if h['name']=='Windows WASAPI'),None)
                        selected[direction]=host['default_'+kind+'_device'] if host else selected[direction]
                return dict(ok=True, devices=devices, selected=selected)
            except Exception as exc:
                return {'ok': False, 'error': str(exc)}

    def _restore_audio_selection(self):
        devices=sd.query_devices(); hosts=sd.query_hostapis()
        selected=[]
        for direction, key in enumerate(getattr(self, '_audio_selection', [None,None])):
            channel='max_input_channels' if direction==0 else 'max_output_channels'
            selected.append(next((i for i,d in enumerate(devices) if key==(d['name'],hosts[d['hostapi']]['name']) and d[channel]>0), -1))
        sd.default.device=selected

    def select_audio_devices(self, input_id, output_id):
        with self._lock:
            if self._estado['status'] in ('calibrating','preparing','recording','stopping'):
                return {'ok':False,'error':'Detén la grabación antes de cambiar dispositivos.'}
            try:
                ids=[int(input_id),int(output_id)]
                for i,direction in zip(ids,['input','output']):
                    if i < -1: raise ValueError('Dispositivo inválido.')
                    d=sd.query_devices(i if i>=0 else None,direction)
                    if d['max_'+direction+'_channels']<1: raise ValueError('Dispositivo incompatible.')
                # Validate the actual recording format before accepting this pair.
                sd.check_input_settings(device=ids[0] if ids[0]>=0 else None,channels=1,samplerate=44100)
                sd.check_output_settings(device=ids[1] if ids[1]>=0 else None,channels=2,samplerate=44100)
                hosts=sd.query_hostapis()
                self._audio_selection=[None if i<0 else (sd.query_devices(i)['name'],hosts[sd.query_devices(i)['hostapi']]['name']) for i in ids]
                sd.default.device=ids
                return {'ok':True}
            except Exception as exc:
                return {'ok':False,'error':str(exc)}

    def search_lyrics(self, title, artist):
        from audio.letras import buscar
        try:
            return {'ok': True, 'results': buscar(title, artist)}
        except Exception:
            return {'ok': False, 'error': 'No se pudo consultar LRCLIB. Revisa la conexión o importa un archivo LRC.'}

    def save_lyrics(self, song_id, text, offset_ms=0, source='Archivo LRC'):
        from audio.letras import guardar
        try:
            return {'ok': True, 'lyrics': guardar(cargar_cancion(song_id), text, offset_ms, source)}
        except Exception as exc:
            return {'ok': False, 'error': str(exc)}

    def set_alignment(self, song_id, take_id, milliseconds=0, mode="manual"):
        from audio.alineacion import guardar_ajuste
        from audio.tomas import _buscar_toma
        try:
            toma = _buscar_toma(cargar_cancion(song_id), take_id)
            guardar_ajuste(toma['voice_path'], milliseconds, modo=mode)
            return {'ok': True}
        except (ValueError, TypeError):
            return {'ok': False, 'error': 'Introduce un desfase entre −2000 y 2000 ms.'}
        except Exception:
            return {'ok': False, 'error': 'No se pudo guardar el desfase.'}
    def _progreso_preparacion(self, mensaje):
        with self._lock:
            self._estado['preparation_message'] = mensaje

    def get_preparation_state(self):
        with self._lock:
            message = self._estado.get('preparation_message', 'Preparando canción…')
            match = re.search(r': (\d+)%', message)
            return {'status': self._estado['status'], 'message': message,
                    'percent': int(match[1]) if match else None}

    def get_feedback(self, song_id, take_id):
        from audio.explicaciones import panel
        for intento in range(2):
            try:
                return {'ok': True, **panel(cargar_cancion(song_id), take_id)}
            except Exception as exc:
                # A result file can still be being written when the UI requests it.
                if intento == 0 and isinstance(exc, (OSError, json.JSONDecodeError)):
                    time.sleep(0.15)
                    continue
                logger = logging.getLogger('karaoke.analysis')
                if not logger.handlers:
                    try:
                        Path('output').mkdir(exist_ok=True)
                        handler = logging.FileHandler('output/errores_analisis.log', encoding='utf-8')
                        handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
                        logger.addHandler(handler)
                    except OSError:
                        logger.addHandler(logging.StreamHandler())
                logger.exception('No se pudo cargar canción=%s toma=%s', song_id, take_id)
                return {'ok': False, 'error': 'No se pudo cargar el análisis. Tu grabación se conserva. Pulsa Volver a cargar; si persiste, revisaremos el registro de errores.'}

    def explain_take(self, song_id, take_id, fragment_id=None):
        from audio.explicaciones import explicar
        try:
            return {'ok': True, **explicar(cargar_cancion(song_id), take_id, fragment_id)}
        except Exception:
            return {'ok': False, 'error': 'No se pudo preparar la explicación. Vuelve a intentarlo.'}

    def __init__(self):
        self._lock = threading.Lock()
        self._guide_preferences = GuidePreferences()
        self._detener = threading.Event()
        self._hilo = None
        self._pitch_pendiente = []
        self._ultimo_punto_usuario = None
        self._estado = self._estado_inicial()
        threading.Thread(target=self._calentar_pitch_tiempo_real, daemon=True).start()

    def _estado_inicial(self):
        return {
            "status": "idle",
            "current": 0.0,
            "duration": 0.0,
            "song_id": None,
            "recording_path": None,
            "result": None,
            "error": None,
            "diagnostics": self._diagnostico_inicial(),
        }

    def _diagnostico_inicial(self):
        return {
            "noise_floor": 0.0,
            "last_rms": 0.0,
            "energy_threshold": 0.0,
            "raw_points": 0,
            "filtered_points": 0,
            "accepted_points": 0,
            "rejected_points": 0,
            "rejected_jumps": 0,
            "pitch_errors": 0,
        }

    def get_songs(self):
        return [self._cancion_para_ui(cancion) for cancion in cargar_canciones()]

    def get_takes(self, song_id):
        try:
            cancion = cargar_cancion(song_id)
            return [self._toma_para_ui(cancion, toma) for toma in listar_tomas(cancion)]
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def edit_take(self, song_id, take_id, name=""):
        with self._lock:
            if self._tarea_en_curso():
                return {"ok": False, "error": "Hay una tarea de audio en curso."}
            self._estado = {
                **self._estado_inicial(),
                "status": "editing",
                "song_id": song_id,
            }

        try:
            cancion = cargar_cancion(song_id)
            toma = actualizar_toma(cancion, take_id, nombre=name)
            with self._lock:
                self._estado = self._estado_inicial()
            return {"ok": True, "take": self._toma_para_ui(cancion, toma)}
        except Exception as exc:
            with self._lock:
                self._estado = {
                    **self._estado_inicial(),
                    "status": "error",
                    "error": str(exc),
                }
            return {"ok": False, "error": str(exc)}

    def set_take_favorite(self, song_id, take_id, favorite):
        with self._lock:
            if self._tarea_en_curso():
                return {"ok": False, "error": "Hay una tarea de audio en curso."}
            self._estado = {
                **self._estado_inicial(),
                "status": "editing",
                "song_id": song_id,
            }

        try:
            cancion = cargar_cancion(song_id)
            toma = actualizar_toma(cancion, take_id, favorita=bool(favorite))
            with self._lock:
                self._estado = self._estado_inicial()
            return {"ok": True, "take": self._toma_para_ui(cancion, toma)}
        except Exception as exc:
            with self._lock:
                self._estado = {
                    **self._estado_inicial(),
                    "status": "error",
                    "error": str(exc),
                }
            return {"ok": False, "error": str(exc)}

    def delete_take(self, song_id, take_id):
        with self._lock:
            if self._tarea_en_curso():
                return {"ok": False, "error": "Hay una tarea de audio en curso."}
            self._estado = {
                **self._estado_inicial(),
                "status": "deleting",
                "song_id": song_id,
            }

        try:
            cancion = cargar_cancion(song_id)
            eliminar_toma(cancion, take_id)
            with self._lock:
                self._estado = self._estado_inicial()
            return {"ok": True, "takes": self.get_takes(song_id)}
        except Exception as exc:
            with self._lock:
                self._estado = {
                    **self._estado_inicial(),
                    "status": "error",
                    "error": str(exc),
                }
            return {"ok": False, "error": str(exc)}

    def select_audio_file(self):
        with self._lock:
            if self._tarea_en_curso():
                return {"ok": False, "error": "Hay una tarea de audio en curso."}

        ruta_audio = self._seleccionar_audio()
        if not ruta_audio:
            return {"ok": False, "cancelled": True}

        ruta = Path(ruta_audio)
        return {
            "ok": True,
            "path": str(ruta),
            "filename": ruta.name,
            "suggested_title": ruta.stem.replace("_", " ").replace("-", " ").strip(),
        }

    def search_youtube(self, query):
        from audio.youtube import buscar_videos
        try:
            return {'ok': True, 'results': buscar_videos(query)}
        except Exception as exc:
            return {'ok': False, 'error': str(exc)}

    def add_song_from_youtube(self, video_id, title, artist=''):
        from audio.youtube import descargar_audio, validar_id
        try:
            video_id = validar_id(video_id)
            title = str(title or '').strip()
            artist = str(artist or '').strip()
            if not title:
                raise ValueError('Ingresa un título para la canción.')
        except ValueError as exc:
            return {'ok': False, 'error': str(exc)}
        with self._lock:
            if self._tarea_en_curso():
                return {'ok': False, 'error': 'Hay una tarea de audio en curso.'}
            self._estado = {**self._estado_inicial(), 'status': 'adding',
                            'preparation_message': 'Conectando con YouTube…'}
        try:
            existing = next((s for s in cargar_canciones()
                             if (s.get('fuente') or {}).get('provider') == 'youtube'
                             and (s.get('fuente') or {}).get('video_id') == video_id), None)
            if existing:
                # A failed preparation retains the original and can be retried.
                cancion = existing if existing.get('preparada') else preparar_cancion(
                    existing['id'], progreso_callback=self._progreso_preparacion)
            else:
                with tempfile.TemporaryDirectory(prefix='karaoke-youtube-') as folder:
                    downloaded = descargar_audio(video_id, folder, self._progreso_preparacion)
                    cancion = agregar_cancion(downloaded['path'], title, artist,
                        progreso_callback=self._progreso_preparacion, fuente=downloaded['source'])
            song_ui = self._cancion_para_ui(cancion)
            with self._lock:
                self._estado = self._estado_inicial()
            return {'ok': True, 'song': song_ui, 'reused': bool(existing)}
        except Exception as exc:
            logging.exception('Error importando canción de YouTube')
            with self._lock:
                self._estado = {**self._estado_inicial(), 'status': 'error', 'error': str(exc)}
            return {'ok': False, 'error': str(exc)}

    def add_song_from_file(self, audio_path, title, artist=""):
        title = str(title or "").strip()
        artist = str(artist or "").strip()
        audio_path = str(audio_path or "").strip()
        if not title:
            return {"ok": False, "error": "Ingresa un titulo para la cancion."}
        if not audio_path:
            return {"ok": False, "error": "Selecciona un archivo de audio."}
        if not Path(audio_path).exists():
            return {"ok": False, "error": "El archivo seleccionado ya no esta disponible."}

        with self._lock:
            if self._tarea_en_curso():
                return {"ok": False, "error": "Hay una tarea de audio en curso."}
            self._estado = {
                **self._estado_inicial(),
                "status": "adding",
            }

        try:
            cancion = agregar_cancion(audio_path, title, artist, progreso_callback=self._progreso_preparacion)
            song_ui = self._cancion_para_ui(cancion)
            with self._lock:
                self._estado = self._estado_inicial()
            return {"ok": True, "song": song_ui}
        except Exception as exc:
            with self._lock:
                self._estado = {
                    **self._estado_inicial(),
                    "status": "error",
                    "error": str(exc),
                }
            return {"ok": False, "error": str(exc)}


    def delete_song(self, song_id):
        with self._lock:
            if self._tarea_en_curso():
                return {"ok": False, "error": "Hay una tarea de audio en curso."}
            self._estado = {
                **self._estado_inicial(),
                "status": "deleting",
                "song_id": song_id,
            }

        try:
            eliminar_cancion(song_id)
            with self._lock:
                self._estado = self._estado_inicial()
            return {"ok": True, "songs": self.get_songs()}
        except Exception as exc:
            with self._lock:
                self._estado = {
                    **self._estado_inicial(),
                    "status": "error",
                    "error": str(exc),
                }
            return {"ok": False, "error": str(exc)}

    def edit_song(self, song_id, title, artist=""):
        title = str(title or "").strip()
        artist = str(artist or "").strip()
        if not title:
            return {"ok": False, "error": "Ingresa un titulo para la cancion."}

        with self._lock:
            if self._tarea_en_curso():
                return {"ok": False, "error": "Hay una tarea de audio en curso."}
            self._estado = {
                **self._estado_inicial(),
                "status": "editing",
                "song_id": song_id,
            }

        try:
            cancion = editar_cancion(song_id, title, artist)
            song_ui = self._cancion_para_ui(cancion)
            with self._lock:
                self._estado = self._estado_inicial()
            return {"ok": True, "song": song_ui, "songs": self.get_songs()}
        except Exception as exc:
            with self._lock:
                self._estado = {
                    **self._estado_inicial(),
                    "status": "error",
                    "error": str(exc),
                }
            return {"ok": False, "error": str(exc)}

    def reprocess_song(self, song_id):
        with self._lock:
            if self._tarea_en_curso():
                return {"ok": False, "error": "Hay una tarea de audio en curso."}
            self._estado = {
                **self._estado_inicial(),
                "status": "reprocessing",
                "song_id": song_id,
            }

        try:
            cancion = regenerar_pitch_referencia(song_id, progreso_callback=self._progreso_preparacion)
            song_ui = self._cancion_para_ui(cancion)
            with self._lock:
                self._estado = self._estado_inicial()
            return {"ok": True, "song": song_ui}
        except Exception as exc:
            with self._lock:
                self._estado = {
                    **self._estado_inicial(),
                    "status": "error",
                    "error": str(exc),
                }
            return {"ok": False, "error": str(exc)}

    def start_session(self, song_id):
        with self._lock:
            if self._tarea_en_curso():
                return {"ok": False, "error": "Ya hay una tarea de audio en curso."}

        try:
            cancion = cargar_cancion(song_id)
            if not cancion.get("preparada"):
                return {"ok": False, "error": "La cancion no esta preparada."}
            if not os.path.exists(cancion.get("instrumental", "")):
                return {"ok": False, "error": "No existe la pista instrumental."}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

        self._detener.clear()
        with self._lock:
            self._pitch_pendiente = []
            self._ultimo_punto_usuario = None
            self._estado = {
                "status": "calibrating",
                "current": 0.0,
                "duration": self._duracion_cancion(cancion),
                "song_id": song_id,
                "recording_path": None,
                "result": None,
                "error": None,
                "diagnostics": self._diagnostico_inicial(),
            }

        self._hilo = threading.Thread(
            target=self._ejecutar_sesion,
            args=(cancion,),
            daemon=True,
        )
        self._hilo.start()
        return {"ok": True, "state": self.get_session_state()}

    def stop_session(self):
        self._detener.set()
        with self._lock:
            if self._estado["status"] in ["calibrating", "preparing", "recording"]:
                self._estado["status"] = "stopping"
        return {"ok": True}

    def get_session_state(self):
        with self._lock:
            estado = dict(self._estado)
            estado["pitch_points"] = list(self._pitch_pendiente)
            self._pitch_pendiente = []
        return estado

    def get_status(self):
        entrada, salida = self._dispositivos_por_defecto()
        return {
            "backend": "Python",
            "ui": "pywebview",
            "ready": True,
            "input_device": entrada,
            "output_device": salida,
        }

    def get_reference_diagnostics(self, song_id):
        try:
            cancion = cargar_cancion(song_id)
            diagnostico = diagnosticar_filtros(cancion)
            return {
                "ok": True,
                "diagnostic": self._diagnostico_referencia_para_ui(diagnostico["referencia"]),
            }
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def _ejecutar_sesion(self, cancion):
        try:
            ruta_grabacion = grabar_con_instrumental(
                cancion,
                detener_evento=self._detener,
                progreso_callback=self._actualizar_progreso,
                pitch_callback=self._agregar_pitch_usuario,
                diagnostico_callback=self._actualizar_diagnostico_live,
                intervalo_pitch=LIVE_PITCH_INTERVAL,
                segundos_chunk_pitch=LIVE_PITCH_CHUNK,
                usar_filtro_aprendido=True,
            )

            with self._lock:
                self._estado["status"] = "comparing"
                self._estado["recording_path"] = ruta_grabacion

            resultado = comparar_grabacion(cancion, ruta_grabacion)
            resultado_ui = self._resultado_para_ui(resultado)
            with self._lock:
                diagnostico = dict(self._estado.get("diagnostics") or {})
            toma = guardar_toma(cancion, ruta_grabacion, resultado, diagnostico)
            resultado_ui["take"] = self._toma_para_ui(cancion, toma)

            with self._lock:
                self._estado["status"] = "finished"
                self._estado["result"] = resultado_ui
        except Exception as exc:
            with self._lock:
                self._estado["status"] = "error"
                self._estado["error"] = str(exc)

    def _actualizar_progreso(self, tiempo):
        with self._lock:
            if self._estado["status"] in ["calibrating", "preparing"]:
                self._estado["status"] = "recording"
            self._estado["current"] = float(tiempo)

    def _agregar_pitch_usuario(self, tiempos, frecuencias):
        midi = hz_to_midi(frecuencias)
        puntos = sorted(
            (
                [float(t), float(m)]
                for t, m in zip(tiempos, midi)
                if not np.isnan(m)
            ),
            key=lambda punto: punto[0],
        )
        aceptados = []
        rechazados_salto = 0
        with self._lock:
            for punto in puntos:
                if self._aceptar_punto_usuario(punto):
                    aceptados.append(punto)
                else:
                    rechazados_salto += 1

            self._pitch_pendiente.extend(aceptados)
            if len(self._pitch_pendiente) > 300:
                self._pitch_pendiente = self._pitch_pendiente[-300:]
            diagnostico = dict(self._estado.get("diagnostics") or self._diagnostico_inicial())
            diagnostico["accepted_points"] += len(aceptados)
            diagnostico["rejected_jumps"] += rechazados_salto
            diagnostico["rejected_points"] += rechazados_salto
            self._estado["diagnostics"] = diagnostico

    def _aceptar_punto_usuario(self, punto):
        tiempo, midi = punto
        if self._ultimo_punto_usuario is None:
            self._ultimo_punto_usuario = punto
            return True

        tiempo_anterior, midi_anterior = self._ultimo_punto_usuario
        delta_t = tiempo - tiempo_anterior
        if delta_t <= 0:
            return False
        if delta_t > LIVE_JUMP_RESET_SECONDS:
            self._ultimo_punto_usuario = punto
            return True
        if abs(midi - midi_anterior) > LIVE_MAX_JUMP_MIDI:
            return False

        self._ultimo_punto_usuario = punto
        return True

    def _actualizar_diagnostico_live(self, info):
        with self._lock:
            diagnostico = dict(self._estado.get("diagnostics") or self._diagnostico_inicial())
            diagnostico["noise_floor"] = float(info.get("noise_floor", diagnostico["noise_floor"]))
            diagnostico["last_rms"] = float(info.get("rms", diagnostico["last_rms"]))
            diagnostico["energy_threshold"] = float(info.get("energy_threshold", diagnostico["energy_threshold"]))
            diagnostico["raw_points"] += int(info.get("raw_points", 0))
            diagnostico["filtered_points"] += int(info.get("filtered_points", 0))
            diagnostico["rejected_points"] += int(info.get("rejected_points", 0))
            diagnostico["pitch_errors"] += int(info.get("pitch_errors", 0))
            self._estado["diagnostics"] = diagnostico

    def _resultado_para_ui(self, resultado):
        grafico = resultado.get("grafico") or {}
        salida = {
            "error_prom": resultado.get("error_prom"),
            "desviacion": resultado.get("desviacion"),
            "tendencia": resultado.get("tendencia"),
            "porcentaje_50": resultado.get("porcentaje_50"),
            "porcentaje_100": resultado.get("porcentaje_100"),
            "puntos_comparados": resultado.get("puntos_comparados"),
            "error_medio_firmado": resultado.get("error_medio_firmado"),
            "mensaje": resultado.get("mensaje"),
            "points_ref": self._puntos_hz_a_midi(
                grafico.get("t_ref", []),
                grafico.get("f_ref", []),
            ),
            "points_user": self._puntos_hz_a_midi(
                grafico.get("t_usr", []),
                grafico.get("f_usr", []),
            ),
        }
        return salida

    def _puntos_hz_a_midi(self, tiempos, frecuencias):
        midi = hz_to_midi(frecuencias)
        return [
            [float(t), float(m)]
            for t, m in zip(tiempos, midi)
            if not np.isnan(m)
        ]

    def _diagnostico_referencia_para_ui(self, diagnostico):
        crudos = self._puntos_hz_a_midi(
            diagnostico.get("t_crudo", []),
            diagnostico.get("f_crudo", []),
        )
        filtrados = self._puntos_hz_a_midi(
            diagnostico.get("t_filtrado", []),
            diagnostico.get("f_filtrado", []),
        )
        corregidos = self._puntos_hz_a_midi(
            diagnostico.get("t_corregido", []),
            diagnostico.get("f_corregido", []),
        )
        return {
            "path": diagnostico.get("ruta", ""),
            "raw_count": int(diagnostico.get("puntos_crudos", 0)),
            "filtered_count": int(diagnostico.get("puntos_filtrados", 0)),
            "corrected_count": int(diagnostico.get("puntos_corregidos", 0)),
            "octave_corrections": int(diagnostico.get("correcciones_octava", 0)),
            "retention": float(diagnostico.get("conservacion", 0.0)),
            "points_raw": self._reducir_puntos(crudos, max_puntos=3500),
            "points_filtered": self._reducir_puntos(filtrados, max_puntos=3500),
            "points_corrected": self._reducir_puntos(corregidos, max_puntos=3500),
        }

    def _duracion_cancion(self, cancion):
        for key in ["instrumental", "original", "vocals"]:
            ruta = cancion.get(key)
            if ruta and os.path.exists(ruta):
                try:
                    return float(sf.info(ruta).duration)
                except RuntimeError:
                    continue
        return 0

    def _puntos_referencia(self, cancion):
        ruta = cancion.get("pitch_referencia")
        if not ruta or not os.path.exists(ruta):
            return []

        tiempos, frecuencias = leer_pitch_csv(ruta)
        midi = hz_to_midi(frecuencias)
        puntos = [
            [float(t), float(m)]
            for t, m in zip(tiempos, midi)
            if not np.isnan(m)
        ]
        return self._reducir_puntos(puntos, max_puntos=3500)

    def _reducir_puntos(self, puntos, max_puntos=900):
        if len(puntos) <= max_puntos:
            return puntos
        salto = max(1, int(np.ceil(len(puntos) / max_puntos)))
        return puntos[::salto]

    def _cancion_para_ui(self, cancion):
        from audio.letras import cargar as cargar_letra
        return {
            "lyrics": cargar_letra(cancion),
            "id": cancion["id"],
            "title": cancion.get("titulo", "Sin titulo"),
            "artist": cancion.get("artista") or "Sin artista",
            "duration": self._duracion_cancion(cancion),
            "prepared": bool(cancion.get("preparada")),
            "points": self._puntos_referencia(cancion),
        }

    def _toma_para_ui(self, cancion, toma):
        metricas = toma.get("metrics") or {}
        grafico = toma.get("graph") or {}
        puntos_ref = self._puntos_hz_a_midi(
            grafico.get("t_ref", []),
            grafico.get("f_ref", []),
        )
        puntos_user = self._puntos_hz_a_midi(
            grafico.get("t_usr", []),
            grafico.get("f_usr", []),
        )
        return {
            "id": toma["id"],
            "song_id": cancion["id"],
            "name": toma.get("name", ""),
            "favorite": bool(toma.get("favorite")),
            "created_at": toma.get("created_at", ""),
            "duration": float(toma.get("duration") or 0),
            "voice_url": self._archivo_url(toma.get("voice_path", "")),
            "instrumental_url": self._archivo_url(cancion.get("instrumental", "")),
            "metrics": metricas,
            "points_ref": self._reducir_puntos(puntos_ref, max_puntos=3500),
            "points_user": self._reducir_puntos(puntos_user, max_puntos=3500),
            "preview_ref": self._reducir_puntos(puntos_ref, max_puntos=80),
            "preview_user": self._reducir_puntos(puntos_user, max_puntos=80),
        }

    def _tarea_en_curso(self):
        return self._estado["status"] in [
            "adding",
            "deleting",
            "calibrating",
            "preparing",
            "recording",
            "stopping",
            "comparing",
            "reprocessing",
            "editing",
        ]

    def _seleccionar_audio(self):
        if not webview.windows:
            return ""

        rutas = webview.windows[0].create_file_dialog(
            webview.FileDialog.OPEN,
            allow_multiple=False,
            file_types=(
                "Audio (*.wav;*.mp3;*.flac;*.ogg;*.m4a)",
                "Todos los archivos (*.*)",
            ),
        )
        if not rutas:
            return ""
        return str(rutas[0])

    def _archivo_url(self, ruta):
        if not ruta:
            return ""
        try:
            return Path(ruta).resolve().as_uri()
        except ValueError:
            return ""

    def _dispositivos_por_defecto(self):
        try:
            default_input, default_output = sd.default.device
        except Exception:
            return "No detectado", "No detectado"

        return (
            self._nombre_dispositivo(default_input),
            self._nombre_dispositivo(default_output),
        )

    def _nombre_dispositivo(self, indice):
        try:
            if indice is None or int(indice) < 0:
                return "No detectado"
            dispositivo = sd.query_devices(int(indice))
            return dispositivo.get("name", "No detectado")
        except Exception:
            return "No detectado"

    def _calentar_pitch_tiempo_real(self):
        try:
            sr = 44100
            t = np.arange(int(sr * 0.22), dtype=float) / sr
            senal = 0.05 * np.sin(2 * np.pi * 440.0 * t)
            extraer_pitch_ligero_desde_audio(senal, sr, usar_filtro_aprendido=True)
        except Exception:
            pass


def main():
    os.chdir(os.environ.get('KARAOKE_DATA_DIR') or Path(__file__).parent)
    if os.name == 'nt':
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('KaraokeStudio.Desktop')
    html_path = Path(__file__).parent / "ui_live" / "index.html"
    backend = LiveBackend()
    window = webview.create_window(
        "Karaoke Studio",
        html_path.resolve().as_uri(),
        js_api=backend,
        width=1280,
        height=820,
        min_size=(980, 620),
    )
    webview.start(debug=False, icon=str(html_path.with_name('icon.ico')))
    return window


if __name__ == "__main__":
    main()
