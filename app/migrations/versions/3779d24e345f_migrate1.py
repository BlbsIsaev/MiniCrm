"""migrate1

Revision ID: 3779d24e345f
Revises: 96c77b14e46d
Create Date: 2025-11-25 10:42:16.368707

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3779d24e345f'
down_revision: Union[str, Sequence[str], None] = '96c77b14e46d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
