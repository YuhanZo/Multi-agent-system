from langgraph.graph import StateGraph, START, END

from .analysis_state import AnalysisState
from .analysis_agent import (
    extract_structured_info,
    score_dimensions,
    advise_investment,
    generate_report,
)

from .eval_agent import (evaluate_report)

def should_revise(state: AnalysisState) -> str:
    MAX_REVISIONS = 3
    if state.get("is_pass", False):
        return "end"
    if state.get("revision_count", 0) >= MAX_REVISIONS:
        return "end"  # reach maxmum retry times
    return "revise"

analysis_builder = StateGraph(AnalysisState)

# Add four nodes
analysis_builder.add_node("extractor", extract_structured_info)
analysis_builder.add_node("scorer", score_dimensions)
analysis_builder.add_node("advisor", advise_investment)
analysis_builder.add_node("report_generator", generate_report)

# Add eval nodes
analysis_builder.add_node("evaluator", evaluate_report)

# Three analysis nodes run in parallel from START
analysis_builder.add_edge(START, "extractor")
analysis_builder.add_edge(START, "scorer")
analysis_builder.add_edge(START, "advisor")

# Converge into report generator
analysis_builder.add_edge(["extractor", "scorer", "advisor"], "report_generator")

# report_generator → evaluator
analysis_builder.add_edge("report_generator", "evaluator")

# check if need revise 
analysis_builder.add_conditional_edges(
    "evaluator",
    should_revise,
    {
        "end": END,
        "revise": "report_generator"
    }
)

analysis_team_graph = analysis_builder.compile()
