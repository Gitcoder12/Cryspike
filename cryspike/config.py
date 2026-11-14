"""Configuration loading and validation for Cryspike."""

from __future__ import annotations

import math
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Optional
from urllib.parse import urlsplit

try:
    import tomllib
except ImportError:  # Python 3.9 and 3.10
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ImportError:  # pragma: no cover - dependency is declared for older Python
        tomllib = None  # type: ignore[assignment]


class CryspikeConfigError(ValueError):
    """Raised when a configuration source contains invalid values."""


@dataclass
class CryspikeConfig:
    interval: int = 5
    gpu_threshold: float = 80.0
    cpu_idle: float = 10.0
    window: int = 5
    gpu: int = -1
    exclude_processes: List[str] = field(default_factory=list)
    webhook_url: Optional[str] = None
    log_file: Optional[str] = None
    daemon: bool = False

    _KEYS = frozenset({
        "interval", "gpu_threshold", "cpu_idle", "window", "gpu",
        "exclude_processes", "webhook_url", "log_file", "daemon",
    })

    @classmethod
    def from_sources(cls, cli_args: Any = None) -> "CryspikeConfig":
        """Load defaults, then TOML, environment variables, and CLI overrides."""
        cfg = cls()
        candidates = (
            Path("cryspike.toml"),
            Path.home() / ".config" / "cryspike" / "config.toml",
            Path.home() / ".cryspike.toml",
        )
        for candidate in candidates:
            if candidate.exists():
                if tomllib is None:
                    raise CryspikeConfigError(
                        "TOML configuration requires tomli on Python 3.9/3.10."
                    )
                try:
                    with candidate.open("rb") as stream:
                        data = tomllib.load(stream)
                except (OSError, ValueError) as exc:
                    raise CryspikeConfigError(
                        f"Could not read configuration file {candidate}: {exc}"
                    ) from exc
                if not isinstance(data, dict):
                    raise CryspikeConfigError(
                        f"Configuration file {candidate} must contain a TOML table."
                    )
                cls._apply_mapping(cfg, data, str(candidate))
                break

        env_values = {
            "interval": ("CRYSPIKE_INTERVAL", int),
            "gpu_threshold": ("CRYSPIKE_GPU_THRESHOLD", float),
            "cpu_idle": ("CRYSPIKE_CPU_IDLE", float),
            "window": ("CRYSPIKE_WINDOW", int),
            "gpu": ("CRYSPIKE_GPU", int),
        }
        for field_name, (env_name, converter) in env_values.items():
            raw = os.getenv(env_name)
            if raw is not None and raw.strip():
                try:
                    setattr(cfg, field_name, converter(raw))
                except ValueError as exc:
                    raise CryspikeConfigError(
                        f"{env_name} must be a valid {converter.__name__}."
                    ) from exc

        if os.getenv("CRYSPIKE_WEBHOOK") is not None:
            raw_webhook = os.environ["CRYSPIKE_WEBHOOK"].strip()
            cfg.webhook_url = raw_webhook or None
        if os.getenv("CRYSPIKE_LOG_FILE") is not None:
            raw_log = os.environ["CRYSPIKE_LOG_FILE"].strip()
            cfg.log_file = raw_log or None
        if os.getenv("CRYSPIKE_EXCLUDE_PROCESSES") is not None:
            cfg.exclude_processes = [
                item.strip()
                for item in os.environ["CRYSPIKE_EXCLUDE_PROCESSES"].split(",")
                if item.strip()
            ]
        if os.getenv("CRYSPIKE_DAEMON") is not None:
            cfg.daemon = cls._parse_bool(
                os.environ["CRYSPIKE_DAEMON"], "CRYSPIKE_DAEMON"
            )

        if cli_args is not None:
            for field_name in (
                "interval", "gpu_threshold", "cpu_idle", "window", "gpu"
            ):
                value = getattr(cli_args, field_name, None)
                if value is not None:
                    setattr(cfg, field_name, value)
            webhook = getattr(cli_args, "webhook", None)
            if webhook:
                cfg.webhook_url = webhook
            log_file = getattr(cli_args, "log_file", None)
            if log_file:
                cfg.log_file = log_file
            excludes = getattr(cli_args, "exclude_process", None)
            if excludes is not None:
                cfg.exclude_processes = list(excludes)
            daemon = getattr(cli_args, "daemon", None)
            if daemon is not None:
                cfg.daemon = bool(daemon)

        cfg.validate()
        return cfg

    @classmethod
    def _apply_mapping(
        cls, cfg: "CryspikeConfig", values: dict, source: str
    ) -> None:
        unknown = sorted(set(values) - cls._KEYS)
        if unknown:
            raise CryspikeConfigError(
                f"Unknown option(s) in {source}: {', '.join(unknown)}"
            )
        for key, value in values.items():
            setattr(cfg, key, value)

    @staticmethod
    def _parse_bool(value: str, source: str) -> bool:
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
        raise CryspikeConfigError(
            f"{source} must be one of true/false, yes/no, on/off, or 1/0."
        )

    def validate(self) -> None:
        """Reject values that could cause invalid monitoring or silent misbehavior."""
        if isinstance(self.interval, bool) or not isinstance(self.interval, int):
            raise CryspikeConfigError("interval must be an integer of at least 1 second.")
        if self.interval < 1:
            raise CryspikeConfigError("interval must be at least 1 second.")

        for name, value in (
            ("gpu_threshold", self.gpu_threshold),
            ("cpu_idle", self.cpu_idle),
        ):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise CryspikeConfigError(f"{name} must be a number from 0 to 100.")
            if not math.isfinite(float(value)) or not 0 <= value <= 100:
                raise CryspikeConfigError(f"{name} must be a number from 0 to 100.")

        if isinstance(self.window, bool) or not isinstance(self.window, int):
            raise CryspikeConfigError("window must be a positive integer.")
        if self.window < 1:
            raise CryspikeConfigError("window must be at least 1.")

        if isinstance(self.gpu, bool) or not isinstance(self.gpu, int) or self.gpu < -1:
            raise CryspikeConfigError("gpu must be -1 (all GPUs) or a non-negative index.")

        if not isinstance(self.exclude_processes, list) or any(
            not isinstance(item, str) or not item.strip()
            for item in self.exclude_processes
        ):
            raise CryspikeConfigError("exclude_processes must be a list of non-empty names.")
        self.exclude_processes = [item.strip() for item in self.exclude_processes]

        if self.webhook_url is not None:
            if not isinstance(self.webhook_url, str):
                raise CryspikeConfigError("webhook_url must be a URL string.")
            parsed = urlsplit(self.webhook_url)
            try:
                _ = parsed.port
            except ValueError as exc:
                raise CryspikeConfigError("webhook_url contains an invalid port.") from exc
            if (
                parsed.scheme != "https"
                or not parsed.hostname
                or parsed.username is not None
                or parsed.password is not None
            ):
                raise CryspikeConfigError("webhook_url must be a valid HTTPS URL.")

        if self.log_file is not None:
            if not isinstance(self.log_file, str) or not self.log_file.strip():
                raise CryspikeConfigError("log_file must be a non-empty path or omitted.")
            self.log_file = self.log_file.strip()

        if not isinstance(self.daemon, bool):
            raise CryspikeConfigError("daemon must be a boolean.")
