"""Consecutive-sample heuristic for suspicious GPU activity."""

from __future__ import annotations

import logging
import math
from collections import deque
from typing import Any, Deque, Optional, Sequence

try:
    import psutil
except ImportError:  # pragma: no cover - dependency is declared in pyproject.toml
    psutil = None

logger = logging.getLogger(__name__)


class MiningDetector:
    """Flag sustained high GPU utilization while total CPU utilization is low.

    This is a heuristic signal, not proof that a process is malware. When NVML
    reports processes and every reported name matches an exclusion, that sample
    is ignored. An empty/unavailable process list never suppresses an alert.
    """

    def __init__(
        self,
        gpu_threshold: float = 80.0,
        cpu_idle_threshold: float = 10.0,
        window_size: int = 5,
    ) -> None:
        if not isinstance(window_size, int) or isinstance(window_size, bool):
            raise ValueError("window_size must be a positive integer.")
        if window_size < 1:
            raise ValueError("window_size must be at least 1.")
        if not self._valid_threshold(gpu_threshold):
            raise ValueError("gpu_threshold must be between 0 and 100.")
        if not self._valid_threshold(cpu_idle_threshold):
            raise ValueError("cpu_idle_threshold must be between 0 and 100.")

        self.gpu_threshold = float(gpu_threshold)
        self.cpu_idle_threshold = float(cpu_idle_threshold)
        self.window_size = window_size
        self._suspicious_history: Deque[float] = deque(maxlen=window_size)

    @staticmethod
    def _valid_threshold(value: Any) -> bool:
        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(float(value))
            and 0 <= value <= 100
        )

    @staticmethod
    def _all_processes_excluded(
        processes: Optional[Sequence[dict]],
        excluded_processes: Optional[Sequence[str]],
    ) -> bool:
        if not processes or not excluded_processes:
            return False

        patterns = [item.casefold().strip() for item in excluded_processes if item.strip()]
        if not patterns:
            return False

        names = [
            str(process.get("name", "unknown")).casefold()
            for process in processes
        ]
        return bool(names) and all(
            any(pattern in name for pattern in patterns)
            for name in names
        )

    def analyze_reading(
        self,
        gpu_util: Optional[float],
        processes: Optional[Sequence[dict]] = None,
        excluded_processes: Optional[Sequence[str]] = None,
    ) -> bool:
        """Record one sample and return True once a full suspicious window exists."""
        if (
            gpu_util is None
            or not isinstance(gpu_util, (int, float))
            or isinstance(gpu_util, bool)
            or not math.isfinite(float(gpu_util))
            or not 0 <= gpu_util <= 100
        ):
            self.reset()
            return False

        if psutil is None:
            logger.warning("psutil is unavailable; CPU-idle state cannot be checked.")
            self.reset()
            return False

        try:
            cpu_util = psutil.cpu_percent(interval=None)
        except Exception as exc:  # keep a transient sensor failure from crashing the monitor
            logger.warning("Could not read CPU utilization (%s).", type(exc).__name__)
            self.reset()
            return False

        if (
            not isinstance(cpu_util, (int, float))
            or isinstance(cpu_util, bool)
            or not math.isfinite(float(cpu_util))
            or not 0 <= cpu_util <= 100
        ):
            logger.warning("CPU utilization reading was invalid; resetting detector window.")
            self.reset()
            return False

        if self._all_processes_excluded(processes, excluded_processes):
            logger.debug("GPU activity belongs only to configured excluded processes.")
            self.reset()
            return False

        is_gpu_high = gpu_util >= self.gpu_threshold
        is_cpu_idle = cpu_util <= self.cpu_idle_threshold

        if is_gpu_high and is_cpu_idle:
            logger.debug(
                "Suspicious sample: GPU %.1f%% | CPU %.1f%%", gpu_util, cpu_util
            )
            self._suspicious_history.append(float(gpu_util))
        else:
            self._suspicious_history.clear()

        if len(self._suspicious_history) == self.window_size:
            logger.warning(
                "Sustained high GPU utilization detected: GPU %.1f%%, CPU %.1f%%.",
                gpu_util,
                cpu_util,
            )
            return True
        return False

    def reset(self) -> None:
        """Clear history so the next alert requires a complete new sample window."""
        self._suspicious_history.clear()
