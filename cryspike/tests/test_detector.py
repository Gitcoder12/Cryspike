from unittest.mock import patch

import pytest

from cryspike.detector import MiningDetector


def test_normal_usage_does_not_alert() -> None:
    detector = MiningDetector(window_size=3)
    with patch("cryspike.detector.psutil.cpu_percent", return_value=50.0):
        assert detector.analyze_reading(20.0) is False
        assert detector.analyze_reading(25.0) is False
        assert detector.analyze_reading(30.0) is False


def test_high_gpu_and_busy_cpu_does_not_alert() -> None:
    detector = MiningDetector(window_size=3)
    with patch("cryspike.detector.psutil.cpu_percent", return_value=60.0):
        assert detector.analyze_reading(95.0) is False
        assert detector.analyze_reading(90.0) is False
        assert detector.analyze_reading(98.0) is False


def test_sustained_gpu_high_and_cpu_idle_triggers_when_window_is_full() -> None:
    detector = MiningDetector(window_size=3)
    with patch("cryspike.detector.psutil.cpu_percent", return_value=5.0):
        assert detector.analyze_reading(95.0) is False
        assert detector.analyze_reading(92.0) is False
        assert detector.analyze_reading(99.0) is True
        detector.reset()
        assert detector.analyze_reading(99.0) is False


def test_normal_sample_breaks_consecutive_window() -> None:
    detector = MiningDetector(window_size=3)
    cpu_samples = [5.0, 80.0, 5.0, 5.0, 5.0]
    with patch("cryspike.detector.psutil.cpu_percent", side_effect=cpu_samples):
        assert detector.analyze_reading(95.0) is False
        assert detector.analyze_reading(95.0) is False
        assert detector.analyze_reading(95.0) is False
        assert detector.analyze_reading(95.0) is False
        assert detector.analyze_reading(95.0) is True


def test_missing_gpu_sample_resets_consecutive_window() -> None:
    detector = MiningDetector(window_size=2)
    with patch("cryspike.detector.psutil.cpu_percent", return_value=5.0):
        assert detector.analyze_reading(95.0) is False
        assert detector.analyze_reading(None) is False
        assert detector.analyze_reading(95.0) is False
        assert detector.analyze_reading(95.0) is True


def test_excluded_processes_suppress_a_sample_only_when_all_are_excluded() -> None:
    detector = MiningDetector(window_size=2)
    excluded = [{"pid": 10, "name": "blender"}]
    with patch("cryspike.detector.psutil.cpu_percent", return_value=2.0):
        assert detector.analyze_reading(
            99.0, processes=excluded, excluded_processes=["blend"]
        ) is False
        assert detector.analyze_reading(99.0) is False
        assert detector.analyze_reading(99.0) is True


def test_empty_process_list_does_not_suppress_sample() -> None:
    detector = MiningDetector(window_size=1)
    with patch("cryspike.detector.psutil.cpu_percent", return_value=2.0):
        assert detector.analyze_reading(
            99.0, processes=[], excluded_processes=["blender"]
        ) is True


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -1.0, 101.0])
def test_invalid_gpu_reading_resets_window(value: float) -> None:
    detector = MiningDetector(window_size=2)
    with patch("cryspike.detector.psutil.cpu_percent", return_value=2.0):
        assert detector.analyze_reading(99.0) is False
        assert detector.analyze_reading(value) is False
        assert detector.analyze_reading(99.0) is False


@pytest.mark.parametrize(
    "kwargs",
    [
        {"window_size": 0},
        {"window_size": -1},
        {"gpu_threshold": 101},
        {"cpu_idle_threshold": -1},
    ],
)
def test_invalid_detector_settings_are_rejected(kwargs: dict) -> None:
    with pytest.raises(ValueError):
        MiningDetector(**kwargs)
