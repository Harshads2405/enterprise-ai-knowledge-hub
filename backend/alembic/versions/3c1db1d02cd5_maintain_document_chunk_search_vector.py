from typing import Sequence, Union

from alembic import op


revision: str = "3c1db1d02cd5"
down_revision: Union[str, Sequence[str], None] = "3b0859555556"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_document_chunk_search_vector()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            NEW.search_vector :=
                to_tsvector(
                    'english',
                    coalesce(NEW.content, '')
                );

            RETURN NEW;
        END;
        $$;
        """
    )

    op.execute(
        """
        DROP TRIGGER IF EXISTS document_chunk_search_vector_trigger
        ON document_chunks;
        """
    )

    op.execute(
        """
        CREATE TRIGGER document_chunk_search_vector_trigger
        BEFORE INSERT OR UPDATE OF content
        ON document_chunks
        FOR EACH ROW
        EXECUTE FUNCTION update_document_chunk_search_vector();
        """
    )

    op.execute(
        """
        UPDATE document_chunks
        SET search_vector =
            to_tsvector(
                'english',
                coalesce(content, '')
            );
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TRIGGER IF EXISTS document_chunk_search_vector_trigger
        ON document_chunks;
        """
    )

    op.execute(
        """
        DROP FUNCTION IF EXISTS update_document_chunk_search_vector();
        """
    )