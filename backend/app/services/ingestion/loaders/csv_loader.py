import csv
from pathlib import Path


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


csv_loader = CSVLoader()
