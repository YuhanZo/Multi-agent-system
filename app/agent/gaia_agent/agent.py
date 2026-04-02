from langchain_core.messages import HumanMessage, SystemMessage
from app.core.llm_factory import LLMFactory, ModelRole
from app.utils.prompt_utils import load_prompt
from .tools import TOOLS
from .gaia_state import GaiaState


def run_agent(state: GaiaState) -> dict:
    """Main ReAct agent node: reasons and calls tools until it has a final answer."""
    llm = LLMFactory.create(ModelRole.ORCHESTRATOR)
    llm_with_tools = llm.bind_tools(TOOLS)

    system_prompt = load_prompt("gaia_agent.md")

    # Build initial messages if this is the first call
    if not state.get("messages"):
        question = state["question"]
        if state.get("file_path"):
            question += f"\n\n(Attached file: {state['file_path']})"
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=question),
        ]
    else:
        messages = state["messages"]

    response = llm_with_tools.invoke(messages)

    # First call: persist init messages (SystemMessage + HumanMessage) too,
    # so subsequent calls have full context in state["messages"].
    if not state.get("messages"):
        return {"messages": messages + [response]}
    return {"messages": [response]}


def extract_answer(state: GaiaState) -> dict:
    """Use LLM to extract a concise final answer from the conversation."""
    llm = LLMFactory.create(ModelRole.WORKER)

    # Get the last assistant message as the raw answer
    raw_answer = ""
    for msg in reversed(state.get("messages", [])):
        if hasattr(msg, "content") and msg.content and not getattr(msg, "tool_calls", None):
            raw_answer = msg.content.strip()
            break

    if not raw_answer:
        return {"final_answer": ""}

    response = llm.invoke([
        SystemMessage(content=(
            "You extract the final answer from a reasoning response. "
            "Return ONLY the answer itself — a single word, number, name, or short phrase. "
            "No explanation, no punctuation, no markdown. "
            "Pay close attention to the unit or format the question asks for — "
            "for example, if the question asks 'how many thousand hours', return the number in thousands. "
            "If the question says to round, apply rounding. "
            "Never use comma separators unless the question explicitly requires them."
        )),
        HumanMessage(content=f"Question: {state['question']}\n\nReasoning: {raw_answer}\n\nFinal answer (only the answer, nothing else):"),
    ])
    return {"final_answer": response.content.strip()}
