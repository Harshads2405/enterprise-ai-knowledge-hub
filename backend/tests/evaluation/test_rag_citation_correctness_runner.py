from evaluation.runners.rag_citation_correctness_runner import (
    extract_citation_claims,
)


def test_extract_citation_claims_with_multiple_sources():
    answer = (
        "Employees are entitled to 20 days of annual leave per year. "
        "[Source\u202f1] [Source\u202f2]"
    )

    claims = extract_citation_claims(answer)

    assert claims == [
        {
            "claim": (
                "Employees are entitled to 20 days of annual leave per year."
            ),
            "source_numbers": [1, 2],
        }
    ]


def test_extract_citation_claims_with_multiple_claims():
    answer = (
        "Employees receive 20 days of annual leave. [Source\u202f1] "
        "Managers approve annual leave requests. [Source\u202f2]"
    )

    claims = extract_citation_claims(answer)

    assert claims == [
        {
            "claim": "Employees receive 20 days of annual leave.",
            "source_numbers": [1],
        },
        {
            "claim": "Managers approve annual leave requests.",
            "source_numbers": [2],
        },
    ]


def test_extract_citation_claims_without_citations():
    answer = "Employees receive annual leave."

    claims = extract_citation_claims(answer)

    assert claims == []