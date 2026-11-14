# AI Worklog — Cryspike

**Audit date:** 2026-11-14  
**Repository:** https://github.com/Gitcoder12/Cryspike  
**Default branch:** `main`  
**Review branch:** `docs/portfolio-operating-kit-2026-11-13`  
**Related draft PRs:** https://github.com/Gitcoder12/Cryspike/pull/1 and https://github.com/Gitcoder12/Cryspike/pull/2

## Purpose and maturity

Python package that samples NVIDIA GPU utilization and system CPU utilization, applies a consecutive-sample heuristic, and reports processes for human investigation. It is not malware proof or an antivirus.

## Verified implementation

- Package: `cryspike/` with CLI, config, detector, NVML monitor and alert delivery.
- Packaging metadata: `pyproject.toml`; console entry point `cryspike`.
- Test module on main: `cryspike/tests/test_detector.py`.
- Main branch has no CI workflow. Open PR #1 proposes a broader CI matrix and substantial hardening; PR #2 is the documentation/operating-kit draft.

## Findings

- **P1 — Python 3.9/3.10 TOML support:** `pyproject.toml` declares Python >=3.9. `cryspike/config.py` falls back to `tomli` when `tomllib` is unavailable, but `tomli` is not declared in main-branch dependencies. TOML configuration can therefore be silently unavailable on supported Python 3.9/3.10 installations.
- **P2 — Configuration validation:** main-branch `from_sources` assigns TOML/environment values with limited type/range validation; invalid interval, threshold, window or GPU values may reach runtime.
- **P2 — Hardware dependency:** actual NVML behavior depends on NVIDIA drivers and device availability; current tests on main do not establish behavior across supported OS/driver combinations.
- **P2 — Evaluation:** high GPU utilization with low CPU utilization is a heuristic and can flag legitimate rendering, gaming, video or ML workloads. README should preserve this limitation.

## Verification

- Default-branch tree, `pyproject.toml`, `config.py` and `monitor.py` inspected.
- Main-branch CI: no workflow available.
- Local tests/build: NOT RUN.
- Not run: physical NVIDIA hardware, driver matrix, webhook integration, packaging build, Python 3.9/3.10 TOML configuration.
- PR #1 is an unmerged proposed hardening change; its exact latest head requires separate CI/review verification.

## Next actions

1. Review PR #1's config validation and Python 3.9/3.10 dependency changes against exact current head.
2. Ensure missing or invalid NVML readings cannot be mistaken for healthy measurements.
3. Test configuration precedence, types, bounds and invalid TOML.
4. Keep webhook payloads bounded, HTTPS-only and explicit about data leaving the host.
5. Measure false positives on labelled benign workloads; never call a heuristic alert proof of malware.

## Status

Assessed: yes. Changed: AI worklog only. Tests run locally: no. CI: not available on main. Independent external-model review: NOT PERFORMED. Merged: no.
