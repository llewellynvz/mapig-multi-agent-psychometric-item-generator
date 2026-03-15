#!/bin/bash
# gsd-pipeline.sh - Run full phase execution pipeline
# Usage: ./gsd-pipeline.sh <phase-number>
#
# Runs Claude Code in headless mode to execute a GSD phase:
# 1. Reads the phase plan and CONTEXT.md
# 2. Implements in wave-based order
# 3. Commits after each wave
# 4. Uses generator scripts for large files (>100KB)

PHASE=$1

if [ -z "$PHASE" ]; then
  echo "Usage: ./gsd-pipeline.sh <phase-number>"
  exit 1
fi

claude -p "Read planning/phases/phase-${PHASE}/PLAN.md and CONTEXT.md, then execute all requirements in wave-based order. Commit after each wave. Use generator scripts for files >100KB." \
  --allowedTools "Edit,Read,Write,Bash,Glob,Grep,Task" \
  --output-format json \
  | jq '.result'
