import json
import re
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from app.core.llm_factory import LLMFactory, ModelRole

from app.core.config import settings
from app.utils.prompt_utils import load_prompt
from .analysis_state import AnalysisState

def _parse_eval_result(text: str) -> dict:
    """Parse evaluation result from LLM response."""
    cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", text).strip()
    try:
        result = json.loads(cleaned)
        return {
            "is_pass": result.get("is_pass", False),
            "feedback": result.get("feedback", "")
        }
    except json.JSONDecodeError:
        return {"is_pass": False, "feedback": text}


def evaluate_report(state: AnalysisState) -> dict:
    """Evaluate the quality of analysis_report."""
    llm = LLMFactory.create(ModelRole.WORKER,"qwen")
    prompt_text = load_prompt("analysis_eval.md")

    prompt = ChatPromptTemplate.from_messages([
        ("system", prompt_text),
        ("human", """
company: {company}

analysis report:
{analysis_report}
""")
    ])

    chain = prompt | llm
    response = chain.invoke({
        "company": state.get("company_name", ""),
        "analysis_report": state.get("analysis_report", ""),
    })

    parsed = _parse_eval_result(response.content)

    return {
        "is_pass": parsed["is_pass"],
        "eval_feedback": parsed["feedback"],
        "revision_count": state.get("revision_count", 0) + 1
    }
