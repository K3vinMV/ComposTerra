"""Simulador de sensor de composta — versión local (HTTP).

Envía lecturas de temperatura, humedad y pH cada 5 s a la API REST.
Los valores derivan gradualmente (random walk) para verse realistas
en la gráfica del dashboard.

Uso:
    python simulador_local.py --lote 1
    python simulador_local.py --lote 2 --escenario maduro
    python simulador_local.py --lote 3 --escenario seco
    python simulador_local.py --lote 1 --intervalo 2

Escenarios:
    termofilico → fase activa: caliente y húmedo, dentro de rango (default)
    maduro      → fase final: frío y seco, composta lista
    seco        → humedad por debajo del rango (dispara alerta)
    frio        → temperatura por debajo del rango (dispara alerta)
    acido       → pH por debajo del rango (dispara alerta)

Nota sobre las fases: los rangos considerados óptimos (45-65 °C, 40-60 % de
humedad) describen la fase termofílica, cuando la actividad microbiana está en
su punto máximo. Una composta MADURA es lo contrario: fría y seca, porque la
actividad ya cesó. Por eso `maduro` sale del rango "óptimo" a propósito — y el
modelo lo clasifica correctamente cuando el lote está avanzado en su ciclo.

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


# Ruido de medición: desviación estándar del error de cada sensor.
# Valores tomados de las hojas de datos de sensores comerciales de bajo costo,
# que es el hardware al que apunta el proyecto:
#   DS18B20 (temperatura de sonda)  ±0.5 °C
#   Sensor capacitivo de humedad    ±2 %
#   Sonda de pH analógica           ±0.1
RUIDO = {"temp": 0.5, "hum": 2.0, "ph": 0.1}


class SensorComposta:
    """Genera lecturas realistas combinando dos fuentes de variación.

    1. Deriva (random walk): el valor real del proceso cambia poco a poco.
       Modela que la composta se calienta o se seca de forma gradual.
    2. Ruido de medición: error instantáneo del sensor alrededor del valor
       real, con distribución normal. Modela la precisión limitada del
       hardware.

    La distinción importa: la deriva se acumula (el estado del proceso
    persiste), el ruido no (cada medición yerra de forma independiente).
    Por eso el estado interno guarda el valor sin ruido y este se agrega
    solo al momento de reportar la lectura.
    """

    def __init__(self, escenario: str):
        cfg = ESCENARIOS[escenario]
        self.temp, self.temp_min, self.temp_max, self.temp_paso = cfg["temp"]
        self.hum, self.hum_min, self.hum_max, self.hum_paso = cfg["hum"]
        self.ph, self.ph_min, self.ph_max, self.ph_paso = cfg["ph"]

    @staticmethod
    def _derivar(valor, vmin, vmax, paso):
        """Random walk acotado: el valor real del proceso evoluciona."""
        valor += random.uniform(-paso, paso)
        return max(vmin, min(vmax, valor))

    @staticmethod
    def _medir(valor_real, sigma, limite_min, limite_max):
        """Agrega error de medición gaussiano y acota a límites físicos."""
        return max(limite_min, min(limite_max, random.gauss(valor_real, sigma)))

    def leer(self) -> dict:
        # El proceso evoluciona (estado interno, sin ruido)
        self.temp = self._derivar(self.temp, self.temp_min, self.temp_max, self.temp_paso)
        self.hum = self._derivar(self.hum, self.hum_min, self.hum_max, self.hum_paso)
        self.ph = self._derivar(self.ph, self.ph_min, self.ph_max, self.ph_paso)

        # El sensor lo mide con su error propio
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
    parser.add_argument("--escenario", choices=ESCENARIOS, default=ESCENARIO_DEFAULT)
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
