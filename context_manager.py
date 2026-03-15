
from __future__ import annotations
from typing import Union
import anthropic
from config import COMPACTOR_MODEL


# Type alias: message content can be a plain string or a list of content blocks
Content = Union[str, list]


class ContextManager:
    
    def __init__(self, budget: int, system: str = ""):
        self._budget = budget       # estimated token limit 
        self._system = system       # base system prompt
        self._messages: list[dict] = [] #communication history
        self._memory: list[str] = [] # Agentic memory: survives compaction
        #message and memory have different life cycle.

    # Message history 

    def add(self, role: str, content: Content) -> None:
        #Append a message.  Content may be str or a list of API blocks.
        self._messages.append({"role": role, "content": content})

    def get_messages(self) -> list[dict]:
        return list(self._messages)

    # System prompt (augmented with memory) 

    def get_system(self) -> str:
        """
        Return the effective system prompt.
        Agentic memory is appended as a special section so it survives
        future compaction rounds (it lives in the system prompt, not history).
        """
        if not self._memory:
            return self._system
        memory_section = (
            "\n\n---\n[Agentic Memory — key facts from previous turns]\n"
            + "\n".join(f"• {fact}" for fact in self._memory)
        )
        return self._system + memory_section

    # Just-in-time context injection 

    def inject_context(self, text: str) -> None:
        """
        Just-in-time: inject a context snippet without polluting the base
        system prompt.  Use this for task-specific knowledge you only need
        once (e.g. a relevant document excerpt, a schema definition).
        """
        self._memory.append(f"[JIT context] {text}")

    # Agentic memory 

    def remember(self, fact: str) -> None:
        """
        Persist an important fact across compaction rounds.
        Good candidates: final answers from tools, key decisions, error states.
        """
        self._memory.append(fact)

    # Compaction 

    def should_compact(self) -> bool:
        """True when estimated token count exceeds the budget."""
        return self._estimate_tokens() > self._budget

    def compact(self, client: anthropic.Anthropic) -> str:
        """
        Summarise the middle of the conversation to free up context window.

        Strategy:
          Keep  : messages[0]  (original task — never discard)
          Summarise: messages[1:-2]  (middle turns — tool calls, iterations)
          Keep  : messages[-2:]  (two most recent turns — still relevant)

        The summary is also written to agentic memory so it survives the
        *next* compaction round as well.
        """
        if len(self._messages) < 5:
            return ""   # not enough history to bother

        to_compress = self._messages[1:-2]
        history_text = "\n".join(
            f"{m['role'].upper()}: {_content_to_str(m['content'])}"
            for m in to_compress
        )
        prompt = (
            "Summarise the following agent conversation in 4-6 sentences. "
            "Preserve: key findings, tool results, decisions made, errors encountered. "
            "Be factual and dense — no filler.\n\n" + history_text
        )
        resp = client.messages.create(
            model=COMPACTOR_MODEL,
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )
        summary: str = resp.content[0].text

        # Rebuild history with summary replacing the middle
        self._messages = (
            [self._messages[0]]
            + [{"role": "assistant", "content": f"[Compacted summary] {summary}"}]
            + self._messages[-2:]
        )

        # Persist key facts to agentic memory
        self.remember(f"Earlier progress (compacted): {summary[:150].rstrip()}…")
        return summary

    # Private 

    def _estimate_tokens(self) -> int:
        """
        Rough heuristic: ~4 characters per token.
        Good enough for triggering compaction; not a billing estimate.
        """
        chars = len(self._system) + sum(len(m) for m in self._memory)
        for msg in self._messages:
            chars += len(_content_to_str(msg["content"]))
        return chars // 4


# Utility 

def _content_to_str(content: Content) -> str:
    """Flatten any content value to plain text for token estimation."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict):
                parts.append(str(block.get("text") or block.get("content") or ""))
            elif hasattr(block, "text"):
                parts.append(block.text)
            else:
                parts.append(str(block))
        return " ".join(parts)
    return str(content)
