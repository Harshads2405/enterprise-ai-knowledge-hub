from typing import Dict, List, Optional, Tuple

from sqlalchemy import select, text
from sqlalchemy.orm import joinedload

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.document_chunk import DocumentChunk


class VectorSearch:
    def search(
        self,
        query_embedding: List[float],
        limit: int = 5,
        department: Optional[str] = None,
    ) -> List[Tuple[DocumentChunk, float]]:
        db = SessionLocal()

        try:
            distance = DocumentChunk.embedding.cosine_distance(query_embedding)

            filters = [
                DocumentChunk.embedding.is_not(None),
                distance <= settings.rag_similarity_threshold,
            ]

            if department is not None:
                filters.append(
                    DocumentChunk.chunk_metadata["department"].as_string()
                    == department
                )

            statement = (
                select(DocumentChunk, distance.label("distance"))
                .options(joinedload(DocumentChunk.document))
                .where(*filters)
                .order_by(distance)
                .limit(limit)
            )

            results = db.execute(statement).all()

            return [
                (chunk, float(distance_value))
                for chunk, distance_value in results
            ]

        finally:
            db.close()

    def keyword_search(
        self,
        query: str,
        limit: int = 5,
        department: Optional[str] = None,
    ) -> List[Tuple[DocumentChunk, float]]:
        db = SessionLocal()

        try:
            params = {"query": query}

            if department is not None:
                params["department"] = department


            ranked_query = text(
                """
                SELECT
                    document_chunks.id,
                    ts_rank_cd(
                        document_chunks.search_vector,
                        plainto_tsquery('english', :query)
                    ) AS rank
                FROM document_chunks
                WHERE document_chunks.search_vector @@
                    plainto_tsquery('english', :query)
                """
            )

            if department is not None:
                ranked_query = text(
                    """
                    SELECT
                        document_chunks.id,
                        ts_rank_cd(
                            document_chunks.search_vector,
                            plainto_tsquery('english', :query)
                        ) AS rank
                    FROM document_chunks
                    WHERE document_chunks.search_vector @@
                        plainto_tsquery('english', :query)
                    AND document_chunks.metadata->>'department' = :department
                    """
                )

            ranked_query = text(
                ranked_query.text
                + """
                ORDER BY rank DESC
                LIMIT :limit
                """
            )

            params["limit"] = limit

            rows = db.execute(ranked_query, params).all()

            if not rows:
                return []

            chunk_ids = [row.id for row in rows]
            rank_map = {row.id: float(row.rank) for row in rows}

            statement = (
                select(DocumentChunk)
                .options(joinedload(DocumentChunk.document))
                .where(DocumentChunk.id.in_(chunk_ids))
            )

            chunks = db.execute(statement).scalars().all()
            chunk_map = {chunk.id: chunk for chunk in chunks}

            return [
                (chunk_map[chunk_id], rank_map[chunk_id])
                for chunk_id in chunk_ids
                if chunk_id in chunk_map
            ]

        finally:
            db.close()

    def hybrid_search(
        self,
        query_embedding: List[float],
        query: str,
        limit: int = 5,
        department: Optional[str] = None,
        vector_limit: int = 10,
        keyword_limit: int = 10,
        rrf_k: int = 60,
    ) -> List[Tuple[DocumentChunk, float]]:
        vector_results = self.search(
            query_embedding=query_embedding,
            limit=vector_limit,
            department=department,
        )

        keyword_results = self.keyword_search(
            query=query,
            limit=keyword_limit,
            department=department,
        )

        scores: Dict[int, float] = {}
        chunks: Dict[int, DocumentChunk] = {}

        for rank, (chunk, _) in enumerate(vector_results, start=1):
            chunks[chunk.id] = chunk
            scores[chunk.id] = scores.get(chunk.id, 0.0) + (
                1.0 / (rrf_k + rank)
            )

        for rank, (chunk, _) in enumerate(keyword_results, start=1):
            chunks[chunk.id] = chunk
            scores[chunk.id] = scores.get(chunk.id, 0.0) + (
                1.0 / (rrf_k + rank)
            )

        ranked_chunks = sorted(
            chunks.values(),
            key=lambda chunk: scores[chunk.id],
            reverse=True,
        )

        return [
            (chunk, scores[chunk.id])
            for chunk in ranked_chunks[:limit]
        ]


vector_search = VectorSearch()