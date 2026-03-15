
import sys
from pathlib import Path
import anthropic
from orchestrator import run_orchestrator
from config import ANTHROPIC_API_KEY

AGENT_MD_PATH = Path(__file__).parent / "AGENT.md"
DEFAULT_TOPIC = "The future of renewable energy storage"


def main() -> None:
    topic = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else DEFAULT_TOPIC

    if not ANTHROPIC_API_KEY:
        print("Error: ANTHROPIC_API_KEY environment variable is not set.")
        sys.exit(1)

    # Load AGENT.md — injected into every agent's system prompt
    agent_md = AGENT_MD_PATH.read_text(encoding="utf-8") if AGENT_MD_PATH.exists() else ""
    if not agent_md:
        print("Warning: AGENT.md not found — agents will run without shared instructions.")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    separator = "─" * 60
    print(separator)
    print("  Research Multi-Agent System")
    print(separator)

    report = run_orchestrator(client, topic, agent_md)

    print("\n" + separator)
    print("  FINAL REPORT")
    print(separator)
    print(report)
    print(separator)


if __name__ == "__main__":
    main()
