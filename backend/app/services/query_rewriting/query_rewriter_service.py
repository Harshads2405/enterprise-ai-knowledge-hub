from app.services.llm.groq_client import groq_client


class QueryRewriterService:
    def rewrite(self, query: str) -> str:
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
{query}
"""

        rewritten_query = groq_client.chat(prompt)

        return rewritten_query.strip()


query_rewriter_service = QueryRewriterService()