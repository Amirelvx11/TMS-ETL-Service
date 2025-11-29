import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

SOURCE_DB = os.getenv("SOURCE_DB")
TARGET_DB = os.getenv("TARGET_DB")

src_engine = create_engine(
    SOURCE_DB,
    pool_pre_ping=True
)

dst_engine = create_engine(
    TARGET_DB,
    pool_pre_ping=True,
    fast_executemany=True,
    max_overflow=5,
    pool_timeout=5,
    pool_recycle=1800,
    connect_args={
        "timeout": 5, 
        "LoginTimeout": 5
        },
)
