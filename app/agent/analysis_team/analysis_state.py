# app/agent/analysis_team/analysis_state.py
from typing import TypedDict, Annotated
import operator

class DimensionScore(TypedDict):
    product: int      # 产品力 (1-10)
    market: int       # 市场空间 (1-10)
    business: int     # 商业模式 (1-10)
    technology: int   # 技术壁垒 (1-10)
    growth: int       # 增长潜力 (1-10)
    team: int         # 团队/执行力 (1-10)


class AnalysisState(TypedDict):
    # 输入字段（从 Research 传入）
    company_name: str
    product_info: str
    market_info: str
    business_info: str
    company_profile: str
    
    # Analysis 自己的输出
    structured_info: dict
    dimension_scores: DimensionScore
    investment_advice: str
    analysis_report: str