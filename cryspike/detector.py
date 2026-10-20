import logging
from collections import deque
from typing import Optional

try:
    import psutil
except ImportError:
    psutil = None

logger = logging.getLogger(__name__)


class MiningDetector:
    """Detects sustained high GPU utilization while CPU is idle."""

    def __init__(
        self,
        gpu_threshold: float = 80.0,
        cpu_idle_threshold: float = 10.0,
        window_size: int = 5,
    ) -> None:
        self.gpu_threshold = gpu_threshold
        self.cpu_idle_threshold = cpu_idle_threshold
        self.window_size = window_size
        self._suspicious_history: deque[float] = deque(maxlen=window_size)

    def analyze_reading(self, gpu_util: Optional[float]) -> bool:
        if gpu_util is None:
            return False

        if psutil is None:
            logger.warning("psutil not installed. Cannot check CPU idle state.")
            cpu_util = 100.0
        else:
            cpu_util = psutil.cpu_percent(interval=None)

        is_gpu_high = gpu_util >= self.gpu_threshold
        is_cpu_idle = cpu_util <= self.cpu_idle_threshold

        if is_gpu_high and is_cpu_idle:
            logger.debug(f"Suspicious: GPU {gpu_util:.1f}% | CPU {cpu_util:.1f}%")
            self._suspicious_history.append(gpu_util)
        else:
            if self._suspicious_history:
                logger.debug(f"Normalized. GPU {gpu_util:.1f}% | CPU {cpu_util:.1f}%")
            self._suspicious_history.clear()

        if len(self._suspicious_history) == self.window_size:
            logger.warning(
                f"ALERT: Sustained high GPU ({gpu_util:.1f}%) while CPU idle ({cpu_util:.1f}%)"
            )
            return True
        return False

    def reset(self) -> None:
        """Clear the sliding window so a new full pattern is required."""
        self._suspicious_history.clear()
