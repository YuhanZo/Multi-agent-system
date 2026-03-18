from typing import TypedDict, Annotated
import operator

try:
    from app.agent.research_team.research_state import CompanyResearchState
except ModuleNotFoundError:
    class CompanyResearchState(TypedDict):  # type: ignore[no-redef]
        company_name: str
        product_info: str
        market_info: str
        business_info: str
        reference_sources: Annotated[list[dict], operator.add]
        company_profile: str


# Default analysis tasks — can be overridden at runtime
DEFAULT_ANALYSIS_TASKS = ["extract", "score", "advise"]


class AnalysisState(CompanyResearchState):
    # Runtime-configurable task list
    analysis_tasks: list[str]

    # Parallel worker outputs (concurrent-safe)
    analysis_results: Annotated[list[dict], operator.add]

    # Final merged report
    analysis_report: str
