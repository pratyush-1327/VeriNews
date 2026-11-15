"""0002 add unverified verdict

Revision ID: 0002_add_unverified_verdict
Revises: 0001_initial_schema
Create Date: 2026-11-15 23:40:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0002_add_unverified_verdict'
down_revision: Union[str, None] = '0001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add UNVERIFIED to verdict_enum
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE verdict_enum ADD VALUE IF NOT EXISTS 'UNVERIFIED'")


def downgrade() -> None:
    pass
