# MeshMind v2 - Native Rust MSVC build test
# Run from Developer PowerShell for VS 2022: .\scripts\test-rust-build.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $PSCommandPath)

$link = Get-Command link.exe -ErrorAction SilentlyContinue
if (-not $link) {
    Write-Host "ERROR: link.exe not in PATH. Run from Developer PowerShell for VS 2022." -ForegroundColor Red
    exit 1
}
if ($link.Source -match "msys64|mingw|msys2|cygwin") {
    Write-Host "ERROR: link.exe is MSYS2/GNU. Use Developer PowerShell for VS 2022." -ForegroundColor Red
    exit 1
}

Write-Host "Testing native Rust build..." -ForegroundColor Cyan
Push-Location $root
cargo build -p meshmind-control-api 2>&1
$ok = ($LASTEXITCODE -eq 0)
Pop-Location
if ($ok) {
    Write-Host "SUCCESS: Native Rust build completed." -ForegroundColor Green
} else {
    Write-Host "FAILED: cargo build exited with $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}
