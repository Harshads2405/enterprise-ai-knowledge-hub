from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.document import Document


class DocumentService:

    def list_documents(
        self,
        db: Session,
        organization_id: int,
        uploaded_by: Optional[int] = None,
    ) -> List[Document]:
        query = (
            db.query(Document)
            .filter(Document.organization_id == organization_id)
        )

        if uploaded_by is not None:
            query = query.filter(Document.uploaded_by == uploaded_by)

        return (
            query
            .order_by(
                Document.updated_at.desc(),
                Document.id.desc(),
            )
            .all()
        )

    def get_document(
        self,
        db: Session,
        document_id: int,
    ) -> Optional[Document]:
        return (
            db.query(Document)
            .filter(Document.id == document_id)
            .first()
        )


document_service = DocumentService()

