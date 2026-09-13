class RAGPromptBuilder:
    def build(
        self,
        question: str,
        context: str,
    ) -> str:
        return f"""You are an enterprise AI assistant.

Answer the user's question using only the provided context.

If the answer cannot be found in the context, say:
"I don't have enough information in the provided knowledge base to answer that."

Do not invent facts or information.

Context:
{context}

User Question:
{question}

Answer:"""


rag_prompt_builder = RAGPromptBuilder()