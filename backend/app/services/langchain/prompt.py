from langchain_core.prompts import ChatPromptTemplate

from app.services.rag.prompts.rag_prompt import (
    RAGPromptBuilder,
)


class EnterpriseRAGPrompt:
    """LangChain representation of the existing RAG prompt."""

    def __init__(self):
        self.prompt_builder = RAGPromptBuilder()

    def build(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    self.prompt_builder.SYSTEM_INSTRUCTIONS
                    + """

KNOWLEDGE BASE CONTEXT
======================
{context}""",
                ),
                (
                    "human",
                    """USER QUESTION
=============

{question}

ANSWER
======
Provide a concise answer using only the knowledge-base context above.

Include source references such as [Source 1] immediately after the factual
statement they support.""",
                ),
            ]
        )


enterprise_rag_prompt = EnterpriseRAGPrompt()
