import pytest

from app.services.metadata.metadata_validator import (
    MetadataValidator,
)


def test_validate_returns_normalized_metadata():
    validator = MetadataValidator()

    metadata = {
        "department": " HR ",
        "document_type": " policy ",
        "version": " 1.0 ",
        "access_level": " INTERNAL ",
    }

    result = validator.validate(metadata)

    assert result == {
        "department": "HR",
        "document_type": "policy",
        "version": "1.0",
        "access_level": "internal",
    }


def test_validate_rejects_missing_required_field():
    validator = MetadataValidator()

    metadata = {
        "department": "HR",
        "document_type": "policy",
        "version": "1.0",
    }

    with pytest.raises(
        ValueError,
        match="Missing required metadata fields",
    ):
        validator.validate(metadata)


def test_validate_rejects_invalid_access_level():
    validator = MetadataValidator()

    metadata = {
        "department": "HR",
        "document_type": "policy",
        "version": "1.0",
        "access_level": "secret",
    }

    with pytest.raises(
        ValueError,
        match="Invalid access_level",
    ):
        validator.validate(metadata)


def test_validate_removes_none_values():
    validator = MetadataValidator()

    metadata = {
        "department": "HR",
        "document_type": "policy",
        "version": "1.0",
        "access_level": "internal",
        "extra_field": None,
    }

    result = validator.validate(metadata)

    assert "extra_field" not in result