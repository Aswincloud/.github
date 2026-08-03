#!/usr/bin/env python3
"""
Probe every hosted aswincloud site and FAIL THE JOB if any is unhealthy.

Reads scripts/sites.json, requests each site, and reports a markdown table.
Exits non-zero when anything is down, so the workflow run goes red.

Email is sent on STATE CHANGE ONLY — when a site newly goes down, or recovers.
A multi-hour outage therefore produces two emails, not one per run. The state
store is this repo's own GitHub issues: an OPEN issue titled

    🔴 Site down — <name>

means "that site was down on the previous run". No database, same trick
security-sweep.yml uses for its tracking issue.

Per-site config supports `expect` (acceptable status codes, default [200])
because not every healthy site returns 200: console.aswincloud.com sits behind
Cloudflare Access and answers 302 to its login page. Redirects are deliberately
NOT followed, or that 302 would be invisible.

A site is only declared down after PROBE_ATTEMPTS failures — one TCP reset
should not wake anybody up.

Env:
  DRY_RUN         "false" to act; anything else previews (default: preview).
  SITES_FILE      Path to the site list (default: scripts/sites.json).
  PROBE_TIMEOUT   Per-request timeout, seconds (default: 15).
  PROBE_ATTEMPTS  Tries before declaring down (default: 3).
  GH_TOKEN        Token for reading/writing issues in this repo (issues: write).
  GITHUB_REPOSITORY  owner/repo, set by Actions; needed for issue operations.
  RESEND_API_KEY  Resend key. If unset, email is skipped (job still fails).
  ALERT_FROM      Verified Resend sender, e.g. "status <status@aswincloud.com>".
  ALERT_TO        Recipient(s), comma-separated.
"""
import concurrent.futures
import json
import os
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

SITES_FILE = os.environ.get("SITES_FILE", "scripts/sites.json")
# Safe by default: only the literal "false" enables real sends/writes, so a typo
# previews instead of emailing.
DRY_RUN = os.environ.get("DRY_RUN", "true").strip().lower() != "false"
TIMEOUT = int(os.environ.get("PROBE_TIMEOUT", "15"))
ATTEMPTS = int(os.environ.get("PROBE_ATTEMPTS", "3"))

REPO = os.environ.get("GITHUB_REPOSITORY", "")
UA = "aswincloud-site-probe/1.0 (+https://github.com/Aswincloud/.github)"
TITLE_PREFIX = "🔴 Site down — "
RESEND_URL = "https://api.resend.com/emails"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """Surface 3xx as the result instead of following it.

    console.aswincloud.com is Access-gated and its healthy answer is a 302 to
    the login page. Following redirects would report the login page's 200 and
    hide whether the site itself is actually up.
    """

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


OPENER = urllib.request.build_opener(NoRedirect)


def probe_once(url):
    """Return (status_code, body_prefix, ms). Raises on connection failure."""
    req = urllib.request.Request(url, headers={"User-Agent": UA}, method="GET")
    t0 = time.monotonic()
    try:
        with OPENER.open(req, timeout=TIMEOUT) as r:
            body = r.read(65536).decode("utf-8", "replace")
            return r.status, body, int((time.monotonic() - t0) * 1000)
    except urllib.error.HTTPError as e:
        # A 4xx/5xx is a RESULT, not a crash — read it and let the caller judge.
        body = ""
        try:
            body = e.read(65536).decode("utf-8", "replace")
        except OSError:
            pass
        return e.code, body, int((time.monotonic() - t0) * 1000)


def probe(site):
    """Return (ok, detail). Retries on failure only; any success wins."""
    url = site["url"]
    expect = site.get("expect") or [200]
    needle = site.get("contains")
    last = ""
    for attempt in range(1, ATTEMPTS + 1):
        try:
            code, body, ms = probe_once(url)
        except (urllib.error.URLError, ssl.SSLError, TimeoutError, OSError) as e:
            last = f"{type(e).__name__}: {str(e)[:90]}"
        else:
            if code not in expect:
                last = f"HTTP {code} (expected {'/'.join(str(c) for c in expect)})"
            elif needle and needle not in body:
                last = f"HTTP {code} but body missing {needle!r}"
            else:
                extra = f" (attempt {attempt})" if attempt > 1 else ""
                return True, f"{code} in {ms}ms{extra}"
        if attempt < ATTEMPTS:
            time.sleep(attempt)  # linear backoff: 1s, 2s, ...
    tries = "attempt" if ATTEMPTS == 1 else "attempts"
    return False, f"{last} after {ATTEMPTS} {tries}"


def probe_all(sites):
    """Probe concurrently so 16 sites take seconds, not 16 x timeout."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        return list(pool.map(probe, sites))


def gh(*args):
    """Run gh, returning the CompletedProcess. Never raises; callers check."""
    return subprocess.run(["gh", *args], capture_output=True, text=True)


def open_issues():
    """Map site name -> open issue number, from this repo's down-issues."""
    if not REPO:
        return {}
    r = gh("issue", "list", "--repo", REPO, "--state", "open",
           "--search", f"{TITLE_PREFIX} in:title", "--limit", "100",
           "--json", "number,title")
    if r.returncode != 0:
        print(f"::warning::could not list issues: {r.stderr.strip()[:120]}")
        return {}
    try:
        items = json.loads(r.stdout or "[]")
    except json.JSONDecodeError:
        return {}
    found = {}
    for it in items:
        t = it.get("title", "")
        if t.startswith(TITLE_PREFIX):
            found[t[len(TITLE_PREFIX):].strip()] = it["number"]
    return found


def issue_open(name, detail, url):
    body = (f"`{name}` is not responding as expected.\n\n"
            f"- URL: {url}\n- Detail: {detail}\n- First seen: {stamp()}\n\n"
            "This issue is the probe's state store — it closes automatically "
            "when the site recovers. Do not close it by hand while the site is "
            "still down, or you will be emailed again on the next run.")
    r = gh("issue", "create", "--repo", REPO, "--title", TITLE_PREFIX + name,
           "--body", body, "--label", "incident")
    if r.returncode != 0:
        # The label may not exist in this repo — retry without it, as
        # security-sweep.yml does for its own create.
        r = gh("issue", "create", "--repo", REPO,
               "--title", TITLE_PREFIX + name, "--body", body)
    if r.returncode != 0:
        print(f"::warning::could not open issue for {name}: "
              f"{r.stderr.strip()[:120]}")


def issue_comment(num, text):
    r = gh("issue", "comment", str(num), "--repo", REPO, "--body", text)
    if r.returncode != 0:
        print(f"::warning::could not comment on #{num}: "
              f"{r.stderr.strip()[:120]}")


def issue_close(num, name, detail):
    issue_comment(num, f"✅ `{name}` recovered — {detail} at {stamp()}. Closing.")
    r = gh("issue", "close", str(num), "--repo", REPO)
    if r.returncode != 0:
        print(f"::warning::could not close #{num}: {r.stderr.strip()[:120]}")


def stamp():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def send_email(down, recovered):
    """Email the transitions. Returns a short status string for the log."""
    key = os.environ.get("RESEND_API_KEY")
    frm = os.environ.get("ALERT_FROM")
    to_raw = os.environ.get("ALERT_TO", "")
    to = [a.strip() for a in to_raw.split(",") if a.strip()]
    if not key or not frm or not to:
        # Never let a missing key mask an outage — the job still fails below.
        return "skipped (RESEND_API_KEY / ALERT_FROM / ALERT_TO not all set)"

    bits = []
    if down:
        bits.append(f"🔴 {len(down)} down: " + ", ".join(n for n, _, _ in down))
    if recovered:
        bits.append(f"✅ {len(recovered)} recovered: "
                    + ", ".join(n for n, _, _ in recovered))
    subject = " / ".join(bits)

    lines = []
    if down:
        lines.append("DOWN")
        lines += [f"  {n}  {u}  — {d}" for n, u, d in down]
        lines.append("")
    if recovered:
        lines.append("RECOVERED")
        lines += [f"  {n}  {u}  — {d}" for n, u, d in recovered]
        lines.append("")
    lines.append(f"Checked at {stamp()}.")
    if REPO:
        lines.append(f"Run: https://github.com/{REPO}/actions/workflows/"
                     "site-probe.yml")
    text = "\n".join(lines)

    rows = "".join(
        f"<tr><td>{'🔴 down' if kind == 'down' else '✅ up'}</td>"
        f"<td><b>{n}</b></td><td><a href=\"{u}\">{u}</a></td><td>{d}</td></tr>"
        for kind, group in (("down", down), ("up", recovered))
        for n, u, d in group
    )
    html = (f"<h2>{subject}</h2><table cellpadding=6 border=1 "
            f"style='border-collapse:collapse'>{rows}</table>"
            f"<p>Checked at {stamp()}.</p>")

    payload = {"from": frm, "to": to, "subject": subject,
               "text": text, "html": html}
    req = urllib.request.Request(
        RESEND_URL, data=json.dumps(payload).encode(), method="POST",
        headers={"Authorization": f"Bearer {key}",
                 "Content-Type": "application/json",
                 # Required, or Resend answers 403 / error 1010.
                 "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            if r.status in (200, 201):
                return f"sent to {len(to)} recipient(s)"
            return f"unexpected status {r.status}"
    except urllib.error.HTTPError as e:
        detail = e.read(500).decode("utf-8", "replace")
        return f"FAILED {e.code}: {detail[:160]}"
    except (urllib.error.URLError, ssl.SSLError, TimeoutError, OSError) as e:
        return f"FAILED {type(e).__name__}: {str(e)[:120]}"


def main():
    try:
        with open(SITES_FILE, encoding="utf-8") as fh:
            sites = json.load(fh)
    except OSError as e:
        print(f"cannot read {SITES_FILE}: {e}", file=sys.stderr)
        sys.exit(2)
    except json.JSONDecodeError as e:
        print(f"{SITES_FILE} is not valid JSON: {e}", file=sys.stderr)
        sys.exit(2)
    if not isinstance(sites, list) or not sites:
        print(f"{SITES_FILE} must be a non-empty JSON array", file=sys.stderr)
        sys.exit(2)
    seen = set()
    for s in sites:
        if not isinstance(s, dict) or not s.get("name") or not s.get("url"):
            print(f"every site needs name + url; bad entry: {s!r}",
                  file=sys.stderr)
            sys.exit(2)
        # Names key the issue state store, so a duplicate would make two sites
        # share one tracking issue and lose transitions.
        if s["name"] in seen:
            print(f"duplicate site name {s['name']!r} — names must be unique",
                  file=sys.stderr)
            sys.exit(2)
        seen.add(s["name"])

    results = probe_all(sites)
    was_down = open_issues()

    rows, down, recovered = [], [], []
    up_n = 0
    for site, (ok, detail) in zip(sites, results):
        name, url = site["name"], site["url"]
        if ok:
            up_n += 1
            rows.append((name, "✅ up", detail))
            if name in was_down:
                recovered.append((name, url, detail))
        else:
            rows.append((name, "🔴 DOWN", detail))
            if name not in was_down:
                down.append((name, url, detail))

    # Act on transitions: open/close the state-store issues.
    if not DRY_RUN and REPO:
        for name, url, detail in down:
            issue_open(name, detail, url)
        for name, url, detail in recovered:
            issue_close(was_down[name], name, detail)
        # Still-down sites get a comment but no email — this is the de-dupe.
        for site, (ok, detail) in zip(sites, results):
            n = site["name"]
            if not ok and n in was_down:
                issue_comment(was_down[n], f"Still down — {detail} at {stamp()}.")

    mail = "no transitions"
    if down or recovered:
        if DRY_RUN:
            mail = ("would email — newly-down="
                    f"{[n for n, _, _ in down]} "
                    f"recovered={[n for n, _, _ in recovered]}")
        else:
            mail = send_email(down, recovered)

    mode = "DRY-RUN (no email, no issues)" if DRY_RUN else "LIVE"
    out = [f"### site probe — {stamp()} — {mode}", "",
           "| site | status | detail |", "|---|---|---|"]
    out += [f"| {n} | {s} | {d} |" for n, s, d in rows]
    down_n = len(rows) - up_n
    out += ["", f"**up={up_n} down={down_n} newly-down={len(down)} "
            f"recovered={len(recovered)}** — email: {mail}"]
    report = "\n".join(out)
    print(report)
    summ = os.environ.get("GITHUB_STEP_SUMMARY")
    if summ:
        open(summ, "a", encoding="utf-8").write(report + "\n")

    if down_n:
        sys.exit(1)


if __name__ == "__main__":
    main()
