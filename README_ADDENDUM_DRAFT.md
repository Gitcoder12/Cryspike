# Cryspike — README Explanation Draft

## In plain language

A small monitor that looks for unusually high GPU use while the rest of the computer appears idle, then reports processes worth checking.

## How it works

The program samples GPU and CPU usage repeatedly. If a GPU stays highly active while CPU use remains low for the configured number of checks, it reports the processes using that GPU so a person can investigate.

## Technical explanation

Lightweight host-monitoring tool sampling GPU and CPU utilization over repeated intervals, with thresholds, exclusions, process listing and optional webhook notifications. High GPU use with low CPU is only a suspicious signal; games, rendering, video, ML workloads and drivers can create false positives. It does not prove cryptomining or malware.

Document supported telemetry backends, sampling period, thresholds, process attribution, multi-GPU handling, exclusions, event schema and webhook behavior.

## Limitations

This is a heuristic alert, not proof of a miner or compromise. Benign workloads and driver behavior may trigger alerts; missing telemetry must not be mistaken for an idle system.

## Contributing

See FEATURE_UPGRADE_PLAN.md and CONTRIBUTING.md.
