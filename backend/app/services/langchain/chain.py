from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

from app.services.langchain.llm import EnterpriseChatModel
from app.services.langchain.prompt import (
    enterprise_rag_prompt,
)
from app.services.langchain.retriever import EnterpriseRetriever


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

    prompt = enterprise_rag_prompt.build(
        question_variable="input",
    )

    document_chain = create_stuff_documents_chain(
        llm,
        prompt,
    )

    return create_retrieval_chain(
        retriever,
        document_chain,
    )