# Masterplans

This folder contains small example and reference masterplans that can be passed to the evaluator with a BWF configuration file:

```bash
water_futures_battle_run_eval masterplans/masterplan-empty.yaml data/configuration.yaml
```

The masterplan file defines the policies and interventions to apply during the simulation. Historical baseline policies are added automatically by the parser, so a masterplan can contain only the future changes that should be tested.

## Files

| File | Purpose |
| --- | --- |
| `masterplan-empty.yaml` | Empty masterplan. This is useful for do-nothing or baseline runs where no additional future interventions are applied beyond the default historical masterplan included by the package. It is also TEAM00 reference masterplan used during the competition for stage 1.|
| `masterplan-TEAM00-stage_2.yml` | TEAM00 reference masterplan used during the competition for stage 2. It only updates the NRW water mitigation budget every 5 years based on the inflation. |
| `masterplan-TEAM00-stage_3.yml` | Same as stage 2. |
| `masterplan-interconn.yaml` | Minimal masterplan used to test national interconnection interventions by installing selected national pipes. |

The TEAM00 files are kept for competition reproducibility. Together with the empty/do-nothing baseline pattern, they document the reference masterplans used for the staged TEAM00 evaluations.

## Usage Notes

- Use these files as examples of valid YAML masterplan structure.
- For a normal single run, pair one masterplan with the relevant stage input `configuration.yaml`.
- Since policies stay in place until amended, running an empty masterplan or a masterplan that doesn't specify some policies, will result to using the [default policies](../src/water_futures_battle/masterplan/default_historical_data.py), i.e., those defined for the historical period.
- These files are examples and reproducibility artifacts; they are not required for using the package API directly.