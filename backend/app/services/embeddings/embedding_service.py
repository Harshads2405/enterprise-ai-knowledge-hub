from sentence_transformers import SentenceTransformer


class EmbeddingService:
    def __init__(self):
        self.model = SentenceTransformer(
            "Orange/orange-nomic-v1.5-1536",
            trust_remote_code=True,
        )

    def embed(self, text: str) -> list:
        embedding = self.model.encode(
            text,
            normalize_embeddings=True,
        )

        return embedding.tolist()


embedding_service = EmbeddingService()