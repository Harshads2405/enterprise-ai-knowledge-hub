from pathlib import Path

import pytest
from docx import Document

from app.services.ingestion.loaders.docx_loader import DOCXLoader
from app.services.ingestion.loaders.pdf_loader import PDFLoader


def test_docx_loader_extracts_paragraphs(tmp_path: Path):
    file_path = tmp_path / "policy.docx"

    document = Document()
    document.add_paragraph("Employee Leave Policy")
    document.add_paragraph("Employees must submit leave requests.")
    document.save(file_path)

    loader = DOCXLoader()

    result = loader.load(str(file_path))

    assert "Employee Leave Policy" in result
    assert "Employees must submit leave requests." in result


def test_docx_loader_rejects_non_docx(tmp_path: Path):
    file_path = tmp_path / "policy.txt"
    file_path.write_text("test", encoding="utf-8")

    loader = DOCXLoader()

    with pytest.raises(ValueError, match="Expected a DOCX file"):
        loader.load(str(file_path))


def test_docx_loader_missing_file(tmp_path: Path):
    file_path = tmp_path / "missing.docx"

    loader = DOCXLoader()

    with pytest.raises(FileNotFoundError, match="File not found"):
        loader.load(str(file_path))


def test_pdf_loader_rejects_non_pdf(tmp_path: Path):
    file_path = tmp_path / "policy.txt"
    file_path.write_text("test", encoding="utf-8")

    loader = PDFLoader()

    with pytest.raises(ValueError, match="Expected a PDF file"):
        loader.load(str(file_path))


def test_pdf_loader_missing_file(tmp_path: Path):
    file_path = tmp_path / "missing.pdf"

    loader = PDFLoader()

    with pytest.raises(FileNotFoundError, match="File not found"):
        loader.load(str(file_path))


