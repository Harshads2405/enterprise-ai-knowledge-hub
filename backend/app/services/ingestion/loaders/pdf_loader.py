from pathlib import Path

from pypdf import PdfReader


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


pdf_loader = PDFLoader()