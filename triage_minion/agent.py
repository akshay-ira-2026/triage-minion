"""The OpenMinion agent: tools for reading + scoring issues, structured output for the plan."""
from __future__ import annotations
import argparse, json, sys
from pydantic import BaseModel
from openminion import Agent, ProviderError, tool
from .core import triage, to_markdown, as_dicts
from .github import fetch_open_issues

class TriagePick(BaseModel):
    number: int
    action: str          # e.g. "fix now", "ask for repro", "label docs", "close as duplicate"
    reason: str

class TriagePlan(BaseModel):
    repo: str
    summary: str
    picks: list[TriagePick]

_CACHE: dict = {}

@tool
def scored_issues(repo: str, limit: int = 20) -> str:
    """Read the open issues of a public GitHub repo (owner/name) and return them scored by kind, severity and urgency, highest first, as JSON."""
    rows = triage(fetch_open_issues(repo, limit))
    _CACHE[repo] = rows
    return json.dumps(as_dicts(rows)[:limit])

INSTRUCTIONS = (
    "You are Triage Minion, a maintainer's helper. Always call scored_issues first. "
    "From its JSON, pick the 5 issues a maintainer should act on today and give each a concrete next action "
    "(fix now, ask for a reproduction, add a docs label, close as duplicate, good first issue). "
    "Never invent an issue number that the tool did not return."
)

def run(repo: str, limit: int = 20, model: str | None = None) -> TriagePlan:
    with Agent(instructions=INSTRUCTIONS, tools=[scored_issues], forced_tools=["scored_issues"],
               output_type=TriagePlan, model=model, session_id=f"triage-{repo}") as agent:
        res = agent.run(f"Triage the open issues of {repo} (read up to {limit}).")
    plan = res.output
    known = {r.number for r in _CACHE.get(repo, [])}
    plan.picks = [p for p in plan.picks if p.number in known]   # guard against hallucinated numbers
    return plan

def main(argv=None):
    ap = argparse.ArgumentParser(description="Triage a public GitHub repo's open issues with OpenMinion")
    ap.add_argument("repo"); ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--model"); ap.add_argument("--offline", action="store_true",
                    help="skip the model: print the deterministic scored report only")
    a = ap.parse_args(argv)
    if a.offline:
        print(to_markdown(a.repo, triage(fetch_open_issues(a.repo, a.limit)))); return 0
    try:
        plan = run(a.repo, a.limit, a.model)
    except ProviderError as e:
        print(f"provider failed: {e.code}: {e.message}", file=sys.stderr); return 2
    print(plan.model_dump_json(indent=2)); return 0

if __name__ == "__main__":
    sys.exit(main())
