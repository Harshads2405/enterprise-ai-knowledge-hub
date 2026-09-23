from app.services.langchain.chain import build_rag_chain


def test_build_rag_chain():
    chain = build_rag_chain(limit=3)

    assert chain is not None