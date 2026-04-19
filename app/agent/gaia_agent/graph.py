from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from .gaia_state import GaiaState
from .agent import plan_question, run_agent, sufficiency_judge, extract_answer
from .tools import TOOLS


def after_judge(state: GaiaState) -> str:
    """P0.2: Route to another search round or finalize."""
    if state.get("is_sufficient", False):
        return "extract_answer"
    return "agent"


gaia_builder = StateGraph(GaiaState)

gaia_builder.add_node("planner", plan_question)           # P0.1
gaia_builder.add_node("agent", run_agent)
gaia_builder.add_node("tools", ToolNode(TOOLS))
gaia_builder.add_node("sufficiency_judge", sufficiency_judge)  # P0.2
gaia_builder.add_node("extract_answer", extract_answer)

gaia_builder.add_edge(START, "planner")
gaia_builder.add_edge("planner", "agent")
gaia_builder.add_conditional_edges(
    "agent",
    tools_condition,
    {"tools": "tools", END: "sufficiency_judge"},     # P0.2: judge before extracting
)
gaia_builder.add_edge("tools", "agent")
gaia_builder.add_conditional_edges(
    "sufficiency_judge",
    after_judge,
    {"extract_answer": "extract_answer", "agent": "agent"},
)
gaia_builder.add_edge("extract_answer", END)

gaia_graph = gaia_builder.compile()
