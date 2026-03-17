from typing import TypedDict, Annotated
import operator

class CompanyResearchState(TypedDict):
    """State for a single company's research (used by subgraph / outsourced team)"""
    # 1. Input parameters
    company_name: str
    
    # 2. Output slots for concurrent workers
    product_info: str
    market_info: str
    business_info: str
    
    # Since 3 workers run concurrently, using a plain list would cause data loss or errors when appending simultaneously.
    # With Annotated and operator.add, LangGraph automatically and safely concatenates results produced concurrently!
    reference_sources: Annotated[list[dict], operator.add]
    
    # 3. Team aggregation output
    # Aggregates the three dimensions above to generate an independent report snippet for this company
    company_profile: str