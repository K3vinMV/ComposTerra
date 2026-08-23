"""Dependencias compartidas — protección JWT de endpoints.

Uso en cualquier router:
    @router.get("/lotes")
    def listar(usuario: Usuario = Depends(get_current_user)): ...
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.database import get_db
from app.models import Usuario

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise exc

    payload = decode_token(credentials.credentials)
    if payload is None or "sub" not in payload:
        raise exc

    usuario = db.query(Usuario).filter(Usuario.email == payload["sub"]).first()
    if usuario is None:
        raise exc
    return usuario
