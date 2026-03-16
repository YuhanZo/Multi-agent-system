from __future__ import annotations

import asyncio

from pydantic_ai import Agent

import config
from agents.worker import run_worker

_aggregate_agent = Agent(f"anthropic:{config.ORCHESTRATOR_MODEL}")


async def run_research_orchestrator(
    target: str,
    competitors: list[str],
) -> dict[str, str]:
    """Run 2N workers in parallel: overview + reviews per company."""
    companies = [target] + competitors

    task_coroutines = []
    task_labels = []

    for company in companies:
        task_coroutines.append(
            run_worker(
                f"Research {company} product: overview, key features, target users, pricing model",
                worker_id=f"{company}-overview",
            )
        )
        task_labels.append(f"{company}_overview")

        task_coroutines.append(
            run_worker(
                f"Research {company} user sentiment: reviews, praise, complaints, ratings",
                worker_id=f"{company}-reviews",
            )
        )
        task_labels.append(f"{company}_reviews")

    print(f"\n[Research Orchestrator] Launching {len(task_coroutines)} workers in parallel ...")
    results = await asyncio.gather(*task_coroutines)
    return dict(zip(task_labels, results))


async def aggregate_research(
    target: str,
    competitors: list[str],
    research_data: dict[str, str],
) -> str:
    """Aggregate worker findings into a structured research summary."""
    findings_block = "\n\n".join(
        f"### {label}\n{content}" for label, content in research_data.items()
    )

    prompt = (
        f"Synthesize the following research data about {target} and its competitors "
        f"({', '.join(competitors)}) into a structured research summary.\n\n"
        f"{findings_block}\n\n"
        f"Write 4-6 cohesive paragraphs covering: product positioning, key differentiators, "
        f"user sentiment, and market gaps. Begin directly with the content, no preamble."
    )

    result = await _aggregate_agent.run(prompt)
    return result.output
