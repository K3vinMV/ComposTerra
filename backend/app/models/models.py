"""Modelos SQLAlchemy — espejo de database/schema.sql."""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    DECIMAL, BigInteger, Date, DateTime, Enum, ForeignKey, Index, String, func,
)
from sqlalchemy.dialects.mysql import BIGINT, INTEGER
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True), primary_key=True, autoincrement=True
    )
    nombre: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(150), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    rol: Mapped[str] = mapped_column(
        Enum("admin", "operador", name="rol_enum"), server_default="operador"
    )


class Lote(Base):
    __tablename__ = "lotes"

    id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True), primary_key=True, autoincrement=True
    )
    fecha_inicio: Mapped[date] = mapped_column(Date)
    material_principal: Mapped[str] = mapped_column(String(100))
    peso_kg: Mapped[Decimal] = mapped_column(DECIMAL(8, 2))
    estado: Mapped[str] = mapped_column(
        Enum("activo", "finalizado", name="estado_enum"), server_default="activo"
    )

    registros: Mapped[list["RegistroSensor"]] = relationship(
        back_populates="lote", cascade="all, delete-orphan", passive_deletes=True
    )
    predicciones: Mapped[list["Prediccion"]] = relationship(
        back_populates="lote", cascade="all, delete-orphan", passive_deletes=True
    )


class RegistroSensor(Base):
    __tablename__ = "registros_sensor"
    __table_args__ = (Index("idx_registros_lote_ts", "id_lote", "timestamp"),)

    id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True), primary_key=True, autoincrement=True
    )
    id_lote: Mapped[int] = mapped_column(
        INTEGER(unsigned=True), ForeignKey("lotes.id", ondelete="CASCADE")
    )
    temperatura: Mapped[Decimal] = mapped_column(DECIMAL(5, 2))  # °C (óptimo 45-65)
    humedad: Mapped[Decimal] = mapped_column(DECIMAL(5, 2))      # %  (óptimo 40-60)
    ph: Mapped[Decimal] = mapped_column(DECIMAL(4, 2))           #    (óptimo 6-8)
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    lote: Mapped["Lote"] = relationship(back_populates="registros")


class Prediccion(Base):
    __tablename__ = "predicciones"
    __table_args__ = (Index("idx_predicciones_lote", "id_lote"),)

    id: Mapped[int] = mapped_column(
        INTEGER(unsigned=True), primary_key=True, autoincrement=True
    )
    id_lote: Mapped[int] = mapped_column(
        INTEGER(unsigned=True), ForeignKey("lotes.id", ondelete="CASCADE")
    )
    resultado: Mapped[str] = mapped_column(
        Enum("optimo", "aceptable", "deficiente", name="resultado_enum")
    )
    confianza: Mapped[Decimal] = mapped_column(DECIMAL(5, 2))  # % 0-100
    fecha: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    lote: Mapped["Lote"] = relationship(back_populates="predicciones")