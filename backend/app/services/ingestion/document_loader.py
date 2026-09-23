from pathlib import Path
from typing import List

from app.services.ingestion.document_unit import DocumentUnit
from app.services.ingestion.text_loader import text_loader
from app.services.ingestion.loaders.pdf_loader import pdf_loader
from app.services.ingestion.loaders.docx_loader import docx_loader
from app.services.ingestion.loaders.csv_loader import csv_loader
from app.services.ingestion.loaders.html_loader import html_loader
from app.services.ingestion.loaders.markdown_loader import markdown_loader
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

        if extension == ".csv":
            return csv_loader.load(file_path)

        if extension in {".html", ".htm"}:
            return html_loader.load(file_path)

        if extension in {".md", ".markdown"}:
            return markdown_loader.load(file_path)

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