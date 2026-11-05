# Helpers for loading the post-battle MS Forms survey and the teams'
# author/affiliation info, for use in the journal article's images.

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

SURVEY_RESPONSES_FILE = "survey_responses.xlsx"


@dataclass
class Question:
    """
    Base class for a survey question. `prefix` is matched against the start
    of the (long) question text in the survey header. Subclasses override
    `parse` to turn the raw cell value into whatever shape is most useful
    for that question type.
    """
    prefix: str

    def parse(self, raw: Any) -> Any:
        return raw
    
    @property
    def categories(self) -> None:
        return None


@dataclass
class OpenQuestion(Question):
    """Free-text answer, returned as-is."""
    
    def parse(self, raw: Any) -> Any:
        raw = str(raw)
        return raw if raw != "nan" else ""


def _match_option(
    value: str, options: dict[str, str], question_prefix: str, has_other: bool = False
) -> str:
    matches = [label for prefix, label in options.items() if value.startswith(prefix)]

    if not matches:
        if has_other:
            # "Other" comes with a free-text bucket in the form; whatever
            # the respondent typed becomes its own (unrecognized) category.
            return value
        raise ValueError(
            f"No matching option for answer {value!r} to question {question_prefix!r}; "
            f"expected one starting with one of {list(options)}"
        )
    if len(matches) > 1:
        raise ValueError(
            f"Ambiguous answer {value!r} for question {question_prefix!r}, "
            f"matches multiple option prefixes: {matches}"
        )
    return matches[0]


@dataclass
class ChoiceQuestion(Question):
    """
    Single-choice answer. `options` maps a prefix of the full (long) answer
    text to a short label suitable for chart ticks/legends, e.g.
    {"< 160 h": "<160 h", ...}. The full wording can be spelled out in a
    figure caption instead of in code. If no options are given, the raw
    answer is returned unchanged. If `has_other` is set, an answer matching
    none of `options` (i.e. the form's free-text "Other" bucket) is not an
    error: it is returned as its own (unrecognized) category, verbatim. If
    `optional` is set, a blank/NaN answer (the question was skippable) is
    not an error either: it is returned as `None` and left out of
    `categories`.
    """
    options: dict[str, str] = field(default_factory=dict)
    has_other: bool = False
    optional: bool = False

    def parse(self, raw: Any) -> str | None:
        value = str(raw).strip()
        if self.optional and value == "nan":
            return None
        if not self.options:
            return value
        return _match_option(value, self.options, self.prefix, self.has_other)

    @property
    def categories(self) -> list[str]:
        return list(self.options.values())


@dataclass
class MultiChoiceQuestion(Question):
    """
    Multiple-choice answer (MS Forms joins selections with ';'). `options`
    maps a prefix of each full answer text to a short label, same as
    ChoiceQuestion. `has_other` behaves the same as in ChoiceQuestion, applied
    independently to each selected value.
    """
    options: dict[str, str] = field(default_factory=dict)
    delimiter: str = ";"
    has_other: bool = False

    def parse(self, raw: Any) -> list[str]:
        values = [v.strip() for v in str(raw).split(self.delimiter) if v.strip()]
        if not self.options:
            return values
        return [_match_option(v, self.options, self.prefix, self.has_other) for v in values]


@dataclass
class LikertQuestion(Question):
    """
    Likert-scale matrix question: MS Forms exports one column per row of
    the matrix, each column header starting with the common `prefix` and
    then naming its row. `options` maps a substring identifying each row's
    column header to a short label, same convention as ChoiceQuestion's
    `options`. If `scale` is given (answer label -> ordinal value), each
    parsed answer is mapped to its numeric value; otherwise the raw label
    is returned unchanged.
    """
    options: dict[str, str] = field(default_factory=dict)
    scale: dict[str, str] = field(default_factory=dict)

    def parse(self, raw: Any) -> str:
        value = str(raw).strip()
        if not self.scale:
            return value
        return _match_option(value, self.scale, self.prefix)

    @property
    def categories(self) -> list[str]:
        return list(self.scale.values())

@dataclass
class ScoreQuestion(Question):
    """
    Numeric score answer, an integer from 0 to 10 (inclusive).
    """

    def parse(self, raw: Any) -> int:
        value = int(raw)
        if not 0 <= value <= 10:
            raise ValueError(
                f"Score answer {value!r} for question {self.prefix!r} out of range [0, 10]"
            )
        return value

    @property
    def categories(self) -> list[int]:
        return list(range(11))


# Maps a short, code-friendly attribute name to the Question describing
# where to find it (prefix of the full question text) and how to parse it.
# Extend this as more questions are needed.
QUESTIONS: dict[str, Question] = {
    ### Section 1
    "authors_background": LikertQuestion(
        prefix="",
        options={
            "Civil engineering": "Civil Eng.",
            "Control or electrical engineering": "Control & Electrical Eng.",
            "Data science/ML/AI": "Data Science & AI",
            "Economics/finance": "Economics",
            "Computer science/software engineering": "Computer Science",
            "Social sciences": "Social Sciences",
            "Hydrology/water resources/environmental engineering": "Environmental Eng.",
            "Other": "Other",
        },
        scale={
            "0 - nobody": "0 - nobody",
            "1 or 2": "1 or 2",
            "3 or 4": "3 or 4",
            "5 or more": "5 or more",
        }
    ),
    "authors_expertise": LikertQuestion(
        prefix="",
        options={
            "Hydraulic modelling (e.g., EPANET)": "Hydraulic mod.",
            "Water distribution system design optimisation": "WDS design",
            "Water distribution system operations optimisation": "WDS operation",
            "Water demand modelling": "Demand mod.",
            "Non-revenue water modelling": "NRW mod.",
            "Water policy and regulation": "Policy-making",
            "Water supply planning": "Supply planning",
            "Planning under uncertainty/DMDU (not limited to WDS)": "DMDU",
            "Multi-objective optimization (not limited to WDS)": "MO optimisation",
            "Climate/hydrological modelling": "Hydroclimatic mod.",
            "Financial modelling/economics": "Financial mod.",
            "Energy systems modelling": "Energy systems mod.",
            "Data science and ML": "AI",
            "Scripting (Python/Matlab/R)": "Scripting",
            "Software engineering (building structured codebases)": "Coding",
        },
        scale={
            "None": "None",
            "Isolate": "Isolated",
            "Partial": "Partial",
            "Strong": "Strong",
            "Deep": "Deep",
        }
    ),
    "time_spent": ChoiceQuestion(
        prefix="What was the approximate total number of hours",
        options={
            "< 160 h": "<160 h",
            "160-480 h": "<480 h",
            "480-800 h": "<800 h",
            "800-1600 h": "<1600 h",
            "> 1600 h": ">1600 h",
        }
    ),
    "token_usage": ChoiceQuestion(
        prefix="How many tokens",
        options={
            "We used them, but": "Unknown",
            "We did not": "Not used",
            "< 1 M tokens": "<1M",
            "1-10 M tokens": "<10M",
            "10-100 M tokens": "<100M",
            "> 100 M tokens": ">100M",
        }
    ),

    ### Section 2
    "methodology_categories": MultiChoiceQuestion(
        prefix="Which of the following best describes the core method",
        options={
            "Scenario-based/multi": "Scenario-based opt.",
            "Robust optimisation": "Robust opt.",
            "Flexible/staged design": "Flexible opt.",
            "Dynamic Adaptive Policy Pathways": "DAPP",
            "Many-Objective Robust": "MORDM",
            "Multi-objective evolutionary algorithms": "MOEA",
            "Mathematical programming": "LP/MILP/NLP",
            "Reinforcement learning": "RL",
            "Model Predictive Control": "Rolling-horizon opt.",
            "Rule-based": "Rule-based",
            "Exploratory modelling": "Simulation Screening",
            "AI-agent-driven": "AI agent driven design",
        },
        has_other=True
    ),
    "autonomousness": ScoreQuestion(
        prefix="Where would you place your overall methodology on this scale, from fully engineer-driven to fully autonomous?",
    ),
    "approach_sequence": ChoiceQuestion(
        prefix="Which approach below best describes how your team organised decisions between the national level",
        options={
            "Single national": "Global optimisation",
            "National decisions first, then the 10 WU plans were developed jointly/coordinated": "National,<br>then WUs jointly",
            "National decisions first, then the 10 WU plans were developed independently": "National,<br>then WUs independently",
            "The 10 WU plans were": "WUs independently,<br>then national coordination",
        }
    ),
    "_levers_groups": LikertQuestion(
        prefix="", #"For each sub-problem"
        options={
            "Non-Revenue Water": "NRW mitigation",
            "Water supply (opening": "WRS",
            "Water distribution (pipe and": "WDS",
            "Solar PV installation": "Solar installation",
            "Water pricing": "WPA",
            "Bond market": "Bond market<br>exposure",
            "National budget": "National budget<br>allocation",
        },
        scale={
            "Group A": "1",
            "Group B": "2",
            "Group C": "3",
            "Group D": "4",
            "Group E": "5",
            "Group F": "6",
            "Not actively": "nan",
        }
    ),
    "hydraulics_reliance": ChoiceQuestion(
        prefix="Did your methodology involve hydraulic simulations",
        options={
            "No, never - hydraulic feasibility of the transport network was omitted": "Omitted",
            "No, never - hydraulic feasibility of the transport network was modelled differently": "Differently",
            "Implicitly": "Implicitly",
            "Explicitly, but simplified": "Explicitly (simplified)",
            "Explicitly and fully": "Explicitly (fully)"
        }
    ),
    "deep_unc_model": LikertQuestion(
        prefix="", # For each of the followin groups of exogenous deep uncertainties
        options={
            "Municipality properties": "Municipalities",
            "Economy (inflation": "Economy",
            "Energy system (ele": "Energy system",
            "Climate\xa0": "Climate",
            "Surface water availability": "Surface water availability",
            "Water demand base-consumption": "Water demand base-consumption"
        },
        scale={
            "Left as is (Business as usual)": "Left as is",
            "Expert-driven scenario (Manually defined by the team)": "Expert-driven scenario",
            "Simple predictive model (e.g. trend extrapolation, sampling)": "Simple predictve model",
            "Advanded statistical/ML predictive model (e.g. XGBoost, LSTM)": "Advanced predictive model"
        }
    ),
    "scenario_combination": ChoiceQuestion(
        prefix="How did your team combine",
        options={
            "We used a single combined scenario": "Single (manual)",
            "We carefully crafted a small number (2-5)": "A few (manual)",
            "We employed automated techniques to generate a": "A lot (automatic)"
        }
    ),
    "scenario_handling": ChoiceQuestion(
        optional=True,
        prefix="Which approach below is most similar to your team's way of handling scenarios?",
        options={
            "One masterplan per scenario, then some heuristics": "For optimisation",
            "One masterplan per scenario, then stress-tested": "For optimisation<br>&<br>stress-test",
            "One robust masterplan considering": "For robust<br>optimisation",
            "One or more masterplans": "For stress-test"
        }
    ),
    "residual_use": ChoiceQuestion(
        prefix="At the start of Stage 2 and Stage 3, past observations",
        options={
            "We did not use the residual explicitly": "Omitted",
            "We used the residual qualitatively": "Qualitative use",
            "We used the residual to automatically": "Quantitative use"
        }
    ),
    "param_unc_model": LikertQuestion(
        prefix="", # For each of the following parametric
        options={
            "Water demand variability": "Water demand variability",
            "Solar PV production variability": "Solar PV production variability",
            "New source construction time": "New source construction time",
            "NRW interventions effectiveness": "NRW mitigation effectiveness",
            "Pipe friction factor decay rate": "Pipe friction factor decay rate",
            "Pumps/Pipes lifetime": "Pumps/Pipes lifetime"
        },
        scale={ 
            "Ignored (deemed not relevant)": "Ignored",
            "Simplified (used expected value)": "Simplified",
            "Conservative (used worst-case value)": "Conservative",
            "Modelled (sampling or analytical approach)": "Modelled"
        }
    ),
    "planning_horizon": ChoiceQuestion(
        prefix="What planning horizon",
        options={
            "25 years": "25 y",
            "26-50 years": "26-50 y",
            "> 50 years": ">50 y"
        }
    ),
    "masterplan_timestep": ChoiceQuestion(
        prefix="At what temporal resolution",
        options={
            "1": "1 y",
            "5": "5 y",
            "Intervention changes in 5 years": "Policies 1 y<br>Interventions 5 y",
            "once per stage": "25 y",
        }
    ),
    # Section 5
    "objectives": LikertQuestion(
        prefix="",
        options={
            "Debt perception": "Debt Burden",
            "Reliability perception": "Reliability Perception",
            "GHG emissions accountability": "Emissions Accountability",
            "Affordability perception": "Affordability Distress",
        },
        scale={
            "Yes, exactly": "Exact",
            "Almost, ours was very similar": "Similar",
            "No, we had": "Different"
        }
    ),
    "relative_importance": ChoiceQuestion(
        prefix="How did your team's methodology incorporate the relative importance",
        options={
            "Fixed weights - combined the multiple objectives in a single one with weights decided a priori": "Fixed weights",
            #"Varying weights - multiple weight combinations to explore the trade-off space": "Weights sweep",
            "No weights - objectives kept separate through a multi-objective formulation": "Many-objective",
            "Mixed approach - One or more objectives treated as hard constraints, others optimised freely": "Multi-objectives<br>and Constraints"
        },
        has_other=True
    ),
    "masterplan_selection": ChoiceQuestion(
        prefix="As each team could submit a single masterplan, how did your team decide which one to submit?",
        options={
            "Not applicable - our methodology provided a single masterplan": "N/A",
            "Quantitative - based on a rule or metric (e.g., choose the knee point or look at the hypervolume)": "Quantitative",
            "Qualitative - gut feeling/personal preference of the team coordinator": "Qualitative (leader)",
            "Qualitative - following a team discussion/consensus": "Qualitative (team)",
            "First Quantitative, after Qualitative (in that orden by ranking)": "Quantitative", # formally "other" but knowing team solution, quantitative works best 
        },
        has_other=True
    ),
    "shifting_priorities": ChoiceQuestion(
        prefix="Did your team change the relative importance of the objectives between stages, and how?",
        options={
            "No - priorities stayed the same for the whole competition": "No",
            "Yes - adjusted based on observed perfromance and comparison with the reference solution": "Yes (performance)",
            "Yes - adjusted based on the released narrative": "Yes (narrative)"
        },
        has_other=True
    ),
    # Section 6
    "evaluator_usage": ChoiceQuestion(
        prefix="How much did your team use the open-source evaluator",
        options={
            "Nothing": "None",
            "Minimum": "Minimum",
            "Enough": "Significant",
            "Extensively": "Extensive"
        }
    ),
    "evaluator_outputs_usage": ChoiceQuestion(
        prefix="Did you incorporate the evaluator's additional output",
        options={
            "No": "None",
            "Yes, partially the hydraulics": "Hydraulics",
            "Yes, partially - ": "Metrics",
            "Yes, fully": "All"
        }
    ),
    "evaluator_fork": ChoiceQuestion(
        prefix="Did you incorporate some components",
        options={
            "No": "No",
            "Yes": "Yes"
        }
    ),
    "evalutor_preference": OpenQuestion(
        prefix="We understand that the delays in releasing"
    ),
    "evaluator_main_challenge": OpenQuestion(
        prefix="What was the main barrier you faced in using the evaluator?"
    ),
    "evaluator_suggestions": OpenQuestion(
        prefix="Additional suggestions about the evaluator?"
    ),

    # Section 7
    "takeaway_1": OpenQuestion(
        prefix="Takeaway #1"
    ),
    "takeaway_2": OpenQuestion(
        prefix="Takeaway #2"
    ),
    "takeaway_3": OpenQuestion(
        prefix="Takeaway #3"
    ),
    "comment": OpenQuestion(
        prefix="Is there any distinctive aspect"
    )


    
}

class SurveyResponse:
    """
    Wraps one participant's/team's row of survey answers (a pd.Series or
    dict keyed by the full question text) and exposes each answer via a
    short attribute name, resolved by matching QUESTIONS[name].prefix
    against the start of the question text and parsing it accordingly.
    """

    def __init__(self, data: pd.Series | dict[str, str]):
        self._data = data if isinstance(data, pd.Series) else pd.Series(data)

    def _raw_answer_for(self, question_prefix: str, row_prefix: str | None = None) -> Any:
        matches = [q for q in self._data.index if str(q).startswith(question_prefix)]
        if row_prefix is not None:
            matches = [q for q in matches if str(q).startswith(row_prefix)]

        if not matches:
            raise KeyError(f"No question found starting with {question_prefix!r}"
                            + (f" and {row_prefix!r}" if row_prefix is not None else ""))
        if len(matches) > 1:
            raise KeyError(f"Multiple questions found starting with {question_prefix!r}"
                            + (f" and {row_prefix!r}" if row_prefix is not None else "")
                            + f": {matches}")

        return self._data[matches[0]]

    def __getattr__(self, name: str) -> Any:
        # __getattr__ is only called when normal attribute lookup fails,
        # so this won't shadow _data or other real attributes/methods.
        if name in QUESTIONS:
            question = QUESTIONS[name]
            if self._data.empty:
                return None
            if isinstance(question, LikertQuestion) and question.options:
                return {
                    label: question.parse(self._raw_answer_for(question.prefix, row_prefix))
                    for row_prefix, label in question.options.items()
                }
            return question.parse(self._raw_answer_for(question.prefix))

        raise AttributeError(f"{type(self).__name__!r} object has no attribute {name!r}")
    
    @classmethod
    def get_question_options(cls, name: str) -> list[str] | None:
        if name in QUESTIONS:
            return QUESTIONS[name].categories

        raise AttributeError(f"{type(cls).__name__!r} object has no attribute {name!r}")
    
    @property
    def levers_groups(self) -> dict[int, set[str]]:

        # Participants could have named the group however they want, I want group A
        # to be the biggest and so on. I will first group the levers and ordered them
        # by count
        raw = self._levers_groups
        if not raw:
            return {}

        groups: dict[str, set[str]] = {}
        for key, value in raw.items():
            if value == "nan":
                continue
            groups.setdefault(value, set()).add(key)

        ordered = sorted(groups.values(), key=len, reverse=True)
        return {i: group for i, group in enumerate(ordered, start=1)}


def upload_survey_responses(teams_dir: Path) -> pd.DataFrame:
    responses_file = teams_dir / SURVEY_RESPONSES_FILE

    if not responses_file.exists():
        raise FileNotFoundError(f"Could not find survey responses file at {responses_file}.")

    df = pd.read_excel(responses_file)
    df["Team ID"] = df["Please insert your team's abstract ID"].apply(lambda i: f"TEAM{i}" if i> 0 else "TEAM00")

    return df.set_index("Team ID")
