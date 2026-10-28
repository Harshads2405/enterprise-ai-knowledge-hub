
import logging

from app.core.config import settings
from app.services.llm.groq_client import (
    LLMClientError,
    groq_client,
)

logger = logging.getLogger(__name__)


class QueryRewriterService:

    def rewrite(self, query: str) -> str:
        if not query or not query.strip():
            return query

        original_query = query.strip()

        if settings.llm_mode.lower() == "mock":
            return original_query

        prompt = f"""
Rewrite the following user query into a concise search query
for an enterprise knowledge base.

Rules:
- Preserve the user's exact intent.
- Preserve important entities and terminology.
- Resolve vague wording when possible.
- Do not answer the question.
- Do not invent facts.
- Do not add unsupported details.
- Keep the rewritten query concise.
- Return only the rewritten search query.
- If the original query is already clear, keep it nearly unchanged.

User query:
{original_query}
"""

        try:
            rewritten_query = groq_client.chat(prompt)

            if not rewritten_query or not rewritten_query.strip():
                logger.warning(
                    "Query rewriting returned empty content; "
                    "using the original query."
                )
                return original_query

            return rewritten_query.strip()

        except LLMClientError:
            logger.warning(
                "Query rewriting failed; using the original query.",
                exc_info=True,
            )
            return original_query


query_rewriter_service = QueryRewriterService()
