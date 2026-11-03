"""Read open issues from a public GitHub repo (no token needed; GITHUB_TOKEN used if set)."""
from __future__ import annotations
import json, os, urllib.request
from datetime import datetime, timezone
from .core import Issue

def fetch_open_issues(repo: str, limit: int = 30) -> list[Issue]:
    url = f"https://api.github.com/repos/{repo}/issues?state=open&per_page={min(limit,100)}"
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json",
                                               "User-Agent": "triage-minion"})
    tok = os.environ.get("GITHUB_TOKEN")
    if tok:
        req.add_header("Authorization", f"Bearer {tok}")
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.load(r)
    now = datetime.now(timezone.utc)
    out = []
    for d in data:
        if "pull_request" in d:
            continue
        created = datetime.fromisoformat(d["created_at"].replace("Z", "+00:00"))
        out.append(Issue(number=d["number"], title=d["title"], body=(d.get("body") or "")[:2000],
                         comments=d.get("comments", 0), labels=[l["name"] for l in d.get("labels", [])],
                         age_days=(now - created).total_seconds() / 86400, url=d["html_url"]))
    return out[:limit]
