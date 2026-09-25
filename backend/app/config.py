"""Configuración central del backend.

Todos los valores se leen de variables de entorno (archivo .env en local,
variables de la instancia en AWS). El código es idéntico en ambos entornos:
lo único que cambia son estos valores.
"""
import sys

from pydantic_settings import BaseSettings, SettingsConfigDict

# Valor de ejemplo que viene en .env.example. Sirve para desarrollo, pero el
# sistema se niega a arrancar en producción si sigue puesto.
SECRETO_DE_EJEMPLO = "dev-secret-cambiar"


class Settings(BaseSettings):
    # Entorno: "desarrollo" o "produccion". En producción se exigen
    # credenciales propias y se ocultan las páginas de documentación.
    entorno: str = "desarrollo"

    database_url: str = "mysql+pymysql://root:password@localhost:3306/composta_db"

    jwt_secret: str = SECRETO_DE_EJEMPLO
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480

    # Orígenes permitidos por CORS, separados por coma.
    cors_origins: str = "http://localhost:3000"

    # Prefijo bajo el que se publican los endpoints.
    # Local: vacío  ->  /lotes
    # AWS:   /api   ->  /api/lotes   (CloudFront enruta /api/* hacia la EC2)
    api_prefix: str = ""

    ml_model_path: str = "../ml/modelos/modelo_composta.joblib"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def es_produccion(self) -> bool:
        return self.entorno.lower().startswith("prod")

    @property
    def lista_cors(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()


def validar_configuracion() -> None:
    """Impide arrancar en producción con credenciales de ejemplo.

    Es preferible que el servicio no levante a que quede publicado firmando
    tokens con un secreto que está a la vista en el repositorio.
    """
    if not settings.es_produccion:
        return

    problemas = []
    if settings.jwt_secret == SECRETO_DE_EJEMPLO or len(settings.jwt_secret) < 32:
        problemas.append(
            "JWT_SECRET debe ser propio y de al menos 32 caracteres.\n"
            "    Genéralo con: python -c \"import secrets; print(secrets.token_urlsafe(48))\""
        )
    if any("localhost" in o for o in settings.lista_cors):
        problemas.append(
            "CORS_ORIGINS todavía apunta a localhost; usa el dominio real del frontend."
        )
    if "root:password@" in settings.database_url:
        problemas.append("DATABASE_URL conserva las credenciales de ejemplo.")

    if problemas:
        print("\nLa configuración no es apta para producción:\n", file=sys.stderr)
        for p in problemas:
            print(f"  - {p}", file=sys.stderr)
        print(
            "\nCorrige el archivo .env, o usa ENTORNO=desarrollo si estás en local.\n",
            file=sys.stderr,
        )
        raise SystemExit(1)
