# Aswincloud

**Developer tooling · Performance profiling · Modern web applications**

[![Website](https://img.shields.io/badge/Website-aswincloud.com-2ea44f?logo=googlechrome&logoColor=white)](https://aswincloud.com)
[![GitHub](https://img.shields.io/badge/GitHub-Aswincloud-181717?logo=github&logoColor=white)](https://github.com/Aswincloud)
[![Made in India](https://img.shields.io/badge/Made%20in-India-FF9933?labelColor=138808&color=FF9933)](https://aswincloud.com)

---

## 🌟 Featured Projects

<!-- REPOS_START -->
| Repository | Description | Language | ⭐ | Updated |
|------------|-------------|----------|:--:|:-------:|
| [ttperf](https://github.com/Aswincloud/ttperf) | A streamlined CLI tool for profiling Tenstorrent's TT-Metal tests and extracting device kernel performance metrics | Python | 3 | 2026-07-23 |
| [ttnn-performance-dashboard](https://github.com/Aswincloud/ttnn-performance-dashboard) | Day-by-day performance tracking dashboard for Tenstorrent TT-Metal TTNN eltwise operations. | JavaScript | 1 | 2026-07-25 |
| [portfolio](https://github.com/Aswincloud/portfolio) | Professional portfolio website built with React, Vite, and Tailwind CSS | JavaScript | 1 | 2026-07-21 |
| [whatsapp_bot](https://github.com/Aswincloud/whatsapp_bot) | WhatsApp AI assistant bot powered by Claude — conversational AI for everyday use | Python | 0 | 2026-07-20 |
| [3d_printing](https://github.com/Aswincloud/3d_printing) | 3D print portfolio and showcase site — custom figurines, decor, and art pieces. Orders via DM | HTML | 0 | 2026-07-25 |
| [AiBuddy](https://github.com/Aswincloud/AiBuddy) | AI-powered chatbot for Microsoft Teams — brings conversational AI into team channels and group chats | Python | 0 | 2026-07-05 |
| [auth](https://github.com/Aswincloud/auth) | Shared, framework-agnostic auth primitives for Cloudflare Workers sites — signed sessions, HMAC tokens, PBKDF2 passwords, owner allowlists, OAuth — plus an optional React login UI. Published as @aswincloud/auth. | TypeScript | 0 | 2026-07-25 |
| [blog](https://github.com/Aswincloud/blog) | blog.aswincloud.com - homelab & home automation | CSS | 0 | 2026-07-25 |
| [chat](https://github.com/Aswincloud/chat) | Full-viewport iframe wrapper hosting the self-hosted Chatwoot widget at chat.aswincloud.com | HTML | 0 | 2026-07-25 |
| [cheap-domain](https://github.com/Aswincloud/cheap-domain) *(archived)* | Get a custom subdomain under aswincloud.com for just ₹20/month | – | 0 | 2026-07-25 |
| [gh-org-guard](https://github.com/Aswincloud/gh-org-guard) | Self-healing GitHub org governance: reconcile branch protection, merge queue, reviews & secret-hygiene across every repo — one weekly workflow. Reference implementation. | Python | 1 | 2026-07-25 |
| [ghadiff](https://github.com/Aswincloud/ghadiff) | Python CLI to compare two GitHub Actions workflow runs — timing, status, and job/step-level diffs with text, JSON, Markdown, and HTML output | Python | 0 | 2026-07-05 |
| [invoicer](https://github.com/Aswincloud/invoicer) | Create, preview, download and email professional invoices. Cloudflare Pages + Functions + D1. | JavaScript | 0 | 2026-07-25 |
| [pr-review-checker](https://github.com/Aswincloud/pr-review-checker) | Web app that analyzes GitHub PRs against CODEOWNERS to compute minimum required approvals, with AI-powered approval predictions from team history | JavaScript | 1 | 2026-07-19 |
| [resume](https://github.com/Aswincloud/resume) | Aswin — Software Engineer. Resume built from HTML/CSS, auto-rendered to PDF. | HTML | 0 | 2026-07-15 |
| [shiptrack](https://github.com/Aswincloud/shiptrack) | Free, open-source, self-hostable shipment tracking for Indian & international couriers — built with Next.js + TypeScript | TypeScript | 1 | 2026-07-05 |
| [slack-join](https://github.com/Aswincloud/slack-join) *(archived)* | – | JavaScript | 0 | 2025-07-15 |
| [status-page](https://github.com/Aswincloud/status-page) | 🟢 Self-hosted, BetterStack-style live status page for a home network — Cloudflare Worker + D1 + a Docker prober, with email & Slack alerts. Runs on the free tier. | TypeScript | 0 | 2026-07-25 |
| [tg-torrent](https://github.com/Aswincloud/tg-torrent) | Telegram bot to remotely add torrents to qBittorrent via magnet links or .torrent files | Python | 0 | 2026-07-05 |
| [ttnn-ops-coverage](https://github.com/Aswincloud/ttnn-ops-coverage) | Interactive zero-dependency dashboard for the TTNN (Tenstorrent) op test matrix — every op across dtype × layout × memory, with per-config PCC/ULP accuracy and run-to-run diffs. Deploys to Cloudflare Workers. | JavaScript | 0 | 2026-07-26 |
| [ttnn-web-calculator](https://github.com/Aswincloud/ttnn-web-calculator) | Web app to test and visualize 150+ Tenstorrent TTNN operations in real time, with PyTorch comparison | HTML | 0 | 2026-07-05 |
| [word-game-bot](https://github.com/Aswincloud/word-game-bot) | Telegram word chain game bot (aiogram v3). Fork of jonowo/on9wordchainbot with DB-backed admin & group authorization. | Python | 0 | 2026-07-25 |
<!-- REPOS_END -->

---

## ⚙️ Engineering practices

This organization is run to professional standards — every repository is governed automatically, with policy defined once and continuously reconciled.

[![Governance](https://img.shields.io/badge/Governance-100%25%20automated-2f6feb)](https://github.com/Aswincloud/.github)
[![Policy](https://img.shields.io/badge/Policy-self--healing-1a7f4b)](https://github.com/Aswincloud/.github)
[![CI](https://img.shields.io/badge/Workflows-actionlint%20gated-6b4fbb?logo=githubactions&logoColor=white)](https://github.com/Aswincloud/.github)
[![Edge](https://img.shields.io/badge/Deploy-Cloudflare%20edge-F38020?logo=cloudflare&logoColor=white)](https://workers.cloudflare.com/)

- **Uniform governance** — every public repository shares one policy baseline: required reviews, code-owner review, protected branches, and resolved conversations before merge.
- **Self-healing** — a scheduled reconciler keeps every repository in policy and brings new repositories into compliance automatically, so nothing drifts.
- **Single source of truth** — shared, reusable workflows are defined once in [`.github`](https://github.com/Aswincloud/.github) and consumed everywhere; no duplication.
- **Quality-gated CI** — workflows are linted and pinned before they merge; automation runs least-privilege.
- **Serverless & edge-native** — projects deploy to Cloudflare Workers & Pages with D1, KV, and Durable Objects, globally distributed and running within free-tier limits.

---

## 📬 Contact

For questions or contributions, open an issue in the relevant repository.
