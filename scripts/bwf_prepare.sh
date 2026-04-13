#!/usr/bin/env bash
# ─────────────────────────────────────────────
# bwf_prepare.sh <team> <stage>
#
#   Appends new data and builds the input folder
#   for the NEXT stage, from the current stage's
#   input + results.
#
#   team  : team name
#   stage : integer (1, 2, 3)
#
# Example:
#   ./bwf_prepare.sh teamalpha  1   → builds bwf_inputs-teamalpha-stage_1
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

if ! [[ "$STAGE" =~ ^[0-9]+$ ]] || (( STAGE < 1 || STAGE > 3 )); then
  echo "Error: stage must be an integer between 1 and 3 (got: '$STAGE')"
  exit 1
fi

PREV_STAGE=$((STAGE - 1))

# ── Derive folder names ───────────────────────
TEAM_DIR="${TEAMS_DIR}/${TEAM}"
STAGE_DIR="${TEAM_DIR}/${STAGE}"
STAGE_INPUT_DIR="${STAGE_DIR}/bwf_inputs-${TEAM}-stage_${STAGE}"
if [[ "$STAGE" -eq 1 ]]; then
  PREV_STAGE_RESULTS_DIR="${BASE_DIR}/bwf_results-historical_stage"
else
  PREV_STAGE_RESULTS_DIR="${TEAM_DIR}/${PREV_STAGE}/bwf_results-${TEAM}-stage_${PREV_STAGE}"
fi

# ── Run ───────────────────────────────────────
echo "──────────────────────────────────────────"
echo " BWF Prepare Next Stage"
echo "  Team           : $TEAM"
echo "  Stage          : $STAGE"
echo "  Prev. Results  : $PREV_STAGE_RESULTS_DIR"
echo "  New System     : $STAGE_INPUT_DIR"
echo "──────────────────────────────────────────"

# shellcheck source=/dev/null
source "${VENV_PATH}/bin/activate"

# Make all these directories inside the new input directory to reproduce the same
# status as in data/
DIRS=(
  "climate" "connections" "economy" "energy" "jurisdictions" "nrw_model" "pipes"
  "pumping_stations" "pumps" "sources" "water_demand_model" "water_utilities"
)

mkdir -p "${DIRS[@]/#/$STAGE_INPUT_DIR/}"

# Define list of (folder, name) pairs that we will run the stage extender on
declare -a PARTS=(
  "economy economy-dynamic_properties"
  "energy energy-dynamic_properties"
  "climate climate-dynamic_properties"
  ". municipalities_related-static_properties"
  "jurisdictions municipalities-dynamic_properties"
  ". sources_related-static_properties"
  "sources sources-dynamic_properties"
  "pipes pipe_options-dynamic_properties"
  "water_demand_model water_demand_model-dynamic_properties"
)

for PART in "${PARTS[@]}"; do
  set -- $PART
  FOLDER=$1
  NAME=$2
  python "data/${FOLDER}/preprocessing-scripts/${NAME}-stage_extender.py" "$STAGE" "$PREV_STAGE_RESULTS_DIR" "$STAGE_INPUT_DIR"
done

# Complete the folder copying the files that don't get extended
FILES_TO_COPY=(
  #connections (nothing)
  
  #economy
  "economy/bonds-static_properties.xlsx"

  #energy
  "energy/solar_farms-static_properties.xlsx"

  #jurisdictions (nothing)

  #nrw_model
  "nrw_model/nrw_model-dynamic_properties.xlsx"

  #pipes
  "pipes/pipe_options-static_properties.xlsx"
  "pipes/pipes-dynamic_properties.xlsx"
  
  #pumping_stations
  "pumping_stations/pumping_stations-static_properties.xlsx"

  #pumps
  "pumps/pump_options-dynamic_properties.xlsx"
  "pumps/pump_options-static_properties.xlsx"

  #sources
  "sources/desalination-dynamic_properties.xlsx"

  #water_demand_model
  "water_demand_model/water_demand_model-static_properties.xlsx"

  #water_utilities
  "water_utilities/water_utilities-static_properties.xlsx"
  "water_utilities/water_utilities-dynamic_properties.xlsx"
)

for FILE in "${FILES_TO_COPY[@]}"; do
  cp "$PREV_STAGE_RESULTS_DIR/$FILE" "$STAGE_INPUT_DIR/$FILE"
done

# Copy the configuration file and updating it with the new filenames
cp "$PREV_STAGE_RESULTS_DIR/configuration.yaml" "$STAGE_INPUT_DIR/configuration.yaml"
python "data/preprocessing-scripts/update_configuration.py" "$STAGE_INPUT_DIR" "$STAGE" "$TEAM"

# Add a custom version file for this new stage
echo "1.${STAGE}.0" > "${STAGE_INPUT_DIR}/VERSION"

# Add the narrative file for readme purposes
cp "data/bwf_narrative-stage_${STAGE}.md" "${STAGE_INPUT_DIR}"

# and finally remove the temp files
rm ${STAGE_INPUT_DIR}/connections/connections-static_properties-temp.xlsx

echo ""
echo "✓ Next stage input ready → $STAGE_INPUT_DIR"
echo ""
echo "  To release results to $TEAM   : $PREV_STAGE_RESULTS_DIR"
echo "  To release next input to $TEAM: $STAGE_INPUT_DIR"