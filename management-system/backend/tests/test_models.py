from models import Setting, User


def test_user_model_exists():
    """Test that User model can be imported and instantiated."""
    user = User()
    assert user is not None
    assert hasattr(user, "username")
    assert hasattr(user, "hashed_password")
    assert hasattr(user, "is_active")
    assert hasattr(user, "permissions")


def test_setting_model_exists():
    """Test that Setting model can be imported and instantiated."""
    setting = Setting()
    assert setting is not None
    assert hasattr(setting, "key")
    assert hasattr(setting, "value")
    assert hasattr(setting, "labels")


def test_models_have_correct_table_names():
    """Test that models have the correct table names."""
    assert User.__tablename__ == "users"
    assert Setting.__tablename__ == "settings"


def test_user_model_columns():
    """Test User model has all required columns."""
    user_columns = [column.name for column in User.__table__.columns]
    expected_columns = ["id", "username", "hashed_password", "is_active", "permissions"]

    for column in expected_columns:
        assert column in user_columns


def test_setting_model_columns():
    """Test Setting model has all required columns."""
    setting_columns = [column.name for column in Setting.__table__.columns]
    expected_columns = ["id", "key", "value", "labels"]

    for column in expected_columns:
        assert column in setting_columns
