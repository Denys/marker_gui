param(
    [Parameter(Mandatory=$true)]
    [string]$PdfPath,

    [string]$OutputDir = (Join-Path $PSScriptRoot "output")
)

$MarkerExe = Join-Path $PSScriptRoot ".venv\Scripts\marker_single.exe"

if (-not (Test-Path $PdfPath)) {
    Write-Error "File PDF non trovato: $PdfPath"
    exit 1
}

Write-Host "Avvio conversione di: $PdfPath" -ForegroundColor Cyan
Write-Host "Destinazione: $OutputDir" -ForegroundColor Cyan

& $MarkerExe "$PdfPath" --output_dir "$OutputDir" --disable_ocr

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nConversione completata con successo in: $OutputDir" -ForegroundColor Green
} else {
    Write-Host "`nErrore durante la conversione (Exit code: $LASTEXITCODE)" -ForegroundColor Red
}
