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


def obtener_metricas() -> dict:
    """Métricas del modelo en producción, generadas durante el entrenamiento."""
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
    """Clasifica el estado del proceso de un lote.

    Args:
        progreso: avance del ciclo, de 0 (inicio) a 1 (fin esperado).
        temperatura: promedio reciente en °C.
        humedad: promedio reciente en %.
        ph: promedio reciente.

    Returns:
        (resultado, confianza, votos) donde `resultado` es la clase más votada,
        `confianza` el porcentaje de árboles que la eligieron, y `votos` el
        desglose completo del ensamble: cuántos árboles votaron por cada clase.
        El desglose permite mostrar de dónde sale la confianza en lugar de
        presentarla como un número sin origen.
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
