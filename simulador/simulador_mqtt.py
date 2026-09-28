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
    parser = argparse.ArgumentParser(
        description="Simulador de sensores por MQTT",
        epilog=(
            "Ejemplos:\n"
            "  Un lote:          --sensor 3:maduro\n"
            "  Varios a la vez:  --sensor 1:termofilico --sensor 2:seco --sensor 3:maduro\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--sensor",
        action="append",
        metavar="LOTE:ESCENARIO",
        help="lote y escenario a simular; repetible para instrumentar varios lotes",
    )
    parser.add_argument("--lote", type=int, help="atajo para un solo lote")
    parser.add_argument("--escenario", choices=ESCENARIOS, default=ESCENARIO_DEFAULT)
    parser.add_argument("--intervalo", type=float, default=INTERVALO_DEFAULT)
    args = parser.parse_args()

    # Cada entrada de --sensor produce una instancia independiente de
    # SensorComposta: los lotes evolucionan por separado, igual que lo harían
    # pilas distintas con su propio sensor.
    sensores = {}
    if args.sensor:
        for entrada in args.sensor:
            if ":" in entrada:
                lote_txt, escenario = entrada.split(":", 1)
            else:
                lote_txt, escenario = entrada, ESCENARIO_DEFAULT
            escenario = escenario.strip()
            if escenario not in ESCENARIOS:
                sys.exit(
                    f"Escenario desconocido: '{escenario}'. "
                    f"Opciones: {', '.join(ESCENARIOS)}"
                )
            sensores[int(lote_txt)] = (escenario, SensorComposta(escenario))
    elif args.lote is not None:
        sensores[args.lote] = (args.escenario, SensorComposta(args.escenario))
    else:
        sys.exit("Indica al menos un sensor con --sensor LOTE:ESCENARIO (o --lote N)")

    cliente = crear_cliente()
    print(f"Conectando a {IOT_ENDPOINT} ...")
    cliente.connect(IOT_ENDPOINT, PUERTO_MQTT, keepalive=60)
    # loop_start mantiene la conexión viva en segundo plano y reconecta solo
    # si se cae, sin que el bucle principal tenga que ocuparse.
    cliente.loop_start()

    print(f"\nSensores activos (publicando cada {args.intervalo}s):")
    for lote, (escenario, _) in sorted(sensores.items()):
        print(f"  lote {lote}  →  composterra/sensores/{lote}  [{escenario}]")
    print("\nCtrl+C para detener.\n")

    try:
        while True:
            for lote, (_, sensor) in sorted(sensores.items()):
                lectura = sensor.leer()
                mensaje = {"id_lote": lote, **lectura}
                resultado = cliente.publish(
                    f"composterra/sensores/{lote}", json.dumps(mensaje), qos=1
                )
                estado = (
                    "OK" if resultado.rc == mqtt.MQTT_ERR_SUCCESS else f"ERROR {resultado.rc}"
                )
                print(
                    f"lote {lote}  "
                    f"T={lectura['temperatura']:6.2f}°C  "
                    f"H={lectura['humedad']:6.2f}%  "
                    f"pH={lectura['ph']:5.2f}  → {estado}"
                )
            print()
            time.sleep(args.intervalo)
    except KeyboardInterrupt:
        print("\nDeteniendo...")
    finally:
        cliente.loop_stop()
        cliente.disconnect()


if __name__ == "__main__":
    main()
