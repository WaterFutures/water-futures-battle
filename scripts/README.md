# Scripts

This folder contains helper scripts used by the organisers to run the Water Futures Battle competition, prepare the staged input databases, rank participant solutions, and build the released documentation/data artifacts.

Most users do not need these scripts to evaluate a single masterplan. After installing the `water_futures_battle` package, the canonical evaluator command is:

```bash
water_futures_battle_run_eval "$MASTERPLAN_FILE" "$CONFIG_FILE"
```

From the repository root, this works out of the box when there is a `data/` folder containing `configuration.yaml` and the referenced input files. For example:

```bash
water_futures_battle_run_eval data/masterplan.json data/configuration.yaml
```

The shell scripts in this folder wrap that command for the competition's organiser workflow, where team submissions and stage outputs are stored in a fixed folder structure.

## Expected Organiser Layout

The organiser scripts assume they are run from the repository root and that team data are organised like this:

```text
teams/
  TEAM01/
    1/
      masterplan.*
      bwf_inputs-TEAM01-stage_1/
        configuration.yaml
        ...
      bwf_results-TEAM01-stage_1/
        ...
    2/
      masterplan.*
      bwf_inputs-TEAM01-stage_2/
      bwf_results-TEAM01-stage_2/
    3/
      masterplan.*
      bwf_inputs-TEAM01-stage_3/
      bwf_results-TEAM01-stage_3/
```

The helper scripts also assume the project virtual environment is available at `.venv/` unless the script is edited.

## Script Overview

| Script | Purpose | Typical use |
| --- | --- | --- |
| `bwf_evaluate.sh` | Evaluates one team masterplan for one stage. It discovers the stage masterplan, resolves the stage input `configuration.yaml`, activates `.venv`, and calls `water_futures_battle_run_eval`. | Organiser automation for repeated team/stage evaluation. |
| `bwf_prepare.sh` | Builds the next staged input database for a team. It starts from the previous stage results, runs the module-specific stage extender scripts shipped under `data/**/preprocessing-scripts/`, copies unchanged files, updates `configuration.yaml`, writes `VERSION`, and adds the stage narrative. | Preparing `bwf_inputs-TEAM-stage_N` before releasing a new stage to a team. |
| `bwf_rank.py` | Loads all completed team results, computes the competition metrics and rankings, applies the stage priority weights, and plots the perception scatter figure. | Reproducing or inspecting the final BWF competition ranking. |
| `estimate_fixed_costs.py` | Estimates water utility fixed costs from the do-nothing `TEAM00` results for a stage. | Organiser calibration step used for stages 2 and 3. |
| `extend_my_results.py` | Extends a results database into a minimal next-stage input database by repeating the latest required annual values. | Quick business-as-usual or exploratory scenarios where detailed stage extender data are not needed. |
| `generate_authors_tex.py` | Converts `teams/authors_info.xlsx` into `authors.tex`, `authors_credit.tex`, and `authors.md`. | Regenerating the paper author and credit lists. |
| `scale_stage_1_balances.py` | Rescales stage-1 final water utility balances to remove the competition cash surplus. | Reproducibility only; this was an organiser-side adjustment during the competition. |
| `Makefile` | Builds release artifacts: data zip, LaTeX source, PDF specification, and the Jekyll/GitHub Pages website. | Release packaging and documentation builds. |

## Common Workflows

### Evaluate a Single Masterplan

Use the package command directly when you already know the masterplan and configuration files:

```bash
water_futures_battle_run_eval path/to/masterplan.json path/to/configuration.yaml
```

The evaluator writes a results folder next to the input data folder. If `scenario_name` is set in `configuration.yaml`, the output folder is named `bwf_results-<scenario_name>`.

### Evaluate a Team Stage

Use the organiser wrapper when the team follows the expected `teams/TEAMID/stage/` layout:

```bash
./scripts/bwf_evaluate.sh TEAM01 1
```

For stage `1`, the script expects:

- `teams/TEAM01/1/bwf_inputs-TEAM01-stage_1/configuration.yaml`
- one `masterplan*` file directly under `teams/TEAM01/1/`

The same pattern applies for stages `2` and `3`.

### Prepare the Next Stage Inputs

After a team stage has been evaluated, prepare the next input database with:

```bash
./scripts/bwf_prepare.sh TEAM01 2
```

The stage argument is the stage to create. For stage `1`, the script starts from `bwf_results-historical_stage`. For stages `2` and `3`, it starts from the team's previous stage results:

```text
teams/TEAM01/1/bwf_results-TEAM01-stage_1  ->  teams/TEAM01/2/bwf_inputs-TEAM01-stage_2
teams/TEAM01/2/bwf_results-TEAM01-stage_2  ->  teams/TEAM01/3/bwf_inputs-TEAM01-stage_3
```

The preparation script is more than a copy operation. It uses the preprocessing scripts in the `data/` folder to append the exogenous data for the new stage, then updates the new stage `configuration.yaml` so it points to the stage-specific files.

This workflow is not a general-purpose future generator. The stage length, random seeds, scenario parameters, and module-specific assumptions are encoded directly in the stage extender scripts under `data/**/preprocessing-scripts/`, and `bwf_prepare.sh` calls a fixed list of those scripts in a fixed order. To generate a different future, change the stage duration, or alter assumptions, those module scripts and possibly this wrapper need to be edited manually. The script is included mainly to document and reproduce the staged workflow used during the competition.

### Rank Completed Teams

Once all stages have been evaluated for the teams in `teams/`, run:

```bash
python scripts/bwf_rank.py
```

The ranking script expects the organiser folder structure and reads each team's `metrics.xlsx` files plus the dynamic municipality population data needed for weighted perceptions. It is kept here both for reproducibility of the competition ranking and as a reference for alternative ranking analyses.

### Estimate Fixed Costs

The organisers used `estimate_fixed_costs.py` during stages 2 and 3 to estimate water utility fixed costs from the `TEAM00` do-nothing results. The workflow was:

1. Run `TEAM00` once without fixed costs.
2. Run the fixed-cost estimation script on those results.
3. Use the generated `cost_normalisation-stage_N.csv` values.
4. Re-run `TEAM00` and then continue with the rest of the teams.

```bash
python scripts/estimate_fixed_costs.py 2
python scripts/estimate_fixed_costs.py 3
```

### Extend Results for a Minimal Next-Stage Scenario

`extend_my_results.py` is useful for quick business-as-usual scenarios. It modifies a results/input folder in place by repeating the latest annual value for variables that must have a value every year in the next stage.

```bash
python scripts/extend_my_results.py path/to/bwf_results-or-input-folder
```

The script intentionally does the bare minimum. Some variables, such as electricity unit costs, are not extended because the evaluator can reuse the latest available value automatically. The script prompts before overwriting files; make a backup before using it.

### Build Release Artifacts

The `Makefile` packages the released data and documentation artifacts:

```bash
cd scripts
make data
make latex
make pdf
make website
```

The PDF specification and the website are built from the same documentation source files. The `preprocess-html` target creates intermediate HTML files used by the Jekyll/GitHub Pages website build.

## Notes

- Run the scripts from the repository root unless a command explicitly changes into `scripts/` first, such as the `make` commands above.
- These scripts are operational helpers, not the stable public API. For a single evaluation, prefer `water_futures_battle_run_eval`.
- Several scripts overwrite generated data. Keep a copy of important team results or input databases before running preparation, extension, or balance-scaling scripts.