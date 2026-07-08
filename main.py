"""Launcher for the LiteLLM proxy that fronts NVIDIA NIM.

Validates required env vars before spawning the LiteLLM subprocess.
Fails fast with a clear message naming the missing or mismatched var.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Final

from dotenv import load_dotenv

# Load .env before anything reads os.environ.
# python-dotenv is already a transitive dep of litellm; no extra install needed.
load_dotenv(Path(__file__).resolve().parent / ".env")

DEFAULT_NIM_MODEL: Final[str] = "nvidia_nim/minimaxai/minimax-m3"
REQUIRED_ENV_VARS: Final[tuple[str, ...]] = (
    "NVIDIA_API_KEY",
    "NIM_DEFAULT_MODEL",
    "NIM_MODEL_ALLOWLIST",
)


def require_env(name: str) -> str:
    """Return the env var's value or exit 1 with a clear message."""
    value = os.environ.get(name)
    if not value:
        sys.stderr.write(f"[nim-proxy] FATAL: required env var '{name}' is missing or empty.\n")
        sys.exit(1)
    return value


def parse_allowlist(raw: str) -> frozenset[str]:
    return frozenset(item.strip() for item in raw.split(",") if item.strip())


def validate_default_in_allowlist(default: str, allowlist: frozenset[str]) -> None:
    if default not in allowlist:
        sys.stderr.write(
            f"[nim-proxy] FATAL: NIM_DEFAULT_MODEL='{default}' is not in "
            f"NIM_MODEL_ALLOWLIST={sorted(allowlist)}.\n"
        )
        sys.exit(1)


def build_litellm_args(port: str) -> list[str]:
    """Construct the argv passed to the litellm CLI."""
    args = [
        "--config",
        "litellm_config.yaml",
        "--port",
        port,
    ]
    if os.environ.get("DEBUG", "").lower() in ("1", "true"):
        args.append("--detailed_debug")
    return args


def main() -> None:
    for var in REQUIRED_ENV_VARS:
        require_env(var)

    default_model = require_env("NIM_DEFAULT_MODEL")
    allowlist = parse_allowlist(require_env("NIM_MODEL_ALLOWLIST"))
    validate_default_in_allowlist(default_model, allowlist)

    port = os.environ.get("PORT", "4000")

    litellm_bin = shutil.which("litellm")
    if not litellm_bin:
        sys.stderr.write("[nim-proxy] FATAL: 'litellm' CLI not found in PATH.\n")
        sys.exit(1)

    print(
        f"[nim-proxy] Booting LiteLLM proxy on port {port} "
        f"(default model: {default_model})."
    )
    subprocess.run([litellm_bin, *build_litellm_args(port)])


if __name__ == "__main__":
    main()
