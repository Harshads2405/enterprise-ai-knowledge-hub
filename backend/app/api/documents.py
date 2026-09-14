from pathlib import Path
from uuid import uuid4
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.document import Document
from app.services.ingestion.ingestion_service import ingestion_service



router = APIRouter(
    prefix="/api/v1/documents",
    tags=["Documents"],
)


BASE_DIR = Path(__file__).resolve().parents[3]
STORAGE_DIR = BASE_DIR / "backend" / "storage" / "documents"

ALLOWED_EXTENSIONS = {
    ".txt",
    ".pdf",
    ".docx",
}


@router.post("/upload")
def upload_document(
    file: UploadFile = File(...),
    organization_id: int = Form(...),
    uploaded_by: int = Form(...),
    department: Optional[str] = Form(None),
    document_type: Optional[str] = Form(None),
    version: Optional[str] = Form(None),
    access_level: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    # 1. Validate file name
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="File name is required.",
        )

    extension = Path(file.filename).suffix.lower()

    # 2. Validate file type
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported document type: {extension}. "
                f"Supported types: {sorted(ALLOWED_EXTENSIONS)}"
            ),
        )

    # 3. Create storage directory
    STORAGE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # 4. Generate unique stored file name
    stored_filename = f"{uuid4().hex}{extension}"
    stored_path = STORAGE_DIR / stored_filename

    try:
        # 5. Save uploaded file
        with stored_path.open("wb") as destination:
            while True:
                chunk = file.file.read(1024 * 1024)

                if not chunk:
                    break

                destination.write(chunk)

        # 6. Build document metadata
        document_metadata = {
            "original_filename": file.filename,
            "stored_filename": stored_filename,
            "department": department,
            "document_type": document_type,
            "version": version,
            "access_level": access_level,
        }

        # 7. Create document record
        document = Document(
            organization_id=organization_id,
            uploaded_by=uploaded_by,
            title=Path(file.filename).stem,
            source_type=extension.lstrip("."),
            source_name=file.filename,
            status="pending",
            document_metadata=document_metadata,
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        # 8. Run ingestion pipeline
        ingestion_service.ingest(
            document_id=document.id,
            file_path=str(stored_path),
        )

        # 9. Refresh document status
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

        if stored_path.exists():
            stored_path.unlink()

        raise HTTPException(
            status_code=500,
            detail=f"Document ingestion failed: {str(error)}",
        )

    finally:
        file.file.close()