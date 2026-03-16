from dotenv import load_dotenv
load_dotenv()

import sys
import asyncio

from config import ANTHROPIC_API_KEY, TAVILY_API_KEY
from agents.research_orchestrator import run_research_orchestrator, aggregate_research


def main() -> None:
    args = sys.argv[1:]
    if len(args) < 2:
        print("Usage: python main.py <target> <competitor1> [competitor2 ...]")
        print("Example: python main.py Notion Obsidian Confluence")
        sys.exit(1)

    target = args[0]
    competitors = args[1:]

    if not ANTHROPIC_API_KEY:
        print("Error: ANTHROPIC_API_KEY not set in .env")
        sys.exit(1)
    if not TAVILY_API_KEY:
        print("Error: TAVILY_API_KEY not set in .env")
        sys.exit(1)

    separator = "-" * 60
    print(separator)
    print(f"  Competitive Analysis: {target} vs {', '.join(competitors)}")
    print(separator)

    async def run() -> str:
        research_data = await run_research_orchestrator(target, competitors)
        print("\n[Orchestrator] Aggregating findings...")
        return await aggregate_research(target, competitors, research_data)

    report = asyncio.run(run())

    print(f"\n{separator}")
    print("  RESEARCH REPORT")
    print(separator)
    print(report)
    print(separator)


if __name__ == "__main__":
    main()
