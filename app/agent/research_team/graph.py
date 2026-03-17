from langgraph.graph import StateGraph, START, END
from .research_state import CompanyResearchState
from .research_agent import research_product, research_market, research_business, synthesize_profile

# 1. initialize state gpraph
research_builder = StateGraph(CompanyResearchState)

# 2. add nodes
research_builder.add_node("product_researcher", research_product)
research_builder.add_node("market_researcher", research_market)
research_builder.add_node("business_researcher", research_business)
research_builder.add_node("profile_synthesizer", synthesize_profile)

# 3. ochestrate nodes
research_builder.add_edge(START, "product_researcher")
research_builder.add_edge(START, "market_researcher")
research_builder.add_edge(START, "business_researcher")

# synthesize results
research_builder.add_edge(["product_researcher", "market_researcher", "business_researcher"], "profile_synthesizer")

# finish workflow
research_builder.add_edge("profile_synthesizer", END)

# compile to subgraph
research_team_graph = research_builder.compile()