from unittest.mock import Mock

from app.services.evaluation.retrieval_dataset import (
    RetrievalEvaluationCase,
)
from app.services.evaluation.retrieval_evaluator import RetrievalEvaluator


def test_retrieval_evaluator_passes_organization_id_to_retrieval_service():
    evaluator = RetrievalEvaluator(organization_id=17)
    evaluator.retrieval_service = Mock()
    evaluator.retrieval_service.retrieve.return_value = []
    case = RetrievalEvaluationCase(
        case_id="case-1",
        question="What is the leave policy?",
        relevant_document_ids=[],
        relevant_chunk_ids=[],
        department="HR",
        relevance_type="any",
    )

    evaluator.evaluate_case(case)

    evaluator.retrieval_service.retrieve.assert_called_once_with(
        query=case.question,
        organization_id=17,
        limit=5,
        department="HR",
    )
