# MeshMind v2 - Bootstrap (Windows)
# Run: .\scripts\bootstrap.ps1
# Verifies environment and prepares the repo for development.

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $PSCommandPath)

Write-Host "MeshMind v2 - Bootstrap" -ForegroundColor Cyan
Write-Host ""

# 1. Run environment check
Write-Host "Running environment check..." -ForegroundColor Gray
& "$root\scripts\check-env.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Environment check failed. Fix issues above before continuing." -ForegroundColor Red
    Write-Host "See docs/DEVELOPER_PREREQUISITES.md" -ForegroundColor Gray
    exit 1
}

# 2. Create data directory
$dataDir = Join-Path $root "data"
if (-not (Test-Path $dataDir)) {
    New-Item -ItemType Directory -Path $dataDir | Out-Null
    Write-Host "[OK] Created data directory" -ForegroundColor Green
}

# 3. Fetch Cargo dependencies (no build)
Write-Host ""
Write-Host "Fetching Rust dependencies..." -ForegroundColor Gray
Set-Location $root
cargo fetch 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Cargo dependencies ready" -ForegroundColor Green
} else {
    Write-Host "[WARN] cargo fetch had issues" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Bootstrap complete. Ready for development." -ForegroundColor Green
Write-Host "  Run control-api: .\scripts\run.ps1" -ForegroundColor Gray
Write-Host "  Run tests: .\scripts\test.ps1" -ForegroundColor Gray
