from app.services.ingestion.file_validator import FileValidator


def test_valid_pdf_file():
    validator = FileValidator()

    result = validator.validate(
        filename="employee_policy.pdf",
        file_size=1024,
    )

    assert result.is_valid is True
    assert result.file_type == "pdf"
    assert result.extension == ".pdf"
    assert result.error is None


def test_valid_supported_file_types():
    validator = FileValidator()

    expected_types = {
        "document.pdf": "pdf",
        "document.docx": "docx",
        "document.txt": "txt",
        "document.csv": "csv",
        "document.html": "html",
        "document.md": "markdown",
    }

    for filename, expected_type in expected_types.items():
        result = validator.validate(
            filename=filename,
            file_size=1024,
        )

        assert result.is_valid is True
        assert result.file_type == expected_type


def test_unsupported_file_type():
    validator = FileValidator()

    result = validator.validate(
        filename="malware.exe",
        file_size=1024,
    )

    assert result.is_valid is False
    assert result.error == "Unsupported file type: .exe."


def test_file_without_extension():
    validator = FileValidator()

    result = validator.validate(
        filename="employee_policy",
        file_size=1024,
    )

    assert result.is_valid is False
    assert result.error == "Unsupported file type: no extension."


def test_file_size_limit():
    validator = FileValidator()

    result = validator.validate(
        filename="large_document.pdf",
        file_size=10 * 1024 * 1024 + 1,
    )

    assert result.is_valid is False
    assert result.error == (
        "File exceeds the maximum allowed size of 10 MB."
    )


def test_empty_filename():
    validator = FileValidator()

    result = validator.validate(
        filename="",
        file_size=1024,
    )

    assert result.is_valid is False
    assert result.error == "Filename is required."


def test_negative_file_size():
    validator = FileValidator()

    result = validator.validate(
        filename="document.pdf",
        file_size=-1,
    )

    assert result.is_valid is False
    assert result.error == "File size cannot be negative."