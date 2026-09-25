"""Punto de entrada de la API.

Local:  uvicorn app.main:app --reload --port 8000
AWS:    Lambda usa `handler` (Mangum) — mismo código, sin cambios.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

app = FastAPI(
    title="Sistema de Monitoreo y Predicción de Calidad de Composta",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}


# Routers
from app.routers import auth, lotes, modelo, predicciones, registros  # noqa: E402

app.include_router(auth.router)
app.include_router(lotes.router)
app.include_router(registros.router)
app.include_router(predicciones.router)
app.include_router(modelo.router)


# Handler para AWS Lambda (migración futura — no afecta ejecución local)
try:
    from mangum import Mangum

    handler = Mangum(app)
except ImportError:  # pragma: no cover
    handler = None
