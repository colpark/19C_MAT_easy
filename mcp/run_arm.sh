#!/bin/bash
# usage: ./run_arm.sh <a0|a1|a2> <tasks dir> [extra harbor args, e.g. -i <task> -k 1 -o <dir>]
# Exports the OpenRouter key (never written to files) and the judge model, then runs harbor with the arm's job config.
set -euo pipefail; cd "$(dirname "$0")"
source /home/aid1/Documents/harbor/v024/.env.openrouter
export LLM_API_KEY="$OPENROUTER_API_KEY" JUDGE_MODEL="${JUDGE_MODEL:-openai/gpt-5-mini}" PATH=$HOME/.local/bin:$PATH
ARM=$1; TASKS=$2; shift 2
exec harbor run -c jobs/$ARM.yaml -p "$TASKS" -y "$@"
