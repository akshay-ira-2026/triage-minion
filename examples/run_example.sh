#!/usr/bin/env bash
# One working example: a real model-backed triage of OpenMinion's own repo.
set -e
openminion setup --provider cortensor-portal --model oss-20b --no-chat   # needs CORTENSOR_API_KEY
python -m triage_minion.agent openminion/openminion --limit 20
