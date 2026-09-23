from app.services.langchain.llm import EnterpriseChatModel


class LangChainGenerationService:
    """Generate answers through the LangChain LLM adapter."""

    def __init__(self):
        self.llm = EnterpriseChatModel()

    def generate(self, prompt: str) -> str:
        if not prompt or not prompt.strip():
            raise ValueError("Generation prompt cannot be empty.")

        response = self.llm.invoke(prompt)

        content = response.content

        if not content or not str(content).strip():
            raise ValueError(
                "LangChain LLM returned an empty response."
            )

        return str(content).strip()


langchain_generation_service = LangChainGenerationService()
