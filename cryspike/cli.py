"""Cryspike CLI entry point."""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

from cryspike.monitor import NvidiaGPUMonitor
from cryspike.detector import MiningDetector
from cryspike.config import CryspikeConfig
from cryspike.alerter import alert


def setup_logging(log_file: str | None = None) -> None:
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
    )


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Cryspike – Detect silent crypto miners via GPU spikes during idle time."
    )
    p.add_argument("--interval", type=int, help="Seconds between checks")
    p.add_argument("--gpu-threshold", type=float, help="GPU %% considered high")
    p.add_argument("--cpu-idle", type=float, help="CPU %% considered idle")
    p.add_argument("--window", type=int, help="Consecutive suspicious readings required")
    p.add_argument("--gpu", type=int, help="GPU index (-1 = all)")
    p.add_argument("--webhook", type=str, help="Discord/Slack webhook URL for alerts")
    p.add_argument("--log-file", type=str, help="Also write logs to this file")
    p.add_argument("--daemon", action="store_true", help="Run quietly (less console noise)")
    p.add_argument("--version", action="version", version="Cryspike 0.3.0")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    cfg = CryspikeConfig.from_sources(args)

    setup_logging(cfg.log_file)
    logger = logging.getLogger(__name__)

    if not cfg.daemon:
        logger.info("Starting Cryspike v0.3...")

    monitor = NvidiaGPUMonitor()
    if not monitor.initialize():
        logger.error("No compatible NVIDIA GPU or driver found. Exiting.")
        sys.exit(1)

    gpu_count = monitor.get_gpu_count()
    if gpu_count == 0:
        logger.error("No GPUs detected.")
        sys.exit(1)

    targets = [cfg.gpu] if cfg.gpu >= 0 else list(range(gpu_count))
    detectors = {
        idx: MiningDetector(
            gpu_threshold=cfg.gpu_threshold,
            cpu_idle_threshold=cfg.cpu_idle,
            window_size=cfg.window,
        )
        for idx in targets
    }

    logger.info(f"Monitoring GPU(s): {targets}")
    logger.info(
        f"Thresholds → GPU ≥ {cfg.gpu_threshold}% | CPU ≤ {cfg.cpu_idle}% | window={cfg.window}"
    )
    if cfg.webhook_url:
        logger.info("Webhook alerts enabled.")
    if not cfg.daemon:
        logger.info("Press Ctrl+C to stop.\n")

    # Prime psutil
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
                    alert(
                        gpu_idx=idx,
                        gpu_util=util,
                        processes=procs,
                        webhook_url=cfg.webhook_url,
                    )
                    detectors[idx].reset()

            time.sleep(cfg.interval)

    except KeyboardInterrupt:
        if not cfg.daemon:
            logger.info("\nStopped by user.")
    finally:
        monitor.shutdown()
        logger.info("Shutdown complete.")


if __name__ == "__main__":
    main()
