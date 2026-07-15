import importlib.util
from pathlib import Path


def load_module():
    module_path = Path(__file__).resolve().parents[1] / "0.0.2.py"
    spec = importlib.util.spec_from_file_location("dcmds", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_load_config_defaults():
    dcmds = load_module()
    cfg = dcmds.load_config()
    assert "safe_mode" in cfg
    assert "theme" in cfg
    assert "history_enabled" in cfg
    assert "history_max" in cfg
    assert "history_path" in cfg


def test_safe_mode_blocked():
    dcmds = load_module()
    dcmds.CONFIG = {"safe_mode": True}
    assert dcmds.safe_mode_blocked("shutdown") is True
    dcmds.CONFIG = {"safe_mode": False}
    assert dcmds.safe_mode_blocked("shutdown") is False
