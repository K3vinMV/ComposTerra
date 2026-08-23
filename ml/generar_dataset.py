"""Genera el dataset simulado para entrenar el modelo de calidad de composta.

Cada fila representa los promedios de un lote: temperatura, humedad, pH
y su etiqueta de calidad (Alta / Media / Baja).

Criterio de etiquetado (rangos óptimos: temp 45-65°C, hum 40-60%, pH 6-8):
    Alta  → los 3 parámetros dentro del rango óptimo
    Media → desviaciones leves (1-2 parámetros ligeramente fuera)
    Baja  → desviaciones fuertes

Uso:
    python generar_dataset.py                # 200 filas → dataset_composta.csv
    python generar_dataset.py --n 35         # mínimo académico
"""
import argparse
import csv
import random
from pathlib import Path

RANGOS = {"temperatura": (45.0, 65.0), "humedad": (40.0, 60.0), "ph": (6.0, 8.0)}


def _dentro(valor: float, rango: tuple[float, float]) -> float:
    """Valor aleatorio dentro del rango óptimo."""
    return random.uniform(*rango)


def _desviado(rango: tuple[float, float], leve: bool) -> float:
    """Valor fuera del rango óptimo, por arriba o por abajo."""
    vmin, vmax = rango
    amplitud = vmax - vmin
    # leve: hasta 15% fuera del rango | fuerte: 20-60% fuera
    d = random.uniform(0.02, 0.15) if leve else random.uniform(0.20, 0.60)
    desviacion = amplitud * d
    return vmax + desviacion if random.random() < 0.5 else vmin - desviacion


def generar_fila() -> dict:
    clase = random.choices(["Alta", "Media", "Baja"], weights=[0.4, 0.3, 0.3])[0]
    params = ["temperatura", "humedad", "ph"]
    fila = {p: _dentro(0, RANGOS[p]) for p in params}

    if clase == "Media":
        # 1 o 2 parámetros ligeramente fuera
        for p in random.sample(params, k=random.choice([1, 2])):
            fila[p] = _desviado(RANGOS[p], leve=True)
    elif clase == "Baja":
        # 1 a 3 parámetros fuertemente fuera
        for p in random.sample(params, k=random.choice([1, 2, 3])):
            fila[p] = _desviado(RANGOS[p], leve=False)

    # límites físicos
    fila["temperatura"] = max(10.0, min(80.0, fila["temperatura"]))
    fila["humedad"] = max(5.0, min(95.0, fila["humedad"]))
    fila["ph"] = max(3.0, min(11.0, fila["ph"]))

    return {
        "temperatura": round(fila["temperatura"], 2),
        "humedad": round(fila["humedad"], 2),
        "ph": round(fila["ph"], 2),
        "calidad": clase,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=200, help="número de filas (mínimo 35)")
    parser.add_argument("--out", default="dataset_composta.csv")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    if args.n < 35:
        parser.error("el dataset debe tener mínimo 35 registros")

    random.seed(args.seed)
    filas = [generar_fila() for _ in range(args.n)]

    ruta = Path(__file__).parent / args.out
    with open(ruta, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["temperatura", "humedad", "ph", "calidad"])
        writer.writeheader()
        writer.writerows(filas)

    conteo = {c: sum(1 for x in filas if x["calidad"] == c) for c in ["Alta", "Media", "Baja"]}
    print(f"Dataset generado: {ruta} ({args.n} filas)")
    print(f"Distribución: {conteo}")


if __name__ == "__main__":
    main()
