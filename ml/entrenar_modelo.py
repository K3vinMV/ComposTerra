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

3. Dos comparaciones independientes, para justificar por separado el algoritmo
   y el conjunto de variables:

   A. Algoritmo (variables fijas). Se contrasta contra dos reglas sin
      aprendizaje y dos modelos entrenados más simples. Se incluyen DOS reglas
      a propósito: la operativa, que es la que usa hoy la planta, y una
      heurística construida específicamente para madurez. Comparar solo contra
      la primera sería un baseline mal planteado, porque responde una pregunta
      distinta ("¿opera bien?" en vez de "¿está madura?").

   B. Variables (algoritmo fijo). Verifica que ni el tiempo ni los sensores
      bastan por separado, y que el aporte real está en la combinación.

   El argumento defendible es el margen sobre los modelos entrenados
   (regresión logística y árbol simple), no sobre las reglas.

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
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

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


def regla_operativa(fila) -> str:
    """Regla que usa hoy la planta: todo dentro de rango = proceso correcto.

    Es la práctica actual contra la que compite el sistema. Su límite es que
    responde "¿la pila opera bien ahora?", no "¿qué tan madura está?".
    """
    dentro = sum(RANGOS[p][0] <= fila[p] <= RANGOS[p][1] for p in RANGOS)
    return {3: "optimo", 2: "aceptable"}.get(dentro, "deficiente")


def regla_madurez(fila) -> str:
    """Heurística de dominio orientada a madurez: composta madura = fría y seca.

    Se incluye para que la comparación sea justa: a diferencia de la regla
    operativa, esta sí fue construida para predecir madurez. Descarta la
    objeción de estar midiendo contra un baseline mal planteado.
    """
    señales = sum(
        [fila["temperatura"] < 35, fila["humedad"] < 35, 6.5 <= fila["ph"] <= 8.5]
    )
    return {3: "optimo", 2: "aceptable"}.get(señales, "deficiente")


def _resumen(acumulado: dict) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "accuracy media": {k: np.mean(v) for k, v in acumulado.items()},
            "desv. estándar": {k: np.std(v) for k, v in acumulado.items()},
            "mínimo": {k: np.min(v) for k, v in acumulado.items()},
        }
    ).round(3)


def comparar_algoritmos(df: pd.DataFrame) -> pd.DataFrame:
    """Justifica la elección de Random Forest (requisito de justificación).

    Compara, sobre el mismo conjunto de variables, cuatro alternativas de
    complejidad creciente: dos reglas sin aprendizaje y dos modelos entrenados
    más simples que el ensamble.
    """
    entrenables = {
        "Árbol de decisión (prof. 3)": DecisionTreeClassifier(
            max_depth=3, random_state=SEMILLA, class_weight="balanced"
        ),
        "Regresión logística": make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=1000, class_weight="balanced"),
        ),
        "Random Forest (modelo final)": None,  # se instancia por partición
    }
    orden = ["Regla operativa de la planta", "Heurística de madurez"] + list(entrenables)
    acumulado = {k: [] for k in orden}

    for semilla in range(N_PARTICIONES):
        gss = GroupShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=semilla)
        idx_tr, idx_te = next(gss.split(df, groups=df["lote"]))
        train, test = df.iloc[idx_tr], df.iloc[idx_te]
        y = test["calidad"]

        acumulado["Regla operativa de la planta"].append(
            accuracy_score(y, test.apply(regla_operativa, axis=1))
        )
        acumulado["Heurística de madurez"].append(
            accuracy_score(y, test.apply(regla_madurez, axis=1))
        )
        for nombre, estimador in entrenables.items():
            modelo = nuevo_modelo() if estimador is None else clone(estimador)
            modelo.fit(train[FEATURES], train["calidad"])
            acumulado[nombre].append(accuracy_score(y, modelo.predict(test[FEATURES])))

    return _resumen(acumulado)


def comparar_variables(df: pd.DataFrame) -> pd.DataFrame:
    """Justifica el conjunto de variables, con el algoritmo fijo.

    Muestra que ni el tiempo ni los sensores bastan por separado: el aporte
    está en la combinación.
    """
    configs = {
        "Solo tiempo": ["progreso"],
        "Solo sensores": ["temperatura", "humedad", "ph"],
        "Tiempo + sensores": FEATURES,
    }
    acumulado = {k: [] for k in configs}

    for semilla in range(N_PARTICIONES):
        gss = GroupShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=semilla)
        idx_tr, idx_te = next(gss.split(df, groups=df["lote"]))
        train, test = df.iloc[idx_tr], df.iloc[idx_te]

        for nombre, feats in configs.items():
            modelo = nuevo_modelo().fit(train[feats], train["calidad"])
            acumulado[nombre].append(
                accuracy_score(test["calidad"], modelo.predict(test[feats]))
            )

    return _resumen(acumulado)


def main():
    if not DATASET.exists():
        sys.exit(f"No se encontró {DATASET}. Ejecuta primero: python preparar_dataset.py")

    df = pd.read_csv(DATASET)
    print(f"Dataset: {len(df)} muestras · {df['lote'].nunique()} lotes")
    print(f"Distribución de clases:\n{df['calidad'].value_counts().to_string()}\n")

    # ---------- A. Justificación del algoritmo ----------
    print("=" * 66)
    print(f"A. COMPARACIÓN DE ALGORITMOS ({N_PARTICIONES} particiones por lote)")
    print("=" * 66)
    algos = comparar_algoritmos(df)
    print(algos.to_string(), "\n")

    completo = algos.loc["Random Forest (modelo final)", "accuracy media"]
    for otro in algos.index:
        if otro.startswith("Random"):
            continue
        delta = (completo - algos.loc[otro, "accuracy media"]) * 100
        print(f"  Random Forest supera a '{otro}' por {delta:+.1f} puntos")

    # ---------- B. Justificación de las variables ----------
    print("\n" + "=" * 66)
    print(f"B. APORTE DE CADA GRUPO DE VARIABLES ({N_PARTICIONES} particiones)")
    print("=" * 66)
    vars_ = comparar_variables(df)
    print(vars_.to_string(), "\n")
    for otro in ["Solo tiempo", "Solo sensores"]:
        delta = (vars_.loc["Tiempo + sensores", "accuracy media"]
                 - vars_.loc[otro, "accuracy media"]) * 100
        print(f"  El conjunto completo supera a '{otro}' por {delta:+.1f} puntos")

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
    # Junto al modelo se guardan sus métricas, para que la aplicación pueda
    # mostrarlas sin recalcular nada ni tener números escritos a mano.
    reporte = classification_report(
        test["calidad"], pred, labels=CLASES, zero_division=0, output_dict=True
    )
    metricas = {
        "entrenado_en": datetime.now().isoformat(timespec="seconds"),
        "dataset": {
            "fuente": "Khandakar et al., Universidad de Qatar (CC BY 4.0)",
            "referencia": "Compost Maturity Prediction and Gas Emissions Monitoring",
            "muestras": int(len(df)),
            "lotes": int(df["lote"].nunique()),
            "distribucion": {k: int(v) for k, v in df["calidad"].value_counts().items()},
            "cortes_score": {"optimo": 58, "aceptable": 37},
        },
        "particion": {
            "estrategia": "GroupShuffleSplit por lote (evita fuga entre muestras del mismo lote)",
            "test_size": TEST_SIZE,
            "muestras_entrenamiento": int(len(train)),
            "muestras_prueba": int(len(test)),
            "lotes_entrenamiento": int(train["lote"].nunique()),
            "lotes_prueba": int(test["lote"].nunique()),
        },
        "hiperparametros": {
            "n_estimators": 300,
            "max_depth": 8,
            "class_weight": "balanced",
            "random_state": SEMILLA,
        },
        "desempeno": {
            "accuracy": round(float(accuracy_score(test["calidad"], pred)), 4),
            "f1_macro": round(float(f1_score(test["calidad"], pred, average="macro")), 4),
            "accuracy_validado": round(float(completo), 4),
            "particiones_validacion": N_PARTICIONES,
        },
        "matriz_confusion": {
            "clases": CLASES,
            "valores": confusion_matrix(test["calidad"], pred, labels=CLASES).tolist(),
        },
        "por_clase": {
            c: {
                "precision": round(reporte[c]["precision"], 3),
                "recall": round(reporte[c]["recall"], 3),
                "f1": round(reporte[c]["f1-score"], 3),
                "soporte": int(reporte[c]["support"]),
            }
            for c in CLASES
        },
        "importancia_variables": {
            f: round(float(i), 4) for f, i in zip(FEATURES, modelo.feature_importances_)
        },
        "comparacion_algoritmos": algos["accuracy media"].round(3).to_dict(),
        "comparacion_variables": vars_["accuracy media"].round(3).to_dict(),
    }

    MODELO_OUT.parent.mkdir(exist_ok=True)
    joblib.dump(
        {
            "modelo": modelo,
            "features": FEATURES,
            "clases": CLASES,
            "duracion_ciclo_referencia_dias": int(df.groupby("lote")["dia"].max().median()),
            "accuracy_validacion": float(completo),
            "metricas": metricas,
        },
        MODELO_OUT,
    )
    print(f"\nModelo y métricas guardados en: {MODELO_OUT}")



if __name__ == "__main__":
    main()
