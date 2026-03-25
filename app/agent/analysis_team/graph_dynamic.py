from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

from .analysis_state import AnalysisState, DEFAULT_ANALYSIS_TASKS
from .analysis_agent_dynamic import run_analysis_worker, generate_report_dynamic


def dispatch_workers(state: AnalysisState):
    """Dynamically dispatch N analysis workers based on analysis_tasks."""
    tasks = state.get("analysis_tasks", DEFAULT_ANALYSIS_TASKS)
    return [Send("worker", {**state, "task": t}) for t in tasks]


analysis_builder_dynamic = StateGraph(AnalysisState)

# Single worker node (executed N times concurrently via Send)
analysis_builder_dynamic.add_node("worker", run_analysis_worker)
analysis_builder_dynamic.add_node("report_generator", generate_report_dynamic)

# Dynamic fan-out from START
analysis_builder_dynamic.add_conditional_edges(START, dispatch_workers)

# All workers converge into report generator
analysis_builder_dynamic.add_edge("worker", "report_generator")

analysis_builder_dynamic.add_edge("report_generator", END)

analysis_team_graph_dynamic = analysis_builder_dynamic.compile()
