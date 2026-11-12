"""Console and HTTPS webhook alert delivery for Cryspike."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)


def _safe_process_text(processes: List[Dict[str, Any]]) -> str:
    if not processes:
        return "No GPU processes were reported by NVML."
    lines = []
    for process in processes:
        name = str(process.get("name", "unknown")).replace(chr(96), "'")
        lines.append(
            f"PID {process.get('pid', '?')} | {name} | "
            f"{process.get('used_memory_mb', 0)} MB"
        )
    return "\n".join(lines)


def format_discord_embed(
    gpu_idx: int, gpu_util: float, processes: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Build a Discord webhook payload within Discord's field-size limit."""
    process_text = _safe_process_text(processes)
    if len(process_text) > 1000:
        process_text = process_text[:997] + "..."

    return {
        "embeds": [{
            "title": "Cryspike: suspicious GPU activity",
            "color": 16733525,
            "fields": [
                {"name": "GPU", "value": str(gpu_idx), "inline": True},
                {"name": "Utilization", "value": f"{gpu_util:.1f}%", "inline": True},
                {"name": "Processes", "value": process_text, "inline": False},
            ],
            "footer": {"text": "Cryspike heuristic alert"},
        }]
    }


def format_text_message(
    gpu_idx: int, gpu_util: float, processes: List[Dict[str, Any]]
) -> Dict[str, str]:
    """Build a Slack-compatible and generic incoming-webhook payload."""
    message = (
        f"Cryspike alert: suspicious GPU activity\n"
        f"GPU: {gpu_idx} | Utilization: {gpu_util:.1f}%\n"
        f"{_safe_process_text(processes)}"
    )
    return {"text": message[:3500]}


def _payload_for_url(
    url: str, gpu_idx: int, gpu_util: float, processes: List[Dict[str, Any]]
) -> Dict[str, Any]:
    hostname = (urlsplit(url).hostname or "").lower()
    if hostname in {"discord.com", "discordapp.com"}:
        return format_discord_embed(gpu_idx, gpu_util, processes)
    return format_text_message(gpu_idx, gpu_util, processes)


def send_webhook(url: str, payload: Dict[str, Any]) -> bool:
    """Send JSON to an HTTPS webhook; never log the URL because it may contain a token."""
    parsed = urlsplit(url)
    try:
        _ = parsed.port
    except ValueError:
        logger.error("Webhook URL has an invalid port.")
        return False
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
    ):
        logger.error("Webhook URL must use HTTPS and include a valid host.")
        return False

    try:
        data = json.dumps(payload).encode("utf-8")
        request = Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Cryspike/0.4",
            },
            method="POST",
        )
        with urlopen(request, timeout=10) as response:
            return 200 <= response.status < 300
    except Exception as exc:  # network errors and serialization errors are non-fatal
        logger.error("Webhook delivery failed (%s).", type(exc).__name__)
        return False


def alert(
    gpu_idx: int,
    gpu_util: float,
    processes: List[Dict[str, Any]],
    webhook_url: Optional[str] = None,
    quiet: bool = False,
) -> None:
    """Emit an alert locally and optionally send it to a webhook."""
    heading = "CRYSPIKE ALERT: SUSPICIOUS GPU ACTIVITY"
    details = (
        f"GPU {gpu_idx} | Utilization {gpu_util:.1f}%\n"
        f"{_safe_process_text(processes)}"
    )

    if quiet:
        logger.warning("%s | %s", heading, details.replace("\n", " | "))
    else:
        print("\n" + "=" * 64)
        print(heading)
        print(details)
        print("=" * 64 + "\n")

    if webhook_url:
        payload = _payload_for_url(webhook_url, gpu_idx, gpu_util, processes)
        if send_webhook(webhook_url, payload):
            logger.info("Webhook notification sent.")
        else:
            logger.warning("Webhook notification was not delivered.")
