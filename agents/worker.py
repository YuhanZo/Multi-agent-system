from __future__ import annotations

import asyncio
from pathlib import Path

from pydantic_ai import Agent
from tavily import TavilyClient

import config

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "RESEARCH_AGENT.md"

worker_agent = Agent(
    f"anthropic:{config.WORKER_MODEL}",
    instructions=_PROMPT_PATH.read_text(encoding="utf-8"),
)


@worker_agent.tool_plain
async def search(query: str) -> str:
    """Search the web for factual information. Use 1-2 times with specific queries (3-7 words)."""
    client = TavilyClient(api_key=config.TAVILY_API_KEY)
    response = await asyncio.to_thread(client.search, query, max_results=3)
    results = response.get("results", [])
    if not results:
        return f"No results found for '{query}'"
    return "\n".join(
        f"[{i+1}] {r.get('title', '')}: {r.get('content', '')[:400]}"
        for i, r in enumerate(results)
    )


async def run_worker(task: str, worker_id: str = "worker") -> str:
    print(f"  [{worker_id}] >> {task[:70]}...")
    result = await worker_agent.run(task)
    print(f"  [{worker_id}] Done.")
    return result.output
