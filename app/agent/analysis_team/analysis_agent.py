import json
import re
from langchain_core.prompts import ChatPromptTemplate
from app.core.llm_factory import LLMFactory, ModelRole


# Compatible with both current config (constants) and PR #18 config (settings object)
try:
    from app.core.config import settings
    ANTHROPIC_API_KEY = settings.ANTHROPIC_API_KEY
    WORKER_MODEL = settings.WORKER_MODEL
    WORKER_MAX_TOKENS = settings.WORKER_MAX_TOKENS
    ORCHESTRATOR_MODEL = settings.ORCHESTRATOR_MODEL
    ORCHESTRATOR_MAX_TOKENS = settings.ORCHESTRATOR_MAX_TOKENS
except ImportError:
    from app.core.config import (
        ANTHROPIC_API_KEY, WORKER_MODEL, WORKER_MAX_TOKENS,
        ORCHESTRATOR_MODEL, ORCHESTRATOR_MAX_TOKENS,
    )

from app.utils.prompt_utils import load_prompt
from .analysis_state import AnalysisState


def _parse_json(text: str) -> dict:
    """Strip markdown code fences and parse JSON from LLM response."""
    cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", text).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {"raw": text}

# 1. Structured Info Extractor
def extract_structured_info(state: AnalysisState):

    llm = LLMFactory.create(ModelRole.WORKER)
    
    prompt_text = load_prompt("analysis_extract.md")

    prompt = ChatPromptTemplate.from_messages([
        ("system", prompt_text),
        ("human", """
         company: {company}

         product info:\n{product_info}

         market info:\n{market_info}

         business info:\n{business_info}

         You MUST use only the information provided above.
         Do NOT use prior knowledge.
         Do NOT invent facts.
         If a field is missing or unsupported, return null or explicitly say the evidence is insufficient.
        """)
    ])

    chain = prompt | llm
    response = chain.invoke({
        "company": state["company_name"],
        "product_info": state.get("product_info", "no info"),
        "market_info": state.get("market_info", "no info"),
        "business_info": state.get("business_info", "no info"),
    })

    return {"structured_info": _parse_json(response.content)}


# 2. Dimension Scorer
def score_dimensions(state: AnalysisState):

    llm = LLMFactory.create(ModelRole.WORKER)
    
    prompt_text = load_prompt("analysis_score.md")

    prompt = ChatPromptTemplate.from_messages([
        ("system", prompt_text),
        ("human", """
         company profile:\n{company_profile}

         product info:\n{product_info}

         market info:\n{market_info}

         business info:\n{business_info}

         You MUST score only based on the information provided above.
         Do NOT use prior knowledge.
         Do NOT invent facts.
         If evidence for a dimension is weak, reflect that uncertainty in the score.
        """)
    ])

    chain = prompt | llm
    response = chain.invoke({
        "company_profile": state.get("company_profile", "no info"),
        "product_info": state.get("product_info", "no info"),
        "market_info": state.get("market_info", "no info"),
        "business_info": state.get("business_info", "no info"),
    })

    return {"dimension_scores": _parse_json(response.content)}


# 3. Investment / Competitive Advisor
def advise_investment(state: AnalysisState):

    llm = LLMFactory.create(ModelRole.ORCHESTRATOR)

    prompt_text = load_prompt("analysis_advise.md")

    prompt = ChatPromptTemplate.from_messages([
        ("system", prompt_text),
        ("human", """
         company: {company}

         company profile:\n{company_profile}

         product info:\n{product_info}

         market info:\n{market_info}

         business info:\n{business_info}

         You MUST use only the information provided above.
         Do NOT use prior knowledge.
         Do NOT invent facts.
         If evidence is insufficient, explicitly mention the uncertainty and missing information.
        """)
    ])

    chain = prompt | llm
    response = chain.invoke({
        "company": state["company_name"],
        "company_profile": state.get("company_profile", "no info"),
        "product_info": state.get("product_info", "no info"),
        "market_info": state.get("market_info", "no info"),
        "business_info": state.get("business_info", "no info"),
    })

    return {"investment_advice": response.content}


# 4. Report Generator (aggregates all analysis outputs)
def generate_report(state: AnalysisState):
    
    llm = LLMFactory.create(ModelRole.ORCHESTRATOR)

    prompt_text = load_prompt("analysis_report.md")

    # get eval feedback
    eval_feedback = state.get("eval_feedback", "")

    prompt = ChatPromptTemplate.from_messages([
        ("system", prompt_text),
        ("human", """
         company: {company}

         structured info:\n{structured_info}

         dimension scores:\n{dimension_scores}

         investment advice:\n{investment_advice}
                
         {revision_context}

         You MUST use only the information provided above.
         Do NOT use prior knowledge.
         Do NOT invent facts.
         If the input evidence is insufficient, preserve that uncertainty in the report instead of filling gaps.
        """)
    ])

    revision_context = ""
    if eval_feedback:
        revision_context = f"""
        --- revision requirements ---
        please improve the report based on feedback below:
        {eval_feedback}
        """

    chain = prompt | llm
    response = chain.invoke({
        "company": state["company_name"],
        "structured_info": json.dumps(state.get("structured_info", {}), ensure_ascii=False, indent=2),
        "dimension_scores": json.dumps(state.get("dimension_scores", {}), ensure_ascii=False),
        "investment_advice": state.get("investment_advice", "no info"),
        "revision_context": revision_context,
    })

    return {"analysis_report": response.content}
