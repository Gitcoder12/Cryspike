import argparse
import logging
import sys
import time

from cryspike.monitor import NvidiaGPUMonitor
from cryspike.detector import MiningDetector

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parses command line arguments."""
    parser = argparse.ArgumentParser(
        description="Cryspike: Detects suspicious GPU activity potentially associated with cryptomining."
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=5,
        help="Time in seconds between GPU checks (default: 5)",
    )
    parser.add_argument(
        "--gpu-threshold",
        type=float,
        default=80.0,
        help="GPU utilization percentage to be considered 'high' (default: 80.0)",
    )
    parser.add_argument(
        "--cpu-idle",
        type=float,
        default=10.0,
        help="CPU utilization percentage to be considered 'idle' (default: 10.0)",
    )
    parser.add_argument(
        "--window",
        type=int,
        default=5,
        help="Consecutive suspicious readings required to trigger an alert (default: 5)",
    )
    return parser.parse_args()


def main() -> None:
    """Main entry point for the Cryspike CLI."""
    args = parse_args()

    logger.info("Starting Cryspike MVP...")
    
    monitor = NvidiaGPUMonitor()
    if not monitor.initialize():
        logger.error("Cannot start Cryspike: No compatible NVIDIA GPU found or driver missing.")
        sys.exit(1)

    detector = MiningDetector(
        gpu_threshold=args.gpu_threshold,
        cpu_idle_threshold=args.cpu_idle,
        window_size=args.window,
    )

    gpu_count = monitor.get_gpu_count()
    logger.info(f"Monitoring {gpu_count} GPU(s). Press Ctrl+C to stop.")
    logger.info(f"Thresholds: GPU > {args.gpu_threshold}%, CPU < {args.cpu_idle}% for {args.window} consecutive checks.")

    # Prime psutil so the first reading isn't 0.0
    # (The detector handles this, but it's good practice)
    try:
        import psutil
        psutil.cpu_percent(interval=None)
    except ImportError:
        pass

    try:
        while True:
            # Check GPU 0 for now. (Multi-GPU support can be added later).
            gpu_util = monitor.get_utilization(device_index=0)
            
            if gpu_util is not None:
                # Feed the reading to the detector
                is_suspicious = detector.analyze_reading(gpu_util)
                
                if is_suspicious:
                    # Print a highly visible alert
                    print("\n" + "="*60)
                    print("⚠️  ALERT: SUSTAINED SUSPICIOUS GPU ACTIVITY DETECTED ⚠️")
                    print(f"GPU 0 has been above {args.gpu_threshold}% while CPU is idle.")
                    print("This could indicate unauthorized cryptomining.")
                    print("Please check your running processes (e.g., using 'nvidia-smi').")
                    print("="*60 + "\n")
            
            # Wait before the next check
            time.sleep(args.interval)

    except KeyboardInterrupt:
        logger.info("\nCryspike stopped by user.")
    finally:
        monitor.shutdown()
        logger.info("Shutdown complete.")


if __name__ == "__main__":
    main()
