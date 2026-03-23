---
layout: default
website_title: Changelog 🕑
prev_page_url: /contact.html
next_page_url: /changelog.html
website_page_authors:
  - D. Zanutto
---

# Changelog 🕑

## The Battle of the Water Futures [Data and Software - [v0.5.1](https://doi.org/10.5281/zenodo.17698299)]

**Release Date:* 23rd March 2026

This patch release introduces the calculation of the key variables in the Python library, e.g., capex, debts, etc. 
The data, the problem description (PDF and website), and the rules and information (website) are unchanged.

### What's New

- **Code**
  - Calculate water utilities' results (capex, balance, etc)

### What's Changed

- **Code**
  - Bug fix: bond issuance interest calculation (bond coupon is in percent points)
  - Bug fix: added missing ageing of the inter-utility connections
  - Bug fix: saved epanet networks filenames (now the week number appears in the name)
  - Bug fix: fairness metric calculation (unit of measurement of lifeline volume is L/day/person)
  - Plus other minor bugs
  
### Important Notes

The evaluator is still incomplete.
A future patch releases of the Python library (0.5.x) will add the last missing feature (complete hydraulic simulations and opex).

---

## The Battle of the Water Futures [Data and Software - [v0.5.0](https://doi.org/10.5281/zenodo.19049692)]

**Release Date:* 16th March 2026

This release addresses the community's feedback on the dynamic topology and introduces several new features for the evaluator.
It also fixes the municipality elevation values that were incorrect in the previous release.

### What's New

- **Data**
  - Municipalities: added `main_destination_municipality` column, representing the municipality inheriting the connections/pipes.
  - Connections: added `pipes_decommission_dates`, `replaced_by`, and `replaces` columns to fully describe pipe and connection presence over time.
  - Connections: added `usable_in_2025` column, indicating which connections are available for participant interventions.

- **Code**
  - Export intermediate results for modelled entities (demands, solar yields, etc.)
  - Export EPANET network files with selected week demands or weekly average demands
  - Export peak demands
  - Apply interventions and policies

### What's Changed

- **Data**
  - Municipalities: reduced elevations for some municipalities to improve tractability.
  - Sources: adjusted capacities to better reflect proximity to demand centres.
  - Connections/Pipes: revised pipe options for several connections; disabled connections between high- and low-elevation areas in Gelderland and Limburg.
  - Connections/Pipes: new ID naming convention — IDs below 2000 are defined from the start; IDs between 2000–3000 exist only in the historical period; IDs above 3000 are defined for 2025 onwards.
  - EPANET networks: updated to reflect current values and all possible interventions (disconnected sources are possible future sources, pipes with 0.0001 diameter are possible connections).

- **Problem Description (PDF and Website)**
  - Minor clarifications addressing the most frequently asked questions.
  - Expanded the section on municipality dissolution and connection inheritance.
  - Updated the appendix to reflect input file changes.

- **Rules and Information (Website)**
  - First deadline extended by one week.
  
### Important Notes

The evaluator is still incomplete.
Future patch releases of the Python library (0.5.x) will add the remaining features (e.g. complete hydraulic simulations).

---

## The Battle of the Water Futures [Data and Software - [v0.4.5](https://doi.org/10.5281/zenodo.18550978)]

**Release Date:**9th February 2026

This release introduces a few clarifications and bug fixes based on community reports and the webinar of Friday 23rd January.

### What's New

- **Data**
  - Pipes: added starting friction coefficient for pipes already existing in 2000.
- **Code**
  - Evolve the dynamic properties and save the system status after the evolution.

### What's Changed

- **Data**
  - Connections: Corrected the ages and added the historical period changes.
  - Water prices & Inflation: Historical data now starts in 1999, as prices are adjusted every first of January based on the pricing adjustment policy, which in the historical period was "by_inflation". Thus 'prices in 2000' are 'prices in 1999' by 'inflation in 1999'.
  - Costs: Historical data now starts in 2000. Costs for subsequent years can be obtained by applying inflation.
  (Note: in the previous release, they were reported for year 2025, but were actually for year 2024, as costs in 2025 will depend on inflation in 2025, which is unknown).
  - Minor: The municipalities' associated demand patterns have been formatted like all other exogenous variables (note: in future stages, new patterns may appear and municipalities can be associated with different patterns through this variable).
  - Overall: recalibarated pipe options and sources capacities.

- **Code**  
  - Fix: Corrected Zenodo download and versioning of the data folder.

- **Rules and Information (Website)**
  - Updated the dates to allow for more time in the first stage, as decided during the community webinar on Friday, January 23rd, based on participant feedback.
  
### Important Notes

Youtube channel and Q&A. We will make more videos on how to use the evaluator

---

## The Battle of the Water Futures [Data and Software - [v0.4.0](https://doi.org/10.5281/zenodo.18306233)]

**Release Date:** 19th January 2026

This release introduces a few clarifications and fixes based on community reports and the alpha version of the evaluator.

### What's New

- **Data**
  - Municipalities population: formatted national projections
  - Climate: formatted historical climate variables
  - Submission form: added a new lever for the bonds amount to the debt ratio
  - Settings: added lifeline volume (Lpcd)

- **Code**  
  - New: added the classes describing the system

- **Problem Description (PDF and Website)**
  - New lever: bond to amount debt ratio (Section 2.3.1.4)

### What's Changed

- **Data**
  - Water demand model: fix unit in per business demand (from m^3/business/day to m^3/business/hour)
  - Non-revenue demand model: fix unit of intervention cost (€/km/year), adjusted starting ages (municipalities' average age)

- **Problem Description (PDF and Website)**
  - Fix NRW image (wrong units)
  - Clarified final balance and water pricing
  - Clarified source energy consumption
  - Clarified climate variables  
  - Numbering of the equations
  - Review Appendix A: Describe all files' purposes and a clearer mapping of the properties in the Excel files.

- **Rules and Information (Website)**
  - Clarified participation rules
  - Distinguished the submission process for the solutions and the abstract
  - More details about the ranking and coherence with the problem description

### Important Notes

We are currently working on the evaluator and making sure it is ready to be made open source.  
This will also be used to create the inp networks, as those currently available are only for visualisation purposes.

---

## The Battle of the Water Futures [Data and Software - [v0.3.0](https://doi.org/10.5281/zenodo.18016963)]

**Release Date:** 22nd December 2025

This release introduces a few clarifications and fixes based on community reports Ensure that you update your dataset and review the updated sections.

### What's New

- **Data**
  - Municipalities' average disposable income (historical)
  - Water demand model (properties and historical data)
  - Economy (historical data on inflation and others)
  - Energy system (historical data)
  - Submission form

- **Problem Description PDF**
  - Executive Summary

### What's Changed

- **Data**
  - Sources and pumping stations parameters
  - National INP network (corrected units)

- **Code**  
  - We dedicated significant time making sure all of our synthetic generation algorithms were correctly seeded to maintain the same value across releases

- **Problem Description PDF (and Website)**
  - Clarified the Disposable Income (Sec. 2.1.2) and Fairness metric (2.4.4)
  - Reordered the economy model description, enriched it with equations, and increased details in the bond description
  - Equations all over 
  - Minor: rendering Appendix A and Section 2.3

- **Rules and Information (Website)**
  - Minor: fix broken links and rendering of equations
  - Added Changelog and important info on Home

### Important Notes

We are currently working on the evaluator and making sure it is ready to be made open source.  
This will also be used to create the inp networks, as those currently available are only for visualisation purposes.

---

## The Battle of the Water Futures [Data and Software - [v0.2.0](https://doi.org/10.5281/zenodo.17935475)]

**Release Date:** 15th December 2025

This release is merely a patch release to add the missing file `water_utilities-static_properties` and to give us the opportunity to match the GitHub versions (previously 0.1.0, now 0.2.0) with the Arxiv version (v2, unchanged).

### What's New
- **Data**
  - Added missing file `water_utilities-static_properties.xlsx` describing the provinces assigned to each water utility.

### What Changed
- **Code**
  - The `Makefile` has been changed to also prepare the zip of the data folder to make sure we don't miss files anymore

### What's Unchanged
- **Problem Description PDF and Website**
- **Website Rules and Information**

### Important Notes
We are currently working on the evaluator and making sure it is ready to be made open source.
The submission form is almost ready.

---

## The Battle of the Water Futures [Data and Software - [v0.1.0](https://zenodo.org/records/17860069)]

**Release date**: 8th December 2025

### Competition Release

This releases marks the official start of the competition!

**What's new:**
- Complete problem description (website and PDF versions)
- Initial dataset
- Helpful EPANET inp network files for visualization of the system topology 

**Technical changes in the repository:**
- Website update
- Data files are supplementary material in the release and Zenodo entry

**What to know:**
The problem description is complete but may undergo minor revisions. This initial dataset may change slightly in future releases due to the probabilistic nature of the algorithms used to generate it. Future releases will include additional data with improved formatting.

Please report any missing data so we can confirm whether it was intentionally excluded or inadvertently lost.

---

## The Battle of the Water Futures [Data and Software - [v0.1.0-beta.3](https://zenodo.org/records/17702680)]

**Release Date**: 24th November 2025

### Timeline Update

This release features an update to the competition timeline in the website.

**What's New**:

New timeline, delaying the start of the competition

**Technical Changes**:

Website updates only
No code or data changes in this pre-release

---

## The Battle of the Water Futures [Data and Software - [v0.1.0-beta.2](https://zenodo.org/records/17698487)]

**Release Date**: 15th October 2025

### Website Update

This release features an update to the project website, which now includes information on the team and a new architecture.

**What's New**:

- Added team member profiles and information
- Enhanced content across multiple pages and website architecture
- Added more details about participating in the competition

**Technical Changes**:

- Website updates only
- No code or data changes in this release

---

## The Battle of the Water Futures [Data and Software - [v0.1.0-beta.1](https://zenodo.org/records/17698300)]

**Release Date**: 1st September 2025

### Competition Announcement
We're excited to announce the start of the Battle of the Water Futures!
This initial release marks the public launch of our project website and Zenodo repository.

**What's New**:

Published project website with initial content and structure
Established online presence for the project

**Note**: This is a beta release focused on establishing our web presence and the Zenodo entry. Code and data releases will follow in future versions.