# Cryspike

**Detect silent crypto miners** by watching for sustained high GPU utilization while the system CPU is idle.

## Why it works

Cryptocurrency miners keep the GPU at high load even when you are not using the machine.  
Cryspike samples GPU utilization (via NVIDIA NVML) + system CPU load (via psutil).  
If the GPU stays hot while the CPU is idle for several consecutive checks, it raises an alert and lists the processes using that GPU.

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

## Usage

```bash
# Default: monitor all GPUs, check every 5 s
cryspike

# Custom thresholds
cryspike --gpu-threshold 70 --cpu-idle 15 --window 8 --interval 3

# Monitor only GPU 0
cryspike --gpu 0
```

## CLI Options

| Flag | Default | Description |
|------|---------|-------------|
| `--interval` | 5 | Seconds between checks |
| `--gpu-threshold` | 80 | GPU % considered high |
| `--cpu-idle` | 10 | CPU % considered idle |
| `--window` | 5 | Consecutive suspicious readings required |
| `--gpu` | -1 | GPU index (-1 = all) |

## How the detector works

1. Every `interval` seconds the tool reads GPU utilization (NVML) and CPU utilization (psutil).
2. A reading is *suspicious* when GPU ≥ threshold **and** CPU ≤ idle threshold.
3. After `window` consecutive suspicious readings an alert is fired and the processes on that GPU are listed.
4. The window is then reset so a new sustained pattern is required for the next alert.

## Project structure

```
cryspike/
├── __init__.py
├── cli.py          # entry point
├── monitor.py      # NVML wrapper (multi-GPU + process listing)
├── detector.py     # sliding-window logic
└── tests/
    └── test_detector.py
```

## License

MIT

---

**Author**: Dharavath Satvik ([@Gitcoder12](https://github.com/Gitcoder12))
