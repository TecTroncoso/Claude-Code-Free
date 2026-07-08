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


def test_no_glm_5_2_anywhere():
    raw = CONFIG_PATH.read_text(encoding="utf-8")
    assert "glm-5.2" not in raw
    cfg = _load()
    for entry in cfg["model_list"]:
        assert "glm-5.2" not in entry["litellm_params"]["model"]


def test_upstream_models_are_known_nim_ids():
    cfg = _load()
    valid = {"meta/llama-3.1-70b-instruct"}
    for entry in cfg["model_list"]:
        m = entry["litellm_params"]["model"]
        assert m.startswith("nvidia_nim/"), f"unsupported provider in {m}"
        assert m.removeprefix("nvidia_nim/") in valid, f"unexpected upstream: {m}"


def test_stream_enabled():
    cfg = _load()
    assert cfg["litellm_settings"]["stream"] is True


def test_general_settings_present():
    cfg = _load()
    assert "general_settings" in cfg
