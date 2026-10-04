from dataclasses import dataclass
from typing import List

from app.services.evaluation.retrieval_dataset import (
    RetrievalEvaluationCase,
)
from app.services.evaluation.retrieval_metrics import (
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)
from app.services.retrieval.decomposed_retrieval_service import (
    decomposed_retrieval_service,
)


@dataclass
class RetrievalEvaluationResult:
    case_id: str
    question: str
    retrieved_chunk_ids: List[int]
    relevant_chunk_ids: List[int]
    recall_at_1: float
    recall_at_3: float
    recall_at_5: float
    precision_at_1: float
    mrr: float
    ndcg_at_3: float
    ndcg_at_5: float


class RetrievalEvaluator:

    def __init__(self):
        self.retrieval_service = decomposed_retrieval_service

    def evaluate_case(
        self,
        case: RetrievalEvaluationCase,
    ) -> RetrievalEvaluationResult:

        results = self.retrieval_service.retrieve(
            query=case.question,
            limit=5,
            department=case.department,
        )

        retrieved_chunk_ids = [
            result.chunk.id
            for result in results
        ]

        relevant_chunk_ids = set(
            case.relevant_chunk_ids
        )

        return RetrievalEvaluationResult(
            case_id=case.case_id,
            question=case.question,
            retrieved_chunk_ids=retrieved_chunk_ids,
            relevant_chunk_ids=case.relevant_chunk_ids,
            recall_at_1=recall_at_k(
                retrieved_chunk_ids,
                relevant_chunk_ids,
                1,
            ),
            recall_at_3=recall_at_k(
                retrieved_chunk_ids,
                relevant_chunk_ids,
                3,
            ),
            recall_at_5=recall_at_k(
                retrieved_chunk_ids,
                relevant_chunk_ids,
                5,
            ),
            precision_at_1=precision_at_k(
                retrieved_chunk_ids,
                relevant_chunk_ids,
                1,
            ),
            mrr=reciprocal_rank(
                retrieved_chunk_ids,
                relevant_chunk_ids,
            ),
            ndcg_at_3=ndcg_at_k(
                retrieved_chunk_ids,
                relevant_chunk_ids,
                3,
            ),
            ndcg_at_5=ndcg_at_k(
                retrieved_chunk_ids,
                relevant_chunk_ids,
                5,
            ),
        )

    def evaluate(
        self,
        dataset: List[RetrievalEvaluationCase],
    ) -> List[RetrievalEvaluationResult]:

        return [
            self.evaluate_case(case)
            for case in dataset
        ]