"""Servicio ML — carga el modelo Random Forest y predice calidad.

El modelo se carga una sola vez (lazy) y se reutiliza en cada request.
En Lambda esto aprovecha el contenedor caliente entre invocaciones.
"""
from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd

from app.config import settings

FEATURES = ["temperatura", "humedad", "ph"]


@lru_cache(maxsize=1)
def _cargar_modelo():
    ruta = Path(settings.ml_model_path)
    if not ruta.is_absolute():
        # relativo a backend/ (donde corre uvicorn)
        ruta = Path(__file__).resolve().parents[2] / ruta
    if not ruta.exists():
        raise FileNotFoundError(
            f"Modelo no encontrado en {ruta}. "
            "Ejecuta ml/generar_dataset.py y ml/entrenar_modelo.py primero."
        )
    return joblib.load(ruta)


def predecir_calidad(temperatura: float, humedad: float, ph: float) -> tuple[str, float]:
    """Devuelve (resultado, confianza%) a partir de promedios del lote."""
    modelo = _cargar_modelo()
    X = pd.DataFrame([[temperatura, humedad, ph]], columns=FEATURES)
    resultado = modelo.predict(X)[0]
    confianza = float(max(modelo.predict_proba(X)[0]) * 100)
    return str(resultado), round(confianza, 2)
