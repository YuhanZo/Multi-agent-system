from langchain_core.messages import HumanMessage, SystemMessage
from app.core.llm_factory import LLMFactory, ModelRole
from app.utils.prompt_utils import load_prompt
from .tools import TOOLS
from .gaia_state import GaiaState


def plan_question(state: GaiaState) -> dict:
    """P0.1: Planner node — decompose the question before entering the ReAct loop."""
    llm = LLMFactory.create(ModelRole.ORCHESTRATOR)

    question = state["question"]
    if state.get("file_path"):
        question += f"\n\n(Attached file: {state['file_path']})"

    response = llm.invoke([
        SystemMessage(content=(
            "You are a planning assistant. Given a question, produce a concise step-by-step research plan.\n\n"
            "Your plan should:\n"
            "1. Identify the question type (factual lookup / calculation / multi-hop / file-based / reasoning)\n"
            "2. List exactly what pieces of information need to be found\n"
            "3. Suggest specific search queries to use (be precise — include names, dates, titles)\n"
            "4. Note any calculations or reasoning steps required after gathering data\n"
            "5. Flag if a file needs to be read first\n\n"
            "Be concise. Output only the plan, no preamble."
        )),
        HumanMessage(content=f"Question: {question}\n\nResearch plan:"),
    ])
    return {"plan": response.content.strip()}


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

        # Inject plan from P0.1 planner if available
        plan = state.get("plan", "")
        human_content = question
        if plan:
            human_content += f"\n\n## Research Plan\n{plan}"

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_content),
        ]
    else:
        messages = state["messages"]

    response = llm_with_tools.invoke(messages)

    # First call: persist init messages (SystemMessage + HumanMessage) too,
    # so subsequent calls have full context in state["messages"].
    if not state.get("messages"):
        return {"messages": messages + [response]}
    return {"messages": [response]}


MAX_SEARCH_ROUNDS = 2  # 0-indexed: rounds 0, 1, 2 = 3 total


def sufficiency_judge(state: GaiaState) -> dict:
    """P0.2: Evaluate whether gathered information is sufficient to answer the question."""
    llm = LLMFactory.create(ModelRole.WORKER)

    # Collect all text from non-tool assistant messages as research summary
    research_so_far = []
    for msg in state.get("messages", []):
        if hasattr(msg, "content") and msg.content:
            if not getattr(msg, "tool_calls", None):
                role = "Assistant" if hasattr(msg, "type") and msg.type == "ai" else "User"
                research_so_far.append(f"[{role}]: {msg.content[:500]}")

    summary = "\n".join(research_so_far[-10:])  # last 10 messages to stay within context

    response = llm.invoke([
        SystemMessage(content=(
            "You are an information sufficiency evaluator.\n"
            "Given a question, a research plan, and the research gathered so far, "
            "decide if there is enough information to give a confident final answer.\n\n"
            "Respond in this exact format:\n"
            "SUFFICIENT: yes/no\n"
            "GAPS: <one sentence describing what specific information is still missing, or 'none'>"
        )),
        HumanMessage(content=(
            f"Question: {state['question']}\n\n"
            f"Plan: {state.get('plan', 'N/A')}\n\n"
            f"Research so far:\n{summary}\n\n"
            "Is the information sufficient?"
        )),
    ])

    text = response.content.strip()
    is_sufficient = "sufficient: yes" in text.lower()
    gaps = ""
    for line in text.splitlines():
        if line.lower().startswith("gaps:"):
            gaps = line.split(":", 1)[-1].strip()
            break

    current_round = state.get("search_round", 0)

    # If not sufficient and rounds remain, inject a guidance message for next round
    if not is_sufficient and current_round < MAX_SEARCH_ROUNDS:
        guidance = HumanMessage(content=(
            f"Your research so far is incomplete. Missing information: {gaps}\n\n"
            "Please search specifically for this missing information now. "
            "Use different, more targeted search queries than before."
        ))
        return {
            "is_sufficient": False,
            "info_gaps": gaps,
            "search_round": current_round + 1,
            "messages": [guidance],
        }

    return {"is_sufficient": True, "info_gaps": gaps}


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
            "No explanation, no markdown.\n\n"
            "Strict formatting rules:\n"
            "- Pay close attention to the unit or format the question asks for. "
            "For example, if the question asks 'how many thousand hours', return the number in thousands.\n"
            "- If the question says to round, apply rounding.\n"
            "- Never use comma separators in numbers unless explicitly asked.\n"
            "- For comma-separated lists, always include a space after each comma (e.g., 'a, b, c').\n"
            "- Never include stage directions or scene prefixes (e.g., 'INT.', 'EXT.', '- DAY'). "
            "If the answer is a location or place name from a script, return only the place name itself.\n"
            "- Return the complete, specific answer. For example, if the answer is a specific species, "
            "give the full species name, not just the genus.\n"
            "- Do not add hyphens to words unless the source explicitly uses them.\n"
            "- If the reasoning says the question cannot be answered, return an empty string."
        )),
        HumanMessage(content=f"Question: {state['question']}\n\nReasoning: {raw_answer}\n\nFinal answer (only the answer, nothing else):"),
    ])
    return {"final_answer": response.content.strip()}
