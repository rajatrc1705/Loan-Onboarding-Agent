import os

from sqlmodel import Session, SQLModel, create_engine

from .settings import DATABASE_URL


def _sqlite_connect_args(database_url: str) -> dict:
    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


engine = create_engine(DATABASE_URL, connect_args=_sqlite_connect_args(DATABASE_URL))


def init_db() -> None:
    auto_create = os.getenv("AUTO_CREATE_TABLES")
    if auto_create is None:
        auto_create = "true" if DATABASE_URL.startswith("sqlite") else "false"
    if auto_create.lower() != "true":
        print("Skipping create_all; AUTO_CREATE_TABLES is disabled.")
        return
    print("Creating all tables, using this engine: ", engine)
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
