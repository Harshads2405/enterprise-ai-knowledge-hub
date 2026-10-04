import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(BASE_DIR))

from app.services.evaluation.retrieval_dataset import (
    load_retrieval_evaluation_dataset,
)
from app.services.evaluation.retrieval_evaluator import (
    RetrievalEvaluator,
)


def run_evaluation():
    dataset = load_retrieval_evaluation_dataset()

    evaluator = RetrievalEvaluator()

    return evaluator.evaluate(dataset)


if __name__ == "__main__":
    results = run_evaluation()

    print()
    print("ADVANCED RAG RETRIEVAL EVALUATION")
    print("=" * 60)

    for result in results:
        print()
        print(f"ID: {result.case_id}")
        print(f"Question: {result.question}")
        print(f"Expected: {result.relevant_chunk_ids}")
        print(f"Retrieved: {result.retrieved_chunk_ids}")

        relevant_retrieved = [
            chunk_id
            for chunk_id in result.retrieved_chunk_ids
            if chunk_id in result.relevant_chunk_ids
        ]

        print(f"Relevant Retrieved: {relevant_retrieved}")

        print(
            f"R@1={result.recall_at_1:.4f} | "
            f"R@3={result.recall_at_3:.4f} | "
            f"R@5={result.recall_at_5:.4f}"
        )

    count = len(results)

    print()
    print("=" * 60)
    print("ADVANCED RAG EVALUATION SUMMARY")
    print("=" * 60)
    print("Corpus: HR + Finance + IT")
    print("Documents: 9")
    print("Benchmark: V2 - Ambiguous Retrieval")
    print(f"Evaluation Cases: {count}")
    print()

    if count:
        print(
            f"Recall@1:     "
            f"{sum(r.recall_at_1 for r in results) / count:.4f}"
        )

        print(
            f"Recall@3:     "
            f"{sum(r.recall_at_3 for r in results) / count:.4f}"
        )

        print(
            f"Recall@5:     "
            f"{sum(r.recall_at_5 for r in results) / count:.4f}"
        )

        print(
            f"Precision@1:  "
            f"{sum(r.precision_at_1 for r in results) / count:.4f}"
        )

        print(
            f"MRR:          "
            f"{sum(r.mrr for r in results) / count:.4f}"
        )

        print(
            f"NDCG@3:       "
            f"{sum(r.ndcg_at_3 for r in results) / count:.4f}"
        )

        print(
            f"NDCG@5:       "
            f"{sum(r.ndcg_at_5 for r in results) / count:.4f}"
        )