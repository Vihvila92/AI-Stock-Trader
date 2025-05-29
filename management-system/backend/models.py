from sqlalchemy import Boolean, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


# User model for authentication
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Integer, default=1, nullable=False)
    permissions = Column(
        String, nullable=True
    )  # JSON string, e.g. '{"can_manage_users": true}'


# Settings model for storing key-value pairs
class Setting(Base):
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False)
    value = Column(String, nullable=False)
    labels = Column(
        String, nullable=True
    )  # JSON: {"fi": "Site name", "en": "Site name"}
    category = Column(String, nullable=True)  # <-- ADD THIS
    type = Column(String, nullable=True)  # <-- ADD THIS
    enum = Column(Text, nullable=True)  # <-- ADD THIS
    default_value = Column(String, nullable=True)  # <-- ADD THIS
    is_editable = Column(Boolean, nullable=True)  # <-- ADD THIS
