# nim-proxy

OpenAI-compatible proxy (LiteLLM) in front of NVIDIA NIM. Designed to be used from Claude Code or any other OpenAI-style client.

The proxy maps a wildcard `*` plus two OpenAI-style model names (`claude-3-5-sonnet-20241022`, `claude-3-7-sonnet-20250219`) onto a single upstream NVIDIA NIM model id. The upstream id is **env-driven** (`NIM_DEFAULT_MODEL`); swapping it is a one-env-var change, no code change required.

---

## Commands

### Render (`render.yaml`)

Render reads `render.yaml` automatically when you connect the repo. No manual commands needed beyond the notes below.

| Where | Command / value | Notes |
|---|---|---|
| `buildCommand` | `pip install uv && uv pip install --system -e .` | Uses `uv` to install the package + dev deps. |
| `startCommand` | `python main.py` | Validates env, then spawns litellm subprocess. |
| `healthCheckPath` | `/health` | Hit by Render; the proxy must respond 200. |
| `region` | `oregon` | Pick whichever you prefer. |
| `plan` | `starter` | Move to `standard` when you outgrow free-tier cold starts. |

**Manual steps in Render dashboard** (cannot be automated — must be done once per service):

1. **Environment → Add Secret**:
   - `NVIDIA_API_KEY` — your NVIDIA NIM API key.
   - `LITELLM_MASTER_KEY` — any strong random string. Required by `litellm[proxy]` to authorize `/health`, `/metrics`, and `/key/generate` admin endpoints.
2. Wait for first build to complete. Proxy will boot to `/health`.
3. Smoke-test:

   ```bash
   curl https://<your-service>.onrender.com/health
   ```

### Local (your machine)

```bash
# 1. Create and activate a virtualenv (Windows PowerShell; for bash/macOS adjust accordingly).
python -m venv venv
.\venv\Scripts\activate

# 2. Install runtime + dev deps. Use either pip or uv.
pip install -e ".[dev]"        # or: pip install "litellm[proxy]" pytest httpx pyyaml python-dotenv

# 3. Copy the env template and fill in your real NVIDIA key.
copy .env.example .env         # Windows
# cp .env.example .env         # bash
# Then edit .env with a real NVIDIA_API_KEY and a strong LITELLM_MASTER_KEY.

# 4. Boot the proxy.
python main.py

# 5. From another terminal, smoke-test:
curl http://localhost:4000/health

# 6. Run the unit suite:
pytest -q
```

**Stop the local proxy**: `Ctrl-C` in the boot terminal.

---

## Environment variables

| Var | Required | Default | Purpose |
|---|---|---|---|
| `NVIDIA_API_KEY` | yes | — | Upstream auth for NVIDIA NIM. Set as Render dashboard secret. |
| `LITELLM_MASTER_KEY` | yes | — | LiteLLM proxy master key for admin endpoints. Set as Render dashboard secret. |
| `NIM_DEFAULT_MODEL` | yes | `nvidia_nim/minimaxai/minimax-m3` | Upstream NIM model id when the request omits `model`. |
| `NIM_MODEL_ALLOWLIST` | yes | — | Comma-separated list of allowed model ids. The proxy fails fast on boot if `NIM_DEFAULT_MODEL` is not in this set. |
| `RATE_LIMIT_BURST` | no | — | Reserved for the future rate-limit slice. |
| `RATE_LIMIT_REFILL_PER_SEC` | no | — | Reserved for the future rate-limit slice. |
| `PORT` | no | `4000` | Auto-injected by Render. |
| `DEBUG` | no | — | If `1` or `true`, the launcher passes `--detailed_debug` to the litellm subprocess (verbose request logs). |

---

## What this proxy does

| Endpoint | Method | Purpose |
|---|---|---|
| `/health` | GET | Liveness probe. Returns 200 once LiteLLM is booted. |
| `/v1/messages` | POST | Anthropic-compatible Messages API (used by Claude Code). |
| `/v1/chat/completions` | POST | OpenAI-compatible chat completions. Supports `stream=true` (chunked SSE forwarded). |
| `/v1/models` | GET | List model names exposed by the proxy. |
| `/metrics` | GET | Prometheus-style metrics from LiteLLM (latency, spend, errors). |
| `/key/generate` | POST | Generate per-client keys (admin endpoint). Auth: `LITELLM_MASTER_KEY`. |

---

## Why this model id

The proxy points at `nvidia_nim/minimaxai/minimax-m3` by default. Swap it via env (no code change):

```bash
# Local
NIM_DEFAULT_MODEL=nvidia_nim/<other-model-id> \
NIM_MODEL_ALLOWLIST=nvidia_nim/<other-model-id> \
python main.py
```

In Render: change `NIM_DEFAULT_MODEL` and `NIM_MODEL_ALLOWLIST` values in service Environment. Next deploy picks them up.

---

## Tests

```bash
pytest -q
```

The suite covers the pre-flight validator (4 cases) and the `litellm_config.yaml` shape (6 cases). No live NIM calls are made.

---

## Follow-up slices (not included)

- Per-key token bucket rate limiter (`RATE_LIMIT_BURST`, `RATE_LIMIT_REFILL_PER_SEC`).
- Custom observer for `LITELLM_MASTER_KEY`-authenticated request latency.
- Real E2E test against NIM (today only the validator + config shape are under test).
