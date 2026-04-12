---
layout: default
website_title: "Participate 🎯"
prev_page_url: /
next_page_url: /motivation.html
website_page_authors:
  - D. Zanutto
---

# How to participate

On this page you can find the [rules](#participation-rules-), [deadlines](#important-dates-️), [submission](#submitting-a-solution-) and [ranking](#ranking-) procedures.

## Participation rules 🚷

The competition is organized as an __invited session__ at the WDSA/CCWI 2026 conference.
Abstract submission, paper publication, and conference registration will follow the [standard conference procedures](https://www.wdsa-ccwi2026.ucy.ac.cy/call-for-papers/) and [platform](https://cmt3.research.microsoft.com/WDSACCWI2026/).
Solution submission will be handled through a different workflow [explained below](#submitting-a-solution-).

- Participants may submit a solution individually or as part of a team, but **each person can only be included in one team**. 
- **A team is considered formed when an extended abstract** (between 500 and 1000 words) **is submitted** through the conference platform.
The abstract should cover the aim, methodology, and originality of the solution the team intends to develop for the competition.
All individuals listed as authors in the abstract will be considered team members.
- Upon acceptance of the abstract, authors who have not yet registered through the standard conference submission will be able to register for the conference.
**At least one team member must register for the conference and present the work at the event.**
*Teams that do not have at least one registered member will not be considered eligible for the competition.*
- Teams whose abstracts have been accepted and who submit a solution following the competition guidelines **will have the option to submit a full paper (6-8 pages) describing their methodology** to be published in the conference proceedings.
Full papers will be reviewed for quality, and feedback will be sent to authors for any necessary revisions.
Full papers should be submitted in standard A4 paper format, following the template provided on the conference website.

More information about the conference and the abstract and paper submission are available on the [conference website](https://www.wdsa-ccwi2026.ucy.ac.cy/call-for-papers/).

> Authors are encouraged but not required to submit a regular contribution to the conference to participate in the competition.

## Important dates 🗓️

<ul>
<li style="color:lightgray"><em>1st September 2025</em>: Competition announcement and website launch</li>
</ul>

> <span style="color:lightgray">Subscribe for updates and let us know if you are interested in participating!</span>

<ul>
<li style="color:lightgray"><em>8th December 2025</em> - Competition begins: Instructions and first batch of data available</li>
</ul>

<span style="color:lightgray">**Stage 1**</span>
<ul>
<li style="color:lightgray"><strong>14th January 2026</strong>: Abstract submission deadline</li>
<li style="color:lightgray"><em>26th January 2026</em>: Abstract acceptance notifications</li>
<li style="color:lightgray">10th April 2026: First stage solution submission deadline</li>
</ul>

<span style="color:#009344">**Stage 2**</span>
- <span style="color:#DF3737;font-weight:bold">24th April 2026</span>: Second stage solution submission deadline

**Stage 3**
- **1st May 2026 (optional)**: Short paper submission deadline
- **8th May 2026**: Third stage solution submission deadline
- **18th May 2026**: Conference starts! 🎉

## Submitting a solution 📩

Solutions can be submitted in any of the three example formats provided in the data folder (Excel, JSON, or YAML) and must follow the provided template.
Name your masterplan file `"masterplan-{abstractID}-stage_{X}"` (e.g. `"masterplan-000-stage_1"`) and email it to <a href="mailto:battlewaterfutures@kwrwater.nl?subject=Competition Updates">battlewaterfutures@kwrwater.nl</a>  with the relevant details in the subject line (e.g. "Masterplan AbstractID Stage 1").
> Note: the masterplans included in the data folder are for illustrative purposes only, remember to remove those interventions before submittion your solution.

Since every participant enters stages 2 and 3 with a different starting system (shaped by their interventions in previous stages) the following process applies after each round's deadline:
- The stage's exogenous drivers will be shared privately with the teams that provide a correct solution first, then released publicly.
These will be complemented by the results of a "status quo" solution (i.e., a solution run with an empty masterplan, serving as a baseline).
- Each team's official results will be sent back privately by the organisers (possibly within the same week).
Teams should expect to be contacted and remain available to help resolve any errors that may arise during evaluation.
That said, participants don't need to wait and are free to preview their own results at any time by extending their previous stage outputs with the new solution and running their masterplan independently.

While edge cases may be reviewed, clearly mistaken solutions will default to the do-nothing baseline for that stage.
A failing solution in one stage does not disqualify the team, and participants can continue with their own solution from the next stage onwards.
For instructions on how to test your solution locally before submission, see the [how to run scenarios]({{ "evaluator/running-scenarios" | relative_url }}).

## Ranking 📊

Competitor solutions will be evaluated using the four metrics detailed in the problem description: economic performance, environmental impact, reliability, and fairness.

The competition consists of multiple rounds.
The ranking formula will blend weighted aggregation of these metrics with multi-criteria decision-making methods, reflecting changing social priorities and societal perspectives.
This formula may vary between rounds to represent how societal values and priorities shift over time.

To simulate real-world decision-making under deep uncertainty, the exact ranking formula will not be disclosed to participants before each submission deadline.
However, the ranking methodology used will be revealed at the end of each round, before the next submission opens.
The final winner will be announced at the conference.

Despite the multi-objective nature of the challenge, each team must submit a single solution per round, requiring participants to identify their own compromise within this complex decision space.