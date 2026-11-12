"""Command-line entry point for Cryspike."""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import Optional, Sequence

from cryspike import __version__
from cryspike.alerter import alert
from cryspike.config import CryspikeConfig, CryspikeConfigError
from cryspike.detector import MiningDetector
from cryspike.monitor import NvidiaGPUMonitor


def setup_logging(log_file: Optional[str] = None, daemon: bool = False) -> None:
    """Configure console logging, or file-only logging in daemon mode."""
    handlers = []
    if not daemon:
        handlers.append(logging.StreamHandler(sys.stdout))
    if log_file:
        expanded_log = Path(log_file).expanduser()
        expanded_log.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(expanded_log, encoding="utf-8"))
    if not handlers:
        handlers.append(logging.NullHandler())

    logging.basicConfig(
        level=logging.INFO if not daemon else logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
        force=True,
    )


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Cryspike: flag sustained high NVIDIA GPU utilization while CPU "
            "utilization remains low."
        )
    )
    parser.add_argument("--interval", type=int, default=None, help="Seconds between samples")
    parser.add_argument("--gpu-threshold", type=float, default=None,
                        help="High GPU utilization threshold (0-100)")
    parser.add_argument("--cpu-idle", type=float, default=None,
                        help="CPU idle threshold (0-100)")
    parser.add_argument("--window", type=int, default=None,
                        help="Consecutive suspicious samples required")
    parser.add_argument("--gpu", type=int, default=None,
                        help="GPU index; -1 monitors every GPU")
    parser.add_argument("--exclude-process", action="append", default=None, metavar="NAME",
                        help="Ignore samples when every NVML-reported GPU process matches NAME")
    parser.add_argument("--webhook", type=str, default=None,
                        help="Discord, Slack, or generic HTTPS webhook")
    parser.add_argument("--log-file", type=str, default=None, help="Write logs to this file")
    parser.add_argument("--daemon", action="store_true", default=None,
                        help="Suppress console output")
    parser.add_argument("--version", action="version", version=f"Cryspike {__version__}")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    try:
        cfg = CryspikeConfig.from_sources(args)
    except CryspikeConfigError as exc:
        print(f"Cryspike configuration error: {exc}", file=sys.stderr)
        return 2

    setup_logging(cfg.log_file, daemon=cfg.daemon)
    logger = logging.getLogger(__name__)

    if not cfg.daemon:
        logger.info("Starting Cryspike v%s.", __version__)

    monitor = NvidiaGPUMonitor()
    if not monitor.initialize():
        logger.error("No usable NVIDIA GPU/driver was found. Exiting.")
        return 1

    try:
        gpu_count = monitor.get_gpu_count()
        if gpu_count < 1:
            logger.error("NVML reported no NVIDIA GPUs.")
            return 1

        if cfg.gpu >= gpu_count:
            logger.error(
                "GPU index %d is out of range; this system has %d GPU(s).",
                cfg.gpu,
                gpu_count,
            )
            return 2

        targets = [cfg.gpu] if cfg.gpu >= 0 else list(range(gpu_count))
        detectors = {
            index: MiningDetector(
                gpu_threshold=cfg.gpu_threshold,
                cpu_idle_threshold=cfg.cpu_idle,
                window_size=cfg.window,
            )
            for index in targets
        }

        logger.info("Monitoring GPU(s): %s", targets)
        logger.info(
            "Thresholds: GPU >= %.1f%% | CPU <= %.1f%% | window=%d",
            cfg.gpu_threshold,
            cfg.cpu_idle,
            cfg.window,
        )

        try:
            import psutil
            psutil.cpu_percent(interval=None)
        except ImportError:
            logger.error("psutil is unavailable; CPU-idle detection cannot run.")
            return 1

        if not cfg.daemon:
            logger.info("Press Ctrl+C to stop.")

        while True:
            for index in targets:
                utilization = monitor.get_utilization(index)
                candidate_processes = None
                if cfg.exclude_processes and utilization is not None:
                    if utilization >= cfg.gpu_threshold:
                        candidate_processes = monitor.get_processes(index)

                triggered = detectors[index].analyze_reading(
                    utilization,
                    processes=candidate_processes,
                    excluded_processes=cfg.exclude_processes,
                )
                if triggered:
                    processes = (
                        candidate_processes
                        if candidate_processes is not None
                        else monitor.get_processes(index)
                    )
                    alert(
                        gpu_idx=index,
                        gpu_util=float(utilization),
                        processes=processes,
                        webhook_url=cfg.webhook_url,
                        quiet=cfg.daemon,
                    )
                    detectors[index].reset()

            time.sleep(cfg.interval)

    except KeyboardInterrupt:
        if not cfg.daemon:
            logger.info("Stopped by user.")
        return 0
    finally:
        monitor.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
