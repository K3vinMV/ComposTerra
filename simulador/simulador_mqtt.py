"""Simulador de sensor de composta — versión MQTT para AWS IoT Core.

AUTENTICACIÓN
-------------
    AmazonRootCA1.pem             
    xxxx-certificate.pem.crt      
    xxxx-private.pem.key           
"""
import argparse
import json
import os
import ssl
import sys
import time
from pathlib import Path

import paho.mqtt.client as mqtt

from simulador_local import ESCENARIOS, ESCENARIO_DEFAULT, SensorComposta

IOT_ENDPOINT = os.getenv("IOT_ENDPOINT", "")
CERTS_DIR = Path(os.getenv("IOT_CERTS_DIR", "./certs"))
CLIENT_ID = os.getenv("IOT_CLIENT_ID", "composterra-sensor")
INTERVALO_DEFAULT = 5
PUERTO_MQTT = 8883  # MQTT sobre TLS


def localizar_certificados() -> tuple[Path, Path, Path]:
    """Encuentra los tres archivos por su extensión, sin depender del nombre.

    AWS les pone un prefijo aleatorio al descargarlos, así que buscarlos por
    patrón evita tener que renombrarlos a mano.
    """
    if not CERTS_DIR.is_dir():
        sys.exit(
            f"No se encontró el directorio de certificados: {CERTS_DIR}\n"
            "Descárgalos al registrar el dispositivo en IoT Core y colócalos ahí."
        )

    def buscar(patron: str, descripcion: str) -> Path:
        encontrados = sorted(CERTS_DIR.glob(patron))
        if not encontrados:
            sys.exit(f"Falta {descripcion} ({patron}) en {CERTS_DIR}")
        return encontrados[0]

    ca = buscar("*AmazonRootCA*.pem", "el certificado raíz de AWS")
    cert = buscar("*certificate.pem.crt", "el certificado del dispositivo")
    llave = buscar("*private.pem.key", "la llave privada del dispositivo")
    return ca, cert, llave


def crear_cliente() -> mqtt.Client:
    if not IOT_ENDPOINT:
        sys.exit(
            "Falta la variable IOT_ENDPOINT.\n"
            "Obtenla en IoT Core → Settings → Device data endpoint, y expórtala:\n"
            '  export IOT_ENDPOINT="xxxxx-ats.iot.us-east-1.amazonaws.com"'
        )

    ca, cert, llave = localizar_certificados()
    cliente = mqtt.Client(client_id=CLIENT_ID)
    cliente.tls_set(
        ca_certs=str(ca),
        certfile=str(cert),
        keyfile=str(llave),
        tls_version=ssl.PROTOCOL_TLSv1_2,
    )

    def al_conectar(client, userdata, flags, rc):
        if rc == 0:
            print(f"Conectado a {IOT_ENDPOINT}")
        else:
            print(f"Fallo de conexión (código {rc})")

    def al_desconectar(client, userdata, rc):
        if rc != 0:
            print("Conexión perdida, reintentando...")

    cliente.on_connect = al_conectar
    cliente.on_disconnect = al_desconectar
    return cliente


def main():
    parser = argparse.ArgumentParser(description="Simulador de sensor por MQTT")
    parser.add_argument("--lote", type=int, required=True, help="ID del lote")
    parser.add_argument("--escenario", choices=ESCENARIOS, default=ESCENARIO_DEFAULT)
    parser.add_argument("--intervalo", type=float, default=INTERVALO_DEFAULT)
    args = parser.parse_args()

    topico = f"composterra/sensores/{args.lote}"
    cliente = crear_cliente()

    print(f"Conectando a {IOT_ENDPOINT} ...")
    cliente.connect(IOT_ENDPOINT, PUERTO_MQTT, keepalive=60)
    # loop_start mantiene la conexión viva en segundo plano y reconecta solo
    # si se cae, sin que el bucle principal tenga que ocuparse.
    cliente.loop_start()

    sensor = SensorComposta(args.escenario)
    print(f"Publicando en {topico} | escenario '{args.escenario}' | cada {args.intervalo}s")
    print("Ctrl+C para detener.\n")

    try:
        while True:
            lectura = sensor.leer()
            mensaje = {"id_lote": args.lote, **lectura}
            resultado = cliente.publish(topico, json.dumps(mensaje), qos=1)
            estado = "OK" if resultado.rc == mqtt.MQTT_ERR_SUCCESS else f"ERROR {resultado.rc}"
            print(
                f"T={lectura['temperatura']:6.2f}°C  "
                f"H={lectura['humedad']:6.2f}%  "
                f"pH={lectura['ph']:5.2f}  → {estado}"
            )
            time.sleep(args.intervalo)
    except KeyboardInterrupt:
        print("\nDeteniendo...")
    finally:
        cliente.loop_stop()
        cliente.disconnect()


if __name__ == "__main__":
    main()
