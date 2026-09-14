from typing import Optional

from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    department: Optional[str] = Field(
        default=None,
        description="Department responsible for the document.",
    )

    document_type: Optional[str] = Field(
        default=None,
        description="Type of document, such as policy, procedure, or guide.",
    )

    version: Optional[str] = Field(
        default=None,
        description="Document version.",
    )

    access_level: Optional[str] = Field(
        default=None,
        description="Access level required to view the document.",
    )