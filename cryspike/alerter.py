"""Alert delivery: console + optional webhook (Discord / Slack / generic)."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

try:
    import urllib.request
except ImportError:
    urllib = None  # type: ignore

logger = logging.getLogger(__name__)


def send_webhook(url: str, payload: Dict[str, Any]) -> bool:
    """POST JSON payload to a webhook URL. Returns True on success."""
    if not url:
        return False
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json", "User-Agent": "Cryspike/0.2"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return 200 <= resp.status < 300
    except Exception as e:
        logger.error(f"Webhook failed: {e}")
        return False


def format_discord_embed(gpu_idx: int, gpu_util: float, processes: List[Dict]) -> Dict:
    """Build a Discord-compatible embed payload."""
    proc_text = "\n".join(
        f"`{p['pid']}` {p['name']} ({p['used_memory_mb']} MB)" for p in processes
    ) or "_No processes reported_"

    return {
        "embeds": [{
            "title": "⚠️ Cryspike Alert – Suspicious GPU Activity",
            "color": 16711680,  # red
            "fields": [
                {"name": "GPU", "value": str(gpu_idx), "inline": True},
                {"name": "Utilization", "value": f"{gpu_util:.1f}%", "inline": True},
                {"name": "Processes", "value": proc_text, "inline": False},
            ],
            "footer": {"text": "Cryspike – silent miner detector"},
        }]
    }


def alert(
    gpu_idx: int,
    gpu_util: float,
    processes: List[Dict],
    webhook_url: Optional[str] = None,
) -> None:
    """Print console alert and optionally fire webhook."""
    print("\n" + "=" * 70)
    print("⚠️  ALERT: SUSTAINED SUSPICIOUS GPU ACTIVITY DETECTED ⚠️")
    print(f"GPU {gpu_idx}  |  Utilization: {gpu_util:.1f}%")
    print("-" * 70)
    if processes:
        print("Processes using this GPU:")
        for p in processes:
            print(f"  PID {p['pid']:6d}  {p['name']:<30}  {p['used_memory_mb']} MB")
    else:
        print("  (No compute processes reported by NVML)")
    print("=" * 70 + "\n")

    if webhook_url:
        payload = format_discord_embed(gpu_idx, gpu_util, processes)
        ok = send_webhook(webhook_url, payload)
        if ok:
            logger.info("Webhook notification sent.")
        else:
            logger.warning("Webhook notification failed.")
