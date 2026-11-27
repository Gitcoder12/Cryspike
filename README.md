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


---

## AI-maintained project notes (secondary — 2026-11-13)

This section supplements the maintainer-authored README above; it does not replace or certify the original claims.

- The current source tree, live data sources and tests are the implementation source of truth. Planned work is not shipped functionality.
- Preserve original and user-provided data. Never silently substitute generated or placeholder records; label synthetic fixtures clearly.
- Record source URLs, licences, collection dates, geographic scope, units, update cadence and confidence for public-data claims.
- Verify execution, tests, links and public claims against the exact current commit before public use.
- See [MODEL_AUDIT_ROUTER.md](MODEL_AUDIT_ROUTER.md) for independent audit and data-integrity rules.


### Proposed hardening clarifications — open PR, not yet merged (2026-11-13)

[PR #1](https://github.com/Gitcoder12/Cryspike/pull/1) proposes stricter configuration validation, handling of missing/invalid sensor readings, more reliable process-exclusion semantics, HTTPS-only webhook checks, and expanded tests/CI. Its revised scope clarifies that high GPU use with low CPU is only a heuristic signal: it does not prove mining or malware, inspect GPU kernels/wallet/network activity, or remove malicious software. A detection should trigger independent process investigation, not an automatic malware verdict. Re-run CI on the exact latest PR head before considering it validated.

---

## Engineering Audit & Handover — 2026-11-17

**Reviewed commit:** `2abfe57eb013cb66f4d1c4ae033e745d97b0c2b6` (`main`). Static inspection covered detector, NVML adapter, and detector tests; tests were not executed.

### Confirmed findings
- Detection is a heuristic based on sustained high GPU utilization while total CPU utilization is low. The detector's own documentation correctly states that this is a suspicious signal, not proof of malware.
- The detector tests cover consecutive-window behavior, normal/busy CPU cases, missing GPU samples, and excluded-process handling. They do not establish real-world detection precision or recall.
- GPU process visibility depends on NVML/driver support and permissions; an empty or unavailable process list must not be interpreted as proof that no process is active.
- Exclusion matching uses substring patterns against process names, so overly broad exclusions can suppress relevant samples.

### Next actions
1. Evaluate on labelled benign workloads (games, rendering, AI inference, video encoding) and controlled mining samples; report false-positive/false-negative rates.
2. Display sensor availability and process-list limitations clearly in every alert.
3. Add tests for multi-GPU failures, permission-denied process lists, broad exclusions, and monitor lifecycle cleanup.

**Verification status:** static source/test inspection only; no GPU hardware run, full tests, or detection benchmark was performed.

---

## Examples Used
- Detecting sustained high GPU utilization while CPU utilization stays low
- Comparing normal GPU workloads with suspicious utilization patterns
- Alerting on repeated suspicious readings without declaring malware

---

## Repository navigation

[Alphabetical file index](FILE_INDEX.md)
