from app.services.retrieval.retrieval_pipeline import retrieval_pipeline
from app.services.retrieval.retrieval_result import RetrievalResult


DECOMPOSED_CASES = [
    {
        "id": "ambiguous_001",
        "question": "What are the requirements for working remotely?",
        "queries": [
            "remote work requirements",
        ],
        "expected": [27],
        "department": "HR",
    },
    {
        "id": "ambiguous_002",
        "question": "What are the requirements for employee leave?",
        "queries": [
            "employee leave requirements",
        ],
        "expected": [26],
        "department": "HR",
    },
    {
        "id": "ambiguous_003",
        "question": "What is the expense policy?",
        "queries": [
            "expense policy",
            "reimbursement policy",
        ],
        "expected": [28, 29],
        "department": "Finance",
    },
    {
        "id": "ambiguous_004",
        "question": "How are security incidents handled?",
        "queries": [
            "security incident handling",
            "security incident response",
        ],
        "expected": [31, 33],
        "department": "IT",
    },
    {
        "id": "ambiguous_005",
        "question": "What happens when access is not authorized?",
        "queries": [
            "unauthorized access",
            "access control requirements",
        ],
        "expected": [32],
        "department": "IT",
    },
    {
        "id": "ambiguous_006",
        "question": (
            "What approval requirements apply to remote work, "
            "travel, and expenses?"
        ),
        "queries": [
            "remote work approval requirements",
            "business travel approval requirements",
            "business expense approval requirements",
        ],
        "expected": [27, 30, 28],
        "department": None,
    },
]


def retrieve_decomposed(
    queries,
    limit=5,
    department=None,
):
    unique_results = {}

    for query in queries:
        results = retrieval_pipeline.retrieve(
            search_queries=[query],
            limit=limit,
            department=department,
        )

        for result in results:
            chunk_id = result.chunk.id

            if chunk_id not in unique_results:
                unique_results[chunk_id] = result
                continue

            existing = unique_results[chunk_id]

            existing.retrieval_queries.extend(
                result.retrieval_queries
            )

            existing.retrieval_ranks.extend(
                result.retrieval_ranks
            )

            existing.retrieval_count += result.retrieval_count

            if (
                result.best_retrieval_rank is not None
                and (
                    existing.best_retrieval_rank is None
                    or result.best_retrieval_rank
                    < existing.best_retrieval_rank
                )
            ):
                existing.best_retrieval_rank = (
                    result.best_retrieval_rank
                )

            existing.reranker_scores.extend(
                result.reranker_scores
            )

            existing.reranker_queries.extend(
                result.reranker_queries
            )

            if (
                result.best_reranker_score is not None
                and (
                    existing.best_reranker_score is None
                    or result.best_reranker_score
                    > existing.best_reranker_score
                )
            ):
                existing.best_reranker_score = (
                    result.best_reranker_score
                )

                existing.best_reranker_query = (
                    result.best_reranker_query
                )

    results = list(unique_results.values())

    for result in results:
        result.reranker_score = result.best_reranker_score

    results.sort(
        key=lambda result: (
            result.best_reranker_score
            if result.best_reranker_score is not None
            else float("-inf")
        ),
        reverse=True,
    )

    return results[:limit]


def main():
    total = len(DECOMPOSED_CASES)
    passed = 0

    print("=" * 70)
    print("DECOMPOSED RETRIEVAL EXPERIMENT")
    print("Groq-independent evaluation")
    print("=" * 70)

    for case in DECOMPOSED_CASES:
        print()
        print(f"Case: {case['id']}")
        print(f"Question: {case['question']}")
        print(f"Queries: {case['queries']}")

        results = retrieve_decomposed(
            queries=case["queries"],
            limit=5,
            department=case["department"],
        )

        retrieved = [result.chunk.id for result in results]
        expected = case["expected"]

        all_required = all(
            chunk_id in retrieved
            for chunk_id in expected
        )

        if all_required:
            passed += 1
            status = "PASS"
        else:
            status = "FAIL"

        print(f"Expected:  {expected}")
        print(f"Retrieved: {retrieved}")
        print(f"Status:    {status}")

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total:  {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Recall-style success: {passed / total:.4f}")
    print("=" * 70)


if __name__ == "__main__":
    main()
