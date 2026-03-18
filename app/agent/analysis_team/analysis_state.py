from typing import TypedDict, Annotated
import operator

try:
    from app.agent.research_team.research_state import CompanyResearchState
except ModuleNotFoundError:
    # Stub until PR #18 (research_team) is merged
    class CompanyResearchState(TypedDict):  # type: ignore[no-redef]
        company_name: str
        product_info: str
        market_info: str
        business_info: str
        reference_sources: Annotated[list[dict], operator.add]
        company_profile: str


class DimensionScore(TypedDict):
    product: int      # 产品力 (1-10)
    market: int       # 市场空间 (1-10)
    business: int     # 商业模式 (1-10)
    technology: int   # 技术壁垒 (1-10)
    growth: int       # 增长潜力 (1-10)
    team: int         # 团队/执行力 (1-10)


# Default tasks for dynamic graph
DEFAULT_ANALYSIS_TASKS = ["extract", "score", "advise"]


class AnalysisState(CompanyResearchState):
    # Outputs of three parallel analysis nodes (static graph)
    structured_info: dict         # 结构化提取：融资轮次、估值、核心产品等
    dimension_scores: DimensionScore  # 六边形打分
    investment_advice: str        # 投资/竞品建议

    # Dynamic graph fields
    analysis_tasks: list[str]                              # runtime task list
    analysis_results: Annotated[list[dict], operator.add]  # concurrent-safe aggregation

    # Final merged report
    analysis_report: str
