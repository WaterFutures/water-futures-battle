# Non-Revenue Water Model

## Overview

Non-revenue water (NRW) is modelled as an uncertain quantity based on the average age of pipes in each municipality's inner distribution network (IDN). Based on this age, municipalities are assigned to one of five NRW classes. Each class has a distinct probability distribution from which daily NRW demand factors are sampled ($m^3/km/day$). Older infrastructure generally has more leaks and therefore higher NRW demand.

## Raw Data

### Assumptions

NRW class bounds are based on the average age of a municipality's inner distribution network.

### Vewin 

[Vewin](https://www.vewin.nl/) is the national association of water companies in the Netherlands.

Key figures on annual NRW and investment budgets from [Vewin's 2022 report](https://www.vewin.nl/wp-content/uploads/2024/06/vewin-dutch-drinking-water-statistics-2022-eng-web.pdf) are used approximately
to calibrate the NRW model parameters.

## Preprocessing Scripts for Initial Dataset Generation

### Dynamic Properties

The notebook [`nrw_model-dynamic_properties-generator.ipynb`](./preprocessing-scripts/nrw_model-dynamic_properties-generator.ipynb) 
generates the initial unit cost for NRW mitigation.
The starting values were manually calibrated against the figures in the Vewin report.

## Initial Dataset Structure

**Table 1**: Overview of the NRW model properties.

| File | Sheet | Property | Unit | Type | Uncertainty treatment | Probability distribution | Dimension(s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `configuration.yaml` | `nrw_model` | Success factor of NRW mitigation intervention `intervention_success_prob`| - | Static | Uncertain | Uniform (`[min,max]`) | Global |
| `nrw_model-dynamic_properties.xlsx` | `nrw_intervention-unit_cost` | Unit cost of NRW mitigation intervention | $€/year/km$ | Dynamic Endogenous | Deterministic | | Time $\times$ State $\times$ NRWClass $\times$ MunicipalitySizeClass |

## The Narrative

This module has no independent narrative because it contains no dynamic exogenous variables.
