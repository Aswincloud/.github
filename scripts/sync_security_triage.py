#!/usr/bin/env python3
"""
Sync the org "Security Triage" Project (v2, #4) with every OPEN security alert
across all Aswincloud repos: Dependabot, secret-scanning, and code-scanning.

Security alerts are not Issues/PRs, so they can't be added to a board directly.
Each alert is mirrored as a DRAFT ISSUE on the board, tagged with Severity +
Finding Type, deduped via a stable marker line in the body:

    <!-- sec-sync:<type>:<repo>:<number> -->

Idempotent. On every run it also RECONCILES status: open alerts -> Todo,
alerts no longer open -> Done (so a wrong status self-heals).

SAFETY: if any alert source returns an error, the run ABORTS instead of
treating the source as "empty" — otherwise a transient 403/5xx would wipe the
board to Done. A source is only trusted as truly-empty on an HTTP 200.

Env:
  GH_TOKEN  PAT with project (write) + dependabot/secret/code-scanning alerts (read).
"""
import json, os, sys, urllib.request, urllib.error

ORG = "Aswincloud"
API = "https://api.github.com"
GQL = f"{API}/graphql"
TOKEN = os.environ["GH_TOKEN"]

PROJECT_ID  = "PVT_kwDODRKA3c4Bb4oh"
STATUS_FIELD = "PVTSSF_lADODRKA3c4Bb4ohzhWlr9Q"
STATUS_TODO  = "f75ad846"
STATUS_DONE  = "98236657"
SEV_FIELD   = "PVTSSF_lADODRKA3c4Bb4ohzhWlr_o"
SEV = {"critical": "b8d25c28", "high": "c8c73b4c", "medium": "42f84471", "low": "1955aa27"}
TYPE_FIELD  = "PVTSSF_lADODRKA3c4Bb4ohzhWlsAg"
TYPE = {"Dependabot": "cd7bd4dd", "Secret": "3be0340b", "Code Scanning": "81e98936"}


class SourceError(RuntimeError):
    """Raised when an alert source can't be read — must abort, never treat as empty."""


def http(method, path, data=None):
    url = path if path.startswith("http") else f"{API}{path}"
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", f"bearer {TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    if body:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as r:
            txt = r.read().decode()
            return r.status, (json.loads(txt) if txt else None), r.headers.get("Link", "")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}"), ""


def gql(query, variables=None):
    st, out, _ = http("POST", GQL, {"query": query, "variables": variables or {}})
    if not out or "errors" in (out or {}):
        raise SourceError(f"GraphQL error: {json.dumps(out, indent=2)}")
    return out["data"]


def _next_link(link_header):
    for part in (link_header or "").split(","):
        seg = part.split(";")
        if len(seg) >= 2 and 'rel="next"' in seg[1]:
            return seg[0].strip().strip("<>")
    return None


def paginate(path, source_name):
    """Follow GitHub Link-header (cursor) pagination. ANY non-200 aborts (fail-safe)."""
    sep = "&" if "?" in path else "?"
    url = f"{path}{sep}per_page=100"
    items = []
    while url:
        st, data, link = http("GET", url)
        if st != 200:
            raise SourceError(
                f"{source_name}: HTTP {st} reading alerts "
                f"({(data or {}).get('message','')}). Aborting to avoid wiping board.")
        if not isinstance(data, list):
            raise SourceError(f"{source_name}: unexpected payload, aborting.")
        items += data
        url = _next_link(link)
    return items


def dependabot_alerts():
    out = []
    for a in paginate(f"/orgs/{ORG}/dependabot/alerts?state=open", "dependabot"):
        sev = (a.get("security_advisory", {}).get("severity") or "low").lower()
        repo, num = a["repository"]["name"], a["number"]
        pkg = a.get("dependency", {}).get("package", {}).get("name", "?")
        title = f"[Dependabot] {repo}: {pkg} — {a.get('security_advisory',{}).get('summary','vulnerability')}"
        out.append({"marker": f"dependabot:{repo}:{num}", "type": "Dependabot",
                    "sev": sev if sev in SEV else "medium",
                    "title": title[:240], "url": a.get("html_url", "")})
    return out


def secret_alerts():
    out = []
    for a in paginate(f"/orgs/{ORG}/secret-scanning/alerts?state=open", "secret-scanning"):
        repo, num = a["repository"]["name"], a["number"]
        kind = a.get("secret_type_display_name", a.get("secret_type", "secret"))
        out.append({"marker": f"secret:{repo}:{num}", "type": "Secret", "sev": "critical",
                    "title": f"[Secret] {repo}: {kind} detected"[:240],
                    "url": a.get("html_url", "")})
    return out


def code_alerts():
    out = []
    for a in paginate(f"/orgs/{ORG}/code-scanning/alerts?state=open", "code-scanning"):
        repo, num = a["repository"]["name"], a["number"]
        rule = a.get("rule", {})
        sev = (rule.get("security_severity_level") or rule.get("severity") or "medium").lower()
        sev = {"error": "high", "warning": "medium", "note": "low"}.get(sev, sev)
        out.append({"marker": f"code:{repo}:{num}", "type": "Code Scanning",
                    "sev": sev if sev in SEV else "medium",
                    "title": f"[CodeQL] {repo}: {rule.get('description', rule.get('id','finding'))}"[:240],
                    "url": a.get("html_url", "")})
    return out


def existing_items():
    """{marker: {id, status}} for draft issues already on the board."""
    out, cursor = {}, None
    while True:
        data = gql("""
          query($pid:ID!,$c:String){ node(id:$pid){ ... on ProjectV2 {
            items(first:100, after:$c){
              pageInfo{ hasNextPage endCursor }
              nodes{ id
                content{ ... on DraftIssue { body } }
                fieldValues(first:20){ nodes{
                  ... on ProjectV2ItemFieldSingleSelectValue {
                    optionId field{ ... on ProjectV2SingleSelectField { id } } } } } }
            } } } }""", {"pid": PROJECT_ID, "c": cursor})["node"]["items"]
        for it in data["nodes"]:
            body = ((it.get("content") or {}).get("body") or "")
            status = None
            for fv in it["fieldValues"]["nodes"]:
                if fv and fv.get("field", {}).get("id") == STATUS_FIELD:
                    status = fv.get("optionId")
            for line in body.splitlines():
                line = line.strip()
                if line.startswith("<!-- sec-sync:") and line.endswith("-->"):
                    marker = line[len("<!-- sec-sync:"):-len(" -->")].strip()
                    out[marker] = {"id": it["id"], "status": status}
        if not data["pageInfo"]["hasNextPage"]:
            break
        cursor = data["pageInfo"]["endCursor"]
    return out


def set_select(item_id, field_id, option_id):
    gql("""
      mutation($pid:ID!,$iid:ID!,$fid:ID!,$oid:String!){
        updateProjectV2ItemFieldValue(input:{
          projectId:$pid,itemId:$iid,fieldId:$fid,
          value:{singleSelectOptionId:$oid}}){ projectV2Item{ id } } }""",
      {"pid": PROJECT_ID, "iid": item_id, "fid": field_id, "oid": option_id})


def add_draft(a):
    body = f"{a['url']}\n\n<!-- sec-sync:{a['marker']} -->"
    item = gql("""
      mutation($pid:ID!,$t:String!,$b:String!){
        addProjectV2DraftIssue(input:{projectId:$pid,title:$t,body:$b}){
          projectItem{ id } } }""",
      {"pid": PROJECT_ID, "t": a["title"], "b": body}
    )["addProjectV2DraftIssue"]["projectItem"]["id"]
    set_select(item, STATUS_FIELD, STATUS_TODO)
    set_select(item, SEV_FIELD, SEV[a["sev"]])
    set_select(item, TYPE_FIELD, TYPE[a["type"]])


def main():
    # Read every source first. If ANY errors, abort before touching the board.
    try:
        alerts = dependabot_alerts() + secret_alerts() + code_alerts()
    except SourceError as e:
        print(f"ABORT (fail-safe): {e}", file=sys.stderr)
        return 1

    by_marker = {a["marker"]: a for a in alerts}
    on_board = existing_items()

    added = fixed = resolved = 0
    for marker, a in by_marker.items():
        if marker not in on_board:
            add_draft(a); added += 1
        elif on_board[marker]["status"] != STATUS_TODO:   # reconcile drift
            set_select(on_board[marker]["id"], STATUS_FIELD, STATUS_TODO); fixed += 1
    for marker, info in on_board.items():
        if marker not in by_marker and info["status"] != STATUS_DONE:
            set_select(info["id"], STATUS_FIELD, STATUS_DONE); resolved += 1

    print(f"New: {added}  Reopened/fixed->Todo: {fixed}  Resolved->Done: {resolved}")
    print(f"Open alerts dependabot/secret/code = "
          f"{sum(1 for a in alerts if a['type']=='Dependabot')}/"
          f"{sum(1 for a in alerts if a['type']=='Secret')}/"
          f"{sum(1 for a in alerts if a['type']=='Code Scanning')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
