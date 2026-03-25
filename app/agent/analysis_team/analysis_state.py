# app/agent/analysis_team/analysis_state.py
from typing import TypedDict, Annotated
import operator

from app.agent.research_team.research_state import CompanyResearchState


class DimensionScore(TypedDict):
    product: int      # 1-10
    market: int       # 1-10
    business: int     # 1-10
    technology: int   # 1-10
    growth: int       # 1-10
    team: int         # 1-10


# Default tasks for dynamic graph
DEFAULT_ANALYSIS_TASKS = ["extract", "score", "advise"]


class AnalysisState(CompanyResearchState):
    # Outputs of three parallel analysis nodes
    structured_info: dict
    dimension_scores: DimensionScore
    investment_advice: str

    # Dynamic graph fields
    analysis_tasks: list[str]
    analysis_results: Annotated[list[dict], operator.add]

    # Final report
    analysis_report: str

    # Eval control fields
    revision_count: int
    eval_feedback: str
    is_pass: bool