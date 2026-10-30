"""Simulador del sensor, versión local por HTTP"""
import argparse
import os
import random
import time

import requests

API_URL = os.getenv("COMPOSTERRA_API", "http://localhost:8000")
EMAIL = os.getenv("COMPOSTERRA_EMAIL", "admin@composterra.mx")
PASSWORD = os.getenv("COMPOSTERRA_PASSWORD")
INTERVALO_DEFAULT = 5  # segundos

ESCENARIOS = {
    # Fase activa: la pila está trabajando. Dentro de los rangos óptimos.
    "termofilico": {"temp": (55.0, 45.0, 65.0, 0.8), "hum": (50.0, 40.0, 60.0, 1.0), "ph": (7.0, 6.0, 8.0, 0.08)},
    # Fase final: actividad microbiana cesada, composta lista. Frío y seco.
    "maduro":      {"temp": (25.0, 20.0, 30.0, 0.6), "hum": (25.0, 20.0, 32.0, 0.8), "ph": (7.4, 7.0, 7.8, 0.06)},
    # Fallas del proceso
    "seco":        {"temp": (58.0, 48.0, 68.0, 0.8), "hum": (32.0, 25.0, 39.0, 1.0), "ph": (7.0, 6.2, 7.8, 0.08)},
    "frio":        {"temp": (35.0, 28.0, 44.0, 0.8), "hum": (50.0, 42.0, 58.0, 1.0), "ph": (6.8, 6.0, 7.6, 0.08)},
    "acido":       {"temp": (52.0, 46.0, 62.0, 0.8), "hum": (48.0, 41.0, 57.0, 1.0), "ph": (5.2, 4.5, 5.9, 0.08)},
}
ESCENARIO_DEFAULT = "termofilico"


RUIDO = {"temp": 0.5, "hum": 2.0, "ph": 0.1}


class SensorComposta:

    def __init__(self, escenario: str):
        cfg = ESCENARIOS[escenario]
        self.temp, self.temp_min, self.temp_max, self.temp_paso = cfg["temp"]
        self.hum, self.hum_min, self.hum_max, self.hum_paso = cfg["hum"]
        self.ph, self.ph_min, self.ph_max, self.ph_paso = cfg["ph"]

    @staticmethod
    def _derivar(valor, vmin, vmax, paso):
        """El valor real cambia poco a poco (random walk)"""
        valor += random.uniform(-paso, paso)
        return max(vmin, min(vmax, valor))

    @staticmethod
    def _medir(valor_real, sigma, limite_min, limite_max):
        """Le suma el error del sensor"""
        return max(limite_min, min(limite_max, random.gauss(valor_real, sigma)))

    def leer(self) -> dict:
        # valor real del proceso
        self.temp = self._derivar(self.temp, self.temp_min, self.temp_max, self.temp_paso)
        self.hum = self._derivar(self.hum, self.hum_min, self.hum_max, self.hum_paso)
        self.ph = self._derivar(self.ph, self.ph_min, self.ph_max, self.ph_paso)

        # lo que mide el sensor
        return {
            "temperatura": round(self._medir(self.temp, RUIDO["temp"], -10, 100), 2),
            "humedad": round(self._medir(self.hum, RUIDO["hum"], 0, 100), 2),
            "ph": round(self._medir(self.ph, RUIDO["ph"], 0, 14), 2),
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
    """Manda la lectura por HTTP"""
    return requests.post(
        f"{API_URL}/registros",
        json={"id_lote": id_lote, **lectura},
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )


def main():
    parser = argparse.ArgumentParser(description="Simulador de sensor de composta")
    parser.add_argument("--lote", type=int, required=True, help="ID del lote")
    parser.add_argument("--escenario", choices=ESCENARIOS, default=ESCENARIO_DEFAULT)
    parser.add_argument("--intervalo", type=float, default=INTERVALO_DEFAULT)
    args = parser.parse_args()

    global PASSWORD
    if not PASSWORD:
        import getpass
        PASSWORD = getpass.getpass(f"Contraseña de {EMAIL}: ")

    print(f"Autenticando en {API_URL} ...")
    token = obtener_token()
    sensor = SensorComposta(args.escenario)
    print(f"Enviando lecturas → lote {args.lote} | escenario '{args.escenario}' | cada {args.intervalo}s")
    print("Ctrl+C para detener.\n")

    while True:
        lectura = sensor.leer()
        try:
            r = enviar_lectura(token, args.lote, lectura)
            if r.status_code == 401:  # token expirado
                token = obtener_token()
                r = enviar_lectura(token, args.lote, lectura)
            estado = "OK" if r.status_code == 201 else f"ERROR {r.status_code}: {r.text}"
            print(f"T={lectura['temperatura']:6.2f}°C  H={lectura['humedad']:6.2f}%  pH={lectura['ph']:5.2f}  → {estado}")
        except requests.ConnectionError:
            print("API no disponible, reintentando...")
        time.sleep(args.intervalo)


if __name__ == "__main__":
    main()
