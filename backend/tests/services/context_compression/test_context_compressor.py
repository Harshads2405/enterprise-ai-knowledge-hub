from app.services.context_compression.context_compressor import (
    ContextCompressor,
)
from app.services.retrieval.retrieval_result import RetrievalResult


def test_annual_leave_approval_sentence_survives_compression():
    compressor = ContextCompressor(
        similarity_threshold=0.45,
        max_sentences=3,
    )

    result = RetrievalResult(
        chunk=type(
            "Chunk",
            (),
            {
                "content": (
                    "Enterprise HR Leave Policy. "
                    "Employees are entitled to 20 days of annual leave per calendar year. "
                    "Annual leave must be requested through the approved leave request process before the planned absence. "
                    "Employees should submit leave requests to their reporting manager through the company's designated leave system. "
                    "Managers are responsible for reviewing leave requests and approving them according to team requirements. "
                    "Unused annual leave may be handled according to the company's applicable leave carry-forward rules."
                ),
                "document": None,
            },
        )(),
        retrieval_score=1.0,
    )

    compressed = compressor.compress(
        query="Who should approve an annual leave request?",
        results=[result],
    )

    assert compressed

    content = compressed[0].compressed_content

    assert (
        "Managers are responsible for reviewing leave requests "
        "and approving them according to team requirements."
        in content
    )


def test_remote_work_manager_approval_sentence_survives_compression():
    compressor = ContextCompressor(
        similarity_threshold=0.45,
        max_sentences=3,
    )

    result = RetrievalResult(
        chunk=type(
            "Chunk",
            (),
            {
                "content": (
                    "Enterprise Remote Work Policy. "
                    "Employees may work remotely when their role and business requirements permit remote work. "
                    "Remote work requests must be submitted through the approved remote work request process. "
                    "Employees should obtain manager approval before working remotely. "
                    "Managers may consider business needs, team collaboration, employee responsibilities, and operational requirements when reviewing remote work requests. "
                    "Employees working remotely are expected to remain available during their agreed working hours. "
                    "This policy applies to employees who are eligible for remote work."
                ),
                "document": None,
            },
        )(),
        retrieval_score=1.0,
    )

    compressed = compressor.compress(
        query="What is the remote work policy?",
        results=[result],
    )

    assert compressed

    content = compressed[0].compressed_content

    assert (
        "Employees should obtain manager approval before working remotely."
        in content
    )
