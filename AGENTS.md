# Agent Instructions — Cryspike

Read README.md, CONTRIBUTING.md and FEATURE_UPGRADE_PLAN.md before editing.

- Treat high GPU utilization as a heuristic signal, never proof of mining or malware.
- Validate telemetry provider output and explicitly handle unavailable values.
- Test benign high-GPU workloads, multiple GPUs, exclusions and threshold windows.
- Do not terminate processes or modify hosts automatically.
- Document webhook payload and obtain explicit operator configuration before sending data externally.
- Work on a branch, run checks and open a PR; do not merge/deploy autonomously.
