from pathlib import Path
from typing import List

from docx import Document

from app.services.ingestion.document_unit import DocumentUnit

class DOCXLoader:
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

        if path.suffix.lower() != ".docx":
            raise ValueError(
                f"Expected a DOCX file: {file_path}"
            )

        document = Document(str(path))

        paragraphs = []

        for paragraph in document.paragraphs:
            text = paragraph.text.strip()

            if text:
                paragraphs.append(text)

        return "\n\n".join(paragraphs)

    def load_with_metadata(
        self,
        file_path: str,
    ) -> List[DocumentUnit]:
        content = self.load(file_path)

        return [
            DocumentUnit(
                content=content,
                metadata={},
            )
        ]


docx_loader = DOCXLoader()