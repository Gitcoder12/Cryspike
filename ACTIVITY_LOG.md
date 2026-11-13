# Cryspike — Activity Log

**Snapshot:** 2026-11-13

## Verified history

No portfolio source-edit PR or issue was recorded in this pass. README describes GPU/CPU utilization monitoring, process listing, exclusions and optional webhook notifications.

## Current scope and limitations

Lightweight host-monitoring tool sampling GPU and CPU utilization over repeated intervals, with thresholds, exclusions, process listing and optional webhook notifications. High GPU use with low CPU is only a suspicious signal; games, rendering, video, ML workloads and drivers can create false positives. It does not prove cryptomining or malware.

## Append-only record

| Date | Contributor / agent | Issue / PR | Device/driver/config | Validation | Result | Evidence / false-positive notes |
|---|---|---|---|---|---|---|
| YYYY-MM-DD | name | link | GPU, OS, driver, thresholds | exact command and workload | pass / fail / not run | evidence |

Record telemetry provider, driver version, sample interval, thresholds, exclusion list and observed false positives. Never label an alert as confirmed malware without investigation.
