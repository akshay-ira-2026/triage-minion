# Triage Minion

An [OpenMinion](https://www.openminion.com) agent for Cortensor Hackathon #5 that reads a public GitHub repo's open issues, scores them, and hands a maintainer the 5 to act on today, each with a concrete next step.

## How it works
1. `scored_issues` (an OpenMinion `@tool`) reads open issues from the GitHub REST API and scores each one by kind (bug, security, docs, feature, question), severity and urgency (comments, age).
2. The agent is forced to call that tool first, then returns a typed `TriagePlan` (Pydantic `output_type`).
3. Any issue number the model returns that the tool never saw is dropped, so the plan can't point at made-up issues.

## Setup
```bash
pip install -e .
export CORTENSOR_API_KEY=...            # Cortensor Portal
openminion setup --provider cortensor-portal --model oss-20b --no-chat
openminion doctor --check-turn
```
Any OpenMinion provider works (`--provider mistral`, `groq`, `openrouter` ...).

## Run
```bash
triage-minion openminion/openminion --limit 20          # model-backed plan (JSON)
triage-minion openminion/openminion --offline           # deterministic scored report, no model
```

## Tests
```bash
pip install pytest && pytest -q
```

## License
Apache-2.0
