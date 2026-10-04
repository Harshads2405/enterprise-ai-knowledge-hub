import json
import sys
import time
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
DATASET_PATH = BASE_DIR / "evaluation" / "datasets" / "rag_evaluation.json"

sys.path.insert(0, str(BASE_DIR))

from app.services.rag.rag_service import rag_service


def load_dataset():
    with open(DATASET_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def evaluate_case(case):
    start = time.perf_counter()

    try:
        response = rag_service.generate(case["question"])
        latency_ms = (time.perf_counter() - start) * 1000

        sources = []

        for source in response.sources or []:
            sources.append(
                {
                    "document_id": getattr(source, "document_id", None),
                    "chunk_id": getattr(source, "chunk_id", None),
                    "rank": getattr(source, "rank", None),
                }
            )

        retrieved_chunk_ids = [
            source["chunk_id"]
            for source in sources
            if source["chunk_id"] is not None
        ]

        return {
            "id": case["id"],
            "question": case["question"],
            "expected_chunk_ids": case["relevant_chunk_ids"],
            "retrieved_chunk_ids": retrieved_chunk_ids,
            "answer": response.answer,
            "sources": sources,
            "should_clarify": response.should_clarify,
            "latency_ms": round(latency_ms, 2),
            "error": None,
        }

    except Exception as exc:
        latency_ms = (time.perf_counter() - start) * 1000

        return {
            "id": case["id"],
            "question": case["question"],
            "expected_chunk_ids": case["relevant_chunk_ids"],
            "retrieved_chunk_ids": [],
            "answer": None,
            "sources": [],
            "should_clarify": None,
            "latency_ms": round(latency_ms, 2),
            "error": f"{type(exc).__name__}: {exc}",
        }


def print_case(result):
    print()
    print("-" * 80)
    print(f"ID: {result['id']}")
    print(f"Question: {result['question']}")
    print(f"Expected chunks: {result['expected_chunk_ids']}")
    print(f"Retrieved chunks: {result['retrieved_chunk_ids']}")
    print(f"Should clarify: {result['should_clarify']}")
    print(f"Latency: {result['latency_ms']:.2f} ms")

    if result["error"]:
        print(f"ERROR: {result['error']}")
    else:
        print(f"Answer: {result['answer']}")


def print_summary(results):
    total = len(results)
    successful = [result for result in results if result["error"] is None]
    failed = [result for result in results if result["error"] is not None]

    latencies = [
        result["latency_ms"]
        for result in successful
    ]

    average_latency = (
        sum(latencies) / len(latencies)
        if latencies
        else 0.0
    )

    print()
    print("=" * 80)
    print("REAL LLM RAG EVALUATION SUMMARY")
    print("=" * 80)
    print(f"Evaluation cases: {total}")
    print(f"Successful:       {len(successful)}")
    print(f"Failed:           {len(failed)}")
    print(f"Average latency:  {average_latency:.2f} ms")

    if failed:
        print()
        print("Failed cases:")
        for result in failed:
            print(
                f"- {result['id']}: "
                f"{result['error']}"
            )


def main():
    dataset = load_dataset()

    print("=" * 80)
    print("REAL LLM RAG EVALUATION")
    print("=" * 80)
    print(f"Dataset: {DATASET_PATH}")
    print(f"Evaluation cases: {len(dataset)}")
    print()
    print("LLM_MODE should be set to 'groq'.")
    print("This runner records the real RAG outputs.")
    print()

    results = []

    for index, case in enumerate(dataset, start=1):
        print(
            f"[{index}/{len(dataset)}] "
            f"Running {case['id']}..."
        )

        result = evaluate_case(case)
        results.append(result)

        print_case(result)

    print_summary(results)

    output_path = (
        BASE_DIR
        / "evaluation"
        / "results"
        / "real_llm_rag_baseline.json"
    )

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(results, file, indent=2, ensure_ascii=False)

    print()
    print(f"Results saved to: {output_path}")


if __name__ == "__main__":
    main()
