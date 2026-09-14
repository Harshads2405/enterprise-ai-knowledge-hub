from typing import List, Tuple

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.db.session import SessionLocal
from app.models.document_chunk import DocumentChunk


class VectorSearch:
    def search(
        self,
        query_embedding: List[float],
        limit: int = 5,
    ) -> List[Tuple[DocumentChunk, float]]:
        db = SessionLocal()

        try:
            distance = DocumentChunk.embedding.cosine_distance(query_embedding)

            statement = (
                select(DocumentChunk, distance.label("distance"))
                .options(joinedload(DocumentChunk.document))
                .where(DocumentChunk.embedding.is_not(None))
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