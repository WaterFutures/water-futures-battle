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
The networks and problem presented in this competition are synthetic and do not represent any real-world situation.
While we utilize real data from trusted sources where possible (e.g., CBS for municipal data, KNMI for wheater observations), other aspects rely on assumptions based on expert knowledge.

We are committed to the model's integrity and, based on competitor feedback, we will continuously test and refine the model (e.g., balancing electricity and infrastructure costs) to ensure it remains physically sound and balanced.
If you identify any significant inconsistencies, please inform us and we will review them promptly.

All versions are archived on Zenodo, with the latest version establishing the official standard.
An open-source evaluator will also be released in the WaterBenchmarkHub (Artelt, 2025), allowing competitors to test their solutions before the final submission.

## Background and motivation

Water distribution systems (WDS) grow organically with cities and are therefore inherently subject to deep uncertainties.
While secondary and tertiary network components can still be adequately selected using established engineering principles, planning the primary and supply network at a regional level requires a different approch that integrates elements of policy-making, standard engineering practice and considerable investments.
This part of the system is extremely critical as failures here can propogate and lead to loss of service for thousands of people and businesses.
Beyond system reliability and deep uncertainties, the complex governance requirements, such as the coordination between national, regional, and local administrations, present a major obstacle to integrated policy-making and long-term planning of these systems.

Over the past decade, the field has steadily refined and built upon several approaches that address WDS planning under uncertainties.
To begin, the introduction of staged design, where interventions are modeled in phases rather then in as single batch representing the target network, provided a tool to represent long-term plans with more realism (for an example on WDS see Creaco et al., 2014).
Next, this modeling framework was extended to include uncertainty, either through a robust approach that accounts for uncertainty (e.g., Creaco et al., 2015), or through a flexible approach where one plan with multiple pathways (in its simplest form: a decision tree) is devised, but only one branch is implemented based on the uncertainties realisation (e.g., Basupi and Kapelan, 2015).

An inherent limitation of robust and flexible plans is that they require accounting for all possible future system interventions and scenarios at the initial planning stage.
Therefore, when uncertainties move away from the accounted values or new opportunities emerge (i.e., under deep uncertainties), these approaches fall short: the water utilities must adapt to the changes in their environment.

An adaptive plan would typically feature at least one of two components.
The first is a periodic re-evaluation and adjustment of the plan based on uncertainty evolution to incorporate new opportunities and information (see, for an example, Beh et al., (2017) on water supply systems, and Skerker et al., (2023) on "the value of learning" in flexible planning for water reservoirs).
The second is the ability to shift between pathways and avoiding locking-up to one (see dynamic adaptive policy pathways for the Rhine Delta, Haasnoot et al., 2013).

Regardless of definitions and classifications, the field also lacks coherence in benchmark definition, as none of these approaches have been systematically tested against each other.
At best, works introducing different methodologies may have used the same benchmark networks (e.g., Anytown or New York Tunnels), but the overall problem descriptions—and thus the assumptions and scenarios surrounding these networks—differ substantially.

Therefore, in the context of the Battle of the Water Futures, the participants' goal is to apply novel methodologies to develop masterplans for a nation's water utilities under deep uncertainties; while the orgainsers objective is to provide a benchmark that advances the state of practice in decision-making under deep uncertainty for water distribution systems and establishes a foundation for benchmarking through a highly customizable, open-source framework.

## Ambition

Participants must develop masterplans for a nation's water utilities operating across different provinces.
However, the BWF presents a level of detail and computational complexity such that the featured transport network optimization problem cannot be solved through brute force optimization.
Moreover, unlike traditional optimization problems with specified scenarios, here, only a description of the environment dynamics and a handful of expert-driven scenarios for key drivers (e.g., population) are provided.
Competitors must embrace uncertainty and decide for themselves what to model and how, reflecting the reality that different teams would make different modeling choices when facing deep uncertainty.

The decision to place participants in a situation of deep uncertainty is deliberate.
While some parameters are uncertain and the evolution of these uncertainty bounds in the future will not be disclosed (e.g., the annual cost of operating a production facility, which varies between minimum and maximum values), past observations will be made available at the end of each competition stage, enabling participants to implement adaptive strategies and learn from accumulated evidence.
Similarly, the competition ranking process has not been announced, only the system requirements are explained in this document (i.e., the metrics under which the system is evaluated), compelling participants to identify their own compromise solutions within this many-objective context.
