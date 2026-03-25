import json
import re
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate

from app.core.config import settings
from app.utils.prompt_utils import load_prompt
from .analysis_state import AnalysisState


def _parse_json(text: str) -> dict:
    """Strip markdown code fences and parse JSON from LLM response."""
    cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", text).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {"raw": text}


def _get_worker_llm():
    return ChatAnthropic(
        model=settings.WORKER_MODEL,
        max_tokens=settings.WORKER_MAX_TOKENS,
        api_key=settings.ANTHROPIC_API_KEY,
        temperature=0.2,
    )


def _get_orchestrator_llm():
    return ChatAnthropic(
        model=settings.ORCHESTRATOR_MODEL,
        max_tokens=settings.ORCHESTRATOR_MAX_TOKENS,
        api_key=settings.ANTHROPIC_API_KEY,
        temperature=0.3,
    )


def _build_context(state: AnalysisState) -> dict:
    """Build common context dict from state for prompt injection."""
    return {
        "company": state["company_name"],
        "company_profile": state.get("company_profile", "no info"),
        "product_info": state.get("product_info", "no info"),
        "market_info": state.get("market_info", "no info"),
        "business_info": state.get("business_info", "no info"),
    }


# Universal analysis worker — handles any task defined in analysis_tasks
def run_analysis_worker(state: AnalysisState):
    task = state["task"]  # "extract" / "score" / "advise" / any future task
    prompt_text = load_prompt(f"analysis_{task}.md")

    llm = _get_orchestrator_llm() if task == "advise" else _get_worker_llm()

    prompt = ChatPromptTemplate.from_messages([
        ("system", prompt_text),
        ("human", """
company: {company}

company profile:\n{company_profile}

product info:\n{product_info}

market info:\n{market_info}

business info:\n{business_info}
""")
    ])

    chain = prompt | llm
    response = chain.invoke(_build_context(state))

    # Parse JSON for extract/score tasks, keep text for advise
    content = _parse_json(response.content) if task in ("extract", "score") else response.content

    return {"analysis_results": [{"task": task, "content": content}]}


# Report Generator — aggregates all worker outputs from analysis_results
def generate_report_dynamic(state: AnalysisState):
    llm = _get_orchestrator_llm()
    prompt_text = load_prompt("analysis_report.md")

    # Build lookup from analysis_results list
    results = {r["task"]: r["content"] for r in state.get("analysis_results", [])}

    prompt = ChatPromptTemplate.from_messages([
        ("system", prompt_text),
        ("human", """
company: {company}

structured info:\n{structured_info}

dimension scores:\n{dimension_scores}

investment advice:\n{investment_advice}
""")
    ])

    chain = prompt | llm
    response = chain.invoke({
        "company": state["company_name"],
        "structured_info": json.dumps(results.get("extract", {}), ensure_ascii=False, indent=2),
        "dimension_scores": json.dumps(results.get("score", {}), ensure_ascii=False),
        "investment_advice": results.get("advise", "no info"),
    })

    return {"analysis_report": response.content}
