from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from cryspike import cli
from cryspike.config import CryspikeConfig, CryspikeConfigError


class FakeMonitor:
    def __init__(self, initialized=True, gpu_count=1, utilization=90.0):
        self.initialized = initialized
        self.gpu_count = gpu_count
        self.utilization = utilization
        self.shutdown_called = False

    def initialize(self):
        return self.initialized

    def get_gpu_count(self):
        return self.gpu_count

    def get_utilization(self, index):
        return self.utilization

    def get_processes(self, index):
        return [{"pid": 42, "name": "python", "used_memory_mb": 128}]

    def shutdown(self):
        self.shutdown_called = True


def configure_main(monkeypatch, cfg, monitor) -> None:
    monkeypatch.setattr(
        cli,
        "CryspikeConfig",
        SimpleNamespace(from_sources=lambda args: cfg),
    )
    monkeypatch.setattr(cli, "NvidiaGPUMonitor", lambda: monitor)
    monkeypatch.setattr(cli, "setup_logging", lambda *args, **kwargs: None)


def test_version_flag_reports_package_version(capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        cli.parse_args(["--version"])
    assert exc.value.code == 0
    assert "Cryspike 0.4.0" in capsys.readouterr().out


def test_invalid_config_returns_exit_code_two(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cli.CryspikeConfig,
        "from_sources",
        Mock(side_effect=CryspikeConfigError("bad config")),
    )
    assert cli.main([]) == 2
    assert "bad config" in capsys.readouterr().err


def test_missing_nvidia_gpu_returns_exit_code_one(monkeypatch) -> None:
    monitor = FakeMonitor(initialized=False)
    configure_main(monkeypatch, CryspikeConfig(), monitor)
    assert cli.main([]) == 1


def test_out_of_range_gpu_is_rejected_and_monitor_is_shutdown(monkeypatch) -> None:
    monitor = FakeMonitor(gpu_count=1)
    configure_main(monkeypatch, CryspikeConfig(gpu=1), monitor)
    assert cli.main([]) == 2
    assert monitor.shutdown_called is True


def test_monitor_stops_cleanly_on_keyboard_interrupt(monkeypatch) -> None:
    monitor = FakeMonitor(utilization=None)
    configure_main(monkeypatch, CryspikeConfig(), monitor)

    class FakeDetector:
        def __init__(self, **kwargs):
            self.reset_called = False

        def analyze_reading(self, reading, **kwargs):
            assert reading is None
            return False

        def reset(self):
            self.reset_called = True

    monkeypatch.setattr(cli, "MiningDetector", FakeDetector)
    monkeypatch.setattr(cli.time, "sleep", Mock(side_effect=KeyboardInterrupt))

    assert cli.main([]) == 0
    assert monitor.shutdown_called is True


def test_alert_path_reports_processes_and_resets_detector(monkeypatch) -> None:
    monitor = FakeMonitor(utilization=96.0)
    configure_main(monkeypatch, CryspikeConfig(window=1), monitor)
    detector = Mock()
    detector.analyze_reading.return_value = True
    monkeypatch.setattr(cli, "MiningDetector", lambda **kwargs: detector)
    alert_mock = Mock()
    monkeypatch.setattr(cli, "alert", alert_mock)
    monkeypatch.setattr(cli.time, "sleep", Mock(side_effect=KeyboardInterrupt))

    assert cli.main([]) == 0
    alert_mock.assert_called_once_with(
        gpu_idx=0,
        gpu_util=96.0,
        processes=[{"pid": 42, "name": "python", "used_memory_mb": 128}],
        webhook_url=None,
        quiet=False,
    )
    detector.reset.assert_called_once()
    assert monitor.shutdown_called is True
