"""
Initial migration: create users and settings tables,
add permissions column, and insert default settings
"""

import json

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "580fde3f9583"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create settings table
    op.create_table(
        "settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("value", sa.String(), nullable=False),
        sa.Column("labels", sa.String(), nullable=True),  # monikielinen label
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )
    op.create_index(op.f("ix_settings_id"), "settings", ["id"], unique=False)
    # Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("is_active", sa.Integer(), nullable=False),
        sa.Column("permissions", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)
    # Insert default settings
    default_settings = [
        # Yleiset asetukset
        {
            "key": "site_name",
            "value": json.dumps(
                {"value": "Management System", "category": "general", "type": "string"}
            ),
            "labels": json.dumps({"en": "Site name", "fi": "Sivuston nimi"}),
        },
        {
            "key": "vantage_api_key",
            "value": json.dumps(
                {"value": "", "category": "api_keys", "type": "string"}
            ),
            "labels": json.dumps({"en": "Vantage API Key", "fi": "Vantage API-avain"}),
        },
        # --- Appearance settings ---
        {
            "key": "theme",
            "value": json.dumps(
                {
                    "value": "system",
                    "category": "appearance",
                    "type": "enum",
                    "enum": [
                        {"value": "light", "label": {"en": "Light", "fi": "Vaalea"}},
                        {"value": "dark", "label": {"en": "Dark", "fi": "Tumma"}},
                        {
                            "value": "system",
                            "label": {"en": "System", "fi": "Järjestelmä"},
                        },
                    ],
                }
            ),
            "labels": json.dumps(
                {
                    "en": "Theme (light/dark/system)",
                    "fi": "Teema (vaalea/tumma/järjestelmä)",
                }
            ),
        },
        {
            "key": "login_background_color",
            "value": json.dumps(
                {"value": "#f9fafb", "category": "appearance", "type": "string"}
            ),
            "labels": json.dumps(
                {"en": "Login background color", "fi": "Kirjautumisen taustaväri"}
            ),
        },
        {
            "key": "login_background_color_dark",
            "value": json.dumps(
                {"value": "#18181b", "category": "appearance", "type": "string"}
            ),
            "labels": json.dumps(
                {
                    "en": "Login background color (dark)",
                    "fi": "Kirjautumisen taustaväri (tumma)",
                }
            ),
        },
        {
            "key": "login_box_color",
            "value": json.dumps(
                {"value": "#fff", "category": "appearance", "type": "string"}
            ),
            "labels": json.dumps(
                {"en": "Login box color", "fi": "Kirjautumislaatikon väri"}
            ),
        },
        {
            "key": "login_box_color_dark",
            "value": json.dumps(
                {"value": "#23272e", "category": "appearance", "type": "string"}
            ),
            "labels": json.dumps(
                {
                    "en": "Login box color (dark)",
                    "fi": "Kirjautumislaatikon väri (tumma)",
                }
            ),
        },
        {
            "key": "login_text_color",
            "value": json.dumps(
                {"value": "#111827", "category": "appearance", "type": "string"}
            ),
            "labels": json.dumps(
                {"en": "Login text color", "fi": "Kirjautumisen tekstiväri"}
            ),
        },
        {
            "key": "login_text_color_dark",
            "value": json.dumps(
                {"value": "#f3f4f6", "category": "appearance", "type": "string"}
            ),
            "labels": json.dumps(
                {
                    "en": "Login text color (dark)",
                    "fi": "Kirjautumisen tekstiväri (tumma)",
                }
            ),
        },
        {
            "key": "logo_url",
            "value": json.dumps(
                {"value": "", "category": "appearance", "type": "string"}
            ),
            "labels": json.dumps({"en": "Logo URL", "fi": "Logon URL"}),
        },
    ]
    conn = op.get_bind()
    for setting in default_settings:
        conn.execute(
            sa.text(
                "INSERT INTO settings (key, value, labels) "
                "VALUES (:key, :value, :labels)"
            ),
            setting,
        )


def downgrade():
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_table("users")
    op.drop_index(op.f("ix_settings_id"), table_name="settings")
    op.drop_table("settings")
