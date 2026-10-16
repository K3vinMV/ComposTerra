"""GET /alertas — historial de alertas para el tablero"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models import Alerta, Usuario
from app.schemas import AlertaOut

router = APIRouter(prefix="/alertas", tags=["alertas"])


@router.get("", response_model=list[AlertaOut])
def listar_alertas(
    solo_abiertas: bool = False,
    id_lote: int | None = None,
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    consulta = select(Alerta).order_by(Alerta.id.desc()).limit(limit)
    if solo_abiertas:
        consulta = consulta.where(Alerta.cerrada_en.is_(None))
    if id_lote is not None:
        consulta = consulta.where(Alerta.id_lote == id_lote)
    return db.scalars(consulta).all()
