"""Punto de entrada de la API de ComposTerra.

Local:  uvicorn app.main:app --reload --port 8000
AWS:    el mismo comando en la instancia EC2, gestionado por systemd.

El prefijo de las rutas es configurable (`API_PREFIX`). En local va vacío y
los endpoints quedan en /lotes, /auth/login, etc. En AWS se pone "/api", para
que CloudFront pueda enrutar /api/* hacia la instancia y servir el frontend
desde S3 bajo el mismo dominio. Así el navegador nunca mezcla HTTPS con HTTP
y no hace falta un certificado propio para la API.
"""
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings, validar_configuracion
from app.routers import auth, lotes, modelo, predicciones, registros

# Se niega a arrancar si el entorno es producción y quedan valores de ejemplo
validar_configuracion()

app = FastAPI(
    title="ComposTerra — API de monitoreo y clasificación de compostaje",
    version="1.0.0",
    # La documentación interactiva se publica solo fuera de producción
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
    """Comprobación de vida. Se queda fuera del prefijo, para que el servidor
    pueda verificarse directamente sin pasar por CloudFront."""
    return {"status": "ok", "entorno": settings.entorno}


# Todos los endpoints cuelgan del prefijo configurado
api = APIRouter(prefix=settings.api_prefix)
api.include_router(auth.router)
api.include_router(lotes.router)
api.include_router(registros.router)
api.include_router(predicciones.router)
api.include_router(modelo.router)
app.include_router(api)


# Adaptador para AWS Lambda. No se usa en el despliegue actual sobre EC2,
# pero deja la puerta abierta sin tocar el resto del código.
try:
    from mangum import Mangum

    handler = Mangum(app)
except ImportError:  # pragma: no cover
    handler = None
