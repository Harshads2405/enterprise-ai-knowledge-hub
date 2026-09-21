import re
from typing import List, Tuple

from app.services.retrieval.retrieval_result import RetrievalResult


class CitationValidationResult:
    def __init__(
        self,
        answer: str,
        is_valid: bool,
        cited_source_numbers: List[int],
        invalid_source_numbers: List[int],
    ):
        self.answer = answer
        self.is_valid = is_valid
        self.cited_source_numbers = cited_source_numbers
        self.invalid_source_numbers = invalid_source_numbers


class CitationValidator:
    CITATION_PATTERN = re.compile(r"\[Source\s+(\d+)\]", re.IGNORECASE)

    def validate(
        self,
        answer: str,
        results: List[RetrievalResult],
    ) -> CitationValidationResult:

        if not answer:
            return CitationValidationResult(
                answer=answer,
                is_valid=True,
                cited_source_numbers=[],
                invalid_source_numbers=[],
            )

        available_source_numbers = set(
            range(1, len(results) + 1)
        )

        cited_source_numbers = [
            int(match)
            for match in self.CITATION_PATTERN.findall(answer)
        ]

        invalid_source_numbers = sorted(
            {
                source_number
                for source_number in cited_source_numbers
                if source_number not in available_source_numbers
            }
        )

        return CitationValidationResult(
            answer=answer,
            is_valid=not invalid_source_numbers,
            cited_source_numbers=sorted(set(cited_source_numbers)),
            invalid_source_numbers=invalid_source_numbers,
        )


citation_validator = CitationValidator()