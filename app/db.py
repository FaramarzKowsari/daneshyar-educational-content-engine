from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import Settings


class Base(DeclarativeBase):
    pass


class Database:
    def __init__(self, settings: Settings):
        settings.ensure_directories()
        self.engine = create_engine(
            f"sqlite:///{settings.db_path}",
            connect_args={"check_same_thread": False},
            future=True,
        )
        self.session_factory = sessionmaker(
            bind=self.engine,
            class_=Session,
            autoflush=False,
            expire_on_commit=False,
        )

    def create_all(self) -> None:
        from app import models  # noqa: F401

        Base.metadata.create_all(self.engine)

    def get_session(self) -> Generator[Session, None, None]:
        with self.session_factory() as session:
            yield session
