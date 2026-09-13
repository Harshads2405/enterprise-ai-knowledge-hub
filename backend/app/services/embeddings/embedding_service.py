from sentence_transformers import SentenceTransformer


class EmbeddingService:
    def __init__(self):
        self.model = SentenceTransformer(
            "Orange/orange-nomic-v1.5-1536",
            trust_remote_code=True,
        )

    def embed_document(self, text: str) -> list:
        embedding = self.model.encode(
            f"search_document: {text}",
            normalize_embeddings=True,
        )

        return embedding.tolist()

    def embed_query(self, text: str) -> list:
        embedding = self.model.encode(
            f"search_query: {text}",
            normalize_embeddings=True,
        )

        return embedding.tolist()


embedding_service = EmbeddingService()