# Security policy

## Scope

Cryspike is a heuristic monitoring utility. It reports suspicious GPU/CPU utilization patterns and may send alert details to a webhook. It is not an antivirus product, does not terminate processes, and does not guarantee detection of cryptocurrency miners.

## Reporting a vulnerability

Please do not publish exploitable details in a public issue. Contact the repository maintainer through the private contact options on the GitHub profile and include:

- A description of the issue and its potential impact.
- The affected Cryspike version and operating system.
- Minimal reproduction steps or a proof of concept, where safe.

Do not include live webhook URLs, access tokens, private process data, or other secrets in reports.

## Safe use

- Treat webhook URLs as credentials and keep them out of source control.
- Use HTTPS webhook endpoints only.
- Review process details before taking action; Cryspike does not determine whether a process is malicious.
