import re
from typing import List, Tuple

from app.services.embeddings.embedding_service import embedding_service
from app.services.retrieval.retrieval_result import RetrievalResult


class ContextCompressor:
    def __init__(
        self,
        similarity_threshold: float = 0.45,
        max_sentences: int = 3,
    ):
        if similarity_threshold < 0.0 or similarity_threshold > 1.0:
            raise ValueError(
                "similarity_threshold must be between 0.0 and 1.0"
            )

        if max_sentences <= 0:
            raise ValueError("max_sentences must be greater than 0")

        self.similarity_threshold = similarity_threshold
        self.max_sentences = max_sentences

    def _split_sentences(self, text: str) -> List[str]:
        text = text.replace("\n", " ").strip()

        if not text:
            return []

        sentences = re.split(r"(?<=[.!?])\s+", text)

        return [
            sentence.strip()
            for sentence in sentences
            if sentence.strip()
        ]

    def _score_sentences(
        self,
        query_embedding: List[float],
        sentences: List[str],
    ) -> List[Tuple[int, str, float]]:
        scored_sentences = []

        sentence_embeddings = [
            embedding_service.embed_document(sentence)
            for sentence in sentences
        ]

        for index, (sentence, sentence_embedding) in enumerate(
            zip(sentences, sentence_embeddings)
        ):
            similarity = sum(
                query_value * sentence_value
                for query_value, sentence_value in zip(
                    query_embedding,
                    sentence_embedding,
                )
            )

            scored_sentences.append(
                (index, sentence, float(similarity))
            )

        return scored_sentences

    def compress(
        self,
        query: str,
        results: List[RetrievalResult],
    ) -> List[RetrievalResult]:
        if not results:
            return []

        query_embedding = embedding_service.embed_query(query)

        compressed_results = []

        for result in results:
            sentences = self._split_sentences(result.chunk.content)

            if not sentences:
                continue

            scored_sentences = self._score_sentences(
                query_embedding=query_embedding,
                sentences=sentences,
            )

            relevant_sentences = [
                item
                for item in scored_sentences
                if item[2] >= self.similarity_threshold
            ]

            relevant_sentences.sort(
                key=lambda item: item[2],
                reverse=True,
            )

            selected = relevant_sentences[: self.max_sentences]

            selected.sort(key=lambda item: item[0])

            if selected:
                result.compressed_content = " ".join(
                    item[1]
                    for item in selected
                )
                compressed_results.append(result)

        return compressed_results


context_compressor = ContextCompressor()