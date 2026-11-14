from argparse import Namespace
from pathlib import Path

import pytest

from cryspike.config import CryspikeConfig, CryspikeConfigError


ENV_NAMES = [
    "CRYSPIKE_INTERVAL",
    "CRYSPIKE_GPU_THRESHOLD",
    "CRYSPIKE_CPU_IDLE",
    "CRYSPIKE_WINDOW",
    "CRYSPIKE_GPU",
    "CRYSPIKE_WEBHOOK",
    "CRYSPIKE_LOG_FILE",
    "CRYSPIKE_EXCLUDE_PROCESSES",
    "CRYSPIKE_DAEMON",
]


def sandbox_config(monkeypatch, tmp_path) -> None:
    for name in ENV_NAMES:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "home")


def test_defaults_are_valid(monkeypatch, tmp_path) -> None:
    sandbox_config(monkeypatch, tmp_path)
    cfg = CryspikeConfig.from_sources()
    assert cfg.interval == 5
    assert cfg.window == 5
    assert cfg.gpu == -1
    assert cfg.exclude_processes == []


def test_cli_overrides_environment_and_toml(monkeypatch, tmp_path) -> None:
    sandbox_config(monkeypatch, tmp_path)
    (tmp_path / "cryspike.toml").write_text(
        "interval = 7\ngpu_threshold = 75.0\n", encoding="utf-8"
    )
    monkeypatch.setenv("CRYSPIKE_INTERVAL", "8")
    args = Namespace(
        interval=9, gpu_threshold=None, cpu_idle=None, window=None, gpu=None,
        webhook=None, log_file=None, exclude_process=None, daemon=None,
    )
    cfg = CryspikeConfig.from_sources(args)
    assert cfg.interval == 9
    assert cfg.gpu_threshold == 75.0


def test_environment_overrides_toml(monkeypatch, tmp_path) -> None:
    sandbox_config(monkeypatch, tmp_path)
    (tmp_path / "cryspike.toml").write_text("interval = 7\n", encoding="utf-8")
    monkeypatch.setenv("CRYSPIKE_INTERVAL", "8")
    cfg = CryspikeConfig.from_sources()
    assert cfg.interval == 8


def test_csv_exclusions_are_parsed(monkeypatch, tmp_path) -> None:
    sandbox_config(monkeypatch, tmp_path)
    monkeypatch.setenv("CRYSPIKE_EXCLUDE_PROCESSES", " blender, OBS ,, ")
    cfg = CryspikeConfig.from_sources()
    assert cfg.exclude_processes == ["blender", "OBS"]


@pytest.mark.parametrize(
    "content",
    [
        "interval = 0\n",
        "window = -1\n",
        "gpu = -2\n",
        "gpu_threshold = 101\n",
        "unknown_setting = true\n",
        "exclude_processes = [1, 2]\n",
    ],
)
def test_invalid_toml_values_are_rejected(monkeypatch, tmp_path, content: str) -> None:
    sandbox_config(monkeypatch, tmp_path)
    (tmp_path / "cryspike.toml").write_text(content, encoding="utf-8")
    with pytest.raises(CryspikeConfigError):
        CryspikeConfig.from_sources()


@pytest.mark.parametrize(
    "value", ["http://example.com/hook", "not-a-url", "https:///missing-host"]
)
def test_non_https_or_invalid_webhook_is_rejected(value: str) -> None:
    cfg = CryspikeConfig(webhook_url=value)
    with pytest.raises(CryspikeConfigError):
        cfg.validate()


def test_bad_environment_number_is_reported(monkeypatch, tmp_path) -> None:
    sandbox_config(monkeypatch, tmp_path)
    monkeypatch.setenv("CRYSPIKE_WINDOW", "many")
    with pytest.raises(CryspikeConfigError, match="CRYSPIKE_WINDOW"):
        CryspikeConfig.from_sources()
