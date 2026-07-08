import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def _base_env() -> dict[str, str]:
    """Minimal env that lets the launcher pass pre-flight (does not exercise a real NIM call)."""
    env = os.environ.copy()
    env["NVIDIA_API_KEY"] = "test-key-not-real"
    env["NIM_DEFAULT_MODEL"] = "nvidia_nim/meta/llama-3.1-70b-instruct"
    env["NIM_MODEL_ALLOWLIST"] = "nvidia_nim/meta/llama-3.1-70b-instruct"
    return env


def run_launcher(env: dict[str, str] | None = None, timeout: float = 5.0) -> subprocess.CompletedProcess:
    """Invoke `main.py` in a subprocess and return CompletedProcess so tests can assert on exit / stderr."""
    return subprocess.run(
        [sys.executable, "main.py"],
        cwd=REPO_ROOT,
        env=env if env is not None else _base_env(),
        capture_output=True,
        text=True,
        timeout=timeout,
    )


@pytest.fixture
def base_env() -> dict[str, str]:
    return _base_env()
