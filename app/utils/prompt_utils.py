import os
from pathlib import Path

def load_prompt(filename: str) -> str:
    current_dir = Path(__file__).resolve().parent
    prompt_path = current_dir.parent / "prompts" / filename
    
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()