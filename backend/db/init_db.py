from sqlalchemy import inspect

from backend.models.base import Base
from backend.db.session import check_database_connection, engine


def init_db() -> None:
    check_database_connection()
    Base.metadata.create_all(bind=engine)


def drop_db() -> None:
    check_database_connection()
    Base.metadata.drop_all(bind=engine)


def get_table_names() -> list[str]:
    check_database_connection()
    return inspect(engine).get_table_names()


if __name__ == "__main__":
    init_db()
    print("Database initialized with tables:", ", ".join(get_table_names()))
