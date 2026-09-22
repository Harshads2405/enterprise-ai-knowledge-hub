from pathlib import Path
from typing import List

from pypdf import PdfReader
from app.services.ingestion.document_unit import DocumentUnit

class PDFLoader:
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

        if path.suffix.lower() != ".pdf":
            raise ValueError(
                f"Expected a PDF file: {file_path}"
            )

        reader = PdfReader(str(path))

        pages = []

        for page in reader.pages:
            text = page.extract_text()

            if text:
                pages.append(text.strip())

        return "\n\n".join(pages)

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

        if path.suffix.lower() != ".pdf":
            raise ValueError(
                f"Expected a PDF file: {file_path}"
            )

        reader = PdfReader(str(path))

        units = []

        for page_number, page in enumerate(
                reader.pages,
                start=1,
        ):
            text = page.extract_text()

            if not text:
                continue

            text = text.strip()

            if not text:
                continue

            units.append(
                DocumentUnit(
                    content=text,
                    metadata={
                        "page": page_number,
                    },
                )
            )

        return units


pdf_loader = PDFLoader()
