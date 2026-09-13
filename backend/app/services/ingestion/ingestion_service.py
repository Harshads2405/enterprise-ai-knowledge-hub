from typing import List

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
        # 1. Load document
        text = document_loader.load(file_path)

        if not text.strip():
            raise ValueError(
                "Document contains no extractable text."
            )

        # 2. Split text into chunks
        chunks = text_chunker.split(text)

        if not chunks:
            raise ValueError(
                "Document produced no chunks."
            )

        # 3. Generate embeddings and store chunks
        indexed_chunks = document_indexer.index_chunks(
            document_id=document_id,
            chunks=chunks,
        )

        return indexed_chunks


ingestion_service = IngestionService()