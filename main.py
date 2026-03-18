from dotenv import load_dotenv
load_dotenv()

import sys
from app.core.config import settings


def main() -> None:
    args = sys.argv[1:]
    if len(args) < 1:
        print("Usage: python main.py <company>")
        print("Example: python main.py Notion")
        sys.exit(1)

    company = args[0]

    if not settings.ANTHROPIC_API_KEY:
        print("Error: ANTHROPIC_API_KEY not set in .env")
        sys.exit(1)

    print(f"  Analysing: {company}")
    # TODO: wire up research_team + analysis_team graphs

if __name__ == "__main__":
    main()
