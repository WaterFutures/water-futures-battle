---
layout: default
website_title: Motivation
prev_page_url: /
next_page_url: /participating.html
website_page_authors:
  - D. Zanutto
---

# Introduction

## Disclaimer
The networks and the problem presented in this competition are synthetic and, despite being based on the Netherlands, do not represent any real-world situation.
While we utilize real data from trusted sources where possible (e.g., CBS^[CBS (Centraal Bureau voor de Statistiek) is the Dutch national statistics agency: https://www.cbs.nl] for municipal data, KNMI^[KNMI (Koninklijk Nederlands Meteorologisch Instituut) is the Dutch meteorological institute: https://www.knmi.nl] for weather observations, Vewin^[Vewin is the association of Dutch drinking water companies: https://www.vewin.nl] for statistics about water utilities), other aspects rely on assumptions based on expert knowledge.

We are committed to the model's integrity and, based on competitor feedback, we will continuously test and refine the model (e.g., balancing electricity and infrastructure costs) to ensure it remains physically sound and balanced.
If you identify any significant inconsistencies, please inform us and we will review them promptly.

All versions are archived on Zenodo, with the latest version establishing the official standard [@battle_zenodo].
An open-source evaluator will also be released in the WaterBenchmarkHub [@wbhub], allowing competitors to test their solutions before the final submission.

## Background and motivation

Water distribution systems (WDS) grow organically with cities and are therefore inherently subject to deep uncertainties.
Strategic WDS planning focuses on the long-term design of the primary supply system – the national grid.
While secondary and tertiary network components can typically be selected using established engineering principles, planning the primary and supply network at a regional level requires a different approach, one that integrates policy considerations, standard engineering practice, and substantial investment.
This part of the system is extremely critical. Failures at this level can propagate and lead to loss of service for thousands of people and businesses.
Beyond system reliability and deep uncertainties, the complex governance requirements, such as the coordination between national, regional, and local administrations, present a major obstacle to integrated policy-making and long-term planning of these systems.

Over the past decade, the field has steadily refined and built upon several approaches that address WDS planning under uncertainties.
To begin, the introduction of staged design, where interventions are modelled in phases rather than in a single batch representing the target network, provided a tool to represent masterplans with more realism [e.g., @Creaco_Franchini_Walski_2014].
Next, this modelling framework was extended to include uncertainty, either through a robust approach that accounts for it [e.g., @Creaco_Franchini_Walski_2015], or through a flexible approach that develops a single plan with multiple pathways.
In its simplest form, this takes the shape of a decision tree, where only one branch is implemented based on how uncertainties unfold [e.g., @Basupi_Kapelan_2015].

An inherent limitation of robust and flexible plans is that they require accounting for all possible future system interventions and scenarios at the initial planning stage.
Therefore, when uncertainties move away from the expected values or new opportunities emerge (i.e., under deep uncertainties), these approaches fall short, and the water utilities must adapt to the changes in their environment.

An adaptive plan would typically feature at least one of two components.
The first component involves periodically re-evaluating and adjusting the plan as uncertainties evolve, allowing new opportunities and information to be incorporated.
For example, see @Beh_Maier_Dandy_2015 on water supply systems, and @Skerker_Zaniolo_Willebrand_Lickley_Fletcher_2023 on "the value of learning" in flexible planning for water reservoirs.
The second is the ability to shift between pathways and avoid locking up to one [see dynamic adaptive policy pathways for the Rhine Delta, @Haasnoot_Kwakkel_Walker_ter_Maat_2013].

Regardless of definitions and classifications, the field also lacks coherence in benchmark definition, as none of these approaches have been systematically tested against each other.
At best, works introducing different methodologies may have used the same benchmark networks (e.g., Anytown or New York Tunnels), but the overall problem descriptions—and thus the assumptions and scenarios surrounding these networks—differ substantially.

Therefore, in the context of this Battle of the Water Futures (BWF), **the participants' goal is to apply innovative methodologies to develop a masterplan for a national water grid under deep uncertainties**.
The organisers, in turn, seek to establish a benchmark that advances decision-making practices for water distribution systems under deep uncertainty, while laying the ground for future benchmarking through a highly customizable, open-source framework.

## Ambition

Participants must develop masterplans for a national water grid with water utilities operating across different provinces.
However, the BWF presents a level of detail and computational complexity such that the featured national grid optimisation problem cannot be solved through brute force optimisation.
Moreover, unlike traditional optimisation problems with specified scenarios, here, only a description of the environment dynamics and a handful of expert-driven scenarios for key drivers (e.g., population) are provided.
Competitors must embrace uncertainty and decide for themselves what to model and how to do so, reflecting the reality that different teams would make different modelling choices when facing deep uncertainty.

The decision to place participants in a context of deep uncertainty is intentional.
The BWF will unfold over three competition stages, each spanning 25 years, to realistically emulate the long-term challenges faced by planners. 
This means that some parameters are uncertain and their uncertainty bounds evolution will be provided only through approximate expert-based scenarios (e.g., population projections vary between minimum and maximum values, though actual outcomes may fall outside these bounds).
At the end of each competition stage, past observations will be made available, enabling participants to implement adaptive strategies and learn from accumulated evidence.
Similarly, the competition ranking process has been deliberately left undisclosed; only the system requirements, namely, the metrics under which the system is evaluated, are outlined in this document.
This approach is more akin to realistic situations and compels participants to identify their own compromise solutions within this many-objective context.
