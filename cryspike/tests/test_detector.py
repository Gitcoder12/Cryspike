import pytest
from unittest.mock import patch
from cryspike.detector import MiningDetector


# We use pytest's monkeypatch or unittest.mock to fake the CPU usage.
# This ensures the tests pass regardless of what your actual laptop is doing.

def test_normal_usage_no_alert() -> None:
    """Test that normal usage (low GPU, high CPU) does not trigger an alert."""
    detector = MiningDetector(gpu_threshold=80.0, cpu_idle_threshold=10.0, window_size=3)
    
    # Fake the CPU being at 50% (not idle)
    with patch('psutil.cpu_percent', return_value=50.0):
        # Feed it 3 readings of low GPU usage
        assert detector.analyze_reading(20.0) is False
        assert detector.analyze_reading(25.0) is False
        assert detector.analyze_reading(30.0) is False


def test_heavy_gaming_no_alert() -> None:
    """Test that high GPU + high CPU (e.g., gaming) does not trigger an alert."""
    detector = MiningDetector(gpu_threshold=80.0, cpu_idle_threshold=10.0, window_size=3)
    
    # Fake the CPU being at 60% (busy rendering the game)
    with patch('psutil.cpu_percent', return_value=60.0):
        # Feed it 3 readings of high GPU usage
        assert detector.analyze_reading(95.0) is False
        assert detector.analyze_reading(90.0) is False
        assert detector.analyze_reading(98.0) is False


def test_crypto_mining_triggers_alert() -> None:
    """Test that sustained high GPU + idle CPU triggers an alert after the window size."""
    detector = MiningDetector(gpu_threshold=80.0, cpu_idle_threshold=10.0, window_size=3)
    
    # Fake the CPU being at 5% (idle)
    with patch('psutil.cpu_percent', return_value=5.0):
        # Reading 1: Suspicious, but window not full yet
        assert detector.analyze_reading(95.0) is False
        # Reading 2: Suspicious, but window not full yet
        assert detector.analyze_reading(92.0) is False
        # Reading 3: Suspicious, window is full (3/3) -> ALERT!
        assert detector.analyze_reading(99.0) is True


def test_interrupted_mining_no_alert() -> None:
    """Test that if the suspicious pattern is interrupted, the window resets."""
    detector = MiningDetector(gpu_threshold=80.0, cpu_idle_threshold=10.0, window_size=3)
    
    # Reading 1: High GPU, idle CPU (Suspicious)
    with patch('psutil.cpu_percent', return_value=5.0):
        assert detector.analyze_reading(95.0) is False
        
    # Reading 2: User opens a heavy app, CPU spikes (Not suspicious)
    with patch('psutil.cpu_percent', return_value=80.0):
        assert detector.analyze_reading(95.0) is False
        
    # Reading 3 & 4: System goes back to idle (Suspicious again)
    with patch('psutil.cpu_percent', return_value=5.0):
        assert detector.analyze_reading(95.0) is False
        assert detector.analyze_reading(95.0) is False
        
    # Reading 5: Should trigger now because the pattern rebuilt after the interruption
    with patch('psutil.cpu_percent', return_value=5.0):
        assert detector.analyze_reading(95.0) is True
