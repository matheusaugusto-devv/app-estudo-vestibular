import logging
from pathlib import Path

from peewee import SqliteDatabase

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DB_PATH = DATA_DIR / "app.db"

database = SqliteDatabase(
    None,
    pragmas={
        "journal_mode": "wal",
        "foreign_keys": 1,
        "cache_size": -1024 * 64,
    },
)


def connect(db_path: Path | None = None) -> SqliteDatabase:
    path = db_path or DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    database.init(str(path))
    database.connect(reuse_if_open=True)
    try:
        database.execute_sql("PRAGMA journal_mode=WAL")
    except Exception as e:
        logger.warning("Failed to enable WAL mode: %s", e)
    return database


def disconnect():
    if not database.is_closed():
        database.close()
