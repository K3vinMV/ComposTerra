"""Entrena y evalúa el clasificador de estado del proceso de compostaje.

ENTRADA   dataset_composta.csv  (generado por preparar_dataset.py)
SALIDA    modelos/modelo_composta.joblib

DECISIONES METODOLÓGICAS
------------------------
1. Partición POR LOTE, no aleatoria.
   Las muestras de un mismo lote son una serie temporal correlacionada. Si el
   día 12 de un lote quedara en entrenamiento y el día 15 del mismo lote en
   prueba, habría fuga de información y el resultado saldría inflado.
   `GroupShuffleSplit` garantiza que ningún lote aparezca en ambos conjuntos.

2. Evaluación sobre múltiples particiones.
   Una sola partición con 63 lotes es sensible al azar. Se promedian N
   particiones distintas y se reporta la desviación estándar.

3. Comparación contra alternativas más simples (requisito de justificación
   del algoritmo). Se contrastan cuatro configuraciones:
     - Baseline de umbrales fijos (sin aprendizaje)
     - Solo tiempo (¿basta un calendario?)
     - Solo sensores (¿basta la lectura instantánea?)
     - Modelo completo
   Ninguna variante simple alcanza al modelo completo: ese es el argumento
   empírico que justifica el uso de Random Forest.

MODELO MATEMÁTICO
-----------------
Random Forest: ensamble de B árboles de decisión. Cada árbol se entrena sobre
una muestra bootstrap y en cada nodo evalúa un subconjunto aleatorio de
variables, eligiendo la división que minimiza la impureza de Gini:

    G(t) = 1 - Σ p(c|t)²        sobre las clases c del nodo t

La predicción final es el voto mayoritario de los B árboles, y la confianza
reportada es la proporción de árboles que votaron por la clase ganadora.

Uso:
    python entrenar_modelo.py
"""
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import GroupShuffleSplit

BASE = Path(__file__).parent
DATASET = BASE / "dataset_composta.csv"
MODELO_OUT = BASE / "modelos" / "modelo_composta.joblib"

FEATURES = ["progreso", "temperatura", "humedad", "ph"]
CLASES = ["optimo", "aceptable", "deficiente"]
N_PARTICIONES = 20
TEST_SIZE = 0.25
SEMILLA = 42

# Rangos óptimos de referencia del proceso (usados por el baseline y por las
# alertas del sistema). Deben coincidir con RANGOS en el frontend.
RANGOS = {"temperatura": (45, 65), "humedad": (40, 60), "ph": (6, 8)}


def nuevo_modelo() -> RandomForestClassifier:
    return RandomForestClassifier(
        n_estimators=300,          # ensamble amplio: estabiliza sin costo relevante
        max_depth=8,               # limita profundidad para evitar sobreajuste
        random_state=SEMILLA,
        class_weight="balanced",   # compensa el desbalance entre clases
    )


def baseline_umbrales(fila) -> str:
    """Clasificación por reglas fijas, sin aprendizaje. Sirve de referencia."""
    dentro = sum(
        RANGOS[p][0] <= fila[p] <= RANGOS[p][1] for p in RANGOS
    )
    return {3: "optimo", 2: "aceptable"}.get(dentro, "deficiente")


def evaluar_configuraciones(df: pd.DataFrame) -> pd.DataFrame:
    """Compara el modelo completo contra alternativas más simples."""
    configs = {
        "Baseline umbrales fijos": None,
        "Solo tiempo": ["progreso"],
        "Solo sensores": ["temperatura", "humedad", "ph"],
        "Modelo completo": FEATURES,
    }
    acumulado = {k: [] for k in configs}

    for semilla in range(N_PARTICIONES):
        gss = GroupShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=semilla)
        idx_tr, idx_te = next(gss.split(df, groups=df["lote"]))
        train, test = df.iloc[idx_tr], df.iloc[idx_te]

        for nombre, feats in configs.items():
            if feats is None:
                pred = test.apply(baseline_umbrales, axis=1)
            else:
                modelo = nuevo_modelo().fit(train[feats], train["calidad"])
                pred = modelo.predict(test[feats])
            acumulado[nombre].append(accuracy_score(test["calidad"], pred))

    return pd.DataFrame(
        {
            "accuracy media": {k: np.mean(v) for k, v in acumulado.items()},
            "desv. estándar": {k: np.std(v) for k, v in acumulado.items()},
            "mínimo": {k: np.min(v) for k, v in acumulado.items()},
        }
    ).round(3)


def main():
    if not DATASET.exists():
        sys.exit(f"No se encontró {DATASET}. Ejecuta primero: python preparar_dataset.py")

    df = pd.read_csv(DATASET)
    print(f"Dataset: {len(df)} muestras · {df['lote'].nunique()} lotes")
    print(f"Distribución de clases:\n{df['calidad'].value_counts().to_string()}\n")

    # ---------- Comparación de configuraciones ----------
    print("=" * 62)
    print(f"COMPARACIÓN DE CONFIGURACIONES ({N_PARTICIONES} particiones por lote)")
    print("=" * 62)
    tabla = evaluar_configuraciones(df)
    print(tabla.to_string(), "\n")

    completo = tabla.loc["Modelo completo", "accuracy media"]
    for alternativa in ["Baseline umbrales fijos", "Solo tiempo", "Solo sensores"]:
        delta = (completo - tabla.loc[alternativa, "accuracy media"]) * 100
        print(f"  Modelo completo supera a '{alternativa}' por {delta:+.1f} puntos")

    # ---------- Modelo final ----------
    print("\n" + "=" * 62)
    print("MODELO FINAL")
    print("=" * 62)
    gss = GroupShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=SEMILLA)
    idx_tr, idx_te = next(gss.split(df, groups=df["lote"]))
    train, test = df.iloc[idx_tr], df.iloc[idx_te]
    print(
        f"Entrenamiento: {len(train)} muestras / {train['lote'].nunique()} lotes  ·  "
        f"Prueba: {len(test)} muestras / {test['lote'].nunique()} lotes\n"
    )

    modelo = nuevo_modelo().fit(train[FEATURES], train["calidad"])
    pred = modelo.predict(test[FEATURES])

    print("Matriz de confusión (filas = real, columnas = predicho):")
    print(
        pd.DataFrame(
            confusion_matrix(test["calidad"], pred, labels=CLASES),
            index=CLASES,
            columns=CLASES,
        ).to_string(),
        "\n",
    )
    print("Reporte de clasificación:")
    print(classification_report(test["calidad"], pred, labels=CLASES, zero_division=0))

    print(f"Accuracy: {accuracy_score(test['calidad'], pred):.3f}")
    print(f"F1-macro: {f1_score(test['calidad'], pred, average='macro'):.3f}\n")

    print("Importancia de variables:")
    for f, imp in sorted(
        zip(FEATURES, modelo.feature_importances_), key=lambda x: -x[1]
    ):
        print(f"  {f:14s} {imp:.3f}")

    # ---------- Exportación ----------
    MODELO_OUT.parent.mkdir(exist_ok=True)
    joblib.dump(
        {
            "modelo": modelo,
            "features": FEATURES,
            "clases": CLASES,
            "duracion_ciclo_referencia_dias": int(df.groupby("lote")["dia"].max().median()),
            "accuracy_validacion": float(completo),
        },
        MODELO_OUT,
    )
    print(f"\nModelo guardado en: {MODELO_OUT}")


if __name__ == "__main__":
    main()
