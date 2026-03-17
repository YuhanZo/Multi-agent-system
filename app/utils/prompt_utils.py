from app.core.config import PROMPT_DIR
from functools import lru_cache

@lru_cache(maxsize=128)
def load_prompt(filename: str) -> str:
    
    prompt_path = PROMPT_DIR / filename
    
    if not prompt_path.exists():
        raise FileNotFoundError(f"can't find prompt file: {prompt_path}")
        
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()