"""Servicio de clasificación del estado del proceso de compostaje.

Carga el modelo Random Forest entrenado y expone una función de predicción.
El modelo se carga una sola vez por proceso (lazy + cache) y se reutiliza en
cada petición.

El archivo .joblib contiene un diccionario con el modelo y sus metadatos, para
que el backend no tenga que asumir el orden de las variables ni las clases:

    {"modelo": ..., "features": [...], "clases": [...], ...}
"""
from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd

from app.config import settings

# Debe coincidir con FEATURES en ml/entrenar_modelo.py
FEATURES = ["progreso", "temperatura", "humedad", "ph"]


@lru_cache(maxsize=1)
def _cargar_bundle() -> dict:
    ruta = Path(settings.ml_model_path)
    if not ruta.is_absolute():
        # relativo a backend/ (directorio desde el que se ejecuta uvicorn)
        ruta = Path(__file__).resolve().parents[2] / ruta
    if not ruta.exists():
        raise FileNotFoundError(
            f"Modelo no encontrado en {ruta}. Ejecuta primero: "
            "python ml/preparar_dataset.py && python ml/entrenar_modelo.py"
        )
    bundle = joblib.load(ruta)
    # Compatibilidad: si el .joblib es un modelo suelto, se envuelve
    if not isinstance(bundle, dict):
        bundle = {"modelo": bundle, "features": FEATURES}
    return bundle


def predecir_estado(
    progreso: float, temperatura: float, humedad: float, ph: float
) -> tuple[str, float]:
    """Clasifica el estado del proceso de un lote.

    Args:
        progreso: avance del ciclo, de 0 (inicio) a 1 (fin esperado).
        temperatura: promedio reciente en °C.
        humedad: promedio reciente en %.
        ph: promedio reciente.

    Returns:
        (resultado, confianza) donde resultado es optimo | aceptable | deficiente
        y confianza es el porcentaje de árboles que votaron por esa clase.
    """
    bundle = _cargar_bundle()
    modelo = bundle["modelo"]
    features = bundle.get("features", FEATURES)

    valores = {
        "progreso": progreso,
        "temperatura": temperatura,
        "humedad": humedad,
        "ph": ph,
    }
    X = pd.DataFrame([[valores[f] for f in features]], columns=features)

    resultado = str(modelo.predict(X)[0])
    confianza = float(max(modelo.predict_proba(X)[0]) * 100)
    return resultado, round(confianza, 2)
