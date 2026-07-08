import os

import pytest

from tests.conftest import run_launcher  # noqa: F401  (re-exported fixture if needed)


def _env_without(missing: str) -> dict[str, str]:
    """Start from a fully-valid env, drop one var, return the modified env."""
    env = {
        "PATH": os.environ.get("PATH", ""),
        "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
        "PYTHONIOENCODING": "utf-8",
    }
    base = {
        "NVIDIA_API_KEY": "test-key",
        "NIM_DEFAULT_MODEL": "meta/llama-3.1-70b-instruct",
        "NIM_MODEL_ALLOWLIST": "meta/llama-3.1-70b-instruct",
    }
    base.pop(missing, None)
    env.update(base)
    return env


def test_missing_nvidia_api_key_fails_fast():
    result = run_launcher(env=_env_without("NVIDIA_API_KEY"))
    assert result.returncode == 1
    assert "NVIDIA_API_KEY" in result.stderr


def test_missing_default_model_fails_fast():
    result = run_launcher(env=_env_without("NIM_DEFAULT_MODEL"))
    assert result.returncode == 1
    assert "NIM_DEFAULT_MODEL" in result.stderr


def test_empty_allowlist_fails_fast():
    env = _env_without("NIM_MODEL_ALLOWLIST")
    env["NIM_MODEL_ALLOWLIST"] = ""
    result = run_launcher(env=env)
    assert result.returncode == 1
    assert "NIM_MODEL_ALLOWLIST" in result.stderr


def test_default_not_in_allowlist_fails_fast():
    env = _env_without("NIM_MODEL_ALLOWLIST")
    env["NIM_DEFAULT_MODEL"] = "meta/llama-3.1-70b-instruct"
    env["NIM_MODEL_ALLOWLIST"] = "meta/llama-3.3-70b-instruct"
    result = run_launcher(env=env)
    assert result.returncode == 1
    assert "not in NIM_MODEL_ALLOWLIST" in result.stderr
