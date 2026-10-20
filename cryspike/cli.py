import argparse
import logging
import sys
import time

from cryspike.monitor import NvidiaGPUMonitor
from cryspike.detector import MiningDetector

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Cryspike: Detect silent crypto miners via GPU spikes during idle time."
    )
    parser.add_argument("--interval", type=int, default=5, help="Seconds between checks (default: 5)")
    parser.add_argument("--gpu-threshold", type=float, default=80.0, help="GPU %% considered high (default: 80)")
    parser.add_argument("--cpu-idle", type=float, default=10.0, help="CPU %% considered idle (default: 10)")
    parser.add_argument("--window", type=int, default=5, help="Consecutive suspicious readings to alert (default: 5)")
    parser.add_argument("--gpu", type=int, default=-1, help="GPU index to monitor (-1 = all, default: all)")
    return parser.parse_args()


def print_alert(gpu_idx: int, gpu_util: float, processes: list) -> None:
    print("\n" + "=" * 70)
    print("⚠️  ALERT: SUSTAINED SUSPICIOUS GPU ACTIVITY DETECTED ⚠️")
    print(f"GPU {gpu_idx} has been above threshold while system CPU is idle.")
    print(f"Current GPU utilization: {gpu_util:.1f}%")
    print("-" * 70)
    if processes:
        print("Processes currently using this GPU:")
        for p in processes:
            print(f"  PID {p['pid']:6d}  {p['name']:<30}  {p['used_memory_mb']} MB")
    else:
        print("  (No compute processes reported by NVML)")
    print("=" * 70 + "\n")


def main() -> None:
    args = parse_args()
    logger.info("Starting Cryspike v0.2...")

    monitor = NvidiaGPUMonitor()
    if not monitor.initialize():
        logger.error("No compatible NVIDIA GPU or driver found. Exiting.")
        sys.exit(1)

    gpu_count = monitor.get_gpu_count()
    if gpu_count == 0:
        logger.error("No GPUs detected.")
        sys.exit(1)

    # Which GPUs to watch
    targets = [args.gpu] if args.gpu >= 0 else list(range(gpu_count))

    detectors = {
        idx: MiningDetector(
            gpu_threshold=args.gpu_threshold,
            cpu_idle_threshold=args.cpu_idle,
            window_size=args.window,
        )
        for idx in targets
    }

    logger.info(f"Monitoring GPU(s): {targets}")
    logger.info(
        f"Thresholds → GPU > {args.gpu_threshold}% | CPU < {args.cpu_idle}% | window={args.window}"
    )
    logger.info("Press Ctrl+C to stop.\n")

    # Prime psutil so first reading is accurate
    try:
        import psutil
        psutil.cpu_percent(interval=None)
    except ImportError:
        pass

    try:
        while True:
            for idx in targets:
                util = monitor.get_utilization(idx)
                if util is None:
                    continue
                if detectors[idx].analyze_reading(util):
                    procs = monitor.get_processes(idx)
                    print_alert(idx, util, procs)
                    detectors[idx].reset()  # require a new full window for next alert
            time.sleep(args.interval)
    except KeyboardInterrupt:
        logger.info("\nStopped by user.")
    finally:
        monitor.shutdown()
        logger.info("Shutdown complete.")


if __name__ == "__main__":
    main()
