from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

from app.services.langchain.llm import EnterpriseChatModel
from app.services.langchain.retriever import EnterpriseRetriever


SYSTEM_PROMPT = """
You are an enterprise knowledge assistant.

Answer the user's question using only the provided context.

If the context does not contain enough information to answer the question,
say that the available knowledge base does not contain enough information.

Do not invent facts.

Context:
{context}
"""


def build_rag_chain(
    limit: int = 3,
    candidate_limit=None,
    department=None,
    document_type=None,
    version=None,
    access_level=None,
):
    retriever = EnterpriseRetriever(
        limit=limit,
        candidate_limit=candidate_limit,
        department=department,
        document_type=document_type,
        version=version,
        access_level=access_level,
    )

    llm = EnterpriseChatModel()

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("human", "{input}"),
        ]
    )

    document_chain = create_stuff_documents_chain(
        llm,
        prompt,
    )

    return create_retrieval_chain(
        retriever,
        document_chain,
    )