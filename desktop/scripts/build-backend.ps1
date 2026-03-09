$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$desktopRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$distRoot = Join-Path $desktopRoot "backend-dist"
$workRoot = Join-Path $desktopRoot ".pyinstaller-work"
$specRoot = Join-Path $desktopRoot ".pyinstaller-spec"
$entryPoint = Join-Path $desktopRoot "backend_entry.py"

$pythonCmd = if ($env:MAPIG_PYTHON_PATH) { $env:MAPIG_PYTHON_PATH } else { "python" }

Write-Host "Checking PyInstaller..."
& $pythonCmd -c "import PyInstaller" *> $null
if ($LASTEXITCODE -ne 0) {
  throw "PyInstaller is not installed. Install it first (example: poetry run pip install pyinstaller)."
}

if (Test-Path $distRoot) { Remove-Item $distRoot -Recurse -Force }
if (Test-Path $workRoot) { Remove-Item $workRoot -Recurse -Force }
if (Test-Path $specRoot) { Remove-Item $specRoot -Recurse -Force }

Write-Host "Building backend executable..."
& $pythonCmd -m PyInstaller `
  --noconfirm `
  --clean `
  --onedir `
  --name "mapig-backend" `
  --distpath $distRoot `
  --workpath $workRoot `
  --specpath $specRoot `
  --collect-submodules "uvicorn" `
  --collect-submodules "langgraph" `
  --collect-submodules "langgraph.checkpoint.sqlite" `
  --collect-submodules "langchain_openai" `
  --collect-submodules "aiosqlite" `
  --add-data "$repoRoot\app;app" `
  --add-data "$repoRoot\data;data" `
  $entryPoint

if ($LASTEXITCODE -ne 0) {
  throw "Backend build failed."
}

$exePath = Join-Path $distRoot "mapig-backend\mapig-backend.exe"
if (-not (Test-Path $exePath)) {
  throw "Expected backend executable was not created: $exePath"
}

Write-Host "Backend build completed: $exePath"
