from typing import Any, Dict, List, Optional


class ConversationStateService:

    CLARIFICATION_MESSAGE_TYPE = (
        "clarification"
    )

    CLARIFICATION_RESPONSE_TYPE = (
        "clarification_response"
    )

    def build_clarification_metadata(
        self,
        original_query: str,
        options: List[Dict[str, str]],
    ) -> Dict[str, Any]:

        return {
            "type": self.CLARIFICATION_MESSAGE_TYPE,
            "pending": True,
            "original_query": original_query,
            "options": options,
        }

    def build_clarification_response_metadata(
        self,
        selected_topic: str,
        original_query: str,
    ) -> Dict[str, Any]:

        return {
            "type": (
                self.CLARIFICATION_RESPONSE_TYPE
            ),
            "pending": False,
            "selected_topic": selected_topic,
            "original_query": original_query,
        }

    def is_pending_clarification(
        self,
        metadata: Optional[Dict[str, Any]],
    ) -> bool:

        if not metadata:
            return False

        return (
            metadata.get("type")
            == self.CLARIFICATION_MESSAGE_TYPE
            and metadata.get("pending") is True
        )

    def get_original_query(
        self,
        metadata: Optional[Dict[str, Any]],
    ) -> Optional[str]:

        if not metadata:
            return None

        return metadata.get(
            "original_query"
        )

    def get_options(
        self,
        metadata: Optional[Dict[str, Any]],
    ) -> List[Dict[str, str]]:

        if not metadata:
            return []

        options = metadata.get(
            "options",
            [],
        )

        if not isinstance(options, list):
            return []

        return options

    def find_selected_topic(
        self,
        user_input: str,
        options: List[Dict[str, str]],
    ) -> Optional[str]:

        normalized_input = (
            " ".join(
                user_input.lower().split()
            )
        )

        for option in options:

            topic = (
                option.get("topic", "")
            )

            label = (
                option.get("label", "")
            )

            if not topic:
                continue

            normalized_topic = (
                " ".join(
                    topic.lower().split()
                )
            )

            normalized_label = (
                " ".join(
                    label.lower().split()
                )
            )

            if (
                normalized_input
                == normalized_topic
            ):
                return topic

            if (
                normalized_input
                == normalized_label
            ):
                return topic

        return None


conversation_state_service = (
    ConversationStateService()
)