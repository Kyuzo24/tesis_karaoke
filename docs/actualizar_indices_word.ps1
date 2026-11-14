$ErrorActionPreference = "Stop"

$root = "C:\Users\Diego Tapia\Desktop\Pene\U\13avo semestre"
$form = Get-ChildItem -LiteralPath $root -Directory | Where-Object { $_.Name -like "Formulaci*" } | Select-Object -First 1
$docPath = Join-Path $form.FullName "Informe final\Documento\Documento final.docx"
$backupPath = Join-Path (Split-Path $docPath) ("Documento final_backup_indices_{0}.docx" -f (Get-Date -Format "yyyyMMdd_HHmmss"))

$word = [Runtime.InteropServices.Marshal]::GetActiveObject("Word.Application")
$doc = $null
for ($i = 1; $i -le $word.Documents.Count; $i++) {
    $candidate = $word.Documents.Item($i)
    if ($candidate.FullName -eq $docPath) {
        $doc = $candidate
        break
    }
}
if ($null -eq $doc) {
    $doc = $word.Documents.Open($docPath)
}

$doc.SaveCopyAs($backupPath)

$wdStory = 6
$wdPageBreak = 7
$wdActiveEndPageNumber = 3
$wdStyleHeading1 = -2
$wdStyleHeading2 = -3
$wdStyleHeading3 = -4
$wdStyleNormal = -1
$wdAlignLeft = 0
$wdAlignCenter = 1
$wdAlignTabRight = 2
$wdTabLeaderDots = 1

function Clean-Text($text) {
    return (($text -replace "`r", "") -replace "`a", "").Trim()
}

function Set-Paragraph-Font($paragraph, [double]$size = 12, [bool]$bold = $false, [int]$align = 0) {
    $paragraph.Range.Font.Name = "Times New Roman"
    $paragraph.Range.Font.Size = $size
    $paragraph.Range.Font.Bold = $(if ($bold) { 1 } else { 0 })
    $paragraph.Alignment = $align
    $paragraph.SpaceAfter = 0
    $paragraph.LineSpacingRule = 0
}

function Add-Entry($doc, $range, $text, $page, [int]$level = 0) {
    $range.InsertAfter("$text`t$page`r")
    $p = $doc.Paragraphs.Item($doc.Paragraphs.Count)
    Set-Paragraph-Font $p 12 $false $wdAlignLeft
    $p.LeftIndent = $word.CentimetersToPoints(0.55 * $level)
    $p.FirstLineIndent = 0
    $p.TabStops.ClearAll()
    $rightPos = $doc.PageSetup.PageWidth - $doc.PageSetup.LeftMargin - $doc.PageSetup.RightMargin
    [void]$p.TabStops.Add($rightPos, $wdAlignTabRight, $wdTabLeaderDots)
    return $doc.Range($p.Range.End, $p.Range.End)
}

function Add-Title($doc, $range, $text) {
    $range.InsertAfter("$text`r")
    $p = $doc.Paragraphs.Item($doc.Paragraphs.Count)
    Set-Paragraph-Font $p 14 $true $wdAlignCenter
    return $doc.Range($p.Range.End, $p.Range.End)
}

function Add-Plain($doc, $range, $text) {
    $range.InsertAfter("$text`r")
    $p = $doc.Paragraphs.Item($doc.Paragraphs.Count)
    Set-Paragraph-Font $p 12 $false $wdAlignLeft
    return $doc.Range($p.Range.End, $p.Range.End)
}

function Get-Paragraphs-After-ContentStart($doc) {
    $introCount = 0
    $startIndex = 0
    for ($i = 1; $i -le $doc.Paragraphs.Count; $i++) {
        $t = Clean-Text $doc.Paragraphs.Item($i).Range.Text
        if ($t -eq "1. Introducción") {
            $introCount += 1
            if ($introCount -eq 1) {
                $startIndex = $i
                break
            }
        }
    }
    $items = @()
    if ($startIndex -gt 0) {
        for ($i = $startIndex; $i -le $doc.Paragraphs.Count; $i++) {
            $items += $doc.Paragraphs.Item($i)
        }
    }
    return $items
}

function Get-Indexable-Items($doc) {
    $items = @()
    foreach ($p in (Get-Paragraphs-After-ContentStart $doc)) {
        $t = Clean-Text $p.Range.Text
        if ($t -match "^[1-4]\. .+") {
            $items += [pscustomobject]@{ Text = $t; Level = 0; Page = $p.Range.Information($wdActiveEndPageNumber) }
        } elseif ($t -match "^[1-4]\.[0-9]+\. .+") {
            $items += [pscustomobject]@{ Text = $t; Level = 1; Page = $p.Range.Information($wdActiveEndPageNumber) }
        } elseif ($t -match "^[1-4]\.[0-9]+\.[0-9]+\. .+") {
            $items += [pscustomobject]@{ Text = $t; Level = 2; Page = $p.Range.Information($wdActiveEndPageNumber) }
        } elseif ($t -eq "Referencias" -or $t -eq "Anexos") {
            $items += [pscustomobject]@{ Text = $t; Level = 0; Page = $p.Range.Information($wdActiveEndPageNumber) }
        }
    }
    return $items
}

function Get-Caption-Items($doc, $kind) {
    $items = @()
    foreach ($p in (Get-Paragraphs-After-ContentStart $doc)) {
        $t = Clean-Text $p.Range.Text
        if ($kind -eq "Figura" -and $t -match "^Figura\s+\d+(\.\d+)?:") {
            $label = ($t -replace "\.\s*Fuente:.*$", "")
            $items += [pscustomobject]@{ Text = $label; Page = $p.Range.Information($wdActiveEndPageNumber) }
        }
        if ($kind -eq "Cuadro" -and $t -match "^Cuadro\s+\d+(\.\d+)?:") {
            $label = ($t -replace "\.\s*Fuente:.*$", "")
            $items += [pscustomobject]@{ Text = $label; Page = $p.Range.Information($wdActiveEndPageNumber) }
        }
    }
    return $items
}

function Style-Document-Headings($doc) {
    $contentStarted = $false
    for ($i = 1; $i -le $doc.Paragraphs.Count; $i++) {
        $p = $doc.Paragraphs.Item($i)
        $t = Clean-Text $p.Range.Text
        if ($t -eq "1. Introducción") {
            $contentStarted = $true
        }
        if (-not $contentStarted) {
            continue
        }
        if ($t -match "^[1-4]\. .+" -or $t -eq "Referencias" -or $t -eq "Anexos") {
            $p.Style = $doc.Styles.Item($wdStyleHeading1)
        } elseif ($t -match "^[1-4]\.[0-9]+\. .+") {
            $p.Style = $doc.Styles.Item($wdStyleHeading2)
        } elseif ($t -match "^[1-4]\.[0-9]+\.[0-9]+\. .+") {
            $p.Style = $doc.Styles.Item($wdStyleHeading3)
        }
    }
}

function Ensure-Anexos($doc) {
    $hasRealAnexos = $false
    $contentStarted = $false
    for ($i = 1; $i -le $doc.Paragraphs.Count; $i++) {
        $t = Clean-Text $doc.Paragraphs.Item($i).Range.Text
        if ($t -eq "1. Introducción") {
            $contentStarted = $true
        }
        if ($contentStarted -and $t -eq "Anexos") {
            $hasRealAnexos = $true
        }
    }
    if (-not $hasRealAnexos) {
        $end = $doc.Content.End - 1
        $r = $doc.Range($end, $end)
        $r.InsertBreak($wdPageBreak)
        $r = $doc.Range($r.End, $r.End)
        $text = "Anexos`rLos anexos de esta entrega se presentan como documentos complementarios al documento principal. Estos artefactos respaldan la especificación, planificación y modelado del sistema desarrollado durante el primer semestre.`rAnexo A: Especificación de requisitos. Archivo: Especificacion de Requisitos.docx.`rAnexo B: Historias de usuario. Archivo: Historias de Usuario.docx.`rAnexo C: Carta Gantt. Archivo: Carta Gantt.xlsx.`rAnexo D: Modelo de datos. Archivo: Modelo de datos.png.`r"
        $r.InsertAfter($text)
    }
}

function Remove-Old-Front-Index($doc) {
    $start = $null
    $contentStart = $null
    $introCount = 0
    for ($i = 1; $i -le $doc.Paragraphs.Count; $i++) {
        $p = $doc.Paragraphs.Item($i)
        $t = Clean-Text $p.Range.Text
        if ($null -eq $start -and $t -eq "TABLA DE CONTENIDOS") {
            $start = $p.Range.Start
        }
        if ($t -eq "1. Introducción") {
            $introCount += 1
            if ($introCount -eq 2) {
                $contentStart = $p.Range.Start
                break
            }
        }
    }
    if ($null -eq $start -or $null -eq $contentStart) {
        throw "No se pudo ubicar el índice manual o el inicio real del capítulo 1."
    }
    $doc.Range($start, $contentStart).Delete()
    return $start
}

function Build-Front-Index($doc, $insertPos, $tocItems, $figItems, $tableItems) {
    $r = $doc.Range($insertPos, $insertPos)
    $r = Add-Title $doc $r "TABLA DE CONTENIDOS"
    foreach ($item in $tocItems) {
        $r = Add-Entry $doc $r $item.Text $item.Page $item.Level
    }
    $r.InsertBreak($wdPageBreak)
    $r = $doc.Range($r.End, $r.End)

    $r = Add-Title $doc $r "ÍNDICE DE FIGURAS"
    foreach ($item in $figItems) {
        $r = Add-Entry $doc $r $item.Text $item.Page 0
    }
    $r.InsertBreak($wdPageBreak)
    $r = $doc.Range($r.End, $r.End)

    $r = Add-Title $doc $r "ÍNDICE DE TABLAS"
    foreach ($item in $tableItems) {
        $r = Add-Entry $doc $r $item.Text $item.Page 0
    }
    $r.InsertBreak($wdPageBreak)
}

function Rebuild-With-Current-Pages($doc, $insertPos) {
    $doc.Repaginate()
    $tocItems = Get-Indexable-Items $doc
    $figItems = Get-Caption-Items $doc "Figura"
    $tableItems = Get-Caption-Items $doc "Cuadro"

    $contentStart = $null
    for ($i = 1; $i -le $doc.Paragraphs.Count; $i++) {
        if ((Clean-Text $doc.Paragraphs.Item($i).Range.Text) -eq "1. Introducción") {
            $contentStart = $doc.Paragraphs.Item($i).Range.Start
            break
        }
    }
    $doc.Range($insertPos, $contentStart).Delete()
    Build-Front-Index $doc $insertPos $tocItems $figItems $tableItems
    $doc.Repaginate()
}

Ensure-Anexos $doc
Style-Document-Headings $doc
$insertPos = Remove-Old-Front-Index $doc

$placeholderToc = Get-Indexable-Items $doc | ForEach-Object { [pscustomobject]@{ Text = $_.Text; Level = $_.Level; Page = 0 } }
$placeholderFig = Get-Caption-Items $doc "Figura" | ForEach-Object { [pscustomobject]@{ Text = $_.Text; Page = 0 } }
$placeholderTables = Get-Caption-Items $doc "Cuadro" | ForEach-Object { [pscustomobject]@{ Text = $_.Text; Page = 0 } }
Build-Front-Index $doc $insertPos $placeholderToc $placeholderFig $placeholderTables

Rebuild-With-Current-Pages $doc $insertPos
Rebuild-With-Current-Pages $doc $insertPos

Style-Document-Headings $doc
$doc.Save()

Write-Output "Documento actualizado: $docPath"
Write-Output "Respaldo creado: $backupPath"
