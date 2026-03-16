
import os

# API
ANTHROPIC_API_KEY: str = os.environ.get("ANTHROPIC_API_KEY", "")
TAVILY_API_KEY: str = os.environ.get("TAVILY_API_KEY", "")

# Models
ORCHESTRATOR_MODEL: str = "claude-sonnet-4-6"
# Workers: handle focused sub-tasks → cheaper / faster model is fine
WORKER_MODEL: str = "claude-haiku-4-5-20251001"
# Compactor: summarises history → cheapest model is sufficient
COMPACTOR_MODEL: str = "claude-haiku-4-5-20251001"

# Token budgets
# Workers compact their context when estimated token count exceeds this.
WORKER_CONTEXT_BUDGET: int = 3_000
# Max tokens the worker can generate in a single turn.
WORKER_MAX_TOKENS: int = 512
# Max tokens the orchestrator can generate per turn.
ORCHESTRATOR_MAX_TOKENS: int = 1_024

# Agentic loop 
# Safety cap: worker exits loop after this many iterations even if not "done".
MAX_WORKER_ITERATIONS: int = 4
