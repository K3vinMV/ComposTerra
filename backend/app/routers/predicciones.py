"""POST /predicciones/{id_lote} — genera y guarda una predicción de calidad.

Flujo: promedia los registros del sensor del lote → Random Forest →
guarda resultado + confianza en la tabla predicciones.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.ml import predecir_calidad
from app.database import get_db
from app.models import Lote, Prediccion, RegistroSensor, Usuario
from app.schemas import PrediccionOut

router = APIRouter(prefix="/predicciones", tags=["predicciones"])


@router.post("/{id_lote}", response_model=PrediccionOut, status_code=status.HTTP_201_CREATED)
def crear_prediccion(
    id_lote: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    if db.get(Lote, id_lote) is None:
        raise HTTPException(status_code=404, detail=f"Lote {id_lote} no encontrado")

    promedios = (
        db.query(
            func.avg(RegistroSensor.temperatura),
            func.avg(RegistroSensor.humedad),
            func.avg(RegistroSensor.ph),
        )
        .filter(RegistroSensor.id_lote == id_lote)
        .one()
    )
    if promedios[0] is None:
        raise HTTPException(
            status_code=400,
            detail=f"El lote {id_lote} no tiene registros de sensor; no se puede predecir",
        )

    try:
        resultado, confianza = predecir_calidad(
            float(promedios[0]), float(promedios[1]), float(promedios[2])
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))

    prediccion = Prediccion(id_lote=id_lote, resultado=resultado, confianza=confianza)
    db.add(prediccion)
    db.commit()
    db.refresh(prediccion)
    return prediccion
