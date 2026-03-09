# MeshMind v2 - Run core (Windows)
# Run: .\scripts\run.ps1
# Starts meshmind-core. Use Developer PowerShell for native builds.

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
Set-Location $root
cargo run -p meshmind-control-api
