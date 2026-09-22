from app.services.ingestion.document_unit import DocumentUnit


def test_document_unit_stores_content_and_metadata():
    unit = DocumentUnit(
        content="Employee leave policy.",
        metadata={
            "page": 3,
            "document_type": "policy",
        },
    )

    assert unit.content == "Employee leave policy."
    assert unit.metadata["page"] == 3
    assert unit.metadata["document_type"] == "policy"


def test_document_unit_defaults_to_empty_metadata():
    unit = DocumentUnit(
        content="Employee leave policy.",
    )

    assert unit.content == "Employee leave policy."
    assert unit.metadata == {}