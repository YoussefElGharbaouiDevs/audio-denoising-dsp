$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$projectPython = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $projectPython)) {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3 -m venv .venv
    } elseif (Get-Command python -ErrorAction SilentlyContinue) {
        & python -m venv .venv
    } else {
        throw 'Installez Python 3.11 à 3.13, puis relancez ce script.'
    }
    if ($LASTEXITCODE -ne 0) { throw 'Impossible de créer l’environnement Python.' }
    & $projectPython -m pip install -r requirements.lock.txt
    if ($LASTEXITCODE -ne 0) { throw 'Installation des dépendances impossible.' }
    & $projectPython -m pip install -e . --no-deps
    if ($LASTEXITCODE -ne 0) { throw 'Installation du projet impossible.' }
}
Write-Host 'Ouvrez http://127.0.0.1:8501 dans votre navigateur. Ctrl+C pour arrêter.'
& $projectPython -m streamlit run app.py
