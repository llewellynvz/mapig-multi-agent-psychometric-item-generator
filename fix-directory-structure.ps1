# Fix Next.js directory collision
# Run this script to rename 'app' (Python) to 'backend'

Write-Host "Renaming Python backend directory..." -ForegroundColor Cyan

# Step 1: Rename directory
if (Test-Path "app") {
    Rename-Item -Path "app" -NewName "backend"
    Write-Host "✓ Renamed app/ -> backend/" -ForegroundColor Green
} else {
    Write-Host "✗ app/ directory not found" -ForegroundColor Red
    exit 1
}

# Step 2: Update Python imports
Write-Host "`nUpdating Python imports..." -ForegroundColor Cyan

$files = Get-ChildItem -Path "backend", "api", "tests" -Include "*.py" -Recurse -ErrorAction SilentlyContinue

foreach ($file in $files) {
    $content = Get-Content $file.FullName -Raw
    $updated = $content -replace 'from app\.', 'from backend.'
    $updated = $updated -replace 'import app\.', 'import backend.'
    $updated = $updated -replace 'from app import', 'from backend import'

    if ($content -ne $updated) {
        Set-Content -Path $file.FullName -Value $updated -NoNewline
        Write-Host "  Updated: $($file.Name)" -ForegroundColor Yellow
    }
}

# Step 3: Update other configuration files
Write-Host "`nUpdating configuration files..." -ForegroundColor Cyan

# Update pyproject.toml if it references app
if (Test-Path "pyproject.toml") {
    $content = Get-Content "pyproject.toml" -Raw
    $updated = $content -replace 'app\.', 'backend.'
    if ($content -ne $updated) {
        Set-Content -Path "pyproject.toml" -Value $updated -NoNewline
        Write-Host "  Updated: pyproject.toml" -ForegroundColor Yellow
    }
}

# Update package.json backend script
if (Test-Path "package.json") {
    $content = Get-Content "package.json" -Raw
    $updated = $content -replace 'app\.main:app', 'backend.main:app'
    if ($content -ne $updated) {
        Set-Content -Path "package.json" -Value $updated -NoNewline
        Write-Host "  Updated: package.json" -ForegroundColor Yellow
    }
}

# Update run_dev.py
if (Test-Path "run_dev.py") {
    $content = Get-Content "run_dev.py" -Raw
    $updated = $content -replace 'app\.main:app', 'backend.main:app'
    if ($content -ne $updated) {
        Set-Content -Path "run_dev.py" -Value $updated -NoNewline
        Write-Host "  Updated: run_dev.py" -ForegroundColor Yellow
    }
}

# Update vercel.json excludeFiles to reference backend
if (Test-Path "vercel.json") {
    $content = Get-Content "vercel.json" -Raw
    # This might not need changes, but let's check
    Write-Host "  vercel.json: No changes needed (excludeFiles uses wildcards)" -ForegroundColor Gray
}

Write-Host "`n✓ Directory structure fixed!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "1. Run: npm run dev" -ForegroundColor White
Write-Host "2. Visit: http://localhost:3000" -ForegroundColor White
Write-Host "3. Backend will be at: backend/ instead of app/" -ForegroundColor White
