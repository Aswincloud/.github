# Security Policy

Thanks for helping keep the **Aswincloud** organization and its users safe.

## Reporting a vulnerability

**Please do not open a public issue for security problems.** Public issues are visible to everyone and can put users at risk before a fix is available.

Instead, report privately through one of these channels:

1. **GitHub private vulnerability reporting** *(preferred)* — on the affected repository, go to the **Security** tab → **Report a vulnerability**. This opens a private advisory visible only to maintainers.
2. **Email** — [security@aswincloud.com](mailto:security@aswincloud.com) (or [aswin@aswincloud.com](mailto:aswin@aswincloud.com)).

When reporting, please include:

- The repository and, if possible, the affected version, commit, or URL.
- A description of the issue and its potential impact.
- Steps to reproduce, a proof of concept, or a code snippet.
- Any suggested remediation, if you have one.

## What to expect

- **Acknowledgement** within **3 business days**.
- An initial assessment and severity triage within **7 business days**.
- Coordinated disclosure: we'll work with you on a fix and a disclosure timeline, and credit you (if you wish) once the issue is resolved.

## Scope

This policy covers all repositories in the [Aswincloud](https://github.com/Aswincloud) organization unless a repository states otherwise in its own `SECURITY.md`.

## Exposed secrets / credentials

If you've found a **leaked secret** (API key, token, password) in one of our repositories:

- Report it privately using the channels above — please **do not** post the secret in a public issue.
- We rotate the credential at its source first, then confirm it is dead, then mark the finding resolved. A GitHub secret-scanning alert marked "revoked" does **not** by itself invalidate a live credential.

## Our safeguards

All repositories in this organization have **secret scanning** and **push protection** enabled, **Dependabot alerts** on, and require **2FA** for members. Secrets belong in environment variables or GitHub Actions secrets — never committed to source.

## Safe harbor

We consider security research conducted in good faith — accessing only your own accounts/data, avoiding privacy violations, service disruption, and data destruction — to be authorized. We will not pursue legal action against researchers who follow this policy. If in doubt, ask first.

## A note on unsolicited "security alert" emails

We receive unsolicited emails claiming to have found vulnerabilities, sometimes with donation links. We appreciate genuine reports, but we validate every claim independently and never send payment in response to unsolicited outreach. Please use the private channels above so we can verify and act on your report properly.
