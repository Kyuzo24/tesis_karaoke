$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$output = Join-Path $root "Carta Gantt_entrega.xlsx"

$phases = @(
    @{Code="F0001";Name="Planificación y diseño";Start=1;End=5;Status="Completada";Tasks=@(
        @{Code="T0001";Name="Definición de objetivos y alcance";Start=1;End=2;Status="Completada"},
        @{Code="T0002";Name="Selección de tecnologías y metodología";Start=1;End=3;Status="Completada"},
        @{Code="T0003";Name="Definición de requisitos e historias de usuario";Start=2;End=4;Status="Completada"},
        @{Code="T0004";Name="Diseño de arquitectura y planificación";Start=4;End=5;Status="Completada"}
    )},
    @{Code="F0002";Name="Base del sistema";Start=3;End=10;Status="Completada";Tasks=@(
        @{Code="T0005";Name="Gestión local de canciones";Start=3;End=4;Status="Completada"},
        @{Code="T0006";Name="Separación de voz y acompañamiento";Start=3;End=5;Status="Completada"},
        @{Code="T0007";Name="Extracción y filtrado del pitch de referencia";Start=4;End=6;Status="Completada"},
        @{Code="T0008";Name="Reproducción y captura del micrófono";Start=7;End=9;Status="Completada"},
        @{Code="T0009";Name="Guardado de grabaciones";Start=9;End=10;Status="Completada"}
    )},
    @{Code="F0003";Name="Comparación y métricas";Start=6;End=13;Status="Parcial";Tasks=@(
        @{Code="T0010";Name="Alineación temporal mediante DTW";Start=6;End=8;Status="Parcial"},
        @{Code="T0011";Name="Definición y cálculo de métricas";Start=9;End=11;Status="Completada"},
        @{Code="T0012";Name="Visualización y almacenamiento de resultados";Start=11;End=12;Status="Completada"},
        @{Code="T0013";Name="Validación inicial del análisis";Start=12;End=13;Status="Parcial"}
    )},
    @{Code="F0004";Name="Interfaz prototipo";Start=9;End=15;Status="Parcial";Tasks=@(
        @{Code="T0014";Name="Desarrollo de interfaz básica";Start=9;End=11;Status="Completada"},
        @{Code="T0015";Name="Integración de catálogo y preparación";Start=10;End=12;Status="Completada"},
        @{Code="T0016";Name="Integración de sesiones, resultados y manejo de errores";Start=12;End=15;Status="Parcial"}
    )},
    @{Code="F0005";Name="Detección de notas en tiempo real";Start=16;End=19;Status="Pendiente";Tasks=@(
        @{Code="T0017";Name="Captura continua de audio por bloques";Start=16;End=17;Status="Pendiente"},
        @{Code="T0018";Name="Estimación y estabilización del pitch";Start=16;End=18;Status="Pendiente"},
        @{Code="T0019";Name="Visualización de notas y evaluación de latencia";Start=18;End=19;Status="Pendiente"}
    )},
    @{Code="F0006";Name="Análisis avanzado";Start=18;End=23;Status="Pendiente";Tasks=@(
        @{Code="T0020";Name="Refinamiento de alineación y métricas temporales";Start=18;End=19;Status="Pendiente"},
        @{Code="T0021";Name="Detección y caracterización de segmentos";Start=19;End=22;Status="Pendiente"},
        @{Code="T0022";Name="Priorización de hallazgos";Start=22;End=23;Status="Pendiente"}
    )},
    @{Code="F0007";Name="Generación de retroalimentación";Start=22;End=25;Status="Pendiente";Tasks=@(
        @{Code="T0023";Name="Generación de observaciones en lenguaje natural";Start=22;End=24;Status="Pendiente"},
        @{Code="T0024";Name="Validación de coherencia y explicabilidad";Start=24;End=25;Status="Pendiente"}
    )},
    @{Code="F0008";Name="Persistencia, evolución e interfaz final";Start=20;End=27;Status="Pendiente";Tasks=@(
        @{Code="T0025";Name="Diseño del modelo de almacenamiento";Start=20;End=21;Status="Pendiente"},
        @{Code="T0026";Name="Registro estructurado de sesiones";Start=21;End=22;Status="Pendiente"},
        @{Code="T0027";Name="Comparación histórica de interpretaciones";Start=23;End=24;Status="Pendiente"},
        @{Code="T0028";Name="Visualización de la evolución";Start=24;End=25;Status="Pendiente"},
        @{Code="T0029";Name="Desarrollo e integración de la interfaz final";Start=23;End=27;Status="Pendiente"}
    )},
    @{Code="F0009";Name="Evaluación y cierre";Start=25;End=30;Status="Pendiente";Tasks=@(
        @{Code="T0030";Name="Pruebas funcionales del sistema";Start=25;End=27;Status="Pendiente"},
        @{Code="T0031";Name="Evaluación técnica y de usabilidad";Start=26;End=28;Status="Pendiente"},
        @{Code="T0032";Name="Correcciones y optimización";Start=28;End=29;Status="Pendiente"},
        @{Code="T0033";Name="Documentación y cierre del proyecto";Start=27;End=30;Status="Pendiente"}
    )}
)

$excel = $null
$workbook = $null
$sheet = $null
try {
    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $false
    $excel.DisplayAlerts = $false
    $workbook = $excel.Workbooks.Add()
    $sheet = $workbook.Worksheets.Item(1)
    $sheet.Name = "Carta Gantt"

    while ($workbook.Worksheets.Count -gt 1) {
        $workbook.Worksheets.Item($workbook.Worksheets.Count).Delete()
    }

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

    $sheet.Range("A1:AI1").Merge()
    $sheet.Range("A1").Value2 = "Carta Gantt - Sistema de análisis vocal"
    $sheet.Range("A1").Font.Bold = $true
    $sheet.Range("A1").Font.Size = 16
    $sheet.Range("A1").Font.Color = $white
    $sheet.Range("A1").Interior.Color = $dark
    $sheet.Range("A1").HorizontalAlignment = -4108
    $sheet.Rows.Item(1).RowHeight = 28

    $sheet.Range("A2:E2").Merge()
    $sheet.Range("A2").Value2 = "Planificación general del proyecto"
    $sheet.Range("A2").Font.Bold = $true
    $sheet.Range("A2").Interior.Color = $phaseFill
    $sheet.Range("F2:T2").Merge()
    $sheet.Range("F2").Value2 = "Primer semestre"
    $sheet.Range("F2").Interior.Color = $semester1
    $sheet.Range("F2").Font.Bold = $true
    $sheet.Range("F2").HorizontalAlignment = -4108
    $sheet.Range("U2:AI2").Merge()
    $sheet.Range("U2").Value2 = "Segundo semestre"
    $sheet.Range("U2").Interior.Color = $semester2
    $sheet.Range("U2").Font.Bold = $true
    $sheet.Range("U2").HorizontalAlignment = -4108

    @("Código","Actividades","Inicio","Fin","Estado") | ForEach-Object -Begin {$i=1} -Process {
        $sheet.Cells.Item(3,$i).Value2 = $_
        $i++
    }
    for ($week=1; $week -le 30; $week++) {
        $sheet.Cells.Item(3,$week+5).Value2 = "$week"
        $sheet.Cells.Item(3,$week+5).Interior.Color = $(if($week -le 15){$semester1}else{$semester2})
    }
    $sheet.Range("A3:AI3").Font.Bold = $true
    $sheet.Range("A3:AI3").HorizontalAlignment = -4108
    $sheet.Range("A3:E3").Interior.Color = $header
    $sheet.Range("A3:E3").Font.Color = $white

    $row = 4
    foreach ($phase in $phases) {
        $sheet.Cells.Item($row,1).Value2 = $phase.Code
        $sheet.Cells.Item($row,2).Value2 = $phase.Name
        $sheet.Cells.Item($row,3).Value2 = "$($phase.Start)"
        $sheet.Cells.Item($row,4).Value2 = "$($phase.End)"
        $sheet.Cells.Item($row,5).Value2 = $phase.Status
        $sheet.Range("A$row:AI$row").Font.Bold = $true
        $sheet.Range("A$row:AI$row").Interior.Color = $phaseFill
        for ($week=$phase.Start; $week -le $phase.End; $week++) {
            $sheet.Cells.Item($row,$week+5).Interior.Color = $header
        }
        $row++

        foreach ($task in $phase.Tasks) {
            $sheet.Cells.Item($row,1).Value2 = $task.Code
            $sheet.Cells.Item($row,2).Value2 = $task.Name
            $sheet.Cells.Item($row,3).Value2 = "$($task.Start)"
            $sheet.Cells.Item($row,4).Value2 = "$($task.End)"
            $sheet.Cells.Item($row,5).Value2 = $task.Status
            $fill = switch ($task.Status) {
                "Completada" {$completed}
                "Parcial" {$partial}
                default {$pending}
            }
            for ($week=$task.Start; $week -le $task.End; $week++) {
                $sheet.Cells.Item($row,$week+5).Interior.Color = $fill
            }
            $row++
        }
    }

    $legendRow = $row + 1
    $sheet.Cells.Item($legendRow,2).Value2 = "Leyenda"
    $sheet.Cells.Item($legendRow,2).Font.Bold = $true
    $legend = @(@("Completada",$completed),@("Parcial",$partial),@("Pendiente",$pending))
    $column = 6
    foreach ($item in $legend) {
        $sheet.Cells.Item($legendRow,$column).Interior.Color = $item[1]
        $sheet.Cells.Item($legendRow,$column+1).Value2 = $item[0]
        $column += 3
    }

    $lastRow = $legendRow
    $sheet.Range("A3:AI$lastRow").Borders.Color = $border
    $sheet.Range("A3:AI$lastRow").Borders.LineStyle = 1
    $sheet.Range("U2:U$lastRow").Borders.Item(7).Weight = 4
    $sheet.Range("U2:U$lastRow").Borders.Item(7).Color = 0x0000C0
    $sheet.Columns.Item("A").ColumnWidth = 11
    $sheet.Columns.Item("B").ColumnWidth = 48
    $sheet.Columns.Item("C").ColumnWidth = 9
    $sheet.Columns.Item("D").ColumnWidth = 9
    $sheet.Columns.Item("E").ColumnWidth = 14
    $sheet.Range("F:AI").ColumnWidth = 3.2
    $sheet.Range("A3:AI$lastRow").VerticalAlignment = -4108
    $sheet.Range("B4:B$lastRow").WrapText = $true
    $sheet.Range("C4:E$lastRow").HorizontalAlignment = -4108
    $sheet.Application.ActiveWindow.SplitColumn = 5
    $sheet.Application.ActiveWindow.SplitRow = 3
    $sheet.Application.ActiveWindow.FreezePanes = $true
    $sheet.PageSetup.Orientation = 2
    $sheet.PageSetup.Zoom = $false
    $sheet.PageSetup.FitToPagesWide = 1
    $sheet.PageSetup.FitToPagesTall = $false
    $sheet.PageSetup.PrintArea = "A1:AI$lastRow"

    $workbook.SaveAs($output, 51)
    Write-Output "Archivo creado: $output"
}
finally {
    if ($workbook) { $workbook.Close($false) }
    if ($excel) { $excel.Quit() }
    if ($sheet) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($sheet) }
    if ($workbook) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($workbook) }
    if ($excel) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel) }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
