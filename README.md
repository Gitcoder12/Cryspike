# Cryspike

**Detect silent crypto miners** by watching for sustained high GPU utilization while the system CPU is idle.

Cryspike is a lightweight tool that samples GPU load + system CPU load. When the GPU stays hot while the machine is idle, it raises an alert and lists the processes using that GPU.

## Why it works

Cryptocurrency miners keep the GPU at high load even when you are not interacting with the machine.  
Cryspike treats a reading as *suspicious* only when:

- GPU utilization ≥ threshold **and**
- System CPU utilization ≤ idle threshold

for a configurable number of consecutive checks. This dramatically reduces false positives from games, rendering, or video encoding.

## Features (v0.3)

- Multi-GPU support
- Process listing on alert (PID, name, GPU memory)
- Configurable exclude list for known-good processes
- Optional Discord / Slack webhook notifications
- TOML config file + environment variables + CLI
- Log to file
- Daemon-friendly mode
- Clean sliding-window detector with reset after alert

## Requirements

- NVIDIA GPU + drivers
- Python ≥ 3.9
- `nvidia-ml-py` and `psutil`

## Install

```bash
git clone https://github.com/Gitcoder12/Cryspike.git
cd Cryspike
pip install -e .
```

## Quick start

```bash
# Monitor all GPUs with defaults
cryspike

# Tighter thresholds + webhook
cryspike --gpu-threshold 70 --window 4 --webhook "https://discord.com/api/webhooks/..."

# Only GPU 0, log to file
cryspike --gpu 0 --log-file /tmp/cryspike.log
```

## Configuration priority

1. CLI flags (highest)
2. Environment variables (`CRYSPIKE_INTERVAL`, `CRYSPIKE_WEBHOOK`, …)
3. TOML file (`cryspike.toml` or `~/.config/cryspike/config.toml`)

See `cryspike.toml.example` for all options.

## CLI reference

| Flag | Default | Description |
|------|---------|-------------|
| `--interval` | 5 | Seconds between checks |
| `--gpu-threshold` | 80 | GPU % considered high |
| `--cpu-idle` | 10 | CPU % considered idle |
| `--window` | 5 | Consecutive suspicious readings required |
| `--gpu` | -1 | GPU index (`-1` = all) |
| `--webhook` | — | Discord/Slack webhook URL |
| `--log-file` | — | Also write logs to this path |
| `--daemon` | false | Quieter output |

## How the detector works

1. Every `interval` seconds → read GPU util (NVML) + CPU util (psutil)
2. Reading is suspicious only if GPU high **and** CPU idle
3. After `window` consecutive suspicious readings → alert + list processes
4. Detector for that GPU is reset (requires a fresh full window for next alert)

## Project structure

```
cryspike/
├── __init__.py
├── cli.py          # entry point
├── monitor.py      # NVML wrapper (multi-GPU + process list)
├── detector.py     # sliding-window logic
├── config.py       # TOML / env / CLI loader
├── alerter.py      # console + webhook delivery
└── tests/
    └── test_detector.py
```

## License

MIT

---

**Author**: Dharavath Satvik ([@Gitcoder12](https://github.com/Gitcoder12))
