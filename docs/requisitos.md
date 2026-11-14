# Documento de Requisitos - Sistema de Karaoke con Evaluacion de Afinacion

Version: 0.1  
Fecha: 2026-06-04  
Estado: Borrador inicial para revision conjunta

## 1. Proposito

Este documento especifica los requisitos de un sistema de karaoke de escritorio que permite cargar canciones, preparar pistas instrumentales, grabar la interpretacion vocal de un usuario y evaluar su afinacion comparando el pitch cantado contra una referencia extraida desde la voz original.

El documento busca servir como base para el desarrollo, validacion y documentacion academica del proyecto de tesis.

## 2. Alcance

El sistema debe permitir a un usuario ejecutar una aplicacion local, gestionar un catalogo de canciones, cantar sobre una pista instrumental generada automaticamente, obtener metricas de afinacion y visualizar graficamente la comparacion entre la melodia esperada y la interpretacion grabada.

El sistema se enfoca en la evaluacion de afinacion vocal. No busca evaluar interpretacion musical completa, ritmo con precision fonetica, calidad timbrica, pronunciacion, expresividad ni similitud de letra.

## 3. Objetivos Del Sistema

- Preparar canciones para karaoke separando la voz principal de la instrumental.
- Extraer una referencia de pitch desde la pista vocal original.
- Reproducir la instrumental mientras se graba el microfono del usuario.
- Extraer el pitch de la grabacion del usuario.
- Comparar el pitch del usuario contra la referencia usando alineamiento temporal.
- Entregar metricas cuantitativas y una visualizacion comprensible de la afinacion.
- Conservar canciones, metadatos, grabaciones y resultados para revision posterior.

## 4. Usuarios Y Actores

### Usuario principal

Persona que utiliza la aplicacion para cantar una cancion, grabar su voz y recibir retroalimentacion sobre afinacion.

### Evaluador o investigador

Persona que revisa los resultados generados por el sistema, analiza metricas, diagnostica el filtrado de pitch y valida el comportamiento del prototipo.

### Sistema externo

Modelo o herramienta de separacion de fuentes de audio, actualmente Demucs, utilizado para generar pistas vocales e instrumentales.

## 5. Supuestos

- La aplicacion se ejecuta localmente en un computador con Python instalado.
- El equipo cuenta con dispositivo de salida de audio y microfono funcional.
- El usuario utiliza audifonos durante la grabacion para reducir filtracion de la instrumental al microfono.
- Las canciones cargadas contienen una voz principal suficientemente clara para extraer pitch.
- Los archivos de audio usados por el usuario corresponden a material que puede utilizar en el contexto del proyecto.
- El procesamiento de separacion de audio puede tardar varios minutos por cancion.

## 6. Restricciones

- La aplicacion actual es de escritorio y utiliza interfaz Tkinter.
- La separacion de fuentes depende de Demucs y de los recursos disponibles del equipo.
- La comparacion se basa en pitch detectado; tramos sin pitch no son comparables.
- El sistema no valida automaticamente si el usuario canta la letra correcta.
- El sistema no garantiza evaluacion objetiva de calidad vocal general.
- La persistencia actual se basa en archivos locales y no en una base de datos.

## 7. Flujo General

1. El usuario abre la aplicacion.
2. El sistema carga el catalogo local de canciones.
3. El usuario agrega una cancion o selecciona una existente.
4. Si agrega una cancion, el sistema copia el audio, separa pistas, genera instrumental y extrae pitch de referencia.
5. El usuario inicia la sesion de canto.
6. El sistema reproduce la instrumental y graba el microfono.
7. El usuario detiene la grabacion o la cancion llega a su fin.
8. El sistema extrae pitch de la grabacion.
9. El sistema compara el pitch del usuario contra la referencia.
10. El sistema muestra metricas y grafico de comparacion.
11. El sistema guarda la grabacion y el resultado.

## 8. Requisitos Funcionales

### RF-01 - Cargar catalogo de canciones

El sistema debe cargar automaticamente las canciones registradas al iniciar la aplicacion.

Criterios de aceptacion:
- Dado que existen canciones con archivo `metadata.json`, cuando se abre la aplicacion, entonces se muestran en la lista de canciones disponibles.
- Dado que no existen canciones registradas, cuando se abre la aplicacion, entonces se muestra un mensaje indicando que se debe agregar una cancion.

### RF-02 - Agregar cancion al catalogo

El sistema debe permitir agregar una cancion desde un archivo de audio local.

Criterios de aceptacion:
- El usuario puede seleccionar archivos en formatos comunes de audio, como WAV, MP3, FLAC, OGG o M4A.
- El sistema solicita titulo y artista.
- El sistema crea un identificador unico para la cancion.
- El sistema copia el audio original a una carpeta propia dentro del catalogo.
- El sistema guarda metadatos de la cancion.

### RF-03 - Preparar pistas de karaoke

El sistema debe preparar una cancion separando la pista vocal y generando una pista instrumental.

Criterios de aceptacion:
- Al agregar una cancion, el sistema ejecuta separacion de fuentes mediante Demucs.
- El sistema conserva la pista vocal generada.
- El sistema crea una pista instrumental mezclando los stems no vocales.
- Si las pistas ya existen y no se solicita reprocesamiento, el sistema puede reutilizarlas.
- Si faltan stems necesarios, el sistema informa un error.

### RF-04 - Extraer pitch de referencia

El sistema debe extraer una secuencia temporal de pitch desde la pista vocal original.

Criterios de aceptacion:
- El sistema genera un archivo CSV de referencia con tiempo, frecuencia y nota.
- El sistema filtra segmentos fuera de rango vocal definido.
- El sistema filtra segmentos de baja energia.
- El sistema elimina segmentos demasiado cortos y saltos atipicos.
- Si no se detecta pitch suficiente, el sistema debe permitir informar el problema sin bloquear la aplicacion.

### RF-05 - Seleccionar cancion

El sistema debe permitir seleccionar una cancion del catalogo.

Criterios de aceptacion:
- Al seleccionar una cancion, el sistema muestra titulo, artista, estado de preparacion y pista instrumental asociada.
- Al seleccionar una cancion preparada, se habilitan las acciones de canto, reprocesamiento, eliminacion y diagnostico.
- Al seleccionar una cancion, el sistema muestra el grafico de notas esperadas cuando existe referencia de pitch.

### RF-06 - Reprocesar referencia

El sistema debe permitir regenerar el pitch de referencia de una cancion ya registrada.

Criterios de aceptacion:
- El usuario puede solicitar reprocesamiento desde la interfaz.
- El sistema pide confirmacion antes de reprocesar.
- El sistema regenera el CSV de pitch de referencia.
- Si falta la pista vocal, el sistema prepara nuevamente la cancion.
- Al finalizar, el sistema actualiza la visualizacion de notas esperadas.

### RF-07 - Eliminar cancion

El sistema debe permitir eliminar una cancion del catalogo.

Criterios de aceptacion:
- El sistema solicita confirmacion antes de eliminar.
- Al confirmar, el sistema elimina metadatos, audio preparado y grabaciones asociadas.
- La accion queda reflejada inmediatamente en la lista de canciones.

### RF-08 - Iniciar sesion de canto

El sistema debe permitir cantar sobre la pista instrumental de la cancion seleccionada.

Criterios de aceptacion:
- El sistema solicita confirmacion antes de iniciar la grabacion.
- Al iniciar, reproduce la instrumental y graba el microfono simultaneamente.
- Mientras graba, deshabilita acciones que puedan interferir con la sesion.
- Durante la reproduccion, actualiza un cursor visual sobre el grafico de notas esperadas.

### RF-09 - Detener grabacion

El sistema debe permitir detener una grabacion en curso.

Criterios de aceptacion:
- El usuario puede detener la grabacion antes de que termine la pista.
- El sistema detiene reproduccion y captura de audio.
- El sistema conserva solo la porcion efectivamente grabada.
- Luego de detener, el sistema inicia la comparacion automaticamente.

### RF-10 - Guardar grabacion

El sistema debe guardar la grabacion vocal del usuario.

Criterios de aceptacion:
- Cada grabacion se guarda como archivo WAV.
- El nombre de la grabacion incluye fecha y hora.
- La grabacion se almacena en una carpeta asociada a la cancion.

### RF-11 - Comparar afinacion

El sistema debe comparar el pitch de la grabacion del usuario contra el pitch de referencia.

Criterios de aceptacion:
- El sistema extrae pitch desde la grabacion del usuario.
- El sistema limita la referencia a la duracion grabada por el usuario.
- El sistema alinea ambas secuencias mediante DTW.
- El sistema descarta errores extremos no representativos.
- Si no existen datos suficientes, muestra un mensaje explicativo.

### RF-12 - Calcular metricas de resultado

El sistema debe calcular metricas cuantitativas de afinacion.

Criterios de aceptacion:
- El sistema calcula error promedio absoluto en cents.
- El sistema calcula desviacion estandar de errores en cents.
- El sistema determina tendencia general: estable, agudo, grave o sin datos.
- El sistema calcula porcentaje de puntos dentro de +/-50 cents.
- El sistema calcula porcentaje de puntos dentro de +/-100 cents.
- El sistema registra la cantidad de puntos comparados.

### RF-13 - Mostrar resultado al usuario

El sistema debe mostrar el resultado de la comparacion en la interfaz.

Criterios de aceptacion:
- El sistema presenta las metricas principales en texto.
- Si no fue posible comparar, el sistema muestra un mensaje claro.
- El estado de la interfaz vuelve a disponible al finalizar.

### RF-14 - Visualizar comparacion de pitch

El sistema debe graficar la referencia y la interpretacion del usuario.

Criterios de aceptacion:
- El grafico muestra tiempo en el eje horizontal.
- El grafico muestra notas musicales en el eje vertical.
- La referencia y el usuario se distinguen con colores y leyenda.
- Los silencios o huecos se representan como cortes visuales.

### RF-15 - Guardar resultado de comparacion

El sistema debe guardar el resultado de cada comparacion.

Criterios de aceptacion:
- El resultado se guarda como JSON junto a la grabacion.
- El JSON incluye metricas calculadas y datos necesarios para graficar.

### RF-16 - Diagnosticar filtrado de pitch

El sistema debe permitir diagnosticar el efecto de los filtros de pitch.

Criterios de aceptacion:
- El usuario puede ejecutar diagnostico sobre la referencia.
- Si existe una grabacion reciente, tambien se diagnostica la voz del usuario.
- El sistema informa puntos crudos, puntos filtrados y porcentaje conservado.
- El sistema grafica pitch crudo versus pitch filtrado.

### RF-17 - Manejar errores operativos

El sistema debe informar errores sin cerrar la aplicacion abruptamente.

Criterios de aceptacion:
- Si falla la separacion de audio, el sistema informa el problema.
- Si falta un archivo requerido, el sistema informa el problema.
- Si falla la grabacion o reproduccion, el sistema informa el problema.
- Luego de un error, la interfaz vuelve a un estado consistente.

## 9. Requisitos No Funcionales

### RNF-01 - Usabilidad

La interfaz debe permitir que un usuario no tecnico pueda cargar una cancion, cantar y obtener resultado sin usar la linea de comandos.

### RNF-02 - Claridad de retroalimentacion

Los resultados deben expresarse con unidades comprensibles y mensajes interpretables, evitando depender solo del grafico.

### RNF-03 - Rendimiento

La interfaz no debe bloquearse durante procesos largos como separacion de audio, reprocesamiento o diagnostico.

### RNF-04 - Persistencia local

El sistema debe conservar canciones, metadatos, grabaciones y resultados en archivos locales para permitir revision posterior.

### RNF-05 - Portabilidad limitada

El sistema debe poder ejecutarse en un entorno local Windows con Python y dependencias instaladas. La portabilidad a otros sistemas operativos queda fuera del alcance inicial.

### RNF-06 - Mantenibilidad

El codigo debe mantener separadas las responsabilidades de catalogo, separacion, extraccion de pitch, comparacion, grabacion y visualizacion.

### RNF-07 - Tolerancia a datos imperfectos

El sistema debe manejar audio con silencios, tramos sin pitch o detecciones incompletas sin producir fallos fatales.

### RNF-08 - Trazabilidad

Los resultados deben quedar asociados a la cancion y a la grabacion correspondiente.

## 10. Datos Del Sistema

### Cancion

Campos esperados:
- `id`: identificador unico.
- `titulo`: nombre de la cancion.
- `artista`: artista o interprete.
- `original`: ruta del audio original copiado al catalogo.
- `vocals`: ruta de la pista vocal separada.
- `instrumental`: ruta de la pista instrumental.
- `pitch_referencia`: ruta del CSV de pitch de referencia.
- `creada_en`: fecha y hora de registro.
- `preparada`: indicador booleano de preparacion.

### Pitch CSV

Columnas esperadas:
- `tiempo`: tiempo en segundos.
- `frecuencia`: frecuencia fundamental en Hz.
- `nota`: nota musical aproximada.

### Resultado JSON

Campos esperados:
- `error_prom`: error promedio absoluto en cents.
- `desviacion`: desviacion estandar en cents.
- `tendencia`: tendencia general de afinacion.
- `porcentaje_50`: porcentaje dentro de +/-50 cents.
- `porcentaje_100`: porcentaje dentro de +/-100 cents.
- `puntos_comparados`: cantidad de puntos usados.
- `grafico`: datos temporales y frecuencias de referencia y usuario.

## 11. Reglas De Negocio Y Calculo

- El pitch se considera valido solo si supera los filtros de rango vocal, energia, duracion minima y estabilidad.
- Las frecuencias se transforman a cents para medir diferencias relativas de afinacion.
- Una media firmada cercana a cero se interpreta como tendencia estable.
- Una media firmada positiva se interpreta como canto mas agudo que la referencia.
- Una media firmada negativa se interpreta como canto mas grave que la referencia.
- Los errores absolutos menores o iguales a 50 cents se consideran dentro de una tolerancia estricta.
- Los errores absolutos menores o iguales a 100 cents se consideran dentro de una tolerancia amplia.
- El alineamiento temporal permite comparar interpretaciones con diferencias de ritmo moderadas.

## 12. Casos De Uso Principales

### CU-01 - Agregar y preparar una cancion

Actor: Usuario principal  
Precondicion: La aplicacion esta abierta.  
Flujo:
1. El usuario presiona "Agregar cancion".
2. El usuario selecciona un archivo de audio.
3. El usuario ingresa titulo y artista.
4. El sistema copia el archivo al catalogo.
5. El sistema ejecuta separacion de fuentes.
6. El sistema genera la pista instrumental.
7. El sistema extrae pitch de referencia.
8. El sistema actualiza el catalogo.

Resultado esperado: La cancion queda disponible para cantar.

### CU-02 - Cantar y recibir evaluacion

Actor: Usuario principal  
Precondicion: Existe una cancion preparada.  
Flujo:
1. El usuario selecciona una cancion.
2. El sistema muestra informacion y notas esperadas.
3. El usuario presiona "Cantar y grabar".
4. El sistema reproduce instrumental y graba microfono.
5. El usuario presiona "Detener y comparar" o espera el fin de la pista.
6. El sistema extrae pitch del usuario.
7. El sistema compara contra referencia.
8. El sistema muestra metricas y grafico.
9. El sistema guarda grabacion y resultado.

Resultado esperado: El usuario obtiene retroalimentacion de afinacion.

### CU-03 - Diagnosticar filtros

Actor: Evaluador o investigador  
Precondicion: Existe una cancion preparada.  
Flujo:
1. El usuario selecciona una cancion.
2. El usuario presiona "Diagnosticar filtros".
3. El sistema calcula pitch crudo y filtrado.
4. El sistema informa conservacion de puntos.
5. El sistema grafica crudo versus filtrado.

Resultado esperado: El evaluador puede analizar si el filtrado esta eliminando demasiados o muy pocos puntos.

## 13. Criterios De Validacion Del Prototipo

- El sistema permite completar el flujo de agregar cancion, cantar y obtener resultado.
- El sistema genera archivos persistentes verificables para canciones, grabaciones y resultados.
- El sistema maneja canciones con silencios sin fallar.
- El sistema reporta "sin datos" cuando no hay pitch suficiente.
- El grafico de notas esperadas se actualiza durante la grabacion.
- El resultado JSON coincide con las metricas mostradas en la interfaz.

## 14. Riesgos

- La separacion de fuentes puede producir pistas vocales con artefactos que afecten la referencia.
- La captura del microfono puede contener ruido, latencia o filtracion de la instrumental.
- La deteccion de pitch puede fallar en voces graves, agudas, susurradas o con vibrato intenso.
- DTW puede alinear segmentos incorrectos si la interpretacion difiere demasiado de la referencia.
- El sistema puede producir una evaluacion numerica aparentemente precisa aunque la entrada sea acusticamente deficiente.

## 15. Fuera De Alcance Inicial

- Evaluacion de letra o pronunciacion.
- Evaluacion de ritmo silabico.
- Evaluacion de timbre, potencia, respiracion o tecnica vocal.
- Soporte multiusuario con cuentas.
- Sincronizacion con letras en pantalla.
- Ranking, puntaje gamificado o historial agregado.
- Exportacion formal de reportes.
- Base de datos relacional o almacenamiento en la nube.
- Aplicacion web o movil.

## 16. Preguntas Abiertas Para Pulir

- Se requiere convertir las metricas actuales a un puntaje final de 0 a 100?
- El sistema debe evaluar ritmo ademas de afinacion?
- La tesis necesita comparar el resultado contra evaluaciones humanas?
- Que formatos de audio se deben declarar oficialmente como soportados?
- Se debe definir una duracion maxima recomendada por cancion?
- Se debe incluir latencia de audio como variable de calibracion?
- Se necesita historial visible de grabaciones por cancion?
- Se debe permitir escuchar la grabacion del usuario desde la aplicacion?
- Se debe permitir exportar resultados para analisis estadistico?
- Que nivel de precision se espera demostrar experimentalmente?

