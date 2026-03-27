"""Top-level graph: chains research_team → analysis_team."""
from typing import TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, START, END

from .research_team.graph import research_team_graph
from .analysis_team.graph import analysis_team_graph
from .analysis_team.analysis_state import DimensionScore


class MainState(TypedDict):
    """Top-level state. Mirrors AnalysisState but overrides reference_sources
    as a plain list (no operator.add reducer) to prevent double-accumulation
    when research and analysis subgraphs each return the field to the parent."""

    # --- from CompanyResearchState ---
    company_name: str
    product_info: str
    market_info: str
    business_info: str
    reference_sources: list[dict]   # plain list — last-write-wins, no accumulation
    company_profile: str

    # --- from AnalysisState ---
    structured_info: dict
    dimension_scores: DimensionScore
    investment_advice: str
    analysis_tasks: list[str]
    analysis_results: Annotated[list[dict], operator.add]
    analysis_report: str
    revision_count: int
    eval_feedback: str
    is_pass: bool


main_builder = StateGraph(MainState)
main_builder.add_node("research", research_team_graph)
main_builder.add_node("analysis", analysis_team_graph)
main_builder.add_edge(START, "research")
main_builder.add_edge("research", "analysis")
main_builder.add_edge("analysis", END)

main_graph = main_builder.compile()
