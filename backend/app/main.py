"""Punto de entrada de la API"""
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings, validar_configuracion
from app.routers import alertas, auth, lotes, modelo, predicciones, registros

validar_configuracion()

app = FastAPI(
    title="ComposTerra — API de monitoreo y clasificación de compostaje",
    version="1.0.0",
    docs_url=None if settings.es_produccion else "/docs",
    redoc_url=None if settings.es_produccion else "/redoc",
    openapi_url=None if settings.es_produccion else "/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.lista_cors,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "entorno": settings.entorno}

api = APIRouter(prefix=settings.api_prefix)
api.include_router(auth.router)
api.include_router(lotes.router)
api.include_router(registros.router)
api.include_router(predicciones.router)
api.include_router(modelo.router)
api.include_router(alertas.router)
app.include_router(api)


try:
    from mangum import Mangum

    handler = Mangum(app)
except ImportError:  # pragma: no cover
    handler = None
