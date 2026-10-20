"""Configuration loader for Cryspike.

Supports:
- CLI arguments (highest priority)
- Environment variables
- Optional TOML config file (cryspike.toml or ~/.config/cryspike/config.toml)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        tomllib = None  # type: ignore


@dataclass
class CryspikeConfig:
    interval: int = 5
    gpu_threshold: float = 80.0
    cpu_idle: float = 10.0
    window: int = 5
    gpu: int = -1  # -1 = all
    exclude_processes: List[str] = field(default_factory=lambda: [
        "chrome", "firefox", "code", "blender", "obs", "steam",
        "Xorg", "gnome-shell", "plasmashell", "nvidia-smi"
    ])
    webhook_url: Optional[str] = None
    log_file: Optional[str] = None
    daemon: bool = False

    @classmethod
    def from_sources(cls, cli_args=None) -> "CryspikeConfig":
        cfg = cls()

        # 1. Load from TOML if present
        for candidate in [
            Path("cryspike.toml"),
            Path.home() / ".config" / "cryspike" / "config.toml",
            Path.home() / ".cryspike.toml",
        ]:
            if candidate.exists() and tomllib is not None:
                with open(candidate, "rb") as f:
                    data = tomllib.load(f)
                for k, v in data.items():
                    if hasattr(cfg, k):
                        setattr(cfg, k, v)
                break

        # 2. Environment variables
        if os.getenv("CRYSPIKE_INTERVAL"):
            cfg.interval = int(os.getenv("CRYSPIKE_INTERVAL"))
        if os.getenv("CRYSPIKE_GPU_THRESHOLD"):
            cfg.gpu_threshold = float(os.getenv("CRYSPIKE_GPU_THRESHOLD"))
        if os.getenv("CRYSPIKE_CPU_IDLE"):
            cfg.cpu_idle = float(os.getenv("CRYSPIKE_CPU_IDLE"))
        if os.getenv("CRYSPIKE_WINDOW"):
            cfg.window = int(os.getenv("CRYSPIKE_WINDOW"))
        if os.getenv("CRYSPIKE_WEBHOOK"):
            cfg.webhook_url = os.getenv("CRYSPIKE_WEBHOOK")
        if os.getenv("CRYSPIKE_LOG_FILE"):
            cfg.log_file = os.getenv("CRYSPIKE_LOG_FILE")

        # 3. CLI overrides everything
        if cli_args is not None:
            if hasattr(cli_args, "interval") and cli_args.interval is not None:
                cfg.interval = cli_args.interval
            if hasattr(cli_args, "gpu_threshold") and cli_args.gpu_threshold is not None:
                cfg.gpu_threshold = cli_args.gpu_threshold
            if hasattr(cli_args, "cpu_idle") and cli_args.cpu_idle is not None:
                cfg.cpu_idle = cli_args.cpu_idle
            if hasattr(cli_args, "window") and cli_args.window is not None:
                cfg.window = cli_args.window
            if hasattr(cli_args, "gpu") and cli_args.gpu is not None:
                cfg.gpu = cli_args.gpu
            if hasattr(cli_args, "webhook") and cli_args.webhook:
                cfg.webhook_url = cli_args.webhook
            if hasattr(cli_args, "log_file") and cli_args.log_file:
                cfg.log_file = cli_args.log_file
            if hasattr(cli_args, "daemon") and cli_args.daemon:
                cfg.daemon = True

        return cfg
