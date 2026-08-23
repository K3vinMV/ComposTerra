"""Crea el usuario administrador inicial.

Uso (desde backend/, con venv activo y .env configurado):
    python scripts/crear_admin.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text

from app.core.security import hash_password
from app.database import SessionLocal

EMAIL = "admin@composta.com"
PASSWORD = "admin123"  # cambiar después del primer login

db = SessionLocal()
existe = db.execute(
    text("SELECT id FROM usuarios WHERE email = :e"), {"e": EMAIL}
).fetchone()

if existe:
    print(f"El usuario {EMAIL} ya existe (id={existe[0]}).")
else:
    db.execute(
        text(
            "INSERT INTO usuarios (nombre, email, password_hash, rol) "
            "VALUES (:n, :e, :p, 'admin')"
        ),
        {"n": "Administrador", "e": EMAIL, "p": hash_password(PASSWORD)},
    )
    db.commit()
    print(f"Usuario creado → {EMAIL} / {PASSWORD}")

db.close()
