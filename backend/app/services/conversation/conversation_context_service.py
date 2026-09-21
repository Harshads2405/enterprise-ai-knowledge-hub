from typing import List

from app.models.message import Message


class ConversationContextService:

    MAX_MESSAGES = 10
    MAX_MESSAGE_LENGTH = 1000

    def get_recent_messages(
        self,
        messages: List[Message],
    ) -> List[Message]:

        if not messages:
            return []

        return messages[-self.MAX_MESSAGES:]

    def build_context(
        self,
        messages: List[Message],
    ) -> str:

        recent_messages = self.get_recent_messages(messages)

        if not recent_messages:
            return ""

        context_parts = []

        for message in recent_messages:
            content = (message.content or "").strip()

            if not content:
                continue

            content = content[:self.MAX_MESSAGE_LENGTH]

            context_parts.append(
                f"{message.role}: {content}"
            )

        return "\n".join(context_parts)

    def build_contextual_query(
        self,
        current_query: str,
        messages: List[Message],
    ) -> str:

        current_query = current_query.strip()

        if not current_query:
            return current_query

        recent_messages = self.get_recent_messages(messages)

        if not recent_messages:
            return current_query

        previous_user_messages = [
            message
            for message in recent_messages
            if message.role == "user"
        ]

        if not previous_user_messages:
            return current_query

        previous_query = (
            previous_user_messages[-1].content or ""
        ).strip()

        if not previous_query:
            return current_query

        if not self._looks_like_follow_up(current_query):
            return current_query

        return (
            f"Previous user question: {previous_query}\n"
            f"Current user question: {current_query}"
        )

    def _looks_like_follow_up(
        self,
        query: str,
    ) -> bool:

        normalized = " ".join(
            query.lower().split()
        )

        follow_up_patterns = (
            "what about",
            "how about",
            "what documents",
            "which documents",
            "what is required",
            "what are required",
            "and what",
            "what else",
            "how much",
            "when can i",
            "when should i",
            "who handles it",
            "who handles this",
            "who approves it",
            "who approves this",
            "can i do that",
            "can i do this",
            "what about this",
            "what about that",
            "how does it work",
            "what does it mean",
        )

        if any(
            pattern in normalized
            for pattern in follow_up_patterns
        ):
            return True

        pronoun_patterns = (
            "this",
            "that",
            "it",
            "they",
            "them",
            "their",
            "those",
            "these",
        )

        words = normalized.split()

        return (
            len(words) <= 8
            and any(
                word in pronoun_patterns
                for word in words
            )
        )


conversation_context_service = ConversationContextService()