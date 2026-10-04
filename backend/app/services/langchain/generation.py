from typing import Dict

from langchain_core.prompts import ChatPromptTemplate

from app.services.langchain.llm import EnterpriseChatModel


class LangChainGenerationService:
    """Generate answers through the LangChain LLM adapter."""

    def __init__(self):
        self.llm = EnterpriseChatModel()

    def generate(self, prompt: str) -> str:
        if not prompt or not prompt.strip():
            raise ValueError("Generation prompt cannot be empty.")

        response = self.llm.invoke(prompt)

        return self._extract_content(response)

    def generate_from_prompt(
        self,
        prompt: ChatPromptTemplate,
        variables: Dict[str, str],
    ) -> str:
        if not prompt:
            raise ValueError("Generation prompt cannot be empty.")

        response = prompt.invoke(variables)

        llm_response = self.llm.invoke(response)

        return self._extract_content(llm_response)

    @staticmethod
    def _extract_content(response) -> str:
        content = response.content

        if not content or not str(content).strip():
            raise ValueError(
                "LangChain LLM returned an empty response."
            )

        return str(content).strip()


langchain_generation_service = LangChainGenerationService()
