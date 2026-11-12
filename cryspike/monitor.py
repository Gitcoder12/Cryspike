"""NVIDIA NVML adapter used to read GPU utilization and active processes."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

try:
    import pynvml
except ImportError:  # pragma: no cover - dependency is declared in pyproject.toml
    pynvml = None

logger = logging.getLogger(__name__)


class NvidiaGPUMonitor:
    """Small lifecycle-safe wrapper around NVIDIA's NVML Python bindings."""

    def __init__(self) -> None:
        self._initialized = False

    def initialize(self) -> bool:
        if pynvml is None:
            logger.error("nvidia-ml-py is not installed; GPU monitoring is unavailable.")
            return False
        if self._initialized:
            return True
        try:
            pynvml.nvmlInit()
            self._initialized = True
            logger.info("NVML initialized.")
            return True
        except pynvml.NVMLError as exc:
            logger.error("Could not initialize NVML (%s).", type(exc).__name__)
            return False

    def get_gpu_count(self) -> int:
        if not self._initialized or pynvml is None:
            return 0
        try:
            return int(pynvml.nvmlDeviceGetCount())
        except pynvml.NVMLError as exc:
            logger.error("Could not query GPU count (%s).", type(exc).__name__)
            return 0

    def get_utilization(self, device_index: int = 0) -> Optional[float]:
        if not self._initialized or pynvml is None:
            return None
        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(device_index)
            utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
            return float(utilization.gpu)
        except pynvml.NVMLError as exc:
            logger.error(
                "Could not query utilization for GPU %d (%s).",
                device_index,
                type(exc).__name__,
            )
            return None

    @staticmethod
    def _memory_megabytes(process: Any) -> int:
        memory = getattr(process, "usedGpuMemory", None)
        if not isinstance(memory, int) or memory < 0 or memory >= 2**63:
            return 0
        return memory // (1024 * 1024)

    def get_processes(self, device_index: int = 0) -> List[Dict[str, Any]]:
        """Return de-duplicated compute/graphics processes reported by NVML."""
        if not self._initialized or pynvml is None:
            return []

        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(device_index)
        except pynvml.NVMLError as exc:
            logger.error(
                "Could not access GPU %d process list (%s).",
                device_index,
                type(exc).__name__,
            )
            return []

        entries: Dict[int, Dict[str, Any]] = {}
        process_queries = (
            "nvmlDeviceGetComputeRunningProcesses",
            "nvmlDeviceGetGraphicsRunningProcesses",
        )
        for query_name in process_queries:
            query = getattr(pynvml, query_name, None)
            if query is None:
                continue
            try:
                running = query(handle)
            except pynvml.NVMLError as exc:
                logger.debug("%s unavailable (%s).", query_name, type(exc).__name__)
                continue

            for process in running:
                pid = int(getattr(process, "pid", 0))
                if pid <= 0:
                    continue
                memory_mb = self._memory_megabytes(process)
                existing = entries.get(pid)
                if existing is None:
                    try:
                        raw_name = pynvml.nvmlSystemGetProcessName(pid)
                        name = (
                            raw_name.decode("utf-8", errors="replace")
                            if isinstance(raw_name, bytes)
                            else str(raw_name)
                        )
                    except pynvml.NVMLError:
                        name = "unknown"
                    entries[pid] = {
                        "pid": pid,
                        "name": name,
                        "used_memory_mb": memory_mb,
                    }
                elif memory_mb > existing["used_memory_mb"]:
                    existing["used_memory_mb"] = memory_mb

        return sorted(entries.values(), key=lambda item: item["pid"])

    def shutdown(self) -> None:
        if not self._initialized or pynvml is None:
            self._initialized = False
            return
        try:
            pynvml.nvmlShutdown()
            logger.info("NVML shut down.")
        except pynvml.NVMLError as exc:
            logger.error("Error during NVML shutdown (%s).", type(exc).__name__)
        finally:
            self._initialized = False
