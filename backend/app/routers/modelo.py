"""GET /modelo/info — expone las métricas del modelo en producción.

"""
from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import get_current_user
from app.core.ml import obtener_metricas
from app.models import Usuario

router = APIRouter(prefix="/modelo", tags=["modelo"])


@router.get("/info")
def info_modelo(_: Usuario = Depends(get_current_user)):
    try:
        return obtener_metricas()
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
