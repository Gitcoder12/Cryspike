import pytest
from unittest.mock import patch
from cryspike.detector import MiningDetector


def test_normal_usage_no_alert() -> None:
    detector = MiningDetector(gpu_threshold=80.0, cpu_idle_threshold=10.0, window_size=3)
    with patch("psutil.cpu_percent", return_value=50.0):
        assert detector.analyze_reading(20.0) is False
        assert detector.analyze_reading(25.0) is False
        assert detector.analyze_reading(30.0) is False


def test_heavy_gaming_no_alert() -> None:
    detector = MiningDetector(gpu_threshold=80.0, cpu_idle_threshold=10.0, window_size=3)
    with patch("psutil.cpu_percent", return_value=60.0):
        assert detector.analyze_reading(95.0) is False
        assert detector.analyze_reading(90.0) is False
        assert detector.analyze_reading(98.0) is False


def test_crypto_mining_triggers_alert() -> None:
    detector = MiningDetector(gpu_threshold=80.0, cpu_idle_threshold=10.0, window_size=3)
    with patch("psutil.cpu_percent", return_value=5.0):
        assert detector.analyze_reading(95.0) is False
        assert detector.analyze_reading(92.0) is False
        assert detector.analyze_reading(99.0) is True


def test_interrupted_mining_resets() -> None:
    detector = MiningDetector(gpu_threshold=80.0, cpu_idle_threshold=10.0, window_size=3)
    with patch("psutil.cpu_percent", return_value=5.0):
        assert detector.analyze_reading(95.0) is False
    with patch("psutil.cpu_percent", return_value=80.0):
        assert detector.analyze_reading(95.0) is False
    with patch("psutil.cpu_percent", return_value=5.0):
        assert detector.analyze_reading(95.0) is False
        assert detector.analyze_reading(95.0) is False
        assert detector.analyze_reading(95.0) is True


def test_reset() -> None:
    detector = MiningDetector(window_size=2)
    with patch("psutil.cpu_percent", return_value=5.0):
        detector.analyze_reading(90.0)
        detector.analyze_reading(90.0)
        assert len(detector._suspicious_history) == 2
        detector.reset()
        assert len(detector._suspicious_history) == 0
