from __future__ import annotations
import anthropic
from context_manager import ContextManager, _content_to_str
from config import (
    WORKER_MODEL,
    WORKER_MAX_TOKENS,
    WORKER_CONTEXT_BUDGET,
    MAX_WORKER_ITERATIONS,
)

# Tool schema

TOOLS = [
    {
        "name": "search",
        "description": "Search the web for factual information on a specific topic.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "A precise search query (3-7 words).",
                }
            },
            "required": ["query"],
        },
    }
]


# Tool execution (mock)

def _mock_search(query: str) -> str:
    """
    Mock search — returns plausible-looking structured results.
    Replace this function body with a real API call in production.

    Example real implementation:
        import httpx
        r = httpx.get("https://api.search.brave.com/res/v1/web/search",
                       headers={"Accept": "application/json",
                                "X-Subscription-Token": BRAVE_API_KEY},
                       params={"q": query, "count": 3})
        snippets = [item["description"] for item in r.json()["web"]["results"]]
        return "\n".join(snippets)
    """
    return (
        f"Search results for '{query}':\n"
        f"[1] Overview: {query.capitalize()} encompasses key principles, "
        f"mechanisms, and real-world applications documented across academic and "
        f"industry sources.\n"
        f"[2] Recent research (2024): Studies confirm growing relevance of {query} "
        f"with measurable impact in three major domains.\n"
        f"[3] Industry perspective: Practitioners report adoption challenges "
        f"primarily around tooling, expertise, and cost."
    )


# Main worker function

def run_worker(
    client: anthropic.Anthropic,
    task: str,
    system_prompt: str,
    worker_id: str = "worker",
) -> str:
    """
    Run one worker agent on a single sub-question.

    Args:
        client:        Anthropic API client
        task:          The sub-question to answer
        system_prompt: Contents of AGENT.md (injected as system prompt)
        worker_id:     Label for log output

    Returns:
        The worker's final text answer.
    """
    print(f"  [{worker_id}] ▶ {task[:70]}...")
    #initialization of the context manager; task is the sub-question
    ctx = ContextManager(budget=WORKER_CONTEXT_BUDGET, system=system_prompt)
    ctx.add("user", task)

    #agentic loop
    for iteration in range(MAX_WORKER_ITERATIONS):

        # Compact if context is getting too large
        if ctx.should_compact():
            print(f"  [{worker_id}] ⚙ Compacting context (iter {iteration})...")
            ctx.compact(client)

        # Call the model 
        response = client.messages.create(
            model=WORKER_MODEL,
            max_tokens=WORKER_MAX_TOKENS,
            system=ctx.get_system(),
            tools=TOOLS,
            messages=ctx.get_messages(),
        )

        # Tool use: execute tools, feed results back
        if response.stop_reason == "tool_use":
            # Store the full assistant turn (contains both text + tool_use blocks)
            ctx.add("assistant", response.content) #save

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    query = block.input.get("query", "")
                    print(f"  [{worker_id}] 🔍 search({query!r})")
                    result = _mock_search(query)

                    # Persist key tool result to agentic memory
                    ctx.remember(f"search('{query}') → {result[:120]}…")

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            ctx.add("user", tool_results) #feed results back as user msg to claude

        # End turn: agent is finished
        elif response.stop_reason == "end_turn":
            final_text = " ".join(
                block.text
                for block in response.content
                if hasattr(block, "text") and block.text
            )
            ctx.add("assistant", final_text)
            print(f"  [{worker_id}] ✓ Done.")
            return final_text

    #(for safety) Fallback if max iterations reached without clean end_turn
    print(f"  [{worker_id}] ⚠ Max iterations reached, returning last output.")
    for msg in reversed(ctx.get_messages()):
        if msg["role"] == "assistant":
            return _content_to_str(msg["content"])
    return "[Worker produced no output]"
