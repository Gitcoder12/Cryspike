# Independent Model Audit Router — Cryspike

**Revision date:** 2026-11-13

## Data and evidence rules
- Never replace real or maintainer-provided data with invented, generated, synthetic or placeholder records.
- Trace sources, licences, collection dates and Git history before changing datasets.
- If provenance cannot be confirmed, preserve the original data and mark it unknown/unverified. Do not fabricate a substitute.
- Synthetic data belongs only in clearly labelled and isolated tests/examples.
- Do not invent people, official records, citations, metrics, benchmark scores, customers, deployments or endorsements.
- Tests pass only when successfully run against the exact reviewed commit.

## README rule
Preserve the last maintainer-authored README as recovered from Git history. Do not rewrite or replace it. Append AI-written information only as a dated, clearly labelled secondary addendum at the very bottom.

## Independent review roles
1. Data provenance and integrity.
2. Code, architecture, API and implementation correctness.
3. Security, privacy, dependency and trust-boundary review.
4. Build, tests, CI, benchmark and reproducibility review.
5. README history, licensing, attribution and link review.
6. Career/research claims and evidence review.

## Audit sequence
1. Record repository URL, default branch, exact HEAD SHA, fork status and PR head.
2. Classify changes as merged, open, closed-unmerged, reverted or unverified.
3. Inventory runtime datasets, fixtures, generated data, APIs and provenance.
4. Compare README against its pre-AI Git-history baseline.
5. Run install/build/lint/test/benchmark commands on the exact commit; inspect CI for suppressed failures.
6. Audit security, privacy, error handling, edge cases, performance and reproducibility.
7. Verify public claims, links and upstream attribution.
8. Publish evidence-based findings before making changes.

## Finding format
Severity (**P0/P1/P2/P3**), exact file/line/symbol, reproduction, expected vs actual behaviour, evidence and commit SHA, confirmed/suspected/unverifiable status, minimal fix, regression test, and any data/README impact.

## Merge gate
- [ ] No fabricated data presented as real or official.
- [ ] Real/user-provided data preserved; no silent substitution.
- [ ] Synthetic examples labelled and isolated.
- [ ] Original README preserved; AI addendum at bottom only.
- [ ] Exact-head tests/CI verified; failures disclosed.
- [ ] No secrets, private personal details, classified or confidential material.
- [ ] Licensing/upstream attribution preserved.
- [ ] Independent second review and maintainer approval recorded.

Repository: **Cryspike**. Do not infer features from name or roadmap. Do not merge, delete, force-push, overwrite data or alter original README during the audit. The repository owner has final approval.
