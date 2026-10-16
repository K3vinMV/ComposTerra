import json
import logging
import urllib.request
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Alerta, Lote, RegistroSensor

log = logging.getLogger("alertas")

# Mantener sincronizado con RANGOS en frontend/src/api/composta.js
RANGOS = {
    "temperatura": (45.0, 65.0, "°C", "Temperatura"),
    "humedad": (40.0, 60.0, "%", "Humedad"),
    "ph": (6.0, 8.0, "", "pH"),
}
UMBRAL_MADURACION = 0.7
LECTURAS_PROMEDIO = 3          # promedia estas lecturas para decidir si alertar
VENTANA_RECIENTE_MIN = 30      # solo se evalúan lecturas de los últimos 30 min
LIMITE_SIN_DATOS_H = 24        # lotes callados por más de un día se ignoran


def _progreso(lote: Lote, hoy: date) -> float:
    dias = (hoy - lote.fecha_inicio).days
    return min(max(dias / (lote.duracion_estimada_dias or 120), 0.0), 1.0)


def _evaluar(param: str, valor: float, progreso: float) -> str | None:
    """Devuelve 'bajo', 'alto' o None si el valor no amerita alerta."""
    minimo, maximo, *_ = RANGOS[param]
    if valor < minimo:
        if progreso >= UMBRAL_MADURACION and param != "ph":
            return None  # enfriarse y secarse al final del ciclo es normal
        return "bajo"
    if valor > maximo:
        return "alto"
    return None


def _abierta(db: Session, id_lote: int, tipo: str) -> Alerta | None:
    return db.scalars(
        select(Alerta).where(
            Alerta.id_lote == id_lote, Alerta.tipo == tipo, Alerta.cerrada_en.is_(None)
        )
    ).first()


def revisar_lotes(db: Session) -> None:
    """Abre y cierra alertas según las lecturas actuales. No envía nada."""
    ahora = db.scalar(select(func.now()))   # hora de la base (UTC)
    hoy = ahora.date()
    lotes = db.scalars(select(Lote).where(Lote.estado == "activo")).all()

    for lote in lotes:
        # ---- sensor sin reportar
        ultima = db.scalar(
            select(func.max(RegistroSensor.timestamp)).where(RegistroSensor.id_lote == lote.id)
        )
        callado = ultima is not None and (
            timedelta(minutes=settings.alertas_sin_datos_min)
            < ahora - ultima
            < timedelta(hours=LIMITE_SIN_DATOS_H)
        )
        alerta = _abierta(db, lote.id, "sin_datos")
        if callado and alerta is None:
            db.add(Alerta(id_lote=lote.id, tipo="sin_datos", abierta_en=ahora))
        elif not callado and alerta is not None and ultima is not None \
                and ahora - ultima <= timedelta(minutes=settings.alertas_sin_datos_min):
            alerta.cerrada_en = ahora

        # ---- variables fuera de rango
        recientes = db.scalars(
            select(RegistroSensor)
            .where(
                RegistroSensor.id_lote == lote.id,
                RegistroSensor.timestamp >= ahora - timedelta(minutes=VENTANA_RECIENTE_MIN),
            )
            .order_by(RegistroSensor.timestamp.desc())
            .limit(LECTURAS_PROMEDIO)
        ).all()
        if not recientes:
            continue  # sin datos frescos no se decide nada sobre las variables

        progreso = _progreso(lote, hoy)
        for param in RANGOS:
            valores = [float(getattr(r, param)) for r in recientes if getattr(r, param) is not None]
            if not valores:
                continue
            promedio = sum(valores) / len(valores)
            direccion = _evaluar(param, promedio, progreso)
            alerta = _abierta(db, lote.id, param)

            if direccion and alerta is None:
                db.add(Alerta(
                    id_lote=lote.id, tipo=param, direccion=direccion,
                    valor=Decimal(f"{promedio:.2f}"), abierta_en=ahora,
                ))
            elif direccion and alerta is not None:
                alerta.valor = Decimal(f"{promedio:.2f}")   # sigue abierta; se actualiza
            elif not direccion and alerta is not None:
                alerta.valor = Decimal(f"{promedio:.2f}")
                alerta.cerrada_en = ahora

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


# ------------------------------------------------------------------ Telegram
def _texto(alerta: Alerta, cierre: bool) -> str:
    lote = f"<b>Lote {alerta.id_lote}</b>"
    if alerta.tipo == "sin_datos":
        return (f"✅ {lote} · el sensor volvió a reportar" if cierre else
                f"📡 {lote} · el sensor no ha reportado en más de "
                f"{settings.alertas_sin_datos_min} min")
    minimo, maximo, unidad, nombre = RANGOS[alerta.tipo]
    valor = f"{alerta.valor:.2f}{(' ' + unidad) if unidad else ''}" if alerta.valor is not None else "—"
    rango = f"{minimo:g} a {maximo:g}{(' ' + unidad) if unidad else ''}"
    if cierre:
        return f"✅ {lote} · {nombre} de nuevo en rango ({valor})"
    estado = "baja" if alerta.direccion == "bajo" else "alta"
    if alerta.tipo == "ph":
        estado = "ácido" if alerta.direccion == "bajo" else "alcalino"
    return f"⚠️ {lote} · {nombre} {estado}\nValor: {valor} (rango {rango})"


def _enviar_telegram(texto: str) -> bool:
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    cuerpo = json.dumps(
        {"chat_id": settings.telegram_chat_id, "text": texto, "parse_mode": "HTML"}
    ).encode()
    peticion = urllib.request.Request(url, data=cuerpo, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(peticion, timeout=10) as r:
            return r.status == 200
    except Exception as e:  # red caída, token inválido, etc.: se reintenta en el siguiente ciclo
        log.warning("No se pudo enviar a Telegram: %s", e)
        return False


def notificar_pendientes(db: Session) -> int:
    """Envía las aperturas y cierres no notificados. Devuelve cuántos mensajes salieron."""
    telegram = bool(settings.telegram_bot_token and settings.telegram_chat_id)
    pendientes = db.scalars(
        select(Alerta).where((Alerta.notificada.is_(False)) | (
            Alerta.cerrada_en.is_not(None) & Alerta.notificada_cierre.is_(False)
        )).order_by(Alerta.id)
    ).all()

    enviados = 0
    for alerta in pendientes:
        if not telegram:
            alerta.notificada = alerta.notificada_cierre = True
            continue
        if not alerta.notificada:
            if alerta.cerrada_en is not None:
                # Se abrió y cerró entre dos revisiones: no vale la pena avisar ninguna de las dos.
                alerta.notificada = alerta.notificada_cierre = True
                continue
            if _enviar_telegram(_texto(alerta, cierre=False)):
                alerta.notificada = True
                enviados += 1
        elif alerta.cerrada_en is not None and not alerta.notificada_cierre:
            if _enviar_telegram(_texto(alerta, cierre=True)):
                alerta.notificada_cierre = True
                enviados += 1

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return enviados
