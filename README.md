# Cryspike

Cryspike is a small Python tool that flags **sustained high NVIDIA GPU utilization while overall CPU utilization stays low**. This pattern can be associated with hidden cryptocurrency mining, but it is only a heuristic signal — it does not prove that a process is malicious or remove malware.

## How it works

1. Read NVIDIA GPU utilization through NVML and total CPU utilization through psutil.
2. Mark a sample as suspicious when GPU utilization is at or above the configured threshold and CPU utilization is at or below the idle threshold.
3. Require a configurable number of consecutive suspicious samples.
4. Report GPU processes when an alert is raised; optionally send a webhook notification.

A missing or invalid sensor reading resets the consecutive-sample window. When an exclusion list is configured, a sample is ignored only when NVML reports at least one GPU process and every reported process name matches an exclusion. An empty or unavailable process list does not suppress alerts.

## Features

- Monitor one NVIDIA GPU or all detected NVIDIA GPUs.
- Consecutive-sample detection with reset after a normal or missing sample.
- Report compute and graphics processes exposed by NVML.
- Optional process-name exclusions.
- TOML configuration, environment variables, and CLI overrides.
- Optional HTTPS webhook notifications for Discord, Slack, or compatible endpoints.
- Console or file-only logging through daemon mode.
- Offline unit tests and GitHub Actions CI.

## Requirements

- Python 3.9 or newer.
- An NVIDIA GPU with a working NVIDIA driver and NVML access.
- Internet access only when installing the package or sending webhook notifications.

Cryspike depends on nvidia-ml-py and psutil. On systems without a supported NVIDIA GPU/driver, monitoring cannot start. It does not currently monitor AMD or Intel GPUs.

## Install

    git clone https://github.com/Gitcoder12/Cryspike.git
    cd Cryspike
    python -m pip install .

For development:

    python -m pip install -e ".[dev]"
    pytest

## Quick start

    # Monitor all detected NVIDIA GPUs
    cryspike

    # Monitor GPU 0 with stricter thresholds
    cryspike --gpu 0 --gpu-threshold 70 --cpu-idle 8 --window 4

    # Send alerts to a Discord or Slack incoming webhook
    cryspike --webhook "https://your-webhook-url"

    # Write logs to a file and suppress console output
    cryspike --daemon --log-file ./cryspike.log

    # Show the installed version
    cryspike --version

## Configuration

Cryspike searches for the first configuration file found in this order:

1. ./cryspike.toml
2. ~/.config/cryspike/config.toml
3. ~/.cryspike.toml

Start with cryspike.toml.example and copy it to one of those paths.

Configuration priority, from highest to lowest:

1. CLI arguments.
2. Environment variables.
3. TOML file.
4. Built-in defaults.

### TOML options

| Option | Default | Meaning |
|---|---:|---|
| interval | 5 | Seconds between samples; must be at least 1 |
| gpu_threshold | 80.0 | GPU utilization threshold, from 0 to 100 |
| cpu_idle | 10.0 | CPU utilization threshold, from 0 to 100 |
| window | 5 | Consecutive suspicious samples required |
| gpu | -1 | -1 monitors all GPUs; otherwise a zero-based GPU index |
| exclude_processes | [] | Optional case-insensitive partial process-name matches |
| webhook_url | unset | Optional HTTPS webhook URL |
| log_file | unset | Optional log file path |
| daemon | false | Suppress console output; use log_file to retain logs |

### Environment variables

- CRYSPIKE_INTERVAL
- CRYSPIKE_GPU_THRESHOLD
- CRYSPIKE_CPU_IDLE
- CRYSPIKE_WINDOW
- CRYSPIKE_GPU
- CRYSPIKE_EXCLUDE_PROCESSES (comma-separated process-name fragments)
- CRYSPIKE_WEBHOOK
- CRYSPIKE_LOG_FILE
- CRYSPIKE_DAEMON (true/false, yes/no, on/off, or 1/0)

### CLI options

| Option | Meaning |
|---|---|
| --interval SECONDS | Seconds between samples |
| --gpu-threshold PERCENT | High GPU utilization threshold |
| --cpu-idle PERCENT | CPU idle threshold |
| --window COUNT | Consecutive suspicious samples required |
| --gpu INDEX | GPU index; -1 monitors all GPUs |
| --exclude-process NAME | Add an excluded process-name fragment; repeat the option |
| --webhook URL | HTTPS incoming webhook URL |
| --log-file PATH | Write logs to a file |
| --daemon | Suppress console output |
| --version | Print the installed version |

Invalid thresholds, non-positive intervals/windows, malformed webhooks, unknown TOML keys, and out-of-range GPU indexes are rejected rather than silently accepted.

## Important limitations

- Cryspike uses aggregate GPU and CPU utilization. It does not inspect GPU kernels, wallet activity, network traffic, executable reputation, or cryptomining signatures.
- High GPU usage can be legitimate (for example, rendering, gaming, or compute workloads); low CPU usage does not uniquely identify mining.
- Process visibility depends on NVIDIA driver permissions and NVML support. If NVML cannot report processes, exclusions do not suppress an alert.
- A detection is an investigation lead, not a malware verdict. Review the listed process and verify it independently before taking action.
- Webhook URLs are credentials. Keep them out of source control and logs. Only HTTPS webhook URLs are accepted.

## Project structure

    cryspike/
    ├── __init__.py
    ├── alerter.py
    ├── cli.py
    ├── config.py
    ├── detector.py
    ├── monitor.py
    └── tests/
        ├── test_alerter.py
        ├── test_config.py
        ├── test_detector.py
        └── test_monitor.py

## License

MIT

**Author:** Dharavath Satvik ([@Gitcoder12](https://github.com/Gitcoder12))
