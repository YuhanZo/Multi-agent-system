"""
GAIA Benchmark Evaluation Script
Runs GAIA Level 1 validation set and reports exact match score.
"""
import sys
import io
import os
import time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from dotenv import load_dotenv
load_dotenv()

from datasets import load_dataset
from app.agent.gaia_agent.graph import gaia_graph


def normalize(answer: str) -> str:
    """Normalize answer for exact match comparison."""
    return answer.strip().lower()


def run_eval(level: int = 1, max_questions: int = None):
    print(f"Loading GAIA Level {level} validation set...")
    ds = load_dataset(
        "gaia-benchmark/GAIA",
        f"2023_level{level}",
        split="validation",
    )

    if max_questions:
        ds = ds.select(range(min(max_questions, len(ds))))

    total = len(ds)
    correct = 0
    results = []

    print(f"Running {total} questions...\n")
    print("=" * 60)

    for i, example in enumerate(ds):
        question = example["Question"]
        expected = example["Final answer"]
        file_path = example.get("file_path", "")

        print(f"[{i+1}/{total}] {question[:80]}...")

        got = ""
        is_correct = False
        for attempt in range(3):
            try:
                state = {"question": question, "file_path": file_path, "messages": []}
                result = gaia_graph.invoke(state)
                got = result.get("final_answer", "")
                is_correct = normalize(got) == normalize(expected)
                if is_correct:
                    correct += 1
                break
            except Exception as e:
                err = str(e)
                if "429" in err or "rate_limit" in err:
                    wait = 30 * (attempt + 1)
                    print(f"  Rate limit, waiting {wait}s...")
                    time.sleep(wait)
                else:
                    print(f"  ✗ ERROR: {e}")
                    break

        status = "✓" if is_correct else "✗"
        print(f"  {status} Expected: {expected} | Got: {got}")
        results.append({"question": question, "expected": expected, "got": got, "correct": is_correct})
        print()

        # Delay between questions to avoid rate limits
        if i < total - 1:
            time.sleep(10)

    print("=" * 60)
    print(f"Score: {correct}/{total} = {correct/total*100:.1f}%")
    return results


if __name__ == "__main__":
    # Pass a number as argument to limit questions, e.g.: python eval_gaia.py 5
    # No argument = run all 53 questions
    max_q = int(sys.argv[1]) if len(sys.argv) > 1 else None
    run_eval(level=1, max_questions=max_q)
