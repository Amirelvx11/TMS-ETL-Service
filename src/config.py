import os
from dotenv import load_dotenv
from sqlalchemy import create_engine


load_dotenv()


def _require_env(key: str) -> str:
    """Ensure required environment variables are present & passed."""
    value = os.getenv(key)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {key}")
    return value

# Required ENV variables
SOURCE_DB = _require_env("SOURCE_DB") # MYSQL SQLAlchemy URI
TARGET_DB = _require_env("TARGET_DB") # MSSQL+pyodbc SQLAlchemy URI
USER_GUID = _require_env("USER_GUID") # ADMIN GUID (for data submission)

# Engines (MySQL and MSSQL)
src_engine = create_engine(
    SOURCE_DB,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=5,
    pool_timeout=5,
    pool_recycle=3600,
)

dst_engine = create_engine(
    TARGET_DB,
    pool_pre_ping=True,
    fast_executemany=True,
    max_overflow=5,
    pool_timeout=5,
    pool_recycle=3600,
    connect_args={"timeout": 5, "LoginTimeout": 5},
)
