"""Prepara el dataset de entrenamiento a partir de datos experimentales reales.

FUENTE
------
Khandakar et al., "Compost Maturity Prediction and Gas Emissions Monitoring:
A Sensor-Based and Interpretable Machine Learning Approach".
Universidad de Qatar. Licencia CC BY 4.0.
https://github.com/hafsa-kibria/Compost-Dataset  (452 muestras, 14 variables)

QUÉ HACE ESTE SCRIPT
--------------------
1. Carga el CSV crudo.
2. Detecta los lotes (cada reinicio de `Day` marca un lote nuevo).
3. Normaliza el tiempo como `progreso` = día / duración del ciclo (0 a 1).
4. Etiqueta cada muestra en tres clases a partir del `Score` de madurez.
5. Guarda `dataset_composta.csv` con solo las columnas que el sistema puede medir.

POR QUÉ SOLO 4 VARIABLES
------------------------
El dataset original trae 14 variables, pero 10 de ellas (relación C/N, amoniaco,
nitratos, carbono orgánico, conductividad, índice de germinación...) requieren
análisis de laboratorio. El sistema solo dispone de tres sensores más la fecha
de inicio del lote, así que el modelo se entrena únicamente con lo que podrá
observar en producción:

    progreso · temperatura · humedad · pH

El aporte del proyecto es precisamente ese: inferir con cuatro variables baratas
de campo un indicador de madurez que normalmente exige laboratorio.

POR QUÉ SE NORMALIZA EL TIEMPO
------------------------------
Los ciclos del dataset duran 27 días de mediana; los de una planta industrial
pueden durar ~120. El día 15 no significa lo mismo en ambos contextos. Expresar
el tiempo como fracción del ciclo hace comparable la fase del proceso entre
escalas distintas.

CRITERIO DE ETIQUETADO
----------------------
Los cortes NO son arbitrarios: se anclan al índice de germinación (GI), que es
el indicador estándar de madurez en la literatura (Zucconi et al.). En este
dataset el Score correlaciona 0.92 con el GI, y los umbrales clásicos de GI
corresponden a estos valores de Score:

    GI ≥ 80 % (composta madura)        → Score ≈ 58  → optimo
    GI 50–80 % (madurez parcial)       → Score ≈ 37  → aceptable
    GI < 50 % (inmadura, fitotóxica)   → Score < 37  → deficiente

Uso:
    python preparar_dataset.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).parent
ENTRADA = BASE / "data" / "compost_khandakar.csv"
SALIDA = BASE / "dataset_composta.csv"

# Cortes de Score anclados a los umbrales de índice de germinación
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

    # --- Lotes: cada vez que Day deja de crecer, empieza una serie nueva ---
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

    # --- Dataset final: solo lo que el sistema puede observar ---
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
