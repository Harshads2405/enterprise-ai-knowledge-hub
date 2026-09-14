from typing import List, Optional, Tuple

from sqlalchemy import select
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


vector_search = VectorSearch()