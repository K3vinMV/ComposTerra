"""Simulador de sensor de composta — versión local (HTTP).

Envía lecturas de temperatura, humedad y pH cada 5 s a la API REST.
Los valores derivan gradualmente (random walk) para verse realistas
en la gráfica del dashboard.

Uso:
    python simulador_local.py --lote 1
    python simulador_local.py --lote 2 --escenario seco
    python simulador_local.py --lote 1 --intervalo 2

Escenarios:
    optimo   → valores dentro de rango (default)
    seco     → humedad baja (dispara alerta)
    frio     → temperatura baja (dispara alerta)
    acido    → pH bajo (dispara alerta)

Migración a AWS: la función `enviar_lectura` se reemplaza por
`client.publish(...)` de paho-mqtt hacia AWS IoT Core. La generación
de datos (`SensorComposta`) no cambia.
"""
import argparse
import random
import time

import requests

API_URL = "http://localhost:8000"
EMAIL = "admin@composta.com"
PASSWORD = "admin123"
INTERVALO_DEFAULT = 5  # segundos

# (valor inicial, mínimo, máximo, deriva máxima por lectura)
ESCENARIOS = {
    "optimo": {"temp": (55.0, 45.0, 65.0, 0.8), "hum": (50.0, 40.0, 60.0, 1.0), "ph": (7.0, 6.0, 8.0, 0.08)},
    "seco":   {"temp": (58.0, 48.0, 68.0, 0.8), "hum": (32.0, 25.0, 39.0, 1.0), "ph": (7.0, 6.2, 7.8, 0.08)},
    "frio":   {"temp": (35.0, 28.0, 44.0, 0.8), "hum": (50.0, 42.0, 58.0, 1.0), "ph": (6.8, 6.0, 7.6, 0.08)},
    "acido":  {"temp": (52.0, 46.0, 62.0, 0.8), "hum": (48.0, 41.0, 57.0, 1.0), "ph": (5.2, 4.5, 5.9, 0.08)},
}


class SensorComposta:
    """Genera lecturas con deriva gradual dentro de los límites del escenario."""

    def __init__(self, escenario: str):
        cfg = ESCENARIOS[escenario]
        self.temp, self.temp_min, self.temp_max, self.temp_paso = cfg["temp"]
        self.hum, self.hum_min, self.hum_max, self.hum_paso = cfg["hum"]
        self.ph, self.ph_min, self.ph_max, self.ph_paso = cfg["ph"]

    @staticmethod
    def _derivar(valor, vmin, vmax, paso):
        valor += random.uniform(-paso, paso)
        return max(vmin, min(vmax, valor))

    def leer(self) -> dict:
        self.temp = self._derivar(self.temp, self.temp_min, self.temp_max, self.temp_paso)
        self.hum = self._derivar(self.hum, self.hum_min, self.hum_max, self.hum_paso)
        self.ph = self._derivar(self.ph, self.ph_min, self.ph_max, self.ph_paso)
        return {
            "temperatura": round(self.temp, 2),
            "humedad": round(self.hum, 2),
            "ph": round(self.ph, 2),
        }


def obtener_token() -> str:
    r = requests.post(
        f"{API_URL}/auth/login",
        json={"email": EMAIL, "password": PASSWORD},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def enviar_lectura(token: str, id_lote: int, lectura: dict) -> requests.Response:
    """Versión local: HTTP POST. En AWS se reemplaza por publish MQTT."""
    return requests.post(
        f"{API_URL}/registros",
        json={"id_lote": id_lote, **lectura},
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )


def main():
    parser = argparse.ArgumentParser(description="Simulador de sensor de composta")
    parser.add_argument("--lote", type=int, required=True, help="ID del lote")
    parser.add_argument("--escenario", choices=ESCENARIOS, default="optimo")
    parser.add_argument("--intervalo", type=float, default=INTERVALO_DEFAULT)
    args = parser.parse_args()

    print(f"Autenticando en {API_URL} ...")
    token = obtener_token()
    sensor = SensorComposta(args.escenario)
    print(f"Enviando lecturas → lote {args.lote} | escenario '{args.escenario}' | cada {args.intervalo}s")
    print("Ctrl+C para detener.\n")

    while True:
        lectura = sensor.leer()
        try:
            r = enviar_lectura(token, args.lote, lectura)
            if r.status_code == 401:  # token expirado → re-login
                token = obtener_token()
                r = enviar_lectura(token, args.lote, lectura)
            estado = "OK" if r.status_code == 201 else f"ERROR {r.status_code}: {r.text}"
            print(f"T={lectura['temperatura']:6.2f}°C  H={lectura['humedad']:6.2f}%  pH={lectura['ph']:5.2f}  → {estado}")
        except requests.ConnectionError:
            print("API no disponible, reintentando...")
        time.sleep(args.intervalo)


if __name__ == "__main__":
    main()
