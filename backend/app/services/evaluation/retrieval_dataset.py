import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass(frozen=True)
class RetrievalEvaluationCase:
    case_id: str
    question: str
    relevant_document_ids: List[int]
    relevant_chunk_ids: List[int]
    department: Optional[str]
    relevance_type: str


def load_retrieval_evaluation_dataset() -> List[RetrievalEvaluationCase]:
    base_dir = Path(__file__).resolve().parents[3]
    dataset_path = (
        base_dir
        / "evaluation"
        / "datasets"
        / "rag_evaluation.json"
    )

    with open(dataset_path, "r", encoding="utf-8") as file:
        raw_cases = json.load(file)

    return [
        RetrievalEvaluationCase(
            case_id=case["id"],
            question=case["question"],
            relevant_document_ids=case.get(
                "relevant_document_ids",
                [],
            ),
            relevant_chunk_ids=case["relevant_chunk_ids"],
            department=case.get("department"),
            relevance_type=case.get(
                "relevance_type",
                "any",
            ),
        )
        for case in raw_cases
    ]


RETRIEVAL_EVALUATION_DATASET = (
    load_retrieval_evaluation_dataset()
)