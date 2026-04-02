from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from .gaia_state import GaiaState
from .agent import run_agent, extract_answer
from .tools import TOOLS

gaia_builder = StateGraph(GaiaState)

gaia_builder.add_node("agent", run_agent)
gaia_builder.add_node("tools", ToolNode(TOOLS))
gaia_builder.add_node("extract_answer", extract_answer)

gaia_builder.add_edge(START, "agent")
gaia_builder.add_conditional_edges(
    "agent",
    tools_condition,
    {"tools": "tools", END: "extract_answer"},
)
gaia_builder.add_edge("tools", "agent")
gaia_builder.add_edge("extract_answer", END)

gaia_graph = gaia_builder.compile()
