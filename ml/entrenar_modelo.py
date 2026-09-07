"""Entrena el clasificador Random Forest de calidad de composta.

- Entrada:  dataset_composta.csv (generado por generar_dataset.py)
- Salida:   modelos/modelo_composta.joblib
- Evaluación (Módulo 4): matriz de confusión, precisión, recall, F1-score

Uso:
    python entrenar_modelo.py
"""
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

BASE = Path(__file__).parent
DATASET = BASE / "dataset_composta.csv"
MODELO_OUT = BASE / "modelos" / "modelo_composta.joblib"

FEATURES = ["temperatura", "humedad", "ph"]
CLASES = ["optimo", "aceptable", "deficiente"]


def main():
    df = pd.read_csv(DATASET)
    print(f"Dataset: {len(df)} filas\n{df['calidad'].value_counts()}\n")

    X, y = df[FEATURES], df["calidad"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    modelo = RandomForestClassifier(
        n_estimators=100,      # 100 árboles
        max_depth=6,           # limita profundidad → evita sobreajuste en dataset chico
        random_state=42,
        class_weight="balanced",
    )
    modelo.fit(X_train, y_train)

    # ----------------------- Evaluación -----------------------
    y_pred = modelo.predict(X_test)
    print("Matriz de confusión (filas=real, columnas=predicho):")
    print(pd.DataFrame(
        confusion_matrix(y_test, y_pred, labels=CLASES),
        index=CLASES, columns=CLASES,
    ))
    print("\nReporte de clasificación:")
    print(classification_report(y_test, y_pred, labels=CLASES))

    print("Importancia de variables:")
    for f, imp in zip(FEATURES, modelo.feature_importances_):
        print(f"  {f}: {imp:.3f}")

    # ----------------------- Exportar -----------------------
    MODELO_OUT.parent.mkdir(exist_ok=True)
    joblib.dump(modelo, MODELO_OUT)
    print(f"\nModelo guardado en: {MODELO_OUT}")


if __name__ == "__main__":
    main()
