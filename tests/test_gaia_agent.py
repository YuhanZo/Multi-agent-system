"""
Quick smoke test for the GAIA agent.
Run: .venv/Scripts/python tests/test_gaia_agent.py
"""
import sys
import io
from dotenv import load_dotenv
load_dotenv()  # must be before any app imports

from app.agent.gaia_agent.graph import gaia_graph


SAMPLE_QUESTIONS = [
    {
        "question": "What is the capital of Australia?",
        "file_path": None,
        "expected": "Canberra",
    },
    {
        "question": "How many studio albums did Taylor Swift release before 2020?",
        "file_path": None,
        "expected": "7",
    },
]

# Create a small CSV file for the file-reading test
import os, csv
_TEST_CSV = os.path.join(os.path.dirname(__file__), "_tmp_scores.csv")
with open(_TEST_CSV, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["name", "score"])
    writer.writerows([["Alice", 95], ["Bob", 87], ["Carol", 92]])

SAMPLE_QUESTIONS.append({
    "question": f"What is the highest score in the file? (file: {_TEST_CSV})",
    "file_path": _TEST_CSV,
    "expected": "95",
})


def run_question(question: str, file_path: str | None = None) -> str:
    result = gaia_graph.invoke({
        "question": question,
        "file_path": file_path,
        "messages": [],
        "final_answer": "",
    })
    return result.get("final_answer", "")


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    for sample in SAMPLE_QUESTIONS:
        print(f"\nQ: {sample['question']}")
        print(f"Expected: {sample['expected']}")
        answer = run_question(sample["question"], sample.get("file_path"))
        match = "✓" if answer.strip().lower() == sample["expected"].lower() else "✗"
        print(f"Got: {answer}  {match}")
        print("-" * 60)

    # cleanup temp file
    if os.path.exists(_TEST_CSV):
        os.remove(_TEST_CSV)
