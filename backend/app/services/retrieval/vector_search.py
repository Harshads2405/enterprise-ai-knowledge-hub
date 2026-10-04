from typing import Dict, List, Optional

from sqlalchemy import select, text
from sqlalchemy.orm import joinedload

from app.db.session import SessionLocal
from app.models.document_chunk import DocumentChunk
from app.services.retrieval.retrieval_result import RetrievalResult


class VectorSearch:
    def search(
        self,
        query_embedding: List[float],
        limit: int = 5,
        department: Optional[str] = None,
        document_type: Optional[str] = None,
        version: Optional[str] = None,
        access_level: Optional[str] = None,
    ) -> List[RetrievalResult]:
        db = SessionLocal()

        try:
            distance = DocumentChunk.embedding.cosine_distance(
                query_embedding
            )

            filters = [
                DocumentChunk.embedding.is_not(None),
            ]

            metadata_filters = {
                "department": department,
                "document_type": document_type,
                "version": version,
                "access_level": access_level,
            }

            for key, value in metadata_filters.items():
                if value is not None:
                    filters.append(
                        DocumentChunk.chunk_metadata[key].as_string()
                        == value
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
                RetrievalResult(
                    chunk=chunk,
                    retrieval_score=float(distance_value),
                )
                for chunk, distance_value in results
            ]

        finally:
            db.close()

    def keyword_search(
        self,
        query: str,
        limit: int = 5,
        department: Optional[str] = None,
        document_type: Optional[str] = None,
        version: Optional[str] = None,
        access_level: Optional[str] = None,
    ) -> List[RetrievalResult]:
        db = SessionLocal()

        try:
            params = {
                "query": query,
                "limit": limit,
            }

            metadata_filters = {
                "department": department,
                "document_type": document_type,
                "version": version,
                "access_level": access_level,
            }

            metadata_conditions = []

            for key, value in metadata_filters.items():
                if value is not None:
                    parameter_name = f"metadata_{key}"

                    params[parameter_name] = value

                    metadata_conditions.append(
                        f"document_chunks.metadata->>'{key}' = "
                        f":{parameter_name}"
                    )

            metadata_filter = ""

            if metadata_conditions:
                metadata_filter = (
                    " AND " + " AND ".join(metadata_conditions)
                )

            ranked_query = text(
                f"""
                SELECT
                    document_chunks.id,
                    ts_rank_cd(
                        document_chunks.search_vector,
                        plainto_tsquery('english', :query)
                    ) AS rank
                FROM document_chunks
                WHERE document_chunks.search_vector @@
                    plainto_tsquery('english', :query)
                {metadata_filter}
                ORDER BY rank DESC, document_chunks.id DESC
                LIMIT :limit
                """
            )

            rows = db.execute(ranked_query, params).all()

            if not rows:
                return []

            chunk_ids = [row.id for row in rows]

            rank_map = {
                row.id: float(row.rank)
                for row in rows
            }

            statement = (
                select(DocumentChunk)
                .options(joinedload(DocumentChunk.document))
                .where(DocumentChunk.id.in_(chunk_ids))
            )

            chunks = db.execute(statement).scalars().all()

            chunk_map = {
                chunk.id: chunk
                for chunk in chunks
            }

            return [
                RetrievalResult(
                    chunk=chunk_map[chunk_id],
                    retrieval_score=rank_map[chunk_id],
                )
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
        document_type: Optional[str] = None,
        version: Optional[str] = None,
        access_level: Optional[str] = None,
        vector_limit: int = 10,
        keyword_limit: int = 10,
        rrf_k: int = 60,
    ) -> List[RetrievalResult]:
        vector_results = self.search(
            query_embedding=query_embedding,
            limit=vector_limit,
            department=department,
            document_type=document_type,
            version=version,
            access_level=access_level,
        )

        keyword_results = self.keyword_search(
            query=query,
            limit=keyword_limit,
            department=department,
            document_type=document_type,
            version=version,
            access_level=access_level,
        )

        scores: Dict[int, float] = {}
        chunks: Dict[int, DocumentChunk] = {}

        for rank, result in enumerate(vector_results, start=1):
            chunk_id = result.chunk.id

            chunks[chunk_id] = result.chunk

            scores[chunk_id] = scores.get(
                chunk_id,
                0.0,
            ) + (1.0 / (rrf_k + rank))

        for rank, result in enumerate(keyword_results, start=1):
            chunk_id = result.chunk.id

            chunks[chunk_id] = result.chunk

            scores[chunk_id] = scores.get(
                chunk_id,
                0.0,
            ) + (1.0 / (rrf_k + rank))

        ranked_chunks = sorted(
            chunks.values(),
            key=lambda chunk: scores[chunk.id],
            reverse=True,
        )

        return [
            RetrievalResult(
                chunk=chunk,
                retrieval_score=scores[chunk.id],
            )
            for chunk in ranked_chunks[:limit]
        ]


vector_search = VectorSearch()