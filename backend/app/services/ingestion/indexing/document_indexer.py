from typing import Dict, List

from app.db.session import SessionLocal
from app.models.document_chunk import DocumentChunk
from app.services.embeddings.embedding_service import embedding_service


class DocumentIndexer:
    def index_chunks(
        self,
        document_id: int,
        chunks: List[str],
        document_metadata: Dict,
    ) -> List[DocumentChunk]:
        db = SessionLocal()

        try:
            indexed_chunks = []

            chunk_metadata = {
                "department": document_metadata.get("department"),
                "document_type": document_metadata.get("document_type"),
                "version": document_metadata.get("version"),
                "access_level": document_metadata.get("access_level"),
            }

            for index, content in enumerate(chunks):
                embedding = embedding_service.embed_document(content)

                chunk = DocumentChunk(
                    document_id=document_id,
                    chunk_index=index,
                    content=content,
                    token_count=len(content.split()),
                    chunk_metadata=chunk_metadata.copy(),
                    embedding=embedding,
                )

                db.add(chunk)
                indexed_chunks.append(chunk)

            db.commit()

            for chunk in indexed_chunks:
                db.refresh(chunk)

            return indexed_chunks

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()


document_indexer = DocumentIndexer()