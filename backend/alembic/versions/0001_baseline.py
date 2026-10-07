"""baseline: starts the migration history (no tables yet)

Revision ID: 0001
Revises:
Create Date: 2026-10-06
"""

from collections.abc import Sequence

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """No tables yet. Workflow/task tables are added as new revisions in Phase 3 and 6."""


def downgrade() -> None:
    """Nothing to undo."""
