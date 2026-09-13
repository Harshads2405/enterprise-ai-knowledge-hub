from typing import List

from app.db.session import SessionLocal
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.ingestion.document_loader import document_loader
from app.services.ingestion.chunking.text_chunker import text_chunker
from app.services.ingestion.indexing.document_indexer import document_indexer


class IngestionService:
    def ingest(
        self,
        document_id: int,
        file_path: str,
    ) -> List[DocumentChunk]:
        db = SessionLocal()

        try:
            # 1. Get document
            document = db.get(Document, document_id)

            if document is None:
                raise ValueError(
                    f"Document not found: {document_id}"
                )

            # 2. Mark document as processing
            document.status = "processing"
            db.commit()

            # 3. Load document
            text = document_loader.load(file_path)

            if not text.strip():
                raise ValueError(
                    "Document contains no extractable text."
                )

            # 4. Split text into chunks
            chunks = text_chunker.split(text)

            if not chunks:
                raise ValueError(
                    "Document produced no chunks."
                )

            # 5. Generate embeddings and store chunks
            indexed_chunks = document_indexer.index_chunks(
                document_id=document_id,
                chunks=chunks,
            )

            # 6. Mark document as completed
            document.status = "completed"
            db.commit()

            return indexed_chunks

        except Exception:
            db.rollback()

            # Try to mark the document as failed
            try:
                document = db.get(Document, document_id)

                if document is not None:
                    document.status = "failed"
                    db.commit()

            except Exception:
                db.rollback()

            raise

        finally:
            db.close()


ingestion_service = IngestionService()