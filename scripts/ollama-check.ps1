# MeshMind v2 - Verify Ollama is installed and running
# Run: .\scripts\ollama-check.ps1
# Optionally specify URL: .\scripts\ollama-check.ps1 -Url "http://localhost:11434"

param(
    [string]$Url = "http://localhost:11434"
)

$ErrorActionPreference = "Continue"

Write-Host "MeshMind v2 - Ollama Check" -ForegroundColor Cyan
Write-Host ""

# 1. ollama CLI
$ollama = Get-Command ollama -ErrorAction SilentlyContinue
if (-not $ollama) {
    Write-Host "[FAIL] ollama CLI not found. Install from https://ollama.ai" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] ollama : $(ollama --version 2>$null)" -ForegroundColor Green

# 2. Ollama API reachability
try {
    $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "[OK] Ollama API reachable at $Url" -ForegroundColor Green
    } else {
        Write-Host "[WARN] Ollama at $Url returned $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "[FAIL] Ollama API unreachable at $Url : $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "  Start Ollama: ollama serve (or launch Ollama app)" -ForegroundColor Gray
    exit 1
}

# 3. List models
try {
    $tagsResponse = Invoke-RestMethod -Uri "$Url/api/tags" -TimeoutSec 5 -ErrorAction Stop
    $models = $tagsResponse.models
    if ($models -and $models.Count -gt 0) {
        Write-Host "[OK] Models available: $($models.Count)" -ForegroundColor Green
        foreach ($m in $models) {
            $name = if ($m.name) { $m.name } else { $m.model }
            $size = if ($m.size) { [math]::Round($m.size / 1GB, 2).ToString() + " GB" } else { "" }
            Write-Host "  - $name $size" -ForegroundColor Gray
        }
    } else {
        Write-Host "[WARN] No models pulled. Run: .\scripts\ollama-pull-models.ps1 -Profile cpu-friendly" -ForegroundColor Yellow
    }
} catch {
    Write-Host "[FAIL] Could not list models: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Ollama check complete." -ForegroundColor Green
