from groq import Groq

from app.core.config import settings


class GroqClient:
    def __init__(self):
        self.client = Groq(
            api_key=settings.groq_api_key,
        )

    def chat(
        self,
        message: str,
        model: str = "openai/gpt-oss-20b",
    ) -> str:

        if settings.llm_mode == "mock":
            return self._mock_response(message)

        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": message,
                }
            ],
        )

        return response.choices[0].message.content

    def _mock_response(self, message: str) -> str:
        return ""


groq_client = GroqClient()
