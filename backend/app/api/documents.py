
from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.document import Document
from app.models.user import User
from app.services.document_service import document_service
from app.services.ingestion.ingestion_service import ingestion_service


router = APIRouter(
    prefix="/api/v1/documents",
    tags=["Documents"],
)

BASE_DIR = Path(__file__).resolve().parents[3]
STORAGE_DIR = BASE_DIR / "backend" / "storage" / "documents"

ALLOWED_EXTENSIONS = {".txt", ".pdf", ".docx"}


@router.post("/upload")

def upload_document(
    file: UploadFile = File(...),
    department: Optional[str] = Form(None),
    document_type: Optional[str] = Form(None),
    version: Optional[str] = Form(None),
    access_level: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="File name is required.",
        )

    extension = Path(file.filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported document type: {extension}. "
                f"Supported types: {sorted(ALLOWED_EXTENSIONS)}"
            ),
        )

    STORAGE_DIR.mkdir(parents=True, exist_ok=True)

    stored_filename = f"{uuid4().hex}{extension}"
    stored_path = STORAGE_DIR / stored_filename

    try:
        with stored_path.open("wb") as destination:
            while True:
                chunk = file.file.read(1024 * 1024)
                if not chunk:
                    break
                destination.write(chunk)

        document_metadata = {
            "original_filename": file.filename,
            "stored_filename": stored_filename,
            "department": department,
            "document_type": document_type,
            "version": version,
            "access_level": access_level,
        }

        document = Document(
            organization_id=current_user.organization_id,
            uploaded_by=current_user.id,
            title=Path(file.filename).stem,
            source_type=extension.lstrip("."),
            source_name=file.filename,
            status="pending",
            document_metadata=document_metadata,
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        ingestion_service.ingest(
            document_id=document.id,
            file_path=str(stored_path),
        )

        db.refresh(document)

        return {
            "id": document.id,
            "title": document.title,
            "source_type": document.source_type,
            "source_name": document.source_name,
            "status": document.status,
        }

    except Exception as error:
        db.rollback()

        # Attempt cleanup regardless of the exception type.
        try:
            if stored_path.exists():
                stored_path.unlink()
        except OSError:
            # Do not replace the original error with a cleanup error.
            pass

        if isinstance(error, HTTPException):
            raise

        raise HTTPException(
            status_code=500,
            detail="Document ingestion failed.",
        ) from None

    finally:
        file.file.close()



@router.get("")
def list_documents(
    uploaded_by: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if uploaded_by is not None and uploaded_by != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only filter documents by your own user ID.",
        )

    documents = document_service.list_documents(
        db=db,
        organization_id=current_user.organization_id,
        uploaded_by=uploaded_by,
    )

    return [
        {
            "id": document.id,
            "title": document.title,
            "source_type": document.source_type,
            "source_name": document.source_name,
            "status": document.status,
            "metadata": document.document_metadata,
            "created_at": document.created_at.isoformat(),
            "updated_at": document.updated_at.isoformat(),
        }
        for document in documents
    ]


@router.get("/{document_id}")
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = document_service.get_document(
        db=db,
        document_id=document_id,
        organization_id=current_user.organization_id,
    )

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    return {
        "id": document.id,
        "title": document.title,
        "source_type": document.source_type,
        "source_name": document.source_name,
        "status": document.status,
        "metadata": document.document_metadata,
        "created_at": document.created_at.isoformat(),
        "updated_at": document.updated_at.isoformat(),
    }
