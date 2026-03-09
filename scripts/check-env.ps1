# MeshMind v2 - Environment check (Windows)
# Run: .\scripts\check-env.ps1
# Requires: Rust MSVC, VS C++ Build Tools, Docker, Node LTS, Python 3.11+, Ollama

$ErrorActionPreference = "Continue"
$errors = @()
$warnings = @()
$blockers = @()

Write-Host "MeshMind v2 - Environment Check (Windows)" -ForegroundColor Cyan
Write-Host ""

# 1. rustup
$rustup = Get-Command rustup -ErrorAction SilentlyContinue
if (-not $rustup) {
    $errors += "rustup not found. Install from https://rustup.rs"
} else {
    Write-Host "[OK] rustup : $(rustup --version 2>$null)" -ForegroundColor Green
}

# 2. Active toolchain (MSVC)
$activeToolchain = $null
if ($rustup) {
    $show = rustup show 2>$null | Out-String
    if ($show -match "active toolchain[\s\S]*?name:\s*(\S+)") { $activeToolchain = $matches[1].Trim() }
    if ($activeToolchain -match "msvc") {
        Write-Host "[OK] Active toolchain : $activeToolchain (MSVC)" -ForegroundColor Green
    } elseif ($activeToolchain -match "gnu") {
        $errors += "Active toolchain is GNU. Use: rustup default stable-x86_64-pc-windows-msvc"
    } else {
        Write-Host "[?] Active toolchain : $activeToolchain" -ForegroundColor Yellow
    }
}

# 3. cargo
$cargo = Get-Command cargo -ErrorAction SilentlyContinue
if (-not $cargo) {
    $errors += "cargo not found"
} else {
    Write-Host "[OK] cargo : $(cargo --version 2>$null)" -ForegroundColor Green
}

# 4 and 5. cl.exe and link.exe - must be Microsoft MSVC, not MSYS2/GNU
$cl = Get-Command cl.exe -ErrorAction SilentlyContinue
$link = Get-Command link.exe -ErrorAction SilentlyContinue
$clPath = if ($cl) { $cl.Source } else { $null }
$linkPath = if ($link) { $link.Source } else { $null }

$clIsMsvc = $clPath -and ($clPath -match "Microsoft Visual Studio") -and ($clPath -match "\\VC\\") -and ($clPath -match "MSVC")
$linkIsMsys = $linkPath -and ($linkPath -match "msys64|mingw|msys2|cygwin")
$linkIsMsvc = $linkPath -and (-not $linkIsMsys) -and ($linkPath -match "Microsoft Visual Studio") -and ($linkPath -match "\\VC\\") -and ($linkPath -match "MSVC")

if ($linkPath -and $linkIsMsys) {
    $blockers += "link.exe is MSYS2/GNU at: $linkPath. Use Developer PowerShell for VS 2022."
}
if (-not $clPath -and -not $linkPath) {
    $blockers += "cl.exe and link.exe not in PATH. Use Developer PowerShell for VS 2022."
}

if ($clIsMsvc) { Write-Host "[OK] cl.exe (MSVC) : $clPath" -ForegroundColor Green }
elseif ($clPath) { Write-Host "[BLOCK] cl.exe (non-MSVC) : $clPath" -ForegroundColor Red }
else { Write-Host "[--] cl.exe : not in PATH" -ForegroundColor Yellow }

if ($linkIsMsvc) { Write-Host "[OK] link.exe (MSVC) : $linkPath" -ForegroundColor Green }
elseif ($linkIsMsys) { Write-Host "[BLOCK] link.exe (MSYS2/GNU) : $linkPath" -ForegroundColor Red }
elseif ($linkPath) { Write-Host "[BLOCK] link.exe (non-MSVC) : $linkPath" -ForegroundColor Red }
else { Write-Host "[--] link.exe : not in PATH" -ForegroundColor Yellow }

# 6. vcvarsall.bat
$vcvarsallPath = $null
if ($linkIsMsvc -and $linkPath -match "(.+\\VC\\)") {
    $candidate = Join-Path $matches[1] "Auxiliary\Build\vcvarsall.bat"
    if (Test-Path $candidate) { $vcvarsallPath = $candidate }
}
if (-not $vcvarsallPath) {
    $paths = @(
        (Join-Path $env:ProgramFiles "Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat"),
        (Join-Path ${env:ProgramFiles(x86)} "Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat")
    )
    foreach ($p in $paths) { if (Test-Path $p) { $vcvarsallPath = $p; break } }
}
if ($vcvarsallPath) { Write-Host "[OK] vcvarsall.bat" -ForegroundColor Green }
elseif ($clIsMsvc -and $linkIsMsvc) { Write-Host "[OK] vcvarsall.bat : (MSVC tools in PATH)" -ForegroundColor Green }
else { $blockers += "vcvarsall.bat NOT FOUND. Install Desktop development with C++." }

# 7. Docker
$docker = Get-Command docker -ErrorAction SilentlyContinue
if ($docker) { Write-Host "[OK] docker : $(docker --version 2>$null)" -ForegroundColor Green }
else { $warnings += "Docker not installed." }

# 8. Node
$node = Get-Command node -ErrorAction SilentlyContinue
if ($node) { Write-Host "[OK] node : $(node --version 2>$null)" -ForegroundColor Green }
else { $warnings += "Node.js not found." }
$npm = Get-Command npm -ErrorAction SilentlyContinue
if ($npm) { Write-Host "[OK] npm : $(npm --version 2>$null)" -ForegroundColor Green }
else { $warnings += "npm not found." }

# 9. Python
$pyCmd = $null
if (Get-Command python -ErrorAction SilentlyContinue) { $pyCmd = "python" }
elseif (Get-Command python3 -ErrorAction SilentlyContinue) { $pyCmd = "python3" }
if ($pyCmd) { Write-Host "[OK] python : $(& $pyCmd --version 2>$null)" -ForegroundColor Green }
else { $warnings += "Python not installed." }

# 10. Ollama
$ollama = Get-Command ollama -ErrorAction SilentlyContinue
if ($ollama) {
    Write-Host "[OK] ollama : $(ollama --version 2>$null)" -ForegroundColor Green
    if ((ollama list 2>$null) -match "llama") { Write-Host "  models: llama present" -ForegroundColor Gray }
} else { $warnings += "Ollama not installed." }

# Summary
Write-Host ""
foreach ($b in $blockers) { Write-Host "BLOCKER: $b" -ForegroundColor Red }
foreach ($e in $errors) { Write-Host "ERROR: $e" -ForegroundColor Red }
foreach ($w in $warnings) { Write-Host "WARN: $w" -ForegroundColor Yellow }

$nativeReady = $clIsMsvc -and $linkIsMsvc
$dockerReady = $null -ne (Get-Command docker -ErrorAction SilentlyContinue)

Write-Host ""
Write-Host "VERDICT: Native Windows Rust: $(if ($nativeReady) { 'READY' } else { 'NOT READY' }) | Docker: $(if ($dockerReady) { 'READY' } else { 'NOT READY' })" -ForegroundColor $(if ($blockers.Count -eq 0 -and $errors.Count -eq 0) { 'Green' } else { 'White' })

if ($blockers.Count -gt 0 -or $errors.Count -gt 0) { exit 1 }
