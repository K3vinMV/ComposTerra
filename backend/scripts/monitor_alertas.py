"""Proceso que revisa los lotes y avisa por Telegram"""
import argparse
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings  # noqa: E402
from app.core.alertas import _enviar_telegram, notificar_pendientes, revisar_lotes  # noqa: E402
from app.database import SessionLocal  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("monitor")


def ciclo() -> None:
    db = SessionLocal()
    try:
        revisar_lotes(db)
        enviados = notificar_pendientes(db)
        if enviados:
            log.info("Mensajes enviados: %d", enviados)
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--una-vez", action="store_true", help="un solo ciclo y salir")
    parser.add_argument("--prueba", action="store_true", help="enviar un mensaje de prueba")
    args = parser.parse_args()

    if not (settings.telegram_bot_token and settings.telegram_chat_id):
        log.warning("TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID vacíos: las alertas se "
                    "registran pero no se envían.")

    if args.prueba:
        ok = _enviar_telegram("🌱 ComposTerra: mensaje de prueba de alertas")
        sys.exit(0 if ok else 1)

    if args.una_vez:
        ciclo()
        return

    log.info("Monitor de alertas iniciado (cada %d s)", settings.alertas_intervalo_s)
    while True:
        try:
            ciclo()
        except Exception:
            log.exception("Error en el ciclo de alertas; se reintenta en el siguiente")
        time.sleep(settings.alertas_intervalo_s)


if __name__ == "__main__":
    main()
