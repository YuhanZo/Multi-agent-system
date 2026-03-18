from langgraph.graph import StateGraph, START, END

from .analysis_state import AnalysisState
from .analysis_agent import (
    extract_structured_info,
    score_dimensions,
    advise_investment,
    generate_report,
)

analysis_builder = StateGraph(AnalysisState)

# Add four nodes
analysis_builder.add_node("extractor", extract_structured_info)
analysis_builder.add_node("scorer", score_dimensions)
analysis_builder.add_node("advisor", advise_investment)
analysis_builder.add_node("report_generator", generate_report)

# Three analysis nodes run in parallel from START
analysis_builder.add_edge(START, "extractor")
analysis_builder.add_edge(START, "scorer")
analysis_builder.add_edge(START, "advisor")

# Converge into report generator
analysis_builder.add_edge(["extractor", "scorer", "advisor"], "report_generator")

# Done
analysis_builder.add_edge("report_generator", END)

analysis_team_graph = analysis_builder.compile()
