"""Procesador de telemetría IoT — AWS Lambda.

VARIABLES DE ENTORNO
--------------------
    DB_HOST      endpoint de la instancia RDS
    DB_USER      usuario de la base de datos
    DB_PASSWORD  contraseña
    DB_NAME      (composta_db)
"""
import json
import logging
import os

import pymysql

log = logging.getLogger()
log.setLevel(logging.INFO)

# Rangos físicos admisibles. 
LIMITES = {
    "temperatura": (-10.0, 100.0),
    "humedad": (0.0, 100.0),
    "ph": (0.0, 14.0),
}

_conexion = None


def _conectar():
    global _conexion
    if _conexion is not None:
        try:
            _conexion.ping(reconnect=True)
            return _conexion
        except Exception:
            _conexion = None

    _conexion = pymysql.connect(
        host=os.environ["DB_HOST"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        connect_timeout=5,
        autocommit=False,
        cursorclass=pymysql.cursors.DictCursor,
    )
    return _conexion


def _validar(mensaje: dict) -> tuple[int, float, float, float]:
    """Comprueba el mensaje y devuelve sus valores ya convertidos."""
    faltantes = [c for c in ("id_lote", "temperatura", "humedad", "ph") if c not in mensaje]
    if faltantes:
        raise ValueError(f"faltan campos en el mensaje: {', '.join(faltantes)}")

    id_lote = int(mensaje["id_lote"])
    valores = {}
    for campo, (minimo, maximo) in LIMITES.items():
        valor = float(mensaje[campo])
        if not minimo <= valor <= maximo:
            raise ValueError(
                f"{campo} fuera de rango físico: {valor} (admitido {minimo} a {maximo})"
            )
        valores[campo] = valor

    return id_lote, valores["temperatura"], valores["humedad"], valores["ph"]


def lambda_handler(event, context):
    """Punto de entrada. `event` es el JSON publicado por el sensor."""
    log.info("Mensaje recibido: %s", json.dumps(event))

    try:
        id_lote, temperatura, humedad, ph = _validar(event)
    except (ValueError, TypeError, KeyError) as e:
        # Mensaje mal formado: se descarta. Volver a intentarlo no lo arreglaría.
        log.error("Mensaje inválido, se descarta: %s", e)
        return {"guardado": False, "motivo": str(e)}

    conexion = _conectar()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT estado FROM lotes WHERE id = %s", (id_lote,))
            lote = cursor.fetchone()

            if lote is None:
                log.warning("El lote %s no existe; se descarta la lectura", id_lote)
                return {"guardado": False, "motivo": "lote inexistente"}

            if lote["estado"] != "activo":
                log.warning("El lote %s está finalizado; se descarta la lectura", id_lote)
                return {"guardado": False, "motivo": "lote finalizado"}

            cursor.execute(
                "INSERT INTO registros_sensor (id_lote, temperatura, humedad, ph) "
                "VALUES (%s, %s, %s, %s)",
                (id_lote, temperatura, humedad, ph),
            )
        conexion.commit()
    except Exception:
        conexion.rollback()
        log.exception("Error al guardar la lectura del lote %s", id_lote)
        raise

    log.info(
        "Lectura guardada · lote %s · %.2f °C · %.2f %% · pH %.2f",
        id_lote, temperatura, humedad, ph,
    )
    return {"guardado": True, "id_lote": id_lote}
