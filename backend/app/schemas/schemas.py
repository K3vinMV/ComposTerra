"""Schemas Pydantic — validación de entrada y formato de salida de la API."""
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


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


class LoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fecha_inicio: date
    material_principal: str
    peso_kg: Decimal
    estado: str


# --------------------------- Registros sensor ------------------------
class RegistroCreate(BaseModel):
    """Payload que envía el simulador de sensor."""
    id_lote: int
    temperatura: Decimal = Field(ge=-10, le=100)
    humedad: Decimal = Field(ge=0, le=100)
    ph: Decimal = Field(ge=0, le=14)


class RegistroOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_lote: int
    temperatura: Decimal
    humedad: Decimal
    ph: Decimal
    timestamp: datetime


# ----------------------------- Predicciones --------------------------
class PrediccionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_lote: int
    resultado: Literal["optimo", "aceptable", "deficiente"]
    confianza: Decimal
    fecha: datetime
