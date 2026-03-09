# MeshMind v2 - Run tests (Windows)
# Run: .\scripts\test.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
Set-Location $root
cargo test -p meshmind-control-api
