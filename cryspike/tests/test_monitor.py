from types import SimpleNamespace

from cryspike.monitor import NvidiaGPUMonitor


def test_monitor_reports_unavailable_when_nvml_is_missing(monkeypatch) -> None:
    monkeypatch.setattr("cryspike.monitor.pynvml", None)
    monitor = NvidiaGPUMonitor()
    assert monitor.initialize() is False
    assert monitor.get_gpu_count() == 0
    assert monitor.get_utilization(0) is None
    assert monitor.get_processes(0) == []


def test_monitor_reads_and_deduplicates_processes(monkeypatch) -> None:
    class FakeNVMLError(Exception):
        pass

    process = SimpleNamespace(pid=123, usedGpuMemory=2 * 1024 * 1024)
    fake = SimpleNamespace(
        NVMLError=FakeNVMLError,
        NVML_VALUE_NOT_AVAILABLE=2**64 - 1,
        nvmlInit=lambda: None,
        nvmlShutdown=lambda: None,
        nvmlDeviceGetCount=lambda: 1,
        nvmlDeviceGetHandleByIndex=lambda index: index,
        nvmlDeviceGetUtilizationRates=lambda handle: SimpleNamespace(gpu=88),
        nvmlDeviceGetComputeRunningProcesses=lambda handle: [process],
        nvmlDeviceGetGraphicsRunningProcesses=lambda handle: [process],
        nvmlSystemGetProcessName=lambda pid: b"python",
    )
    monkeypatch.setattr("cryspike.monitor.pynvml", fake)

    monitor = NvidiaGPUMonitor()
    assert monitor.initialize() is True
    assert monitor.get_gpu_count() == 1
    assert monitor.get_utilization(0) == 88.0
    assert monitor.get_processes(0) == [
        {"pid": 123, "name": "python", "used_memory_mb": 2}
    ]
    monitor.shutdown()
    assert monitor.get_gpu_count() == 0
