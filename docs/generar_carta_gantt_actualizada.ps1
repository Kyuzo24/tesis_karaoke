$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$output = Join-Path $root "Carta Gantt_actualizada.xlsx"

$phases = @(
    @{ Code="F0001"; Name="Planificación, especificación y diseño"; Start=1; End=15; Status="Parcial"; Tasks=@(
        @{Code="T0001";Name="Definir problema, objetivos y alcance";Start=1;End=2;Status="Completada"},
        @{Code="T0002";Name="Explorar tecnologías y definir metodología";Start=1;End=3;Status="Completada"},
        @{Code="T0003";Name="Especificar requisitos e historias de usuario";Start=2;End=4;Status="Completada"},
        @{Code="T0004";Name="Diseñar arquitectura lógica y flujo general";Start=4;End=6;Status="Completada"},
        @{Code="T0005";Name="Actualizar alcance, objetivos y planificación";Start=13;End=15;Status="Completada"}
    )},
    @{ Code="F0002"; Name="Preparación de canciones y referencia"; Start=3; End=7; Status="Completada"; Tasks=@(
        @{Code="T0006";Name="Implementar catálogo y gestión de archivos";Start=3;End=4;Status="Completada"},
        @{Code="T0007";Name="Separar voz y acompañamiento con Demucs";Start=3;End=5;Status="Completada"},
        @{Code="T0008";Name="Generar pista instrumental";Start=4;End=5;Status="Completada"},
        @{Code="T0009";Name="Extraer y filtrar pitch de referencia";Start=4;End=6;Status="Completada"},
        @{Code="T0010";Name="Visualizar melodía esperada";Start=6;End=7;Status="Completada"}
    )},
    @{ Code="F0003"; Name="Sesión de canto y comparación base"; Start=6; End=15; Status="Parcial"; Tasks=@(
        @{Code="T0011";Name="Reproducir acompañamiento y capturar micrófono";Start=7;End=9;Status="Completada"},
        @{Code="T0012";Name="Detener y guardar interpretaciones";Start=9;End=10;Status="Completada"},
        @{Code="T0013";Name="Implementar alineación base mediante DTW";Start=8;End=10;Status="Parcial"},
        @{Code="T0014";Name="Calcular métricas globales de afinación";Start=10;End=11;Status="Completada"},
        @{Code="T0015";Name="Graficar comparación y guardar resultado JSON";Start=11;End=12;Status="Completada"},
        @{Code="T0016";Name="Implementar manejo inicial de errores";Start=12;End=15;Status="Parcial"}
    )},
    @{ Code="F0004"; Name="Interfaz prototipo e integración inicial"; Start=9; End=15; Status="Parcial"; Tasks=@(
        @{Code="T0017";Name="Construir interfaz básica con Tkinter";Start=9;End=11;Status="Completada"},
        @{Code="T0018";Name="Integrar catálogo y preparación de canciones";Start=10;End=12;Status="Completada"},
        @{Code="T0019";Name="Integrar grabación, métricas y gráficos";Start=12;End=14;Status="Completada"},
        @{Code="T0020";Name="Implementar diagnóstico técnico del pitch";Start=14;End=15;Status="Completada"},
        @{Code="T0021";Name="Registrar pruebas y evidencia del primer semestre";Start=14;End=15;Status="Parcial"}
    )},
    @{ Code="F0005"; Name="Detección de notas en tiempo real"; Start=16; End=19; Status="Pendiente"; Tasks=@(
        @{Code="T0022";Name="Implementar captura continua mediante bloques";Start=16;End=17;Status="Pendiente"},
        @{Code="T0023";Name="Estimar frecuencia fundamental en tiempo real";Start=16;End=18;Status="Pendiente"},
        @{Code="T0024";Name="Estabilizar y convertir pitch a nota musical";Start=18;End=19;Status="Pendiente"},
        @{Code="T0025";Name="Medir y ajustar latencia de visualización";Start=19;End=19;Status="Pendiente"}
    )},
    @{ Code="F0006"; Name="Análisis avanzado de la interpretación"; Start=18; End=23; Status="Pendiente"; Tasks=@(
        @{Code="T0026";Name="Refinar alineación y métricas temporales";Start=18;End=19;Status="Pendiente"},
        @{Code="T0027";Name="Detectar segmentos problemáticos dinámicos";Start=19;End=21;Status="Pendiente"},
        @{Code="T0028";Name="Caracterizar problemáticas de afinación";Start=21;End=22;Status="Pendiente"},
        @{Code="T0029";Name="Priorizar hallazgos por magnitud y duración";Start=22;End=23;Status="Pendiente"}
    )},
    @{ Code="F0007"; Name="Retroalimentación en lenguaje natural"; Start=22; End=25; Status="Pendiente"; Tasks=@(
        @{Code="T0030";Name="Construir hallazgos estructurados y trazables";Start=22;End=23;Status="Pendiente"},
        @{Code="T0031";Name="Generar retroalimentación mediante reglas y plantillas";Start=23;End=24;Status="Pendiente"},
        @{Code="T0032";Name="Evaluar incorporación de un LLM";Start=24;End=24;Status="Pendiente"},
        @{Code="T0033";Name="Validar coherencia y explicabilidad";Start=24;End=25;Status="Pendiente"}
    )},
    @{ Code="F0008"; Name="Persistencia, historial y evolución"; Start=20; End=25; Status="Pendiente"; Tasks=@(
        @{Code="T0034";Name="Definir modelo de datos y tecnología de persistencia";Start=20;End=21;Status="Pendiente"},
        @{Code="T0035";Name="Implementar repositorio estructurado de sesiones";Start=21;End=22;Status="Pendiente"},
        @{Code="T0036";Name="Comparar sesiones de una misma canción";Start=23;End=24;Status="Pendiente"},
        @{Code="T0037";Name="Visualizar evolución y resumir cambios";Start=24;End=25;Status="Pendiente"}
    )},
    @{ Code="F0009"; Name="Interfaz definitiva e integración"; Start=21; End=27; Status="Pendiente"; Tasks=@(
        @{Code="T0038";Name="Diseñar mockups y seleccionar tecnología gráfica";Start=21;End=22;Status="Pendiente"},
        @{Code="T0039";Name="Implementar vistas principales";Start=23;End=25;Status="Pendiente"},
        @{Code="T0040";Name="Implementar vistas de resultados e historial";Start=25;End=26;Status="Pendiente"},
        @{Code="T0041";Name="Integrar módulos y mejorar experiencia de uso";Start=26;End=27;Status="Pendiente"}
    )},
    @{ Code="F0010"; Name="Evaluación, correcciones y cierre"; Start=25; End=30; Status="Pendiente"; Tasks=@(
        @{Code="T0042";Name="Crear y ejecutar pruebas funcionales automatizadas";Start=25;End=27;Status="Pendiente"},
        @{Code="T0043";Name="Evaluar precisión, latencia y robustez";Start=26;End=28;Status="Pendiente"},
        @{Code="T0044";Name="Evaluar segmentos y retroalimentación";Start=27;End=28;Status="Pendiente"},
        @{Code="T0045";Name="Realizar prueba de usabilidad";Start=28;End=28;Status="Pendiente"},
        @{Code="T0046";Name="Aplicar correcciones y optimizaciones finales";Start=28;End=29;Status="Pendiente"},
        @{Code="T0047";Name="Definir distribución y preparar manuales";Start=29;End=29;Status="Pendiente"},
        @{Code="T0048";Name="Completar memoria y presentación final";Start=27;End=30;Status="Pendiente"}
    )},
    @{ Code="F0011"; Name="Documentación de memoria"; Start=1; End=30; Status="Parcial"; Tasks=@(
        @{Code="T0049";Name="Redactar formulación y fundamentos iniciales";Start=1;End=6;Status="Completada"},
        @{Code="T0050";Name="Documentar requisitos, arquitectura y avance";Start=12;End=15;Status="Completada"},
        @{Code="T0051";Name="Actualizar capítulos de metodología y desarrollo";Start=16;End=26;Status="Pendiente"},
        @{Code="T0052";Name="Redactar evaluación, resultados y conclusiones";Start=27;End=30;Status="Pendiente"}
    )}
)

$requirements = @(
    @("RF01","Gestionar catálogo de canciones","Funcional","Completado","Catálogo local cargado y visible en la interfaz"),
    @("RF02","Agregar una canción","Funcional","Completado","Copia de audio, metadatos e identificador único"),
    @("RF03","Preparar una canción","Funcional","Completado","Separación mediante Demucs implementada"),
    @("RF04","Generar pista instrumental","Funcional","Completado","Mezcla de stems instrumentales implementada"),
    @("RF05","Extraer pitch de referencia","Funcional","Completado","Extracción mediante Pyworld o pYIN"),
    @("RF06","Procesar pitch de referencia","Funcional","Completado","Filtros de rango, energía, duración y saltos"),
    @("RF07","Visualizar melodía esperada","Funcional","Completado","Gráfico de notas esperadas disponible"),
    @("RF08","Iniciar sesión de canto","Funcional","Completado","Flujo integrado desde la interfaz"),
    @("RF09","Reproducir acompañamiento","Funcional","Completado","Reproducción simultánea con captura"),
    @("RF10","Capturar audio en tiempo real","Funcional","Parcial","Existe grabación en tiempo real, no captura por bloques"),
    @("RF11","Detectar nota en tiempo real","Funcional","Pendiente","No implementado"),
    @("RF12","Estabilizar nota detectada","Funcional","Pendiente","No implementado"),
    @("RF13","Visualizar nota actual","Funcional","Pendiente","No implementado"),
    @("RF14","Finalizar sesión","Funcional","Completado","Detención manual mediante evento"),
    @("RF15","Guardar interpretación","Funcional","Completado","Grabaciones WAV asociadas a la canción"),
    @("RF16","Alinear interpretaciones","Funcional","Parcial","DTW base implementado; falta refinamiento y validación"),
    @("RF17","Calcular métricas","Funcional","Parcial","Métricas globales disponibles; faltan métricas temporales"),
    @("RF18","Detectar segmentos problemáticos","Funcional","Pendiente","No implementado"),
    @("RF19","Caracterizar problemas","Funcional","Pendiente","No implementado"),
    @("RF20","Priorizar hallazgos","Funcional","Pendiente","No implementado"),
    @("RF21","Generar retroalimentación","Funcional","Pendiente","No implementado"),
    @("RF22","Visualizar resultados","Funcional","Parcial","Métricas y curvas disponibles; faltan segmentos y feedback"),
    @("RF23","Guardar resultados","Funcional","Parcial","JSON básico disponible; falta estructura completa"),
    @("RF24","Gestionar errores operacionales","Funcional","Parcial","Manejo inicial implementado sin cobertura sistemática"),
    @("RF25","Diagnosticar calidad del pitch","Funcional","Completado","Diagnóstico crudo versus filtrado implementado"),
    @("RF26","Integrar un modelo de lenguaje","Funcional","Pendiente","Decisión abierta"),
    @("RF27","Comparar sesiones","Funcional","Pendiente","No implementado"),
    @("RF28","Visualizar evolución","Funcional","Pendiente","No implementado"),
    @("RF29","Resumir cambios entre sesiones","Funcional","Pendiente","No implementado"),
    @("RNF01","Usabilidad","No funcional","Parcial","Existe interfaz funcional; falta evaluación"),
    @("RNF02","Claridad de la retroalimentación","No funcional","Pendiente","Retroalimentación aún no implementada"),
    @("RNF03","Modularidad","No funcional","Completado","Responsabilidades separadas en módulos de audio"),
    @("RNF04","Evolución de la interfaz","No funcional","Parcial","Lógica separada parcialmente de Tkinter"),
    @("RNF05","Latencia de detección","No funcional","Pendiente","Detección en tiempo real aún no implementada"),
    @("RNF06","Continuidad de la interfaz","No funcional","Parcial","Procesos largos usan hilos; falta flujo en tiempo real"),
    @("RNF07","Rendimiento en tiempo real","No funcional","Pendiente","No evaluado"),
    @("RNF08","Robustez acústica","No funcional","Parcial","Filtros y casos sin datos; falta evaluación controlada"),
    @("RNF09","Persistencia local","No funcional","Parcial","Archivos locales disponibles; falta repositorio histórico"),
    @("RNF10","Privacidad","No funcional","Completado","Procesamiento y archivos permanecen localmente"),
    @("RNF11","Trazabilidad","No funcional","Parcial","Resultados asociados por carpeta; faltan hallazgos trazables"),
    @("RNF12","Explicabilidad","No funcional","Pendiente","No existen problemas ni feedback explicable"),
    @("RNF13","Mantenibilidad","No funcional","Parcial","Código modular, pero sin pruebas automatizadas"),
    @("RNF14","Dependencias externas","No funcional","Parcial","Demucs integrado; falta estrategia para fallos y LLM"),
    @("RNF15","Distribución","No funcional","Completado","Ejecución local mediante Python y archivo BAT"),
    @("RNF16","Disponibilidad sin conexión","No funcional","Completado","Funciones actuales operan localmente" )
)

$excel = $null
$workbook = $null
try {
    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $false
    $excel.DisplayAlerts = $false
    $workbook = $excel.Workbooks.Add()

    $gantt = $workbook.Worksheets.Item(1)
    $gantt.Name = "Carta Gantt"
    $audit = $workbook.Worksheets.Add()
    $audit.Name = "Avance requisitos"
    $gantt.Move($audit)

    $dark = 0x593B1F
    $header = 0x806040
    $semester1 = 0xE2F0D9
    $semester2 = 0xD9EAF7
    $completed = 0x70AD47
    $partial = 0x00C0FF
    $pending = 0xD9A26C
    $phaseFill = 0xE7E6E6
    $white = 0xFFFFFF
    $border = 0xA6A6A6

    $gantt.Range("A1:AI1").Merge()
    $gantt.Range("A1").Value2 = "Carta Gantt actualizada - Sistema de análisis vocal"
    $gantt.Range("A1").Font.Bold = $true
    $gantt.Range("A1").Font.Size = 16
    $gantt.Range("A1").Font.Color = $white
    $gantt.Range("A1").Interior.Color = $dark
    $gantt.Range("A1").HorizontalAlignment = -4108
    $gantt.Rows.Item(1).RowHeight = 28

    $taskList = @($phases | ForEach-Object { $_.Tasks } | ForEach-Object { $_ })
    $completeCount = @($taskList | Where-Object Status -eq "Completada").Count
    $partialCount = @($taskList | Where-Object Status -eq "Parcial").Count
    $taskProgress = [math]::Round((($completeCount + 0.5 * $partialCount) / $taskList.Count) * 100, 1)
    $taskProgressText = $taskProgress.ToString("0.0").Replace(".", ",")
    $gantt.Range("A2:E2").Merge()
    $gantt.Range("A2").Value2 = "Corte: fin semana 15 | Avance de tareas: $taskProgressText% | Requisitos completos: 35,6%"
    $gantt.Range("A2").Font.Bold = $true
    $gantt.Range("A2").Interior.Color = $phaseFill
    $gantt.Range("F2:T2").Merge()
    $gantt.Range("F2").Value2 = "Primer semestre - semanas 1 a 15"
    $gantt.Range("F2").Interior.Color = $semester1
    $gantt.Range("F2").Font.Bold = $true
    $gantt.Range("F2").HorizontalAlignment = -4108
    $gantt.Range("U2:AI2").Merge()
    $gantt.Range("U2").Value2 = "Segundo semestre - semanas 16 a 30"
    $gantt.Range("U2").Interior.Color = $semester2
    $gantt.Range("U2").Font.Bold = $true
    $gantt.Range("U2").HorizontalAlignment = -4108

    @("Código","Actividades","Semana inicio","Semana fin","Estado") | ForEach-Object -Begin {$i=1} -Process {
        $gantt.Cells.Item(3,$i).Value2 = $_; $i++
    }
    for ($week=1; $week -le 30; $week++) {
        $gantt.Cells.Item(3,$week+5).Value2 = "$week"
        $gantt.Cells.Item(3,$week+5).Interior.Color = $(if($week -le 15){$semester1}else{$semester2})
    }
    $gantt.Range("A3:AI3").Font.Bold = $true
    $gantt.Range("A3:AI3").HorizontalAlignment = -4108
    $gantt.Range("A3:AI3").VerticalAlignment = -4108
    $gantt.Range("A3:E3").Interior.Color = $header
    $gantt.Range("A3:E3").Font.Color = $white

    $row = 4
    foreach ($phase in $phases) {
        $gantt.Cells.Item($row,1).Value2 = $phase.Code
        $gantt.Cells.Item($row,2).Value2 = $phase.Name
        $gantt.Cells.Item($row,3).Value2 = "$($phase.Start)"
        $gantt.Cells.Item($row,4).Value2 = "$($phase.End)"
        $gantt.Cells.Item($row,5).Value2 = $phase.Status
        $gantt.Range("A$row:AI$row").Font.Bold = $true
        $gantt.Range("A$row:AI$row").Interior.Color = $phaseFill
        for ($week=$phase.Start; $week -le $phase.End; $week++) {
            $gantt.Cells.Item($row,$week+5).Interior.Color = $header
        }
        $row++
        foreach ($task in $phase.Tasks) {
            $gantt.Cells.Item($row,1).Value2 = $task.Code
            $gantt.Cells.Item($row,2).Value2 = $task.Name
            $gantt.Cells.Item($row,3).Value2 = "$($task.Start)"
            $gantt.Cells.Item($row,4).Value2 = "$($task.End)"
            $gantt.Cells.Item($row,5).Value2 = $task.Status
            $fill = switch ($task.Status) {
                "Completada" {$completed}
                "Parcial" {$partial}
                default {$pending}
            }
            for ($week=$task.Start; $week -le $task.End; $week++) {
                $gantt.Cells.Item($row,$week+5).Interior.Color = $fill
            }
            $row++
        }
    }

    $legendRow = $row + 1
    $gantt.Cells.Item($legendRow,2).Value2 = "Leyenda"
    $gantt.Cells.Item($legendRow,2).Font.Bold = $true
    $legend = @(@("Completada",$completed),@("Parcial",$partial),@("Pendiente",$pending))
    $col = 6
    foreach($item in $legend){
        $gantt.Cells.Item($legendRow,$col).Interior.Color = $item[1]
        $gantt.Cells.Item($legendRow,$col+1).Value2 = $item[0]
        $col += 3
    }
    $gantt.Cells.Item($legendRow+2,2).Value2 = "Nota: los requisitos parciales no se contabilizan como completados en el 35,6%."
    $gantt.Range($gantt.Cells.Item($legendRow+2,2),$gantt.Cells.Item($legendRow+2,12)).Merge()
    $gantt.Cells.Item($legendRow+2,2).Font.Italic = $true

    $lastRow = $legendRow + 2
    $gantt.Range("A3:AI$lastRow").Borders.Color = $border
    $gantt.Range("A3:AI$lastRow").Borders.LineStyle = 1
    $gantt.Range("U2:U$lastRow").Borders.Item(7).Weight = 4
    $gantt.Range("U2:U$lastRow").Borders.Item(7).Color = 0x0000C0
    $gantt.Columns.Item("A").ColumnWidth = 11
    $gantt.Columns.Item("B").ColumnWidth = 48
    $gantt.Columns.Item("C").ColumnWidth = 12
    $gantt.Columns.Item("D").ColumnWidth = 12
    $gantt.Columns.Item("E").ColumnWidth = 14
    $gantt.Range("F:AI").ColumnWidth = 3.2
    $gantt.Range("A3:AI$lastRow").VerticalAlignment = -4108
    $gantt.Range("B4:B$lastRow").WrapText = $true
    $gantt.Range("C4:E$lastRow").HorizontalAlignment = -4108
    $gantt.Application.ActiveWindow.SplitColumn = 5
    $gantt.Application.ActiveWindow.SplitRow = 3
    $gantt.Application.ActiveWindow.FreezePanes = $true
    $gantt.PageSetup.Orientation = 2
    $gantt.PageSetup.Zoom = $false
    $gantt.PageSetup.FitToPagesWide = 1
    $gantt.PageSetup.FitToPagesTall = $false
    $gantt.PageSetup.PrintArea = "A1:AI$lastRow"

    $audit.Range("A1:F1").Merge()
    $audit.Range("A1").Value2 = "Auditoría de avance de requisitos al cierre del primer semestre"
    $audit.Range("A1").Interior.Color = $dark
    $audit.Range("A1").Font.Color = $white
    $audit.Range("A1").Font.Bold = $true
    $audit.Range("A1").Font.Size = 15
    $audit.Range("A1").HorizontalAlignment = -4108
    $audit.Range("A2:F2").Merge()
    $audit.Range("A2").Value2 = "16 de 45 requisitos completados = 35,6%. Los requisitos parciales se muestran, pero no se suman al porcentaje."
    $audit.Range("A2").Interior.Color = $phaseFill
    $audit.Range("A2").Font.Bold = $true
    @("Código","Requisito","Tipo","Estado","Avance","Evidencia u observación") | ForEach-Object -Begin {$i=1} -Process {
        $audit.Cells.Item(4,$i).Value2 = $_; $i++
    }
    $audit.Range("A4:F4").Interior.Color = $header
    $audit.Range("A4:F4").Font.Color = $white
    $audit.Range("A4:F4").Font.Bold = $true
    $audit.Range("A4:F4").HorizontalAlignment = -4108
    $row = 5
    foreach($req in $requirements){
        for($col=1;$col -le 4;$col++){$audit.Cells.Item($row,$col).Value2=$req[$col-1]}
        $progress = switch($req[3]){"Completado"{1.0};"Parcial"{0.5};default{0.0}}
        $audit.Cells.Item($row,5).Value2 = $(if($progress -eq 1){"100%"}elseif($progress -eq 0.5){"50%"}else{"0%"})
        $audit.Cells.Item($row,6).Value2 = $req[4]
        $audit.Cells.Item($row,4).Interior.Color = switch($req[3]){"Completado"{$completed};"Parcial"{$partial};default{$pending}}
        $row++
    }
    $audit.Range("A4:F$($row-1)").Borders.Color = $border
    $audit.Range("A4:F$($row-1)").Borders.LineStyle = 1
    $audit.Columns.Item("A").ColumnWidth = 11
    $audit.Columns.Item("B").ColumnWidth = 36
    $audit.Columns.Item("C").ColumnWidth = 15
    $audit.Columns.Item("D").ColumnWidth = 14
    $audit.Columns.Item("E").ColumnWidth = 11
    $audit.Columns.Item("F").ColumnWidth = 62
    $audit.Range("A4:F$($row-1)").WrapText = $true
    $audit.Range("A4:F$($row-1)").VerticalAlignment = -4108
    $audit.Range("A4:E$($row-1)").HorizontalAlignment = -4108
    $audit.Application.ActiveWindow.SplitRow = 4
    $audit.Application.ActiveWindow.FreezePanes = $true
    $audit.PageSetup.Orientation = 2
    $audit.PageSetup.Zoom = $false
    $audit.PageSetup.FitToPagesWide = 1
    $audit.PageSetup.FitToPagesTall = $false

    $gantt.Activate()
    $workbook.SaveAs($output, 51)
    Write-Output "Archivo creado: $output"
    Write-Output "Tareas: $($taskList.Count) | Completadas: $completeCount | Parciales: $partialCount | Avance: $taskProgress%"
}
finally {
    if ($workbook) { $workbook.Close($false) }
    if ($excel) { $excel.Quit() }
    if ($audit) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($audit) }
    if ($gantt) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($gantt) }
    if ($workbook) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($workbook) }
    if ($excel) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel) }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
