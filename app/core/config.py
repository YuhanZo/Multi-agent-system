
import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Read Absolute Path
APP_ROOT_DIR = Path(__file__).resolve().parent.parent
PROMPT_DIR = APP_ROOT_DIR / "prompt"
ENV_DIR = ".env"

class Settings(BaseSettings):
    # --- LLM Provider ---
    LLM_PROVIDER: str = "anthropic"  # anthropic | openai | qwen
    
    # --- API Keys ---
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    DASHSCOPE_API_KEY: str = ""  # Qwen
    TAVILY_API_KEY: str = ""  # TODO: search tool implement
    
    # --- LangSmith  ---
    LANGCHAIN_TRACING_V2: str = "true"
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_PROJECT: str = "Company_Research_Agent"

    # --- Models ---
    ORCHESTRATOR_MODEL: str = "claude-sonnet-4-6"
    WORKER_MODEL: str = "claude-haiku-4-5-20251001"
    COMPACTOR_MODEL: str = "claude-haiku-4-5-20251001"

    # --- Token budgets ---
    WORKER_CONTEXT_BUDGET: int = 3000
    WORKER_MAX_TOKENS: int = 512
    ORCHESTRATOR_MAX_TOKENS: int = 1024

    # --- Agentic loop ---
    MAX_WORKER_ITERATIONS: int = 4

    # update config from .env file
    model_config = SettingsConfigDict(
        env_file=str(ENV_DIR), 
        env_file_encoding="utf-8",
        extra="ignore"
        
    )
      
# 3. instantiate setting
settings = Settings()