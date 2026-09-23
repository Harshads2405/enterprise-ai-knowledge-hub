from typing import Dict


class MetadataValidator:
    REQUIRED_FIELDS = {
        "department",
        "document_type",
        "version",
        "access_level",
    }

    ALLOWED_ACCESS_LEVELS = {
        "public",
        "internal",
        "confidential",
        "restricted",
    }

    def validate(
        self,
        metadata: Dict,
    ) -> Dict:
        if not isinstance(metadata, dict):
            raise ValueError(
                "Document metadata must be a dictionary."
            )

        normalized = {
            key: value
            for key, value in metadata.items()
            if value is not None
        }

        missing_fields = [
            field
            for field in self.REQUIRED_FIELDS
            if not normalized.get(field)
        ]

        if missing_fields:
            raise ValueError(
                "Missing required metadata fields: "
                + ", ".join(sorted(missing_fields))
            )

        access_level = str(
            normalized["access_level"]
        ).strip().lower()

        if access_level not in self.ALLOWED_ACCESS_LEVELS:
            raise ValueError(
                f"Invalid access_level: {normalized['access_level']}"
            )

        normalized["department"] = str(
            normalized["department"]
        ).strip()

        normalized["document_type"] = str(
            normalized["document_type"]
        ).strip()

        normalized["version"] = str(
            normalized["version"]
        ).strip()

        normalized["access_level"] = access_level

        return normalized


metadata_validator = MetadataValidator()