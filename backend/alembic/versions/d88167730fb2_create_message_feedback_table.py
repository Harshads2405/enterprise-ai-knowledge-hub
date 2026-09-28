"""create message feedback table

Revision ID: d88167730fb2
Revises: 3c1db1d02cd5
Create Date: 2026-09-28 13:41:51.897991

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d88167730fb2"
down_revision: Union[str, None] = "3c1db1d02cd5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "message_feedback",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "message_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "rating",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "comment",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["message_id"],
            ["messages.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_message_feedback_message_id"),
        "message_feedback",
        ["message_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_message_feedback_user_id"),
        "message_feedback",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_message_feedback_user_id"),
        table_name="message_feedback",
    )

    op.drop_index(
        op.f("ix_message_feedback_message_id"),
        table_name="message_feedback",
    )

    op.drop_table("message_feedback")
