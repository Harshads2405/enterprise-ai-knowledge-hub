import csv
from pathlib import Path
from typing import List

from app.services.ingestion.document_unit import DocumentUnit


class CSVLoader:
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

        if path.suffix.lower() != ".csv":
            raise ValueError(
                f"Expected a CSV file: {file_path}"
            )

        rows = []

        with path.open(
            "r",
            encoding="utf-8",
            newline="",
        ) as file:
            reader = csv.reader(file)

            for row in reader:
                rows.append(" | ".join(cell.strip() for cell in row))

        return "\n".join(rows)

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


csv_loader = CSVLoader()
