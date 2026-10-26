from evaluation.runners import rag_retrieval_runner


def test_runner_passes_configured_organization_to_evaluator(monkeypatch):
    captured = {}

    class FakeEvaluator:
        def __init__(self, organization_id):
            captured["organization_id"] = organization_id

        def evaluate(self, dataset):
            return dataset

    monkeypatch.setattr(
        rag_retrieval_runner,
        "get_evaluation_organization_id",
        lambda: 23,
    )
    monkeypatch.setattr(
        rag_retrieval_runner,
        "load_retrieval_evaluation_dataset",
        lambda: ["case"],
    )
    monkeypatch.setattr(
        rag_retrieval_runner,
        "RetrievalEvaluator",
        FakeEvaluator,
    )

    assert rag_retrieval_runner.run_evaluation() == ["case"]
    assert captured["organization_id"] == 23
