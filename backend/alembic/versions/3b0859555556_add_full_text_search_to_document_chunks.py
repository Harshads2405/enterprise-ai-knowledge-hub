"""add full text search to document chunks

Revision ID: 3b0859555556
Revises: 324eaa3bd2e5
Create Date: 2026-09-14 13:01:49.464911

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "3b0859555556"
down_revision: Union[str, None] = "324eaa3bd2e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "document_chunks",
        sa.Column(
            "search_vector",
            postgresql.TSVECTOR(),
            nullable=True,
        ),
    )

    op.execute(
        """
        UPDATE document_chunks
        SET search_vector = to_tsvector(
            'english',
            coalesce(content, '')
        )
        """
    )

    op.create_index(
        "ix_document_chunks_search_vector",
        "document_chunks",
        ["search_vector"],
        unique=False,
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.execute(
        "DROP INDEX IF EXISTS ix_document_chunks_search_vector"
    )

    op.execute(
        "ALTER TABLE document_chunks DROP COLUMN IF EXISTS search_vector"
    )