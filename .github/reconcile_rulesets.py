#!/usr/bin/env python3
"""Reconcile an 'org-baseline' branch ruleset across PUBLIC, ACTIVE repos.

Floor-only baseline: block force-push + deletion, require a PR with all review
threads resolved, 0 required approvals (a solo owner can still merge their own
PR). GitHub applies EVERY matching ruleset, so this stacks with any richer
per-repo ruleset (e.g. a 'main protection' ruleset carrying a merge queue +
CODEOWNERS) — it only adds a floor and never removes rules. Proven on blog.

DRY_RUN=true (default) reports what WOULD change and writes nothing.
Skips: private (rulesets need Pro/Team), archived, forks, templates, empty.

Enforce mode needs the token to hold administration:write. If it doesn't yet
(the Aswincloud Bot App has to be granted it in the App's settings), the write
fails cleanly with a 'needs App administration:write' note rather than crashing.
"""
import json
import os
import subprocess
import sys

ORG = os.environ.get("ORG", "Aswincloud")
DRY_RUN = os.environ.get("DRY_RUN", "true").strip().lower() != "false"
BASELINE = "org-baseline"


def gh(path, *extra, method=None, body=None):
    args = ["gh", "api"]
    if method:
        args += ["-X", method]
    args.append(path)
    args += list(extra)
    if body is not None:
        args += ["--input", "-"]
    r = subprocess.run(args, capture_output=True, text=True,
                       input=(json.dumps(body) if body is not None else None))
    return r  # caller inspects returncode/stderr


def desired_rules():
    return [
        {"type": "deletion"},
        {"type": "non_fast_forward"},
        {"type": "pull_request", "parameters": {
            "required_approving_review_count": 0,
            "dismiss_stale_reviews_on_push": False,
            "require_code_owner_review": False,
            "require_last_push_approval": False,
            "required_review_thread_resolution": True,
        }},
    ]


def payload():
    return {
        "name": BASELINE,
        "target": "branch",
        "enforcement": "active",
        "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}},
        "rules": desired_rules(),
    }


# Fields we actually manage per rule type. GitHub injects extra defaults on
# store (allowed_merge_methods, required_reviewers, nulls...), so we compare
# ONLY our intent — otherwise the reconciler would "drift" forever and rewrite
# every repo on every run.
MANAGED = {
    "deletion": [],
    "non_fast_forward": [],
    "pull_request": [
        "required_approving_review_count",
        "require_code_owner_review",
        "required_review_thread_resolution",
    ],
}


def norm(rules):
    by_type = {r["type"]: (r.get("parameters") or {}) for r in rules}
    slim = {}
    for rtype, keys in MANAGED.items():
        if rtype not in by_type:
            slim[rtype] = None  # a managed rule is missing -> drift
            continue
        params = by_type[rtype]
        slim[rtype] = {k: params.get(k) for k in keys}
    return json.dumps(slim, sort_keys=True)


def skip_reason(repo):
    if repo["private"]:
        return "private (needs Pro/Team)"
    if repo["archived"]:
        return "archived"
    if repo["fork"]:
        return "fork"
    if repo.get("is_template"):
        return "template"
    if not repo.get("default_branch"):
        return "empty (no default branch)"
    return None


def find_baseline(repo):
    r = gh(f"repos/{ORG}/{repo}/rulesets")
    if r.returncode != 0:
        return None, r.stderr.strip()
    for rs in json.loads(r.stdout or "[]"):
        if rs.get("name") == BASELINE:
            full = gh(f"repos/{ORG}/{repo}/rulesets/{rs['id']}")
            return json.loads(full.stdout), None
    return None, None


def write(repo, cur):
    if cur is None:
        r = gh(f"repos/{ORG}/{repo}/rulesets", method="POST", body=payload())
    else:
        r = gh(f"repos/{ORG}/{repo}/rulesets/{cur['id']}", method="PUT", body=payload())
    if r.returncode == 0:
        return None
    err = r.stderr
    if "administration" in err.lower() or "resource not accessible" in err.lower() \
            or "not accessible by integration" in err.lower():
        return "needs App administration:write"
    return err.strip()[:70]


def main():
    r = gh(f"orgs/{ORG}/repos", "--paginate", "--jq",
           ".[] | {name, private, archived, fork, is_template, default_branch}")
    if r.returncode != 0:
        print(f"failed to list repos: {r.stderr}", file=sys.stderr)
        sys.exit(2)
    repos = sorted((json.loads(x) for x in r.stdout.splitlines() if x.strip()),
                   key=lambda x: x["name"])

    rows = []
    c = {"create": 0, "update": 0, "in_sync": 0, "skip": 0, "error": 0, "blocked": 0}
    want = norm(desired_rules())

    for repo in repos:
        name = repo["name"]
        why = skip_reason(repo)
        if why:
            c["skip"] += 1
            rows.append((name, "skip", why))
            continue
        cur, err = find_baseline(name)
        if err:
            c["error"] += 1
            rows.append((name, "error", err[:60]))
            continue
        drifted = cur is not None and (
            norm(cur.get("rules", [])) != want or cur.get("enforcement") != "active")
        if cur is None or drifted:
            act = "CREATE" if cur is None else "UPDATE"
            note = "no org-baseline present" if cur is None else "drifted from baseline"
            if not DRY_RUN:
                problem = write(name, cur)
                if problem:
                    c["blocked"] += 1
                    rows.append((name, "BLOCKED", problem))
                    continue
            c["create" if cur is None else "update"] += 1
            rows.append((name, act, note))
        else:
            c["in_sync"] += 1
            rows.append((name, "in-sync", ""))

    mode = "DRY-RUN (no changes)" if DRY_RUN else "ENFORCE"
    out = [f"### org-baseline reconcile — {mode}", "",
           "| repo | action | note |", "|---|---|---|"]
    out += [f"| {n} | {a} | {note} |" for n, a, note in rows]
    out += ["", f"**create={c['create']} update={c['update']} in-sync={c['in_sync']} "
            f"skip={c['skip']} blocked={c['blocked']} error={c['error']}**"]
    report = "\n".join(out)
    print(report)
    summ = os.environ.get("GITHUB_STEP_SUMMARY")
    if summ:
        with open(summ, "a", encoding="utf-8") as fh:
            fh.write(report + "\n")
    # Fail the run if anything genuinely errored OR was blocked on permissions,
    # so enforce mode is visibly red until the App is granted admin:write.
    if c["error"] or c["blocked"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
