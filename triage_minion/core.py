"""Pure, testable triage logic. No network, no model."""
from __future__ import annotations
import re
from dataclasses import dataclass, field, asdict

KIND_RULES = [
    ("bug", r"\b(bug\w*|crash\w*|error\w*|exception\w*|traceback|fail\w*|broken|regression\w*|segfault\w*|panic\w*)\b"),
    ("security", r"\b(cve|vulnerab\w*|xss|csrf|injection|leak\w*|secrets?|token exposed)\b"),
    ("docs", r"\b(docs?|documentation|readme|typo|example)\b"),
    ("feature", r"\b(feature|support for|add|allow|would be nice|proposal|request)\b"),
    ("question", r"\b(how (do|can|to)|question|\?$)"),
]
SEV_WORDS = {
    "critical": r"\b(data loss|security|cve|crash|production|outage|all users)\b",
    "high": r"\b(regression|broken|cannot|can't|blocks?|fails?)\b",
}

@dataclass
class Issue:
    number: int
    title: str
    body: str = ""
    comments: int = 0
    labels: list = field(default_factory=list)
    age_days: float = 0.0
    url: str = ""

@dataclass
class Triage:
    number: int
    title: str
    kind: str
    severity: str
    score: float
    reasons: list
    url: str = ""

def classify(issue: Issue) -> tuple[str, list]:
    text = f"{issue.title}\n{issue.body}".lower()
    hits = [k for k, rx in KIND_RULES if re.search(rx, text, re.M)]
    existing = [l.lower() for l in issue.labels]
    aliases = {"security": ("security", "vulnerab"), "bug": ("bug", "defect"),
               "docs": ("doc",), "feature": ("feature", "enhancement"), "question": ("question", "support")}
    for k in ("security", "bug", "docs", "feature", "question"):
        if any(a in l for l in existing for a in aliases[k]):
            return k, [f"label '{k}' already set"]
    if not hits:
        return "other", ["no keyword matched"]
    return hits[0], [f"matched '{hits[0]}' keywords"]

def severity(issue: Issue, kind: str) -> str:
    text = f"{issue.title}\n{issue.body}".lower()
    if kind == "security" or re.search(SEV_WORDS["critical"], text):
        return "critical"
    if kind == "bug" and re.search(SEV_WORDS["high"], text):
        return "high"
    if kind in ("bug", "feature"):
        return "medium"
    return "low"

SEV_W = {"critical": 40, "high": 25, "medium": 12, "low": 4}

def score(issue: Issue, sev: str) -> float:
    engagement = min(issue.comments, 20) * 1.5
    staleness = min(issue.age_days, 90) / 9
    return round(SEV_W[sev] + engagement + staleness, 1)

def triage(issues: list[Issue]) -> list[Triage]:
    out = []
    for i in issues:
        kind, why = classify(i)
        sev = severity(i, kind)
        s = score(i, sev)
        why = why + [f"severity {sev}", f"{i.comments} comments", f"{round(i.age_days)} days open"]
        out.append(Triage(i.number, i.title, kind, sev, s, why, i.url))
    return sorted(out, key=lambda t: -t.score)

def to_markdown(repo: str, rows: list[Triage], top: int = 10) -> str:
    lines = [f"# Triage report: {repo}", "", f"{len(rows)} open issues read, top {min(top, len(rows))} below.", ""]
    for r in rows[:top]:
        lines += [f"## #{r.number} {r.title}", f"- kind: {r.kind}", f"- severity: {r.severity}",
                  f"- score: {r.score}", f"- why: {'; '.join(r.reasons)}", f"- link: {r.url}", ""]
    return "\n".join(lines)

def as_dicts(rows):
    return [asdict(r) for r in rows]
