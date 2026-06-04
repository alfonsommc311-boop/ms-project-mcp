<#
  MS Project MCP - 1-click installer for Windows.

  Creates a local virtual environment, installs the server (console script
  `ms-project-mcp`), and registers it in Claude Code. Re-runnable (idempotent).

  Usage (from the repo root):
      powershell -ExecutionPolicy Bypass -File install.ps1
#>
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

function Info($m) { Write-Host $m -ForegroundColor Cyan }
function Ok($m)   { Write-Host "  $m" -ForegroundColor Green }
function Warn($m) { Write-Host "  $m" -ForegroundColor Yellow }
function Die($m)  { Write-Host "  $m" -ForegroundColor Red; exit 1 }

Info "== MS Project MCP installer =="

# --- 1) Prerequisites -------------------------------------------------------
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Die "Python 3.10+ is required. Install it from https://python.org and re-run."
}
$venvPy = Join-Path $root ".venv\Scripts\python.exe"
$hasUv  = [bool](Get-Command uv -ErrorAction SilentlyContinue)

# --- 2) Virtual env + install ----------------------------------------------
Info "Installing into .venv ..."
if ($hasUv) {
    uv venv 2>&1 | Out-Null
    uv pip install . --python $venvPy
} else {
    if (-not (Test-Path $venvPy)) { python -m venv .venv }
    & $venvPy -m pip install --upgrade pip --quiet
    & $venvPy -m pip install . --quiet
}

$exe = Join-Path $root ".venv\Scripts\ms-project-mcp.exe"
if (-not (Test-Path $exe)) { Die "Install failed: console script 'ms-project-mcp' was not created." }
Ok "Installed: $exe"

# --- 3) Smoke test ----------------------------------------------------------
& $venvPy -c "import ms_project_mcp.server" 2>$null
if ($LASTEXITCODE -ne 0) { Die "Smoke test failed: package does not import." }
Ok "Import smoke test passed."

# --- 4) Register in Claude Code --------------------------------------------
$cmdEscaped = $exe -replace '\\', '\\'
$json = '{"type":"stdio","command":"' + $cmdEscaped + '"}'
if (Get-Command claude -ErrorAction SilentlyContinue) {
    Info "Registering 'ms-project' in Claude Code (user scope) ..."
    try { claude mcp remove ms-project -s user 2>$null } catch {}
    claude mcp add-json ms-project --scope user $json
    Ok "Registered."
} else {
    Warn "Claude CLI not found. Register this MCP server manually with:"
    Warn $json
}

# --- 5) Next steps ----------------------------------------------------------
Info "Done. Next steps:"
Write-Host "  1) Open Microsoft Project with a project file (or the server creates one)."
Write-Host "  2) Restart Claude Code so it loads the 'ms-project' server."
Write-Host "  3) Ask: 'list the tasks in my project'."
