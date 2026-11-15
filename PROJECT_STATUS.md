# Project Status — Cryspike

**Snapshot date:** 2026-11-16  
**Status type:** Initial repository snapshot  
**Default branch:** main  
**Review completeness:** Partial — not a code audit or release certification

## Project purpose
Python GPU-monitoring heuristic intended to flag sustained high GPU utilization when system CPU utilization remains low and optionally report processes.

## Current maturity (README/upstream description; not independently verified)
Root contains cryspike package, pyproject.toml, requirements.txt, TOML example, SECURITY.md and README; README describes NVML/psutil-based multi-GPU monitoring, sliding windows, excludes, CLI and optional webhooks.

## Observed repository structure
cryspike/, pyproject.toml, requirements.txt, cryspike.toml.example, README.md, SECURITY.md and repository guidance.

## Known issues and risks to investigate
The GPU-high/CPU-idle condition is a heuristic, not proof of cryptomining or malware. It may miss miners that also use CPU and can flag benign GPU workloads under some conditions. Verify multi-GPU mapping, permissions, NVML error paths, process visibility and webhook secret handling. No hardware tests or unit tests run.

## Recommended next actions
Run unit tests and static checks; test threshold/window/reset behavior with deterministic fake telemetry; test multiple GPUs, driver absence and permission errors; measure false positives/negatives on benign rendering/ML and known miner workloads; phrase alerts as suspicious GPU activity, never confirmed malware.

## Verification record
| Check | Result |
|---|---|
| Default-branch top-level tree | Inspected |
| README | Inspected |
| Deep source review | Not performed |
| Tests / build / runtime | Not run |
| Security / dependency audit | Not run |
| Hardware / deployment checks | Not run |
| Independent review | Not performed |

## Change log
- 2026-11-16: Added this initial status snapshot on a review branch. No application code or existing data changed.

> Update this file only after the corresponding inspection or verification has actually been performed. Distinguish upstream capabilities, README claims, observed facts and unrun checks.