"""Fix settings metadata: set category/type for all settings"""

import sqlalchemy as sa
from alembic import op

revision = "20240525fixmeta"
down_revision = "20240524efmeta"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    # site_name
    conn.execute(
        sa.text(
            """
        UPDATE settings SET category='general', type='string'
        WHERE key='site_name'
    """
        )
    )
    # vantage_api_key
    conn.execute(
        sa.text(
            """
        UPDATE settings SET category='api_keys', type='string'
        WHERE key='vantage_api_key'
    """
        )
    )
    # theme
    conn.execute(
        sa.text(
            """
        UPDATE settings SET category='appearance', type='enum',
        enum='[{"value": "light", "label": {"en": "Light", "fi": "Vaalea"}},
        {"value": "dark", "label": {"en": "Dark", "fi": "Tumma"}},
        {"value": "system", "label": {"en": "System", "fi": "Järjestelmä"}}]'
        WHERE key='theme'
    """
        )
    )
    # appearance-asetukset
    for key in [
        "login_background_color",
        "login_background_color_dark",
        "login_box_color",
        "login_box_color_dark",
        "login_text_color",
        "login_text_color_dark",
        "logo_url",
    ]:
        conn.execute(
            sa.text(
                "UPDATE settings SET category='appearance', "
                "type='string' WHERE key=:key"
            ),
            {"key": key},
        )


def downgrade():
    # Ei palauteta arvoja, vain tyhjennetään category/type/enum
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "UPDATE settings SET category=NULL, type=NULL, enum=NULL "
            "WHERE key IN ('site_name', 'vantage_api_key', 'theme', "
            "'login_background_color', 'login_background_color_dark', "
            "'login_box_color', 'login_box_color_dark', 'login_text_color', "
            "'login_text_color_dark', 'logo_url')"
        )
    )
