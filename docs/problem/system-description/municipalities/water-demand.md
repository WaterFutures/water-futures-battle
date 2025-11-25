---
layout: default
website_title: Water Demand Model
parent: /problem/system-description/municipalities
parent_title: Municipalities
prev_page_url: /problem/system-description/municipalities/
next_page_url: /problem/system-description/municipalities/nrw.html
website_page_authors:
  - S. Alvisi
  - V. Marsili
  - F. Mazzoni
  - D. Zanutto
---

#### Water Demand Model

The methodology developed to generate water consumption time series builds on historical data from the Dutch Drinking Water Statistics (Vewin, 2022), which provide nationwide trends in total drinking water production, sectoral water use, and non-revenue water over the period 2000–2024. Specifically, water-consumption time series generation is structured into three phases.

Phase I. The first phase estimates the annual water volume supplied to each municipality using information on households, and businesses, complemented by projected data where required. These annual volumes are calibrated to match national totals reported in official statistics and then randomized around the calibrated value to introduce variability among municipalities.

Phase II. In the second phase, representative hourly consumption profiles are assigned to each municipality using a library of year-long, normalized profiles derived from district-metered areas and pre-processed to remove leakage effects. In greater detail, for each municipality, two residential profiles are selected from the library according to municipality population class, while a single non-residential profile is drawn from a dedicated set.

Phase III. The third phase produces the final hourly time series by applying a Fourier series-based approach which combines seasonal modulation, climate-related adjustments, and random perturbations to capture temporal variability. The two residential profiles associated with each municipality are aggregated through weighted combinations, and both residential and non-residential profiles are scaled to match the previously estimated yearly volumes. The outcome is a set of 8,760-point hourly water consumption series for each municipality. 


