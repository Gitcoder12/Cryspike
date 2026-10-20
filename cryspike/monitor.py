import logging
from typing import Optional, List, Dict, Any

try:
    import pynvml
except ImportError:
    pynvml = None

logger = logging.getLogger(__name__)


class NvidiaGPUMonitor:
    """Interface with NVIDIA GPUs via NVML. Supports multi-GPU and process listing."""

    def __init__(self) -> None:
        self._initialized = False

    def initialize(self) -> bool:
        if pynvml is None:
            logger.warning("nvidia-ml-py not installed. GPU monitoring disabled.")
            return False
        try:
            pynvml.nvmlInit()
            self._initialized = True
            logger.info("NVML initialized. GPU monitoring active.")
            return True
        except pynvml.NVMLError as e:
            logger.warning(f"Failed to initialize NVML: {e}")
            return False

    def get_gpu_count(self) -> int:
        if not self._initialized:
            return 0
        try:
            return pynvml.nvmlDeviceGetCount()
        except pynvml.NVMLError as e:
            logger.error(f"Error getting GPU count: {e}")
            return 0

    def get_utilization(self, device_index: int = 0) -> Optional[float]:
        if not self._initialized:
            return None
        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(device_index)
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            return float(util.gpu)
        except pynvml.NVMLError as e:
            logger.error(f"Error querying GPU {device_index}: {e}")
            return None

    def get_processes(self, device_index: int = 0) -> List[Dict[str, Any]]:
        """Return list of processes currently using the GPU."""
        if not self._initialized:
            return []
        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(device_index)
            procs = pynvml.nvmlDeviceGetComputeRunningProcesses(handle)
            result = []
            for p in procs:
                try:
                    name = pynvml.nvmlSystemGetProcessName(p.pid)
                except pynvml.NVMLError:
                    name = "unknown"
                result.append({
                    "pid": p.pid,
                    "name": name.decode() if isinstance(name, bytes) else str(name),
                    "used_memory_mb": p.usedGpuMemory // (1024 * 1024) if p.usedGpuMemory else 0,
                })
            return result
        except pynvml.NVMLError as e:
            logger.error(f"Error listing processes on GPU {device_index}: {e}")
            return []

    def shutdown(self) -> None:
        if self._initialized:
            try:
                pynvml.nvmlShutdown()
                logger.info("NVML shutdown cleanly.")
            except pynvml.NVMLError as e:
                logger.error(f"Error during NVML shutdown: {e}")
            finally:
                self._initialized = False
