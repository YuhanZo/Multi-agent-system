from __future__ import annotations
import json
import anthropic
from worker import run_worker
from config import ORCHESTRATOR_MODEL, ORCHESTRATOR_MAX_TOKENS


def run_orchestrator(
    client: anthropic.Anthropic,
    topic: str,
    agent_md: str,
) -> str:
    """
    Orchestrate the full research pipeline.

    Args:
        client:    Anthropic API client
        topic:     The research topic (free-form string)
        agent_md:  Contents of AGENT.md, injected into every worker

    Returns:
        A synthesised research report as a string.
    """
    print(f"\n[Orchestrator] Topic: {topic}")
    print("[Orchestrator] Step 1/3 — Decomposing into sub-questions...")
    # currently running in series.
    subtasks = _decompose(client, topic)
    # for loop for workers
    for i, t in enumerate(subtasks, 1):
        print(f"  Sub-question {i}: {t}")

    print(f"\n[Orchestrator] Step 2/3 — Running {len(subtasks)} workers...")
    results: dict[str, str] = {}
    for i, task in enumerate(subtasks, 1):
        #result is a dictionary
        result = run_worker(client, task, agent_md, worker_id=f"worker-{i}")
        results[task] = result

    print("\n[Orchestrator] Step 3/3 — Aggregating into final report...")
    report = _aggregate(client, topic, results)
    return report


# Private helpers 

#return JSON because we'll use json.loads() to parse it
def _decompose(client: anthropic.Anthropic, topic: str) -> list[str]:

    prompt = (
        f"Split the following research topic into exactly 3 focused sub-questions "
        f"that together cover it comprehensively.\n\n"
        f"Topic: {topic}\n\n"
        f"Rules:\n"
        f"- Return ONLY a valid JSON array of 3 strings.\n"
        f"- No markdown fences, no explanation, no preamble.\n"
        f"- Each question must be self-contained (answerable without the others).\n\n"
        f'Example output: ["What is X?", "How does X work?", "What are X\'s limitations?"]'
    )
    resp = client.messages.create(
        model=ORCHESTRATOR_MODEL,
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = resp.content[0].text.strip()

    # Strip accidental markdown code fences
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    # prevent the mistake of returning sth instead of 3questions
    subtasks: list[str] = json.loads(raw)
    assert len(subtasks) == 3, f"Expected 3 sub-questions, got {len(subtasks)}"
    return subtasks

#systhesise the worker findings into a final report
def _aggregate(
    client: anthropic.Anthropic,
    topic: str,
    results: dict[str, str],
) -> str:
    """
    Synthesise worker findings into a coherent final report.
    The orchestrator model is used here (smarter = better synthesis).
    """
    findings_block = "\n\n".join(
        f"### Sub-question: {question}\n{answer}"
        for question, answer in results.items()
    )
    prompt = (
        f"Write a research summary on the topic: **{topic}**\n\n"
        f"The following findings were gathered by specialist research agents:\n\n"
        f"{findings_block}\n\n"
        f"Instructions:\n"
        f"- Write 3-5 cohesive paragraphs.\n"
        f"- Synthesise across findings — do not just list them sequentially.\n"
        f"- Highlight agreements, tensions, or gaps between the sub-answers.\n"
        f"- Begin directly with the report content (no 'Here is a summary...' preamble).\n"
        f"- Use plain prose; no markdown headers."
    )
    resp = client.messages.create(
        model=ORCHESTRATOR_MODEL,
        max_tokens=ORCHESTRATOR_MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text
