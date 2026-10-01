from src.db.connection import connect, database
from src.db.models import ALL_MODELS


def init_db(db_path=None) -> None:
    connect(db_path)
    database.create_tables(ALL_MODELS, safe=True)
