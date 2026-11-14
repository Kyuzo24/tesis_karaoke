# Continuación del proyecto Karaoke Studio

Estado registrado el 14 de noviembre de 2026. Este archivo es una guía para retomar el trabajo; las conversaciones exportadas y el código conservan el detalle y deben consultarse cuando haga falta.

## Punto de partida en el nuevo PC

El usuario es Diego Tapia y está desarrollando su proyecto de titulación en Ingeniería Civil en Computación de la Universidad de Talca. Solicitó respaldar el proyecto y sus chats porque su PC presenta problemas, para continuar en otro equipo con el contexto disponible.

Abre este repositorio como proyecto en Codex y utiliza este mensaje:

> Lee CONTEXTO_PARA_CODEX.md, README.md y docs/contexto_codex/LEEME.md. Revisa el historial exportado pertinente antes de proponer cambios. Quiero continuar el proyecto de tesis desde su estado actual. Distingue lo implementado, lo propuesto en conversaciones antiguas y lo demostrado mediante pruebas. No des por completado un respaldo ni una validación sin comprobarlo.

## Estado del producto

Karaoke Studio es una aplicación de escritorio para la práctica del canto con una referencia musical. Combina backend Python y una interfaz HTML/CSS/JavaScript mostrada mediante pywebview. El punto de entrada del desarrollo es `desktop_live.py`; la interfaz está en `ui_live` y el procesamiento y almacenamiento en `audio`.

El flujo permite incorporar canciones locales o desde YouTube Music, separar voz e instrumental, obtener la referencia tonal, reproducir la instrumental y grabar al usuario, mostrar las notas durante el canto, comparar posteriormente la afinación y conservar tomas, resultados y retroalimentación por fragmentos. Consulta el código antes de atribuir características concretas: el historial abarca versiones anteriores.

Archivos relevantes:

- `audio/pitch.py`, `audio/alineacion.py`, `audio/comparacion.py`, `audio/metricas.py`: detección de frecuencia fundamental, alineación y comparación.
- `audio/segmentacion.py`, `audio/retroalimentacion.py`, `audio/explicaciones.py`: fragmentación y explicaciones.
- `audio/catalogo.py`, `audio/biblioteca.py`, `audio/tomas.py`: canciones, colecciones y grabaciones.
- `audio/youtube.py`, `instalar_youtube.bat`, `requirements-youtube.txt`: integración con YouTube en entorno separado.
- `scripts/`, `tests/`: evaluaciones, experimentos y pruebas.
- `packaging/`: generación del paquete e instalador para Windows. El instalador más reciente encontrado en origen es 1.0.2.

El entorno de audio de origen usaba Python 3.10. `requirements-entorno-original.txt` es un inventario de versiones, con incompatibilidades declaradas entre algunas dependencias; no debe presentarse como una instalación reproducible validada. El instalador incluye su propio entorno. No se ha probado la restauración en el nuevo PC.

## Conversaciones conservadas

El índice está en `docs/contexto_codex/indice.json`; hay transcripciones Markdown y registros JSONL de ocho chats, incluidos dos archivados. Los títulos son los mostrados por la aplicación durante el respaldo.

| Chat | ID | Contenido principal |
|---|---|---|
| Describe el proyecto | `019e8aa4-55db-7a22-841e-2c9a8d427c15` | Desarrollo de la aplicación, interfaz, análisis y gestión de tomas. |
| Crear documento de requisitos | `019e932f-de5f-7b72-bf7a-cf2c55f2673d` | Especificación de requisitos. |
| Formular memoria paso a paso | `019eb3a5-07e3-7163-a098-145f9d55e5f3` | Memoria, estructura, documentos, decisiones, presentación y defensa. |
| Busca datasets para detectar notas | `01a08154-4c27-7551-9cfa-e8e7d2bcf73a` | Evaluación y mejoras del algoritmo, conjuntos de datos y trabajo relacionado. |
| Analiza documentos de tesis | `01a1570f-a3cd-7de3-9846-8bfc7596f2ee` | Trabajo reciente sobre la memoria, objetivos y alcance. |
| Subir proyecto a GitHub | `01a1db86-a51a-7763-8f16-5a729e09225d` | Traslado a otro PC, respaldo del código, datos y chats. |

Los dos chats archivados adicionales aparecen con sus títulos originales en el índice; uno trata sobre incorporar un catálogo de canciones y comparar con la voz del usuario, y otro se llama «que puedes hacer».

## Último punto de trabajo académico identificado

En «Analiza documentos de tesis» se estaba revisando la estructura de la memoria final y, después, los objetivos y el alcance. La última consulta conservada del usuario pregunta si los objetivos originales deberían mantenerse o corregirse y si contienen palabras problemáticas, como «optimizar», que exijan demostrar un óptimo.

La respuesta previa propone conservar el propósito y precisar expresiones difíciles de evaluar: «técnicas adecuadas», «representación temporal estable», «en tiempo real», «desempeño vocal», «segmentos problemáticos», «detectar dinámicamente» y «priorizar». Son recomendaciones de revisión, no una aprobación final del usuario ni evidencia de que se cumplieron todos los objetivos.

El objetivo general citado en esa conversación es apoyar la práctica autodidacta mediante una aplicación de escritorio que detecte notas durante la interpretación, analice posteriormente la afinación respecto de una referencia, permita seguir la evolución e identifique segmentos para entregar retroalimentación comprensible. Antes de redactar su versión definitiva, contrastar la formulación original con los antecedentes, el código y la evidencia de evaluación.

Los antecedentes usados en ese hilo estaban fuera de la carpeta del código, en `Entrega Final`. Se incluyen copias en `docs/antecedentes_traslado/Entrega Final` para conservar el LaTeX de la entrega previa, la propuesta de estructura, la pauta y el formato de memoria. Las transcripciones pueden citar rutas antiguas del PC original.

En los hilos académicos el usuario ha pedido trabajar gradualmente y justificar los cambios técnicos y de alcance, con explicaciones útiles para la defensa. No presentar mejoras propuestas como implementadas ni afirmar eficacia pedagógica o evolución del usuario sin evidencia.

## Respaldo y restauración

Repositorio privado creado durante el traslado: `https://github.com/Kyuzo24/tesis_karaoke`.

El código y los documentos se guardan en Git. Los datos de trabajo se empaquetaron en seis `proyecto-*.zip` y un `perfil-aplicacion.zip`, con un manifiesto de tamaños y hashes SHA-256. También se preparó el instalador 1.0.2. Los ZIP se verificaron localmente y contienen 3205 archivos originales. La disponibilidad remota debe comprobarse en la sección Releases: durante el respaldo se detectaron tiempos de espera al subir a GitHub y no debe asumirse que los ZIP ya están publicados.

Las carpetas excluidas de Git incluyen `canciones`, `grabaciones`, `data`, `output` y `separated`, además de entornos y paquetes generados. Para restaurar el proyecto hacen falta las descargas de datos, además del código. Las referencias de algunas canciones apuntan a `output/htdemucs`; al trasladarlas a la versión instalada, conservar también esa estructura bajo su carpeta `Datos`.

Los historiales exportados permiten recuperar el contexto desde archivos. No se ha comprobado una importación nativa que restituya estos mismos chats en la barra lateral de otra instalación. La copia del chat de traslado es una instantánea y no incluye mensajes posteriores al momento de exportarla.
