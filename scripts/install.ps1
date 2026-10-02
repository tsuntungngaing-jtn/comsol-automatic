param([string]$Python = "python")
$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Push-Location -LiteralPath $RepoRoot
try {
    & $Python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw "Python venv creation failed. Install Python 3.10+ first." }
    $VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
    & $VenvPython -m pip install -e ".[test]"
    if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed." }
    & $VenvPython -m server.main doctor
    if ($LASTEXITCODE -ne 0) { throw "Doctor failed." }
    Write-Host "MCP runtime installed. This does not verify skill-list visibility. Follow docs/connectors.md to install the skill into a client-discoverable directory and configure its connector."
    Write-Host "Keep this repository in place: editable install uses its bundled vendor source and cases."
} finally { Pop-Location }
