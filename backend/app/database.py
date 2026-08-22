"""Conexión a MySQL con SQLAlchemy.

Local → MySQL local. AWS → RDS MySQL (solo cambia DATABASE_URL).
pool_pre_ping evita errores por conexiones muertas (importante en Lambda/RDS).
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True, pool_recycle=3600)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """Dependencia de FastAPI: una sesión por request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
