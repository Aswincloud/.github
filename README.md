# Aswincloud

Welcome to **Aswincloud** – an organization focused on developer tooling, performance profiling, and modern web applications.

## 🗂️ Public Repositories

<!-- REPOS_START -->
| Repository | Description | Language | ⭐ | Updated |
|------------|-------------|----------|:--:|:-------:|
| [ttperf](https://github.com/Aswincloud/ttperf) | A streamlined CLI tool for profiling Tenstorrent's TT-Metal tests and extracting device kernel performance metrics | Python | 3 | 2026-07-27 |
| [ttnn-performance-dashboard](https://github.com/Aswincloud/ttnn-performance-dashboard) | Day-by-day performance tracking dashboard for Tenstorrent TT-Metal TTNN eltwise operations. | JavaScript | 1 | 2026-08-01 |
| [portfolio](https://github.com/Aswincloud/portfolio) | Professional portfolio website built with React, Vite, and Tailwind CSS | JavaScript | 1 | 2026-08-02 |
| [whatsapp_bot](https://github.com/Aswincloud/whatsapp_bot) | WhatsApp AI assistant bot powered by Claude — conversational AI for everyday use | Python | 0 | 2026-07-27 |
| [3d_printing](https://github.com/Aswincloud/3d_printing) | 3D print portfolio and showcase site — custom figurines, decor, and art pieces. Orders via DM | HTML | 0 | 2026-08-01 |
| [AiBuddy](https://github.com/Aswincloud/AiBuddy) | AI-powered chatbot for Microsoft Teams — brings conversational AI into team channels and group chats | Python | 0 | 2026-07-27 |
| [auth](https://github.com/Aswincloud/auth) | Shared, framework-agnostic auth primitives for Cloudflare Workers sites — signed sessions, HMAC tokens, PBKDF2 passwords, owner allowlists, OAuth — plus an optional React login UI. Published as @aswincloud/auth. | TypeScript | 0 | 2026-07-27 |
| [blog](https://github.com/Aswincloud/blog) | blog.aswincloud.com - homelab & home automation | CSS | 0 | 2026-07-31 |
| [chat](https://github.com/Aswincloud/chat) | Full-viewport iframe wrapper hosting the self-hosted Chatwoot widget at chat.aswincloud.com | HTML | 0 | 2026-07-27 |
| [cheap-domain](https://github.com/Aswincloud/cheap-domain) *(archived)* | Get a custom subdomain under aswincloud.com for just ₹20/month | – | 0 | 2026-07-25 |
| [gh-org-guard](https://github.com/Aswincloud/gh-org-guard) | Self-healing GitHub org governance: reconcile branch protection, merge queue, reviews & secret-hygiene across every repo — one weekly workflow. Reference implementation. | Python | 1 | 2026-07-27 |
| [ghadiff](https://github.com/Aswincloud/ghadiff) | Python CLI to compare two GitHub Actions workflow runs — timing, status, and job/step-level diffs with text, JSON, Markdown, and HTML output | Python | 0 | 2026-07-27 |
| [invoicer](https://github.com/Aswincloud/invoicer) | Create, preview, download and email professional invoices. Cloudflare Pages + Functions + D1. | JavaScript | 0 | 2026-07-30 |
| [pr-review-checker](https://github.com/Aswincloud/pr-review-checker) | Web app that analyzes GitHub PRs against CODEOWNERS to compute minimum required approvals, with AI-powered approval predictions from team history | JavaScript | 1 | 2026-07-27 |
| [resume](https://github.com/Aswincloud/resume) | Aswin — Software Engineer. Resume built from HTML/CSS, auto-rendered to PDF. | HTML | 0 | 2026-08-01 |
| [shiptrack](https://github.com/Aswincloud/shiptrack) | Free, open-source, self-hostable shipment tracking for Indian & international couriers — built with Next.js + TypeScript | TypeScript | 1 | 2026-07-27 |
| [slack-join](https://github.com/Aswincloud/slack-join) *(archived)* | – | JavaScript | 0 | 2025-07-15 |
| [status-page](https://github.com/Aswincloud/status-page) | 🟢 Self-hosted, BetterStack-style live status page for a home network — Cloudflare Worker + D1 + a Docker prober, with email & Slack alerts. Runs on the free tier. | TypeScript | 0 | 2026-07-27 |
| [tg-torrent](https://github.com/Aswincloud/tg-torrent) | Telegram bot to remotely add torrents to qBittorrent via magnet links or .torrent files | Python | 0 | 2026-07-05 |
| [ttnn-ops-coverage](https://github.com/Aswincloud/ttnn-ops-coverage) | Interactive zero-dependency dashboard for the TTNN (Tenstorrent) op test matrix — every op across dtype × layout × memory, with per-config PCC/ULP accuracy and run-to-run diffs. Deploys to Cloudflare Workers. | JavaScript | 0 | 2026-08-01 |
| [ttnn-web-calculator](https://github.com/Aswincloud/ttnn-web-calculator) | Web app to test and visualize 150+ Tenstorrent TTNN operations in real time, with PyTorch comparison | HTML | 0 | 2026-07-05 |
| [word-game-bot](https://github.com/Aswincloud/word-game-bot) | Telegram word chain game bot (aiogram v3). Fork of jonowo/on9wordchainbot with DB-backed admin & group authorization. | Python | 0 | 2026-07-27 |
<!-- REPOS_END -->

## 🤖 Org automation

Workflows in this repo that run against the whole org:

| Workflow | Schedule | What it does |
|---|---|---|
| [`reconcile-rulesets.yml`](.github/workflows/reconcile-rulesets.yml) | Mondays 06:17 UTC | Reasserts the branch-protection baseline on every public repo |
| [`security-sweep.yml`](.github/workflows/security-sweep.yml) | Mondays 06:17 UTC | Audits secret scanning + push protection, opens a tracking issue |
| [`site-probe.yml`](.github/workflows/site-probe.yml) | every 15 min | Checks every hosted site is serving; fails the run and emails if not |
| [`sync-security-triage.yml`](.github/workflows/sync-security-triage.yml) | every 6 h | Mirrors open security alerts onto the Security Triage board |

### Site uptime probe

[`scripts/probe_sites.py`](scripts/probe_sites.py) requests every site in
[`scripts/sites.json`](scripts/sites.json) and **fails the run** if any is
unhealthy. Stdlib only, no dependencies.

**To add or remove a site, edit `scripts/sites.json`** — one object per site:

| Field | Required | Meaning |
|---|:--:|---|
| `name` | yes | Short label used in the report and the tracking issue title |
| `url` | yes | Exact URL to request |
| `expect` | no | Acceptable status codes, default `[200]` |
| `contains` | no | Substring that must appear in the body (catches "200 but blank page") |
| `note` | no | Why a non-200 is correct, for the next reader |

Sites are probed at `/` rather than a health endpoint on purpose: the root is the
user-visible surface and exercises static-asset serving too, which a Worker-only
health route does not.

**`console` expects `302`, and that is correct** — it sits behind Cloudflare
Access, so a redirect to the login page means it is up. The probe deliberately
does **not** follow redirects, or that 302 would be invisible. Don't "fix" it
to 200.

**Email is sent on state change only.** An open issue titled `🔴 Site down — <name>`
is the state store, so a site that stays down gets one email and one issue, with
later runs adding a comment. Recovery closes the issue and sends one more email.
A site is only declared down after 3 failed attempts, so a single TCP reset
doesn't page anyone.

Secrets (all optional — if any is unset the email is skipped with a warning and
**the run still fails**, so a missing key can never mask an outage):
`RESEND_API_KEY`, `ALERT_FROM`, `ALERT_TO`.

Run it locally without emailing anyone:

```bash
DRY_RUN=true python3 scripts/probe_sites.py
```

Exit codes: `0` all up · `1` something is down · `2` the probe itself couldn't
run (missing or malformed `sites.json`).

## 📬 Contact

For questions or contributions, feel free to open an issue in the relevant repository.