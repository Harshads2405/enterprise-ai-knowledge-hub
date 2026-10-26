import json
import re
import time
from pathlib import Path

from sqlalchemy import select

from app.db.session import SessionLocal
from app.core.config import get_evaluation_organization_id
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.retrieval.retrieval_result import RetrievalResult

from app.services.rag.rag_service import rag_service

from evaluation.evaluators.citation_correctness_judge import (
    CitationCorrectnessJudge,
    CitationCorrectnessJudgeError,
)


BASE_DIR = Path(__file__).resolve().parents[2]

BASELINE_PATH = (
    BASE_DIR
    / "evaluation"
    / "results"
    / "real_llm_rag_baseline.json"
)

OUTPUT_PATH = (
    BASE_DIR
    / "evaluation"
    / "results"
    / "citation_correctness_baseline.json"
)


CITATION_PATTERN = re.compile(
    r"\[Source\s+(\d+)\]",
    re.IGNORECASE,
)


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_baseline():
    return load_json(BASELINE_PATH)


def extract_citation_claims(answer: str):
    claims = []

    if not answer:
        return claims

    matches = list(
        CITATION_PATTERN.finditer(answer)
    )

    if not matches:
        return claims

    previous_citation_end = 0
    index = 0

    while index < len(matches):
        first_match = matches[index]

        # Text since the previous citation block is the candidate claim.
        claim_text = answer[
            previous_citation_end:first_match.start()
        ].strip()

        source_numbers = [
            int(first_match.group(1))
        ]

        citation_block_end = first_match.end()
        next_index = index + 1

        # Collect consecutive citations belonging to the same claim.
        while next_index < len(matches):
            next_match = matches[next_index]

            between_citations = answer[
                citation_block_end:next_match.start()
            ]

            if between_citations.strip():
                break

            source_numbers.append(
                int(next_match.group(1))
            )

            citation_block_end = next_match.end()
            next_index += 1

        if claim_text:
            # If the segment contains multiple sentences,
            # use the final sentence immediately preceding
            # the citation block.
            sentence_parts = re.split(
                r"(?<=[.!?])\s+",
                claim_text,
            )

            claim = sentence_parts[-1].strip()

            if claim:
                claims.append(
                    {
                        "claim": claim,
                        "source_numbers": source_numbers,
                    }
                )

        previous_citation_end = citation_block_end
        index = next_index

    return claims

def build_retrieved_results(case):
    expected_chunk_ids = case.get("retrieved_chunk_ids", [])

    if not expected_chunk_ids:
        return []

    with SessionLocal() as db:
        statement = select(DocumentChunk).where(
            DocumentChunk.id.in_(expected_chunk_ids),
            Document.organization_id == get_evaluation_organization_id(),
        ).join(
            Document,
            DocumentChunk.document_id == Document.id,
        )

        chunks = db.scalars(statement).all()

        chunks_by_id = {
            chunk.id: chunk
            for chunk in chunks
        }

        missing_chunk_ids = [
            chunk_id
            for chunk_id in expected_chunk_ids
            if chunk_id not in chunks_by_id
        ]

        if missing_chunk_ids:
            raise ValueError(
                "Baseline chunks were not found in the database: "
                f"{missing_chunk_ids}"
            )

        # Preserve the exact order recorded in the baseline.
        ordered_chunks = [
            chunks_by_id[chunk_id]
            for chunk_id in expected_chunk_ids
        ]

        return [
            RetrievalResult(
                chunk=chunk,
                retrieval_score=0.0,
            )
            for chunk in ordered_chunks
        ]

def align_results_with_baseline(
    retrieved_results,
    expected_chunk_ids,
):
    results_by_chunk_id = {
        result.chunk.id: result
        for result in retrieved_results
    }

    missing_chunk_ids = [
        chunk_id
        for chunk_id in expected_chunk_ids
        if chunk_id not in results_by_chunk_id
    ]

    if missing_chunk_ids:
        raise ValueError(
            "Baseline retrieval chunks were not reproduced: "
            f"{missing_chunk_ids}"
        )

    return [
        results_by_chunk_id[chunk_id]
        for chunk_id in expected_chunk_ids
    ]

def evaluate():
    baseline_cases = load_baseline()

    judge = CitationCorrectnessJudge()

    results = []

    total = len(baseline_cases)

    for index, case in enumerate(
        baseline_cases,
        start=1,
    ):
        case_id = case["id"]

        print(f"[{index}/{total}] {case_id}")

        answer = case.get("answer", "")
        should_clarify = case.get(
            "should_clarify",
            False,
        )

        result = {
            "id": case_id,
            "question": case["question"],
            "generated_answer": answer,
            "retrieved_chunk_ids": case.get(
                "retrieved_chunk_ids",
                [],
            ),
            "should_clarify": should_clarify,
            "citations": [],
            "average_citation_correctness": None,
            "error": None,
        }

        if should_clarify:
            print(
                "  clarification case - "
                "citation scoring skipped"
            )

            result["reason"] = (
                "Citation scoring skipped because the "
                "RAG system correctly requested clarification."
            )

            results.append(result)
            continue

        try:
            retrieved_results = build_retrieved_results(
                case
            )

            citation_claims = extract_citation_claims(
                answer
            )

            if not citation_claims:
                result["reason"] = (
                    "No citations were found in the generated answer."
                )

                print("  no citations found")

                results.append(result)
                continue

            case_scores = []

            for citation_claim in citation_claims:
                claim = citation_claim["claim"]

                for source_number in citation_claim[
                    "source_numbers"
                ]:
                    citation_result = {
                        "source_number": source_number,
                        "claim": claim,
                        "citation_correctness": None,
                        "reason": "",
                        "judge_latency_ms": None,
                        "error": None,
                    }

                    source_index = source_number - 1

                    if (
                        source_index < 0
                        or source_index >= len(
                            retrieved_results
                        )
                    ):
                        citation_result["error"] = (
                            "Citation references an unavailable "
                            "retrieved source."
                        )

                        print(
                            f"  Source {source_number}: "
                            "invalid source number"
                        )

                        result["citations"].append(
                            citation_result
                        )

                        continue

                    retrieval_result = retrieved_results[
                        source_index
                    ]

                    cited_source = (
                        retrieval_result.chunk.content
                    )

                    try:
                        started_at = time.perf_counter()

                        judge_result = judge.evaluate(
                            question=case["question"],
                            claim=claim,
                            cited_source=cited_source,
                        )

                        citation_result[
                            "judge_latency_ms"
                        ] = round(
                            (
                                time.perf_counter()
                                - started_at
                            )
                            * 1000,
                            2,
                        )

                        citation_result[
                            "citation_correctness"
                        ] = judge_result[
                            "citation_correctness"
                        ]

                        citation_result["reason"] = (
                            judge_result["reason"]
                        )

                        case_scores.append(
                            judge_result[
                                "citation_correctness"
                            ]
                        )

                        print(
                            f"  Source {source_number}: "
                            f"{judge_result['citation_correctness']}/5"
                        )

                    except CitationCorrectnessJudgeError as exc:
                        citation_result["error"] = str(exc)

                        print(
                            f"  Source {source_number}: "
                            f"ERROR: {exc}"
                        )

                    result["citations"].append(
                        citation_result
                    )

            if case_scores:
                result[
                    "average_citation_correctness"
                ] = round(
                    sum(case_scores) / len(case_scores),
                    4,
                )

        except Exception as exc:
            result["error"] = str(exc)

            print(f"  ERROR: {exc}")

        results.append(result)

    scored_cases = [
        result
        for result in results
        if result[
            "average_citation_correctness"
        ]
        is not None
    ]

    clarification_cases = [
        result
        for result in results
        if result["should_clarify"]
    ]

    failed_cases = [
        result
        for result in results
        if result["error"] is not None
    ]

    citation_scores = [
        result["average_citation_correctness"]
        for result in scored_cases
    ]

    summary = {
        "total_cases": total,
        "citation_scored_cases": len(
            scored_cases
        ),
        "clarification_cases": len(
            clarification_cases
        ),
        "failed_cases": len(
            failed_cases
        ),
        "average_citation_correctness": (
            round(
                sum(citation_scores)
                / len(citation_scores),
                4,
            )
            if citation_scores
            else None
        ),
    }

    output = {
        "summary": summary,
        "results": results,
    }

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            output,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print()
    print("=" * 60)
    print("CITATION CORRECTNESS EVALUATION SUMMARY")
    print("=" * 60)
    print(
        f"Total cases:                 "
        f"{summary['total_cases']}"
    )
    print(
        "Citation-scored cases:       "
        f"{summary['citation_scored_cases']}"
    )
    print(
        "Clarification cases:         "
        f"{summary['clarification_cases']}"
    )
    print(
        f"Failed cases:                "
        f"{summary['failed_cases']}"
    )
    print(
        "Average citation correctness:"
        f" {summary['average_citation_correctness']}/5"
    )
    print(
        f"Results saved to:            "
        f"{OUTPUT_PATH}"
    )


if __name__ == "__main__":
    evaluate()
