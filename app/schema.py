from typing import TypedDict, Annotated
import operator

# ===== Research Team =====
class ResearchInput(TypedDict):
    company_name: str

class ResearchOutput(TypedDict):
    company_name: str
    product_info: str
    market_info: str
    business_info: str
    reference_sources: list[dict]
    company_profile: str

# ===== Analysis Team =====
class AnalysisInput(TypedDict):
    """Analysis 需要的输入，从 ResearchOutput 提取"""
    company_name: str
    product_info: str
    market_info: str
    business_info: str
    company_profile: str

class DimensionScore(TypedDict):
    product: int
    market: int
    business: int
    technology: int
    growth: int
    team: int

class AnalysisOutput(TypedDict):
    structured_info: dict
    dimension_scores: DimensionScore
    investment_advice: str
    analysis_report: str