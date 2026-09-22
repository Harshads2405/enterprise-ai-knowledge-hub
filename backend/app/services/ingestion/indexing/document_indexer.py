from typing import Dict, List, Union

from app.db.session import SessionLocal
from app.models.document_chunk import DocumentChunk
from app.services.embeddings.embedding_service import embedding_service
from app.services.ingestion.document_unit import DocumentUnit


class DocumentIndexer:
    def index_chunks(
        self,
        document_id: int,
        chunks: List[Union[str, DocumentUnit]],
        document_metadata: Dict,
    ) -> List[DocumentChunk]:
        db = SessionLocal()

        try:
            indexed_chunks = []

            base_metadata = {
                "department": document_metadata.get("department"),
                "document_type": document_metadata.get("document_type"),
                "version": document_metadata.get("version"),
                "access_level": document_metadata.get("access_level"),
            }

            for index, chunk_item in enumerate(chunks):
                if isinstance(chunk_item, DocumentUnit):
                    content = chunk_item.content
                    chunk_metadata = {
                        **base_metadata,
                        **chunk_item.metadata,
                    }
                else:
                    content = chunk_item
                    chunk_metadata = base_metadata.copy()

                embedding = embedding_service.embed_document(content)

                chunk = DocumentChunk(
                    document_id=document_id,
                    chunk_index=index,
                    content=content,
                    token_count=len(content.split()),
                    chunk_metadata=chunk_metadata,
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