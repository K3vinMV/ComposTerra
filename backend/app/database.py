"""Conexión a MySQL con SQLAlchemy."""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={"init_command": "SET time_zone = '+00:00'"},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """Abre una sesión por request y la cierra al final"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
