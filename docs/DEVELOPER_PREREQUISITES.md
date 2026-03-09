# MeshMind v2 - Developer Prerequisites

Windows-first setup. Use Developer PowerShell for VS 2022 for native Rust work.

## Confirmed Working (Ready Now)

| Component | Status | Notes |
|-----------|--------|-------|
| Rust MSVC toolchain | READY | `stable-x86_64-pc-windows-msvc` |
| Visual Studio C++ Build Tools | READY | Desktop development with C++ |
| Docker Desktop | READY | For reproducible builds |
| Node.js LTS | Check | Run `scripts/check-env.ps1` |
| Python 3.11+ | Check | For future workers |
| Ollama | Check | For local models |

## Required: Developer PowerShell for VS 2022

For native Rust MSVC builds, use **Developer PowerShell for VS 2022** (Start menu). Do not use a normal PowerShell where MSYS2/MinGW may put GNU `link.exe` before MSVC in PATH.

## Install Steps (If Not Ready)

1. **Rust**: https://rustup.rs → `rustup default stable-x86_64-pc-windows-msvc`
2. **VS Build Tools**: https://visualstudio.microsoft.com/visual-cpp-build-tools/ → Modify → "Desktop development with C++"
3. **Docker**: https://www.docker.com/products/docker-desktop/
4. **Node LTS**: https://nodejs.org/
5. **Ollama**: https://ollama.ai → `ollama pull llama3.2:3b`

## Verification

```powershell
.\scripts\check-env.ps1
.\scripts\test-rust-build.ps1   # From Developer PowerShell
```

## Run/Test Commands

| Command | Purpose |
|---------|---------|
| `.\scripts\check-env.ps1` | Verify environment |
| `.\scripts\bootstrap.ps1` | Full bootstrap (check + data dir + deps) |
| `.\scripts\run.ps1` | Start meshmind-core |
| `.\scripts\test.ps1` | Run cargo tests |
| `.\scripts\test-rust-build.ps1` | Verify native Rust build (Developer PS) |

## What Still Needs Manual Setup

- **First-time users**: Install Rust, VS Build Tools, Docker, Node, Python, Ollama per steps above
- **MSYS2 users**: Ensure Developer PowerShell is used so MSVC tools take precedence over GNU link.exe
- **Ollama models**: Run `ollama pull llama3.2:3b` after installing Ollama
