from pathlib import Path
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
            document = db.get(Document, document_id)

            if document is None:
                raise ValueError(
                    f"Document not found: {document_id}"
                )

            document.status = "processing"
            db.commit()

            extension = Path(file_path).suffix.lower()

            if extension in {".pdf", ".txt", ".docx", ".csv"}:
                units = document_loader.load_with_metadata(file_path)

                if not units:
                    raise ValueError("Document contains no extractable text.")

                chunks = text_chunker.split_units(units)
            else:
                text = document_loader.load(file_path)

                if not text.strip():
                    raise ValueError("Document contains no extractable text.")

                chunks = text_chunker.split(text)

            if not chunks:
                raise ValueError(
                    "Document produced no chunks."
                )

            indexed_chunks = document_indexer.index_chunks(
                document_id=document_id,
                chunks=chunks,
                document_metadata=document.document_metadata,
            )

            document.status = "completed"
            db.commit()

            return indexed_chunks

        except Exception:
            db.rollback()

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