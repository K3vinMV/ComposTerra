"""Configuración central

Al migrar a AWS solo cambian los valores del .env / variables de
entorno de Lambda
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "mysql+pymysql://root:password@localhost:3306/composta_db"
    jwt_secret: str = "dev-secret-cambiar"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480
    cors_origins: str = "http://localhost:3000"
    ml_model_path: str = "../ml/modelos/modelo_composta.joblib"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
