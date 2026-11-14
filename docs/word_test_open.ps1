$ErrorActionPreference = "Stop"
$root = "C:\Users\Diego Tapia\Desktop\Pene\U\13avo semestre"
$form = Get-ChildItem -LiteralPath $root -Directory | Where-Object { $_.Name -like "Formulaci*" } | Select-Object -First 1
$target = Join-Path $form.FullName "Informe final\Documento\Documento final.docx"
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$doc = $word.Documents.Open($target, $false, $true, $false)
Write-Output "OPENED paras=$($doc.Paragraphs.Count)"
$doc.Close([ref]0)
$word.Quit()
Write-Output "CLOSED"
