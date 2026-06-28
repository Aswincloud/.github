#!/usr/bin/env python3
"""
Sync the org-level "PR Review Queue" Project (v2) with every PR in the org.

Fully automated — run on a schedule. No manual board edits required.
  * Every OPEN pull request across all org repos is added to the board (Status = Todo).
  * Any board item whose PR has since been MERGED or CLOSED is moved to Status = Done.

Requires an env var GH_TOKEN holding a PAT/token with `project` + `repo` scope,
because the default GITHUB_TOKEN cannot write to organization Projects v2.
"""
import json
import os
import sys
import urllib.request

ORG = "Aswincloud"
PROJECT_NUMBER = 3
API = "https://api.github.com/graphql"
TOKEN = os.environ["GH_TOKEN"]

OPEN_TO_STATUS = "Todo"      # awaiting review
CLOSED_TO_STATUS = "Done"    # merged or closed


def gql(query, variables=None):
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(
        API, data=body,
        headers={"Authorization": f"bearer {TOKEN}",
                 "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        out = json.load(r)
    if "errors" in out:
        raise SystemExit(f"GraphQL error: {json.dumps(out['errors'], indent=2)}")
    return out["data"]


def get_project():
    data = gql(
        """
        query($org:String!, $num:Int!) {
          organization(login:$org) {
            projectV2(number:$num) {
              id
              fields(first:30) {
                nodes {
                  ... on ProjectV2SingleSelectField {
                    id name options { id name }
                  }
                }
              }
            }
          }
        }""",
        {"org": ORG, "num": PROJECT_NUMBER},
    )["organization"]["projectV2"]
    status = next(f for f in data["fields"]["nodes"]
                  if f.get("name") == "Status")
    opts = {o["name"]: o["id"] for o in status["options"]}
    return data["id"], status["id"], opts


def all_open_prs():
    """Yield node IDs of every OPEN PR in the org (paginated over repos+PRs)."""
    repo_cursor = None
    while True:
        data = gql(
            """
            query($org:String!, $rc:String) {
              organization(login:$org) {
                repositories(first:50, after:$rc) {
                  pageInfo { hasNextPage endCursor }
                  nodes {
                    pullRequests(states:OPEN, first:100) {
                      nodes { id }
                    }
                  }
                }
              }
            }""",
            {"org": ORG, "rc": repo_cursor},
        )["organization"]["repositories"]
        for repo in data["nodes"]:
            for pr in repo["pullRequests"]["nodes"]:
                yield pr["id"]
        if not data["pageInfo"]["hasNextPage"]:
            break
        repo_cursor = data["pageInfo"]["endCursor"]


def project_items(project_id):
    """Yield (itemId, prState) for every PR item already on the board."""
    cursor = None
    while True:
        data = gql(
            """
            query($pid:ID!, $c:String) {
              node(id:$pid) {
                ... on ProjectV2 {
                  items(first:100, after:$c) {
                    pageInfo { hasNextPage endCursor }
                    nodes {
                      id
                      content { ... on PullRequest { state } }
                    }
                  }
                }
              }
            }""",
            {"pid": project_id, "c": cursor},
        )["node"]["items"]
        for it in data["nodes"]:
            content = it.get("content") or {}
            if "state" in content:
                yield it["id"], content["state"]
        if not data["pageInfo"]["hasNextPage"]:
            break
        cursor = data["pageInfo"]["endCursor"]


def add_pr(project_id, content_id):
    return gql(
        """
        mutation($pid:ID!, $cid:ID!) {
          addProjectV2ItemById(input:{projectId:$pid, contentId:$cid}) {
            item { id }
          }
        }""",
        {"pid": project_id, "cid": content_id},
    )["addProjectV2ItemById"]["item"]["id"]


def set_status(project_id, item_id, field_id, option_id):
    gql(
        """
        mutation($pid:ID!, $iid:ID!, $fid:ID!, $oid:String!) {
          updateProjectV2ItemFieldValue(input:{
            projectId:$pid, itemId:$iid, fieldId:$fid,
            value:{singleSelectOptionId:$oid}
          }) { projectV2Item { id } }
        }""",
        {"pid": project_id, "iid": item_id, "fid": field_id, "oid": option_id},
    )


def main():
    project_id, status_field, opts = get_project()
    todo = opts.get(OPEN_TO_STATUS)
    done = opts.get(CLOSED_TO_STATUS)
    if not todo or not done:
        raise SystemExit(
            f"Status field is missing '{OPEN_TO_STATUS}'/'{CLOSED_TO_STATUS}' "
            f"options. Found: {list(opts)}")

    # 1) Ensure every open PR is on the board, marked Todo.
    added = 0
    for cid in all_open_prs():
        item_id = add_pr(project_id, cid)   # idempotent
        set_status(project_id, item_id, status_field, todo)
        added += 1
    print(f"Open PRs ensured on board (Status=Todo): {added}")

    # 2) Reconcile: any board item whose PR is no longer open -> Done.
    closed = 0
    for item_id, state in project_items(project_id):
        if state in ("MERGED", "CLOSED"):
            set_status(project_id, item_id, status_field, done)
            closed += 1
    print(f"Resolved PRs moved to Status=Done: {closed}")


if __name__ == "__main__":
    sys.exit(main())
