"""Prepara el dataset"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).parent
ENTRADA = BASE / "data" / "compost_khandakar.csv"
SALIDA = BASE / "dataset_composta.csv"

CORTE_OPTIMO = 58.0      # GI ≈ 80 %
CORTE_ACEPTABLE = 37.0   # GI ≈ 50 %

COLUMNAS_SENSOR = {"Temperature": "temperatura", "MC(%)": "humedad", "pH": "ph"}


def etiquetar(score: float) -> str:
    if score >= CORTE_OPTIMO:
        return "optimo"
    if score >= CORTE_ACEPTABLE:
        return "aceptable"
    return "deficiente"


def main():
    if not ENTRADA.exists():
        sys.exit(
            f"No se encontró {ENTRADA}\n"
            "Descarga el dataset con:\n"
            "  mkdir -p ml/data && cd ml/data\n"
            '  curl -L -o compost_khandakar.csv \\\n'
            '    "https://raw.githubusercontent.com/hafsa-kibria/Compost-Dataset/main/Compost%20Data.csv"'
        )

    df = pd.read_csv(ENTRADA)
    print(f"Dataset original: {len(df)} muestras, {len(df.columns)} variables")

    # --- Lotes ---
    df["lote"] = (df["Day"].diff() <= 0).cumsum()
    duraciones = df.groupby("lote")["Day"].max()
    print(f"Lotes detectados: {df['lote'].nunique()}")
    print(
        f"Duración de ciclo: mediana {duraciones.median():.0f} días "
        f"(min {duraciones.min():.0f}, max {duraciones.max():.0f})"
    )

    # --- Tiempo normalizado (0 = inicio del ciclo, 1 = fin) ---
    dur_por_fila = df.groupby("lote")["Day"].transform("max").replace(0, np.nan)
    df["progreso"] = (df["Day"] / dur_por_fila).fillna(0).clip(0, 1)

    # --- Etiqueta ---
    df["calidad"] = df["Score"].apply(etiquetar)

    # --- Dataset final ---
    salida = df.rename(columns=COLUMNAS_SENSOR)[
        ["lote", "dia", "progreso", "temperatura", "humedad", "ph", "calidad"]
        if "dia" in df.columns
        else ["lote", "Day", "progreso", "temperatura", "humedad", "ph", "calidad"]
    ].rename(columns={"Day": "dia"})

    salida.to_csv(SALIDA, index=False)

    print(f"\nDistribución de clases:\n{salida['calidad'].value_counts().to_string()}")
    print(f"\nDataset preparado: {SALIDA} ({len(salida)} filas)")
    print("Variables de entrenamiento: progreso, temperatura, humedad, ph")


if __name__ == "__main__":
    main()
