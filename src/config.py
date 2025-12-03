import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from .logger import get_logger

load_dotenv()
log = get_logger("config")

def _require_env(key: str) -> str:
    """Ensure required environment variables are present."""
    val = os.getenv(key)
    if not val:
        raise RuntimeError(f"Missing required environment variable: {key}")
    return val

# Required ENV variables
SOURCE_DB = _require_env("SOURCE_DB") # pyodbc SQLAlchemy URI
TARGET_DB = _require_env("TARGET_DB") # pyodbc SQLAlchemy URI
USER_GUID = _require_env("USER_GUID") # MUST be valid in system.User.Id

# Engines (MySQL and MSSQL)
src_engine = create_engine(SOURCE_DB, pool_pre_ping=True)
log.debug("Source engine (MySQL) created.")

dst_engine = create_engine(
    TARGET_DB,
    pool_pre_ping=True,
    fast_executemany=True,
    max_overflow=5,
    pool_timeout=5,
    pool_recycle=1800,
    connect_args={"timeout": 5, "LoginTimeout": 5},
)
log.debug("Destination engine (MSSQL) created.")
