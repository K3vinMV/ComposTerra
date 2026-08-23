"""Endpoints de lotes y sus registros de sensor. Todos requieren JWT."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models import Lote, Prediccion, RegistroSensor, Usuario
from app.schemas import LoteCreate, LoteOut, PrediccionOut, RegistroOut

router = APIRouter(prefix="/lotes", tags=["lotes"])


def _obtener_lote(db: Session, id_lote: int) -> Lote:
    lote = db.get(Lote, id_lote)
    if lote is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lote {id_lote} no encontrado",
        )
    return lote


@router.get("", response_model=list[LoteOut])
def listar_lotes(
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    return db.query(Lote).order_by(Lote.fecha_inicio.desc()).all()


@router.post("", response_model=LoteOut, status_code=status.HTTP_201_CREATED)
def crear_lote(
    datos: LoteCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    lote = Lote(**datos.model_dump())
    db.add(lote)
    db.commit()
    db.refresh(lote)
    return lote


@router.patch("/{id_lote}/estado", response_model=LoteOut)
def cambiar_estado(
    id_lote: int,
    estado: str = Query(pattern="^(activo|finalizado)$"),
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    lote = _obtener_lote(db, id_lote)
    lote.estado = estado
    db.commit()
    db.refresh(lote)
    return lote


@router.get("/{id_lote}/registros", response_model=list[RegistroOut])
def listar_registros(
    id_lote: int,
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    """Registros más recientes primero.

    - Dashboard tiempo real: limit=1 (última lectura)
    - Gráfica histórica: limit alto (el frontend los reordena ascendente)
    """
    _obtener_lote(db, id_lote)
    return (
        db.query(RegistroSensor)
        .filter(RegistroSensor.id_lote == id_lote)
        .order_by(RegistroSensor.timestamp.desc(), RegistroSensor.id.desc())
        .limit(limit)
        .all()
    )


@router.get("/{id_lote}/predicciones", response_model=list[PrediccionOut])
def listar_predicciones(
    id_lote: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    _obtener_lote(db, id_lote)
    return (
        db.query(Prediccion)
        .filter(Prediccion.id_lote == id_lote)
        .order_by(Prediccion.fecha.desc())
        .all()
    )
