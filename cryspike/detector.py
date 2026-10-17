import logging
from collections import deque
from typing import Optional

# Gracefully handle missing dependency
try:
    import psutil
except ImportError:
    psutil = None

logger = logging.getLogger(__name__)


class MiningDetector:
    """
    Analyzes GPU utilization data to detect sustained suspicious activity
    during periods when the system (CPU) appears idle.
    """

    def __init__(self, gpu_threshold: float = 80.0, cpu_idle_threshold: float = 10.0, window_size: int = 5) -> None:
        """
        :param gpu_threshold: GPU utilization percentage to be considered "high" (default 80%).
        :param cpu_idle_threshold: CPU utilization percentage to be considered "idle" (default 10%).
        :param window_size: Number of consecutive suspicious readings required to trigger an alert.
        """
        self.gpu_threshold = gpu_threshold
        self.cpu_idle_threshold = cpu_idle_threshold
        self.window_size = window_size
        
        # We store the recent history of suspicious readings
        self._suspicious_history: deque[float] = deque(maxlen=window_size)

    def analyze_reading(self, gpu_util: Optional[float]) -> bool:
        """
        Takes a single GPU utilization reading and determines if it is suspicious.
        
        :param gpu_util: Current GPU utilization percentage (0-100), or None if unavailable.
        :return: True if a sustained suspicious pattern is detected, False otherwise.
        """
        if gpu_util is None:
            return False

        # If psutil isn't available, we can't check CPU idle state. 
        # For this MVP, we'll assume the system might be busy to avoid false positives.
        if psutil is None:
            logger.warning("psutil is not installed. Cannot accurately detect idle state.")
            cpu_util = 100.0  # Assume busy to prevent false alarms
        else:
            # interval=None makes this non-blocking (compares against last call)
            cpu_util = psutil.cpu_percent(interval=None)

        is_gpu_high = gpu_util >= self.gpu_threshold
        is_cpu_idle = cpu_util <= self.cpu_idle_threshold

        if is_gpu_high and is_cpu_idle:
            logger.debug(f"Suspicious spike: GPU at {gpu_util}%, CPU at {cpu_util}%")
            self._suspicious_history.append(gpu_util)
        else:
            # If the user starts using the PC, or GPU load drops, reset the timer
            if len(self._suspicious_history) > 0:
                logger.debug(f"Activity normalized. GPU: {gpu_util}%, CPU: {cpu_util}%. Clearing history.")
            self._suspicious_history.clear()

        # Check if we have hit the required window size
        if len(self._suspicious_history) == self.window_size:
            logger.warning(f"ALERT: Sustained high GPU activity ({gpu_util}%) during idle CPU state ({cpu_util}%).")
            return True

        return False
