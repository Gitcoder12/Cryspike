import logging
from typing import Optional

# Gracefully handle missing dependency
try:
    import pynvml
except ImportError:
    pynvml = None

# Set up module-level logger
logger = logging.getLogger(__name__)


class NvidiaGPUMonitor:
    """
    A class to interface with NVIDIA GPUs via NVML.
    Handles initialization and querying of GPU utilization safely.
    """

    def __init__(self) -> None:
        self._initialized = False

    def initialize(self) -> bool:
        """
        Initializes the NVML library.
        Returns True if successful, False otherwise (e.g., no NVIDIA drivers).
        """
        if pynvml is None:
            logger.warning("nvidia-ml-py package is not installed. GPU monitoring disabled.")
            return False

        try:
            pynvml.nvmlInit()
            self._initialized = True
            logger.info("NVML initialized successfully. GPU monitoring active.")
            return True
        except pynvml.NVMLError as e:
            # This catches missing drivers or no compatible GPUs
            logger.warning(f"Failed to initialize NVML: {e}. GPU monitoring disabled.")
            return False

    def get_gpu_count(self) -> int:
        """Returns the number of available NVIDIA GPUs."""
        if not self._initialized:
            return 0
        try:
            return pynvml.nvmlDeviceGetCount()
        except pynvml.NVMLError as e:
            logger.error(f"Error getting GPU count: {e}")
            return 0

    def get_utilization(self, device_index: int = 0) -> Optional[float]:
        """
        Returns the current GPU utilization percentage (0-100) for a specific GPU.
        Returns None if it cannot be retrieved.
        """
        if not self._initialized:
            return None

        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(device_index)
            utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
            return float(utilization.gpu)
        except pynvml.NVMLError as e:
            logger.error(f"Error querying utilization for GPU {device_index}: {e}")
            return None

    def shutdown(self) -> None:
        """Cleanly shuts down the NVML library."""
        if self._initialized:
            try:
                pynvml.nvmlShutdown()
                logger.info("NVML shutdown cleanly.")
            except pynvml.NVMLError as e:
                logger.error(f"Error during NVML shutdown: {e}")
            finally:
                self._initialized = False
