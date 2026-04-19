from typing import TypedDict, Annotated
import operator


class GaiaState(TypedDict):
    # Input
    question: str
    file_path: str | None       # optional attached file

    # P0.1: Planning layer
    plan: str                   # step-by-step plan generated before ReAct loop

    # P0.2: Multi-round search
    search_round: int           # current round index (starts at 0)
    is_sufficient: bool         # sufficiency_judge verdict
    info_gaps: str              # what's still missing, injected into next round

    # ReAct loop
    messages: Annotated[list, operator.add]  # full message history

    # Output
    final_answer: str
