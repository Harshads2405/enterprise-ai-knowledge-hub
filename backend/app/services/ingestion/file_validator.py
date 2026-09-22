from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class FileValidationResult:
    is_valid: bool
    file_type: Optional[str] = None
    extension: Optional[str] = None
    error: Optional[str] = None


class FileValidator:
    SUPPORTED_EXTENSIONS = {
        ".pdf": "pdf",
        ".docx": "docx",
        ".txt": "txt",
        ".csv": "csv",
        ".html": "html",
        ".htm": "html",
        ".md": "markdown",
        ".markdown": "markdown",
    }

    MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024

    def validate(
        self,
        filename: str,
        file_size: int,
    ) -> FileValidationResult:

        if not filename or not filename.strip():
            return FileValidationResult(
                is_valid=False,
                error="Filename is required.",
            )

        if file_size < 0:
            return FileValidationResult(
                is_valid=False,
                error="File size cannot be negative.",
            )

        if file_size > self.MAX_FILE_SIZE_BYTES:
            return FileValidationResult(
                is_valid=False,
                error="File exceeds the maximum allowed size of 10 MB.",
            )

        extension = Path(filename).suffix.lower()

        if extension not in self.SUPPORTED_EXTENSIONS:
            return FileValidationResult(
                is_valid=False,
                extension=extension or None,
                error=(
                    f"Unsupported file type: "
                    f"{extension or 'no extension'}."
                ),
            )

        return FileValidationResult(
            is_valid=True,
            file_type=self.SUPPORTED_EXTENSIONS[extension],
            extension=extension,
        )


file_validator = FileValidator()