# MeshMind v2 — Test Plan: Model Configuration

Test coverage plan for model configuration and Ollama integration.

## Unit Tests (Config Layer)

### Config loading

| Test | Description |
|------|-------------|
| `config_loads_default_profile` | When no config file, default profile `cpu-friendly` is used |
| `config_loads_from_file` | TOML file is parsed; profile and models are correct |
| `config_env_overrides_profile` | `MESHMIND_MODEL_PROFILE` overrides file |
| `config_env_overrides_per_role` | `MESHMIND_MODEL_CHAT` etc. override profile for that role |
| `config_missing_file_uses_defaults` | Missing config path yields defaults, no panic |
| `config_invalid_toml_returns_error` | Malformed TOML returns Err, no panic |
| `config_unknown_profile_returns_error` | Invalid profile name returns Err |

### Model resolution

| Test | Description |
|------|-------------|
| `resolve_models_returns_all_roles` | chat, enrichment, embeddings populated from profile |
| `resolve_models_optional_image_caption` | image_caption present only if in config |
| `resolve_models_env_overrides` | Per-role env vars override profile |
| `resolve_models_fallback` | If role missing in profile, use chat model or return clear error |

## Integration Tests (Ollama)

### Health check

| Test | Description |
|------|-------------|
| `ollama_health_ok_when_running` | GET / returns 200 when Ollama is running (skip if Ollama not available) |
| `ollama_health_fail_when_down` | GET / fails when Ollama not running (mock or assume env) |

### Model availability

| Test | Description |
|------|-------------|
| `ollama_tags_returns_models` | GET /api/tags returns JSON with models array (skip if Ollama not available) |
| `model_matches_exact` | `llama3.2:3b` in config matches `llama3.2:3b` in tags |
| `model_matches_with_tag` | `llama3.2` in config matches `llama3.2:latest` or `llama3.2` in tags |
| `model_missing_detected` | Requested model not in tags yields "missing" |

## Mock Strategy

- **Unit tests:** No network. Use fixture TOML files and mock `ModelConfig` types.
- **Integration tests:** Use `OLLAMA_URL`; skip tests if `http://localhost:11434` unreachable (e.g. `#[ignore]` with env gate).
- **CI:** Optional Ollama container in CI for integration tests; or mark as `#[ignore]` and run manually.

## Test Files

| File | Scope |
|------|-------|
| `crates/core/src/config/model_config.rs` (or similar) | Unit tests for config parsing |
| `crates/core/tests/model_config_test.rs` | Integration tests for config + optional Ollama |

## Coverage Targets

- Config parsing: 100% of parse paths
- Model resolution: All branches (profile, env override, fallback)
- Ollama client: Happy path + error handling (connection refused, timeout, invalid JSON)
