$ErrorActionPreference = "Stop"

$root = "C:\Users\Diego Tapia\Desktop\Pene\U\13avo semestre"
$form = Get-ChildItem -LiteralPath $root -Directory | Where-Object { $_.Name -like "Formulaci*" } | Select-Object -First 1
$folder = Join-Path $form.FullName "Informe final\Documento"
$target = Join-Path $folder "Documento final_con_indices.docx"
$backup = Join-Path $folder "Documento final_backup_antes_indices.docx"
$log = Join-Path "C:\Users\Diego Tapia\Desktop\Pene\U\Tesis\tesis_karaoke\docs" "reconstruir_indices_com.log"
Set-Content -LiteralPath $log -Value "inicio"

Copy-Item -LiteralPath $backup -Destination $target -Force
Add-Content -LiteralPath $log -Value "backup restaurado"

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
Add-Content -LiteralPath $log -Value "word creado"
$doc = $word.Documents.Open($target, $false, $false, $false)
Add-Content -LiteralPath $log -Value "documento abierto"

$wdPageBreakChar = [char]12
$wdActiveEndPageNumber = 3
$wdStyleHeading1 = -2
$wdStyleHeading2 = -3
$wdStyleHeading3 = -4
$wdAlignLeft = 0
$wdAlignCenter = 1
$wdAlignTabRight = 2
$wdTabLeaderDots = 1

function Clean-Text($text) {
    return (($text -replace "`r", "") -replace "`a", "").Trim()
}

function Is-Chapter($text) {
    return ($text -like "1. Introducci*" -or
            $text -like "2. Marco te*" -or
            $text -like "3. Metodolog*" -or
            $text -like "4. Desarrollo" -or
            $text -eq "Referencias" -or
            $text -eq "Anexos")
}

function Heading-Level($text) {
    if (Is-Chapter $text) { return 0 }
    if ($text -match "^[1-4]\.[0-9]+\.[0-9]+\. .+") { return 2 }
    if ($text -match "^[1-4]\.[0-9]+\. .+") { return 1 }
    return $null
}

function Find-Manual-Index-Bounds($doc) {
    $start = $null
    $contentStart = $null
    $introCount = 0
    for ($i = 1; $i -le $doc.Paragraphs.Count; $i++) {
        $p = $doc.Paragraphs.Item($i)
        $t = Clean-Text $p.Range.Text
        if ($null -eq $start -and $t -eq "TABLA DE CONTENIDOS") {
            $start = $p.Range.Start
        }
        if ($t -like "1. Introducci*") {
            $introCount += 1
            if ($introCount -eq 2) {
                $contentStart = $p.Range.Start
                break
            }
        }
    }
    if ($null -eq $start -or $null -eq $contentStart) {
        throw "No se pudo ubicar el indice manual."
    }
    return @($start, $contentStart)
}

function Find-Front-Bounds($doc) {
    $start = $null
    $contentStart = $null
    for ($i = 1; $i -le $doc.Paragraphs.Count; $i++) {
        $p = $doc.Paragraphs.Item($i)
        $t = Clean-Text $p.Range.Text
        if ($null -eq $start -and $t -eq "TABLA DE CONTENIDOS") {
            $start = $p.Range.Start
        } elseif ($null -ne $start -and $t -like "1. Introducci*" -and $t -notmatch "`t") {
            $contentStart = $p.Range.Start
            break
        }
    }
    if ($null -eq $start -or $null -eq $contentStart) {
        throw "No se pudo ubicar el inicio del contenido."
    }
    return @($start, $contentStart)
}

function Ensure-Anexos($doc) {
    $has = $false
    $introCount = 0
    $started = $false
    for ($i = 1; $i -le $doc.Paragraphs.Count; $i++) {
        $t = Clean-Text $doc.Paragraphs.Item($i).Range.Text
        if ($t -like "1. Introducci*") {
            $introCount += 1
            if ($introCount -ge 2) { $started = $true }
        }
        if ($started -and $t -eq "Anexos") { $has = $true }
    }
    if (-not $has) {
        $o = [char]0x00F3
        $end = $doc.Content.End - 1
        $r = $doc.Range($end, $end)
        $text = "$wdPageBreakChar`rAnexos`rLos anexos de esta entrega se presentan como documentos complementarios al documento principal. Estos artefactos respaldan la especificaci$o, planificaci$o y modelado del sistema desarrollado durante el primer semestre.`rAnexo A: Especificaci$o de requisitos. Archivo: Especificacion de Requisitos.docx.`rAnexo B: Historias de usuario. Archivo: Historias de Usuario.docx.`rAnexo C: Carta Gantt. Archivo: Carta Gantt.xlsx.`rAnexo D: Modelo de datos. Archivo: Modelo de datos.png.`r"
        $r.InsertAfter($text)
    }
}

function Style-Headings($doc) {
    $started = $false
    for ($i = 1; $i -le $doc.Paragraphs.Count; $i++) {
        $p = $doc.Paragraphs.Item($i)
        $t = Clean-Text $p.Range.Text
        if ($t -like "1. Introducci*") { $started = $true }
        if (-not $started) { continue }
        $level = Heading-Level $t
        if ($level -eq 0) { $p.Style = $doc.Styles.Item($wdStyleHeading1) }
        elseif ($level -eq 1) { $p.Style = $doc.Styles.Item($wdStyleHeading2) }
        elseif ($level -eq 2) { $p.Style = $doc.Styles.Item($wdStyleHeading3) }
    }
}

function Collect-Items($doc, [bool]$withPages) {
    $items = New-Object System.Collections.Generic.List[object]
    $started = $false
    for ($i = 1; $i -le $doc.Paragraphs.Count; $i++) {
        $p = $doc.Paragraphs.Item($i)
        $t = Clean-Text $p.Range.Text
        if ($t -like "1. Introducci*" -and $t -notmatch "`t") { $started = $true }
        if (-not $started) { continue }

        $page = $(if ($withPages) { $p.Range.Information($wdActiveEndPageNumber) } else { 0 })
        $level = Heading-Level $t
        if ($null -ne $level) {
            $items.Add([pscustomobject]@{ Kind="toc"; Text=$t; Level=$level; Page=$page })
        } elseif ($t -match "Figura\s+\d+(\.\d+)?:") {
            $label = ([regex]::Match($t, "Figura\s+\d+(\.\d+)?:.*").Value -replace "\.\s*Fuente:.*$", "")
            $items.Add([pscustomobject]@{ Kind="fig"; Text=$label; Level=0; Page=$page })
        } elseif ($t -match "Cuadro\s+\d+(\.\d+)?:") {
            $label = ([regex]::Match($t, "Cuadro\s+\d+(\.\d+)?:.*").Value -replace "\.\s*Fuente:.*$", "")
            $items.Add([pscustomobject]@{ Kind="tab"; Text=$label; Level=0; Page=$page })
        }
    }
    return $items
}

function Build-Front-Text($items) {
    $I = [string]([char]0x00CD)
    $sb = New-Object System.Text.StringBuilder
    [void]$sb.Append("TABLA DE CONTENIDOS`r")
    foreach ($item in ($items | Where-Object { $_.Kind -eq "toc" })) {
        [void]$sb.Append(("{0}`t{1}`r" -f $item.Text, $item.Page))
    }
    [void]$sb.Append("$wdPageBreakChar")
    [void]$sb.Append("${I}NDICE DE FIGURAS`r")
    foreach ($item in ($items | Where-Object { $_.Kind -eq "fig" })) {
        [void]$sb.Append(("{0}`t{1}`r" -f $item.Text, $item.Page))
    }
    [void]$sb.Append("$wdPageBreakChar")
    [void]$sb.Append("${I}NDICE DE TABLAS`r")
    foreach ($item in ($items | Where-Object { $_.Kind -eq "tab" })) {
        [void]$sb.Append(("{0}`t{1}`r" -f $item.Text, $item.Page))
    }
    [void]$sb.Append("$wdPageBreakChar")
    return $sb.ToString()
}

function Format-Front($doc) {
    $bounds = Find-Front-Bounds $doc
    $range = $doc.Range($bounds[0], $bounds[1])
    $rightPos = $doc.PageSetup.PageWidth - $doc.PageSetup.LeftMargin - $doc.PageSetup.RightMargin
    foreach ($p in $range.Paragraphs) {
        $t = Clean-Text $p.Range.Text
        $p.Range.Font.Name = "Times New Roman"
        $p.Range.Font.Size = 12
        $p.Range.Font.Bold = 0
        $p.Alignment = $wdAlignLeft
        $p.SpaceAfter = 0
        $p.TabStops.ClearAll()
        [void]$p.TabStops.Add($rightPos, $wdAlignTabRight, $wdTabLeaderDots)
        $p.LeftIndent = 0
        if ($t -in @("TABLA DE CONTENIDOS", "ÍNDICE DE FIGURAS", "ÍNDICE DE TABLAS")) {
            $p.Alignment = $wdAlignCenter
            $p.Range.Font.Bold = 1
            $p.Range.Font.Size = 14
        } elseif ($t -match "^[1-4]\.[0-9]+\.[0-9]+\.") {
            $p.LeftIndent = $word.CentimetersToPoints(1.0)
        } elseif ($t -match "^[1-4]\.[0-9]+\.") {
            $p.LeftIndent = $word.CentimetersToPoints(0.55)
        }
    }
}

Ensure-Anexos $doc
Add-Content -LiteralPath $log -Value "anexos ok"
Style-Headings $doc
Add-Content -LiteralPath $log -Value "headings ok"

$bounds = Find-Manual-Index-Bounds $doc
Add-Content -LiteralPath $log -Value "bounds manual $($bounds[0]) $($bounds[1])"
$doc.Range($bounds[0], $bounds[1]).Delete()
Add-Content -LiteralPath $log -Value "indice viejo borrado"

$items = Collect-Items $doc $false
Add-Content -LiteralPath $log -Value "items placeholder $($items.Count)"
$front = Build-Front-Text $items
Add-Content -LiteralPath $log -Value "front creado len $($front.Length)"
$doc.Range($bounds[0], $bounds[0]).InsertAfter($front)
Add-Content -LiteralPath $log -Value "front insertado"
$doc.Repaginate()
Add-Content -LiteralPath $log -Value "repaginado 1"

$itemsWithPages = Collect-Items $doc $true
Add-Content -LiteralPath $log -Value "items paginas $($itemsWithPages.Count)"
$bounds2 = Find-Front-Bounds $doc
Add-Content -LiteralPath $log -Value "bounds front $($bounds2[0]) $($bounds2[1])"
$doc.Range($bounds2[0], $bounds2[1]).Delete()
Add-Content -LiteralPath $log -Value "front placeholder borrado"
$frontFinal = Build-Front-Text $itemsWithPages
Add-Content -LiteralPath $log -Value "front final len $($frontFinal.Length)"
$doc.Range($bounds2[0], $bounds2[0]).InsertAfter($frontFinal)
Add-Content -LiteralPath $log -Value "front final insertado"
Format-Front $doc
Add-Content -LiteralPath $log -Value "front formateado"
Style-Headings $doc
Add-Content -LiteralPath $log -Value "headings final ok"
$doc.Repaginate()
Add-Content -LiteralPath $log -Value "repaginado final"
$doc.Save()
Add-Content -LiteralPath $log -Value "guardado"
$doc.Close([ref]0)
$word.Quit()

Write-Output "Documento actualizado: $target"
Write-Output "Entradas: $($itemsWithPages.Count)"
