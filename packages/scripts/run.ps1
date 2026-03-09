# MeshMind v2 - Task runner (Windows)
# Usage: .\packages\scripts\run.ps1 <target>
# Targets: infra-up | infra-down | control-api | web | test | lint

param([Parameter(Position=0)]$Target = "help")

$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

switch ($Target) {
    "infra-up"   { docker compose -f "$root\infrastructure\docker-compose.yml" up -d }
    "infra-down" { docker compose -f "$root\infrastructure\docker-compose.yml" down }
    "control-api"{ Set-Location $root; cargo run -p meshmind-control-api }
    "web"        { Set-Location "$root\apps\web"; npm run dev }
    "test"       {
        Set-Location $root
        cargo test -p meshmind-control-api
        Set-Location "$root\apps\web"; npm run build
    }
    "lint"       {
        Set-Location $root
        cargo clippy -p meshmind-control-api
        Set-Location "$root\apps\web"; npm run lint
    }
    default {
        Write-Host "Targets: infra-up | infra-down | control-api | web | test | lint"
    }
}
