from typing import TypedDict, Annotated
import operator


class GaiaState(TypedDict):
    # Input
    question: str
    file_path: str | None       # optional attached file

    # ReAct loop
    messages: Annotated[list, operator.add]  # full message history

    # Output
    final_answer: str
