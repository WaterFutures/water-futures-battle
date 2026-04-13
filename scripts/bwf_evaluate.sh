#!/usr/bin/env bash
# ─────────────────────────────────────────────
# bwf_evaluate.sh <team> <stage>
#
#   team  : team name, or "historical" for stage 0
#   stage : integer (0, 1, 2, ...)
#
# Example:
#   ./bwf_evaluate.sh historical 0
#   ./bwf_evaluate.sh teamalpha  1
#   ./bwf_evaluate.sh teamalpha  2
# ─────────────────────────────────────────────

# ── CONFIG ───────────────────────────────────
BASE_DIR="."
TEAMS_DIR="${BASE_DIR}/teams"
VENV_PATH="./.venv"
# ─────────────────────────────────────────────

set -euo pipefail

TEAM="${1:-}"
STAGE="${2:-}"

# ── Validate args ─────────────────────────────
if [[ -z "$TEAM" || -z "$STAGE" ]]; then
  echo "Usage: $0 <team|historical> <stage>"
  exit 1
fi

if ! [[ "$STAGE" =~ ^[0-9]+$ ]] || (( STAGE < 0 || STAGE > 3 )); then
  echo "Error: stage must be an integer between 0 and 3 (got: '$STAGE')"
  exit 1
fi

# ── Derive folder and file names ───────────────
if [[ "$STAGE" -eq 0 ]]; then
  RUN_DIR="${BASE_DIR}"
  INPUT_DIR="data"
  MASTERPLAN_FILE="data/masterplan.json"
  RESULTS_DIR="bwf_results-historical_stage"
else
  RUN_DIR="${TEAMS_DIR}/${TEAM}/${STAGE}"
  INPUT_DIR="bwf_inputs-${TEAM}-stage_${STAGE}"
  MASTERPLAN_FILE=$(find "${TEAMS_DIR}/${TEAM}/${STAGE}/" -maxdepth 1 \
    -name "masterplan*" | head -1)
  if [[ -z "$MASTERPLAN_FILE" ]]; then
    echo "Error: no masterplan file found in $INPUT_DIR"
    exit 1
  fi
  RESULTS_DIR="bwf_results-${TEAM}-stage_${STAGE}"
fi
CONFIG_FILE="${TEAMS_DIR}/${TEAM}/${STAGE}/${INPUT_DIR}/configuration.yaml"
CONFIG_FILE="$(realpath "$CONFIG_FILE")"
MASTERPLAN_FILE="$(realpath "$MASTERPLAN_FILE")"

# ── Run ───────────────────────────────────────
echo "──────────────────────────────────────────"
echo " BWF Evaluate"
echo "  Team      : $TEAM"
echo "  Stage     : $STAGE"
echo "  Run from  : $RUN_DIR"
echo "  Input     : $INPUT_DIR"
echo "  Results   : $RESULTS_DIR"
echo "  Solution  : $MASTERPLAN_FILE"
echo "──────────────────────────────────────────"

# shellcheck source=/dev/null
source "${VENV_PATH}/bin/activate"

# Change run directory so logs are saved there
cd $RUN_DIR 

water_futures_battle_run_eval $MASTERPLAN_FILE $CONFIG_FILE

echo ""
echo "✓ Evaluation complete → $RUN_DIR/$RESULTS_DIR"