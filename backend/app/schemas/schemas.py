"""Schemas Pydantic — validación de entrada y formato de salida de la API."""
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_serializer


# ------------------------------- Auth --------------------------------
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    email: EmailStr
    rol: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioOut


# ------------------------------- Lotes -------------------------------
class LoteCreate(BaseModel):
    fecha_inicio: date
    material_principal: str = Field(max_length=100)
    peso_kg: Decimal = Field(gt=0)
    # Duración esperada del ciclo; se usa para normalizar el tiempo en el modelo
    duracion_estimada_dias: int = Field(default=120, ge=1, le=365)


class LoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fecha_inicio: date
    material_principal: str
    peso_kg: Decimal
    duracion_estimada_dias: int
    estado: str


# --------------------------- Registros sensor ------------------------
class RegistroCreate(BaseModel):
    """Payload que envía el simulador de sensor."""
    id_lote: int
    temperatura: Decimal = Field(ge=-10, le=100)
    humedad: Decimal = Field(ge=0, le=100)
    ph: Decimal = Field(ge=0, le=14)


def _como_utc(valor: datetime) -> datetime:
    
    return valor if valor.tzinfo else valor.replace(tzinfo=timezone.utc)


class RegistroOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_lote: int
    temperatura: Decimal
    humedad: Decimal
    ph: Decimal
    timestamp: datetime

    @field_serializer("timestamp")
    def _serializar_timestamp(self, valor: datetime) -> datetime:
        return _como_utc(valor)


# ----------------------------- Predicciones --------------------------
class PrediccionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_lote: int
    resultado: Literal["optimo", "aceptable", "deficiente"]
    confianza: Decimal
    fecha: datetime

    @field_serializer("fecha")
    def _serializar_fecha(self, valor: datetime) -> datetime:
        return _como_utc(valor)


class PrediccionDetalleOut(PrediccionOut):

    votos: dict | None = None
    entradas: dict | None = None


# ------------------------------- Alertas -----------------------------
class AlertaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_lote: int
    tipo: Literal["temperatura", "humedad", "ph", "sin_datos"]
    direccion: Literal["bajo", "alto"] | None
    valor: Decimal | None
    abierta_en: datetime
    cerrada_en: datetime | None

    @field_serializer("abierta_en", "cerrada_en")
    def _serializar_fechas(self, valor: datetime | None) -> datetime | None:
        return _como_utc(valor) if valor else None
