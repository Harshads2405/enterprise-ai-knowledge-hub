from pathlib import Path

import pytest
from docx import Document

from app.services.ingestion.loaders.docx_loader import DOCXLoader
from app.services.ingestion.loaders.pdf_loader import PDFLoader
from app.services.ingestion.loaders.csv_loader import CSVLoader
from app.services.ingestion.document_loader import DocumentLoader
from app.services.ingestion.loaders.html_loader import HTMLLoader
from app.services.ingestion.loaders.markdown_loader import MarkdownLoader
from app.services.ingestion.text_loader import TextLoader


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


def test_csv_loader_extracts_rows(tmp_path: Path):
    file_path = tmp_path / "employees.csv"

    file_path.write_text(
        "Name,Department,Role\n"
        "John,IT,Developer\n"
        "Sarah,HR,Manager\n",
        encoding="utf-8",
    )

    loader = CSVLoader()

    result = loader.load(str(file_path))

    assert "Name | Department | Role" in result
    assert "John | IT | Developer" in result
    assert "Sarah | HR | Manager" in result


def test_csv_loader_rejects_non_csv(tmp_path: Path):
    file_path = tmp_path / "employees.txt"
    file_path.write_text("test", encoding="utf-8")

    loader = CSVLoader()

    with pytest.raises(ValueError, match="Expected a CSV file"):
        loader.load(str(file_path))


def test_csv_loader_missing_file(tmp_path: Path):
    file_path = tmp_path / "missing.csv"

    loader = CSVLoader()

    with pytest.raises(FileNotFoundError, match="File not found"):
        loader.load(str(file_path))

def test_document_loader_routes_csv(tmp_path: Path):
    file_path = tmp_path / "employees.csv"

    file_path.write_text(
        "Name,Department,Role\n"
        "John,IT,Developer\n"
        "Sarah,HR,Manager\n",
        encoding="utf-8",
    )

    loader = DocumentLoader()

    result = loader.load(str(file_path))

    assert "Name | Department | Role" in result
    assert "John | IT | Developer" in result
    assert "Sarah | HR | Manager" in result

def test_html_loader_extracts_visible_text(tmp_path: Path):
    file_path = tmp_path / "policy.html"

    file_path.write_text(
        """
        <html>
            <head>
                <title>Employee Policy</title>
                <style>.hidden { display: none; }</style>
            </head>
            <body>
                <h1>Employee Leave Policy</h1>
                <p>Employees must submit leave requests.</p>
                <script>
                    console.log("ignored");
                </script>
            </body>
        </html>
        """,
        encoding="utf-8",
    )

    loader = HTMLLoader()

    result = loader.load(str(file_path))

    assert "Employee Policy" in result
    assert "Employee Leave Policy" in result
    assert "Employees must submit leave requests." in result
    assert "console.log" not in result
    assert ".hidden" not in result


def test_html_loader_accepts_htm(tmp_path: Path):
    file_path = tmp_path / "policy.htm"

    file_path.write_text(
        "<h1>Employee Leave Policy</h1>",
        encoding="utf-8",
    )

    loader = HTMLLoader()

    result = loader.load(str(file_path))

    assert result == "Employee Leave Policy"


def test_html_loader_rejects_non_html(tmp_path: Path):
    file_path = tmp_path / "policy.txt"
    file_path.write_text("test", encoding="utf-8")

    loader = HTMLLoader()

    with pytest.raises(ValueError, match="Expected an HTML file"):
        loader.load(str(file_path))


def test_html_loader_missing_file(tmp_path: Path):
    file_path = tmp_path / "missing.html"

    loader = HTMLLoader()

    with pytest.raises(FileNotFoundError, match="File not found"):
        loader.load(str(file_path))

def test_document_loader_routes_html(tmp_path: Path):
    file_path = tmp_path / "policy.html"

    file_path.write_text(
        """
        <html>
            <body>
                <h1>Employee Leave Policy</h1>
                <p>Employees must submit leave requests.</p>
            </body>
        </html>
        """,
        encoding="utf-8",
    )

    loader = DocumentLoader()

    result = loader.load(str(file_path))

    assert "Employee Leave Policy" in result
    assert "Employees must submit leave requests." in result

def test_markdown_loader_extracts_readable_text(tmp_path: Path):
    file_path = tmp_path / "policy.md"

    file_path.write_text(
        """
        # Employee Leave Policy

        ## Rules

        - Employees must submit leave requests.
        - Managers must approve requests.

        **Important:** Submit requests before the deadline.

        [Leave Portal](https://example.com)
        """,
        encoding="utf-8",
    )

    loader = MarkdownLoader()

    result = loader.load(str(file_path))

    assert "Employee Leave Policy" in result
    assert "Rules" in result
    assert "Employees must submit leave requests." in result
    assert "Managers must approve requests." in result
    assert "Important: Submit requests before the deadline." in result
    assert "Leave Portal" in result

    assert "# " not in result
    assert "**" not in result
    assert "[Leave Portal]" not in result


def test_markdown_loader_accepts_markdown_extension(tmp_path: Path):
    file_path = tmp_path / "policy.markdown"

    file_path.write_text(
        "# Employee Leave Policy",
        encoding="utf-8",
    )

    loader = MarkdownLoader()

    result = loader.load(str(file_path))

    assert result == "Employee Leave Policy"


def test_markdown_loader_rejects_non_markdown(tmp_path: Path):
    file_path = tmp_path / "policy.txt"
    file_path.write_text("test", encoding="utf-8")

    loader = MarkdownLoader()

    with pytest.raises(
        ValueError,
        match="Expected a Markdown file",
    ):
        loader.load(str(file_path))


def test_markdown_loader_missing_file(tmp_path: Path):
    file_path = tmp_path / "missing.md"

    loader = MarkdownLoader()

    with pytest.raises(
        FileNotFoundError,
        match="File not found",
    ):
        loader.load(str(file_path))

def test_document_loader_routes_markdown(tmp_path: Path):
    file_path = tmp_path / "policy.md"

    file_path.write_text(
        """
        # Employee Leave Policy

        Employees must submit leave requests.
        """,
        encoding="utf-8",
    )

    loader = DocumentLoader()

    result = loader.load(str(file_path))

    assert "Employee Leave Policy" in result
    assert "Employees must submit leave requests." in result
    assert "# " not in result

def test_text_loader_load_with_metadata(tmp_path: Path):
    file_path = tmp_path / "policy.txt"

    file_path.write_text(
        "Employees must submit leave requests.",
        encoding="utf-8",
    )

    loader = TextLoader()

    units = loader.load_with_metadata(str(file_path))

    assert len(units) == 1
    assert units[0].content == "Employees must submit leave requests."
    assert units[0].metadata == {}

def test_document_loader_routes_txt_with_metadata(tmp_path: Path):
    file_path = tmp_path / "policy.txt"

    file_path.write_text(
        "Employees must submit leave requests.",
        encoding="utf-8",
    )

    loader = DocumentLoader()

    units = loader.load_with_metadata(str(file_path))

    assert len(units) == 1
    assert units[0].content == "Employees must submit leave requests."
    assert units[0].metadata == {}