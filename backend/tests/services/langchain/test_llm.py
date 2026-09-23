from langchain_core.messages import HumanMessage

from app.services.langchain.llm import EnterpriseChatModel


def test_enterprise_chat_model_generates_response():
    llm = EnterpriseChatModel()

    response = llm.invoke(
        [
            HumanMessage(
                content="Explain what RAG is."
            )
        ]
    )

    assert response.content
    assert isinstance(response.content, str)
