"""
Add explicit metadata columns to settings table
(category, type, enum, default_value, is_editable)
"""

import json

import sqlalchemy as sa
from alembic import op

revision = "20240524efmeta"
down_revision = "580fde3f9583"
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns
    op.add_column("settings", sa.Column("category", sa.String(), nullable=True))
    op.add_column("settings", sa.Column("type", sa.String(), nullable=True))
    op.add_column("settings", sa.Column("enum", sa.Text(), nullable=True))
    op.add_column("settings", sa.Column("default_value", sa.String(), nullable=True))
    op.add_column(
        "settings",
        sa.Column("is_editable", sa.Boolean(), nullable=True, server_default="true"),
    )

    # Migrate metadata from value JSON to new columns
    conn = op.get_bind()
    result = conn.execute(sa.text("SELECT id, value FROM settings"))
    for row in result:
        try:
            meta = (
                json.loads(row.value)
                if row.value and row.value.strip().startswith("{")
                else None
            )
        except Exception:
            meta = None
        if meta and isinstance(meta, dict):
            category = meta.get("category")
            typ = meta.get("type")
            enum = json.dumps(meta.get("enum")) if "enum" in meta else None
            default_value = meta.get("default") or meta.get("default_value") or None
            # Päivitä rivi
            conn.execute(
                sa.text(
                    """
                UPDATE settings SET category=:category, type=:typ,
                enum=:enum, default_value=:default_value WHERE id=:id
            """
                ),
                dict(
                    category=category,
                    typ=typ,
                    enum=enum,
                    default_value=default_value,
                    id=row.id,
                ),
            )


def downgrade():
    op.drop_column("settings", "category")
    op.drop_column("settings", "type")
    op.drop_column("settings", "enum")
    op.drop_column("settings", "default_value")
    op.drop_column("settings", "is_editable")
