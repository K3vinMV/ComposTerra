"""POST /predicciones/{id_lote} — clasifica el estado actual del proceso.

Flujo:
    1. Calcula el avance del ciclo (progreso = días transcurridos / duración estimada).
    2. Promedia las lecturas recientes del sensor (ventana de 24 h).
    3. Clasifica con el Random Forest y persiste el resultado.

"""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.ml import predecir_estado
from app.database import get_db
from app.models import Lote, Prediccion, RegistroSensor, Usuario
from app.schemas import PrediccionDetalleOut, PrediccionOut

router = APIRouter(prefix="/predicciones", tags=["predicciones"])

VENTANA_HORAS = 24


@router.post(
    "/{id_lote}",
    response_model=PrediccionDetalleOut,
    status_code=status.HTTP_201_CREATED,
)
def crear_prediccion(
    id_lote: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    lote = db.get(Lote, id_lote)
    if lote is None:
        raise HTTPException(status_code=404, detail=f"Lote {id_lote} no encontrado")

    # --- 1. Avance del ciclo, normalizado a [0, 1] ---
    dias_transcurridos = (datetime.now().date() - lote.fecha_inicio).days
    duracion = lote.duracion_estimada_dias or 120
    progreso = min(max(dias_transcurridos / duracion, 0.0), 1.0)

    # --- 2. Lecturas recientes ---
    desde = datetime.now() - timedelta(hours=VENTANA_HORAS)
    consulta = db.query(
        func.avg(RegistroSensor.temperatura),
        func.avg(RegistroSensor.humedad),
        func.avg(RegistroSensor.ph),
    ).filter(RegistroSensor.id_lote == id_lote)

    promedios = consulta.filter(RegistroSensor.timestamp >= desde).one()
    if promedios[0] is None:
        # Sin lecturas en la ventana: se recurre al historial completo del lote
        promedios = consulta.one()
    if promedios[0] is None:
        raise HTTPException(
            status_code=400,
            detail=f"El lote {id_lote} no tiene registros de sensor; no se puede predecir",
        )

    # --- 3. Clasificación ---
    temperatura, humedad, ph = (float(promedios[i]) for i in range(3))
    try:
        resultado, confianza, votos = predecir_estado(progreso, temperatura, humedad, ph)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))

    prediccion = Prediccion(id_lote=id_lote, resultado=resultado, confianza=confianza)
    try:
        db.add(prediccion)
        db.commit()
        db.refresh(prediccion)
    except Exception:
        db.rollback()
        raise

    # La respuesta incluye el desglose de la votación y las entradas usadas,
    # para que la interfaz pueda explicar cómo se llegó al resultado.
    return PrediccionDetalleOut(
        **PrediccionOut.model_validate(prediccion).model_dump(),
        votos=votos,
        entradas={
            "progreso": round(progreso, 3),
            "dias_transcurridos": dias_transcurridos,
            "duracion_estimada_dias": duracion,
            "temperatura": round(temperatura, 2),
            "humedad": round(humedad, 2),
            "ph": round(ph, 2),
        },
    )
