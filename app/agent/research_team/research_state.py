from typing import TypedDict, Annotated
import operator

class CompanyResearchState(TypedDict):
    """State for a single company's research (used by subgraph / outsourced team)"""
    # 3 areas below:

    # this is input
    company_name: str
    
    # Output slots for concurrent workers
    product_info: str
    market_info: str
    business_info: str
    
    # Important part:
    # Since 3 workers run concurrently, using a plain list would cause data loss or errors when appending simultaneously.
    # With Annotated and operator.add, LangGraph automatically and safely concatenates results produced concurrently!
    reference_sources: Annotated[list[dict], operator.add]
    
    # Aggregation output. After workers finish, aggregate results into a comprehensive profile.
    company_profile: str