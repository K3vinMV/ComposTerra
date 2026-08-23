"""POST /registros — ingesta de lecturas del sensor (simulador).

Local: el simulador llama este endpoint vía HTTP cada 5 s.
AWS:   se reemplaza por MQTT → IoT Core → Lambda que inserta directo
       en RDS; este endpoint puede conservarse para pruebas.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models import Lote, RegistroSensor, Usuario
from app.schemas import RegistroCreate, RegistroOut

router = APIRouter(prefix="/registros", tags=["registros"])


@router.post("", response_model=RegistroOut, status_code=status.HTTP_201_CREATED)
def crear_registro(
    datos: RegistroCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    lote = db.get(Lote, datos.id_lote)
    if lote is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lote {datos.id_lote} no encontrado",
        )
    if lote.estado != "activo":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El lote {datos.id_lote} está finalizado; no acepta lecturas",
        )

    registro = RegistroSensor(**datos.model_dump())
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return registro
