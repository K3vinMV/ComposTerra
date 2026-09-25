"""Crea el usuario administrador inicial.
"""
import argparse
import os
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text

from app.core.security import hash_password
from app.database import SessionLocal

EMAIL = os.getenv("ADMIN_EMAIL", "admin@composterra.mx")
NOMBRE = os.getenv("ADMIN_NOMBRE", "Administrador")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--reiniciar",
        action="store_true",
        help="cambia la contraseña si el usuario ya existe",
    )
    args = parser.parse_args()

    password = os.getenv("ADMIN_PASSWORD")
    generada = password is None
    if generada:
        # 16 bytes en base64 -> ~22 caracteres imprevisibles
        password = secrets.token_urlsafe(16)

    db = SessionLocal()
    try:
        existe = db.execute(
            text("SELECT id FROM usuarios WHERE email = :e"), {"e": EMAIL}
        ).fetchone()

        if existe and not args.reiniciar:
            print(f"El usuario {EMAIL} ya existe (id={existe[0]}).")
            print("Usa --reiniciar si quieres cambiarle la contraseña.")
            return

        if existe:
            db.execute(
                text("UPDATE usuarios SET password_hash = :p WHERE email = :e"),
                {"p": hash_password(password), "e": EMAIL},
            )
            accion = "Contraseña actualizada"
        else:
            db.execute(
                text(
                    "INSERT INTO usuarios (nombre, email, password_hash, rol) "
                    "VALUES (:n, :e, :p, 'admin')"
                ),
                {"n": NOMBRE, "e": EMAIL, "p": hash_password(password)},
            )
            accion = "Usuario creado"
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    print(f"\n{accion}")
    print(f"  Correo:     {EMAIL}")
    if generada:
        print(f"  Contraseña: {password}")
        print("\n  Guárdala ahora: no vuelve a mostrarse y no queda registrada.")
    else:
        print("  Contraseña: la definida en ADMIN_PASSWORD")
    print()


if __name__ == "__main__":
    main()
