from pathlib import Path
from typing import List

from app.services.ingestion.document_unit import DocumentUnit


class TextLoader:
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

        return path.read_text(
            encoding="utf-8"
        )

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


text_loader = TextLoader()