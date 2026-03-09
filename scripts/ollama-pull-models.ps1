# MeshMind v2 - Pull Ollama models for a profile
# Run: .\scripts\ollama-pull-models.ps1 -Profile cpu-friendly
# Profiles: cpu-friendly | better-quality | minimal

param(
    [ValidateSet("cpu-friendly", "better-quality", "minimal")]
    [string]$Profile = "cpu-friendly"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$configPath = Join-Path $root "config\meshmind-models.toml"

# Model sets per profile (mirrors config; no TOML parse to avoid deps)
$profileModels = @{
    "cpu-friendly"   = @("llama3.2:3b", "nomic-embed-text")
    "better-quality" = @("llama3.2", "mistral:7b", "nomic-embed-text")
    "minimal"        = @("llama3.2:1b", "nomic-embed-text")
}

$models = $profileModels[$Profile]
if (-not $models) {
    Write-Host "Unknown profile: $Profile" -ForegroundColor Red
    exit 1
}

# Check ollama
$ollama = Get-Command ollama -ErrorAction SilentlyContinue
if (-not $ollama) {
    Write-Host "ollama not found. Install from https://ollama.ai" -ForegroundColor Red
    exit 1
}

Write-Host "MeshMind v2 - Pull models for profile: $Profile" -ForegroundColor Cyan
Write-Host "Models: $($models -join ', ')" -ForegroundColor Gray
Write-Host ""

foreach ($m in $models) {
    Write-Host "Pulling $m..." -ForegroundColor Yellow
    & ollama pull $m
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[FAIL] ollama pull $m failed" -ForegroundColor Red
        exit $LASTEXITCODE
    }
    Write-Host "[OK] $m" -ForegroundColor Green
}

Write-Host ""
Write-Host "Done. Run .\scripts\ollama-check.ps1 to verify." -ForegroundColor Green
