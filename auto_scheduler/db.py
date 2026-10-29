"""
db.py
=====
Thin SQLAlchemy engine factory shared by every module in auto_scheduler.
Returns a NullPool engine (no persistent connections) — safe for use
in background threads and scripts.
"""

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.pool import NullPool

from .config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME


def get_engine():
    """Create and return a fresh SQLAlchemy engine."""
    url = URL.create(
        drivername="mysql+pymysql",
        username=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
    )

    engine = create_engine(
        url,
        poolclass=NullPool,
        connect_args={
            "local_infile":   True,
            "connect_timeout": 15,
            "read_timeout":   180,
            "write_timeout":  180,
            "ssl_disabled":   True,
        },
    )
    return engine
