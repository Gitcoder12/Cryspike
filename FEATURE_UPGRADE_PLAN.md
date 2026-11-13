# Cryspike — Feature Upgrade Plan

## Objective

A small monitor that looks for unusually high GPU use while the rest of the computer appears idle, then reports processes worth checking.

## P0 — telemetry and correctness

- [ ] Document supported GPU telemetry providers/drivers and behavior when metrics are unavailable.
- [ ] Test threshold windows, consecutive-sample logic, exclusions, multiple GPUs and false-positive cases.

## P1 — explainable alerts

- [ ] Add structured event output with sampled values, process metadata and rule rationale.
- [ ] Make webhook delivery bounded, retry-safe and explicit about what data leaves the host.

## P2 — evaluation and packaging

- [ ] Evaluate detection precision/recall using labelled normal workloads and safe synthetic miner-like traces.
- [ ] Add packaging/service lifecycle checks only after platform support is documented.

## Contributor work packages

1. Telemetry-provider adapters and unavailable-state behavior.
2. Threshold/consecutive-sample test matrix.
3. Alert schema, process listing and webhook controls.
4. Safe labelled workload evaluation.

## Definition of done

- [ ] Unsupported telemetry is explicit rather than silently treated as zero.
- [ ] Alerts include evidence and configurable threshold context.
- [ ] False positives and benign high-GPU workloads are tested.
- [ ] Webhook payload and data sent off-device are documented.
