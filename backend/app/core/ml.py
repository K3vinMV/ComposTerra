"""Servicio de clasificación del estado del proceso de compostaje"""
from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd

from app.config import settings

FEATURES = ["progreso", "temperatura", "humedad", "ph"]


@lru_cache(maxsize=1)
def _cargar_bundle() -> dict:
    ruta = Path(settings.ml_model_path)
    if not ruta.is_absolute():
        ruta = Path(__file__).resolve().parents[2] / ruta
    if not ruta.exists():
        raise FileNotFoundError(
            f"Modelo no encontrado en {ruta}. Ejecuta primero: "
            "python ml/preparar_dataset.py && python ml/entrenar_modelo.py"
        )
    bundle = joblib.load(ruta)
    if not isinstance(bundle, dict):
        bundle = {"modelo": bundle, "features": FEATURES}
    return bundle


def obtener_metricas() -> dict:
    bundle = _cargar_bundle()
    metricas = bundle.get("metricas")
    if metricas is None:
        raise FileNotFoundError(
            "El modelo no incluye métricas. Reentrena con: python ml/entrenar_modelo.py"
        )
    return metricas


def predecir_estado(
    progreso: float, temperatura: float, humedad: float, ph: float
) -> tuple[str, float, dict]:

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

    proporciones = modelo.predict_proba(X)[0]
    n_arboles = len(modelo.estimators_)
    votos = {
        str(clase): {
            "proporcion": round(float(p) * 100, 2),
            "arboles": int(round(float(p) * n_arboles)),
        }
        for clase, p in zip(modelo.classes_, proporciones)
    }

    resultado = str(modelo.predict(X)[0])
    confianza = float(max(proporciones) * 100)
    return resultado, round(confianza, 2), {"total_arboles": n_arboles, "por_clase": votos}
