# nim-proxy

OpenAI-compatible proxy (LiteLLM) in front of NVIDIA NIM. Designed to be used from Claude Code or any other OpenAI-style client.

The proxy maps two OpenAI-style model names (`claude-3-5-sonnet-20241022`, `claude-3-7-sonnet-20250219`) onto a single upstream NVIDIA NIM model id. Swapping the upstream model is a one-line env change; no code change required.

## Quick start (local)

```bash
python -m venv .venv
.venv\Scripts\activate              # Windows
pip install -e ".[dev]" || true      # or: pip install litellm pytest pyyaml httpx
copy .env.example .env              # then edit .env with a real NVIDIA_API_KEY
python main.py
```

The launcher validates `NVIDIA_API_KEY`, `NIM_DEFAULT_MODEL`, and `NIM_MODEL_ALLOWLIST` before booting LiteLLM. It exits non-zero with a clear message if any of those are missing or mismatched.

Once booted:

- `GET  /healthz`                           — proxy is alive.
- `POST /v1/chat/completions`               — OpenAI-compatible chat completions.
- `POST /v1/chat/completions` w/ `stream`   — chunked SSE passthrough.

## Render deploy

1. Push this repo to GitHub/GitLab.
2. In Render: **New → Web Service → connect repo**.
3. Render reads `render.yaml` automatically and provisions the service.
4. **Manual step (cannot be automated):** in the Render dashboard go to your service → **Environment** → **Add Secret** → set `NVIDIA_API_KEY` with your real NVIDIA key. Render injects it into the runtime; the proxy will pass the pre-flight validator and boot.
5. Wait for `/healthz` to return 200. Test with:

   ```bash
   curl https://<your-service>.onrender.com/v1/chat/completions \
     -H "Authorization: Bearer ${ANTHROPIC_API_KEY}" \
     -H "Content-Type: application/json" \
     -d '{"model":"claude-3-5-sonnet-20241022","messages":[{"role":"user","content":"ping"}]}'
   ```

## Environment variables

| Var | Required | Default | Purpose |
|-----|----------|---------|---------|
| `NVIDIA_API_KEY` | yes | — | Upstream auth for NVIDIA NIM. |
| `NIM_DEFAULT_MODEL` | yes | `minimaxai/minimax-m3` | Upstream NIM model id when the request omits `model`. |
| `NIM_MODEL_ALLOWLIST` | yes | — | Comma-separated list of allowed model ids. The proxy fails fast if `NIM_DEFAULT_MODEL` is not in this set. |
| `RATE_LIMIT_BURST` | no | — | Reserved for the future rate-limit slice. |
| `RATE_LIMIT_REFILL_PER_SEC` | no | — | Reserved for the future rate-limit slice. |
| `PORT` | no | `4000` | Auto-injected by Render. |

## Why this model

The proxy maps OpenAI-style Claude model names to an upstream NVIDIA NIM model id. The default in this repo is `minimaxai/minimax-m3` because it is available on the NVIDIA NIM free inference tier.

To swap the upstream:

```bash
# Local
NIM_DEFAULT_MODEL=nvidia/llama-3.3-nemotron-super-49b-v1 \
NIM_MODEL_ALLOWLIST=nvidia/llama-3.3-nemotron-super-49b-v1 \
python main.py
```

In Render: change the values of `NIM_DEFAULT_MODEL` and `NIM_MODEL_ALLOWLIST` in the service Environment. The next deployment picks them up.

## Tests

```bash
pytest -q
```

10 unit tests cover the pre-flight validator and the `litellm_config.yaml` shape. They run without any live NIM calls.

## Follow-up slices (not included)

- Per-key token bucket rate limiter (`RATE_LIMIT_BURST`, `RATE_LIMIT_REFILL_PER_SEC`).
- Custom `/metrics` endpoint with Prometheus text format.
- Real E2E test against NIM (currently only the validator + config shape are under test).
