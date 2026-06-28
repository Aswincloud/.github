#!/usr/bin/env python3
"""
Sync the org "Security Triage" Project (v2, #4) with every OPEN security alert
across all Aswincloud repos: Dependabot, secret-scanning, and code-scanning.

Security alerts are not Issues/PRs, so they can't be added to a board directly.
Instead each alert is mirrored as a DRAFT ISSUE on the board, tagged with
Severity + Finding Type, and deduped via a stable marker line in the body:

    <!-- sec-sync:<type>:<repo>:<number> -->

Re-running is idempotent: existing markers are skipped; alerts that are no
longer open have their draft moved to Status = Done.

Env:
  GH_TOKEN  PAT with `project` + `repo` + `security_events` scope.
"""
import json, os, sys, urllib.request, urllib.error

ORG = "Aswincloud"
PROJECT_NUMBER = 4
API = "https://api.github.com"
GQL = f"{API}/graphql"
TOKEN = os.environ["GH_TOKEN"]

# --- Project field/option IDs (Security Triage #4) ---
PROJECT_ID  = "PVT_kwDODRKA3c4Bb4oh"
STATUS_FIELD = "PVTSSF_lADODRKA3c4Bb4ohzhWlr9Q"
STATUS_TODO  = "f75ad846"
STATUS_DONE  = "98236657"
SEV_FIELD   = "PVTSSF_lADODRKA3c4Bb4ohzhWlr_o"
SEV = {"critical": "b8d25c28", "high": "c8c73b4c",
       "medium": "42f84471", "low": "1955aa27"}
TYPE_FIELD  = "PVTSSF_lADODRKA3c4Bb4ohzhWlsAg"
TYPE = {"Dependabot": "cd7bd4dd", "Secret": "3be0340b",
        "Code Scanning": "81e98936"}


def http(method, path, data=None, accept=None):
    url = path if path.startswith("http") else f"{API}{path}"
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", f"bearer {TOKEN}")
    req.add_header("Accept", accept or "application/vnd.github+json")
    if body:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as r:
            txt = r.read().decode()
            return r.status, (json.loads(txt) if txt else None)
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")


def gql(query, variables=None):
    st, out = http("POST", GQL, {"query": query, "variables": variables or {}})
    if not out or "errors" in (out or {}):
        raise SystemExit(f"GraphQL error: {json.dumps(out, indent=2)}")
    return out["data"]


def paginate(path):
    """REST pagination over ?page= for org alert endpoints; tolerate 404/disabled."""
    page, items = 1, []
    while True:
        sep = "&" if "?" in path else "?"
        st, data = http("GET", f"{path}{sep}per_page=100&page={page}")
        if st != 200 or not isinstance(data, list):
            break
        items += data
        if len(data) < 100:
            break
        page += 1
    return items


# ---------- Collect open alerts (org-level endpoints) ----------
def dependabot_alerts():
    out = []
    for a in paginate(f"/orgs/{ORG}/dependabot/alerts?state=open"):
        sev = (a.get("security_advisory", {}).get("severity") or "low").lower()
        sev = "critical" if sev == "critical" else sev
        repo = a["repository"]["name"]
        num = a["number"]
        pkg = a.get("dependency", {}).get("package", {}).get("name", "?")
        title = f"[Dependabot] {repo}: {pkg} — {a.get('security_advisory',{}).get('summary','vulnerability')}"
        out.append({
            "marker": f"dependabot:{repo}:{num}",
            "type": "Dependabot", "sev": sev if sev in SEV else "medium",
            "title": title[:240], "url": a.get("html_url", ""),
        })
    return out


def secret_alerts():
    out = []
    for a in paginate(f"/orgs/{ORG}/secret-scanning/alerts?state=open"):
        repo = a["repository"]["name"]
        num = a["number"]
        kind = a.get("secret_type_display_name", a.get("secret_type", "secret"))
        out.append({
            "marker": f"secret:{repo}:{num}",
            "type": "Secret", "sev": "critical",   # leaked secrets = treat as critical
            "title": f"[Secret] {repo}: {kind} detected"[:240],
            "url": a.get("html_url", ""),
        })
    return out


def code_alerts():
    out = []
    for a in paginate(f"/orgs/{ORG}/code-scanning/alerts?state=open"):
        repo = a["repository"]["name"]
        num = a["number"]
        rule = a.get("rule", {})
        sev = (rule.get("security_severity_level")
               or rule.get("severity") or "medium").lower()
        sev = {"error": "high", "warning": "medium", "note": "low"}.get(sev, sev)
        out.append({
            "marker": f"code:{repo}:{num}",
            "type": "Code Scanning", "sev": sev if sev in SEV else "medium",
            "title": f"[CodeQL] {repo}: {rule.get('description', rule.get('id','finding'))}"[:240],
            "url": a.get("html_url", ""),
        })
    return out


# ---------- Board state ----------
def existing_items():
    """Return {marker: itemId} for draft issues already on the board."""
    out, cursor = {}, None
    while True:
        data = gql("""
          query($pid:ID!,$c:String){ node(id:$pid){ ... on ProjectV2 {
            items(first:100, after:$c){
              pageInfo{ hasNextPage endCursor }
              nodes{ id content{ ... on DraftIssue { body } } }
            } } } }""", {"pid": PROJECT_ID, "c": cursor})["node"]["items"]
        for it in data["nodes"]:
            body = ((it.get("content") or {}).get("body") or "")
            for line in body.splitlines():
                line = line.strip()
                if line.startswith("<!-- sec-sync:") and line.endswith("-->"):
                    marker = line[len("<!-- sec-sync:"):-len(" -->")].strip()
                    out[marker] = it["id"]
        if not data["pageInfo"]["hasNextPage"]:
            break
        cursor = data["pageInfo"]["endCursor"]
    return out


def add_draft(alert):
    body = f"{alert['url']}\n\n<!-- sec-sync:{alert['marker']} -->"
    item = gql("""
      mutation($pid:ID!,$t:String!,$b:String!){
        addProjectV2DraftIssue(input:{projectId:$pid,title:$t,body:$b}){
          projectItem{ id } } }""",
      {"pid": PROJECT_ID, "t": alert["title"], "b": body}
    )["addProjectV2DraftIssue"]["projectItem"]["id"]
    set_select(item, STATUS_FIELD, STATUS_TODO)
    set_select(item, SEV_FIELD, SEV[alert["sev"]])
    set_select(item, TYPE_FIELD, TYPE[alert["type"]])
    return item


def set_select(item_id, field_id, option_id):
    gql("""
      mutation($pid:ID!,$iid:ID!,$fid:ID!,$oid:String!){
        updateProjectV2ItemFieldValue(input:{
          projectId:$pid,itemId:$iid,fieldId:$fid,
          value:{singleSelectOptionId:$oid}}){ projectV2Item{ id } } }""",
      {"pid": PROJECT_ID, "iid": item_id, "fid": field_id, "oid": option_id})


def main():
    alerts = dependabot_alerts() + secret_alerts() + code_alerts()
    by_marker = {a["marker"]: a for a in alerts}
    on_board = existing_items()

    added = 0
    for marker, a in by_marker.items():
        if marker not in on_board:
            add_draft(a)
            added += 1
    print(f"New security alerts mirrored to board: {added}")

    resolved = 0
    for marker, item_id in on_board.items():
        if marker not in by_marker:          # alert no longer open
            set_select(item_id, STATUS_FIELD, STATUS_DONE)
            resolved += 1
    print(f"Resolved alerts moved to Done: {resolved}")
    print(f"Currently open alerts: dependabot/secret/code = "
          f"{sum(1 for a in alerts if a['type']=='Dependabot')}/"
          f"{sum(1 for a in alerts if a['type']=='Secret')}/"
          f"{sum(1 for a in alerts if a['type']=='Code Scanning')}")


if __name__ == "__main__":
    sys.exit(main())
