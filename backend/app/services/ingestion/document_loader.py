from pathlib import Path
from typing import List

from app.services.ingestion.document_unit import DocumentUnit
from app.services.ingestion.text_loader import text_loader
from app.services.ingestion.loaders.pdf_loader import pdf_loader
from app.services.ingestion.loaders.docx_loader import docx_loader


class DocumentLoader:
    def load(self, file_path: str) -> str:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"File not found: {file_path}"
            )

        if not path.is_file():
            raise ValueError(
                f"Path is not a file: {file_path}"
            )

        extension = path.suffix.lower()

        if extension == ".txt":
            return text_loader.load(file_path)

        if extension == ".pdf":
            return pdf_loader.load(file_path)

        if extension == ".docx":
            return docx_loader.load(file_path)

        raise ValueError(
            f"Unsupported document type: {extension}"
        )

    def load_with_metadata(
        self,
        file_path: str,
    ) -> List[DocumentUnit]:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"File not found: {file_path}"
            )

        if not path.is_file():
            raise ValueError(
                f"Path is not a file: {file_path}"
            )

        extension = path.suffix.lower()

        if extension == ".pdf":
            return pdf_loader.load_with_metadata(file_path)

        raise ValueError(
            f"Metadata-aware loading is not supported for: {extension}"
        )


document_loader = DocumentLoader()