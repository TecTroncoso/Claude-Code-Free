from pathlib import Path

import yaml

CONFIG_PATH = Path(__file__).resolve().parent.parent / "litellm_config.yaml"


def _load() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_config_parses():
    cfg = _load()
    assert isinstance(cfg, dict)


def test_two_or_more_model_entries():
    cfg = _load()
    assert len(cfg["model_list"]) >= 2




def test_upstream_models_resolved_from_env():
    """Each model_list entry MUST resolve the upstream NIM id via `os.environ/NIM_DEFAULT_MODEL`.

    Hard-coding a literal NIM id (e.g. `nvidia_nim/meta/llama-3.1-70b-instruct`) was the
    bug that originally broke this proxy; the model id is intended to be env-driven.
    """
    cfg = _load()
    for entry in cfg["model_list"]:
        m = entry["litellm_params"]["model"]
        assert m == "os.environ/NIM_DEFAULT_MODEL", (
            f"upstream id should be env-resolved, got: {m!r}"
        )


def test_stream_enabled():
    cfg = _load()
    assert cfg["litellm_settings"]["stream"] is True


def test_general_settings_present():
    cfg = _load()
    assert "general_settings" in cfg
