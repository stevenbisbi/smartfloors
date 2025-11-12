from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # MongoDB
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "smartfloors"
    
    # Collections
    READINGS_COLLECTION: str = "readings"
    ALERTS_COLLECTION: str = "alerts"
    
    # Umbrales de temperatura (°C)
    TEMP_MIN_INFORMATIVA: float = 18.0
    TEMP_MAX_INFORMATIVA: float = 26.0
    TEMP_MIN_MEDIA: float = 16.0
    TEMP_MAX_MEDIA: float = 28.0
    TEMP_MIN_CRITICA: float = 14.0
    TEMP_MAX_CRITICA: float = 30.0
    
    # Umbrales de humedad (%)
    HUMEDAD_MIN_INFORMATIVA: float = 30.0
    HUMEDAD_MAX_INFORMATIVA: float = 60.0
    HUMEDAD_MIN_MEDIA: float = 25.0
    HUMEDAD_MAX_MEDIA: float = 70.0
    HUMEDAD_MIN_CRITICA: float = 20.0
    HUMEDAD_MAX_CRITICA: float = 80.0
    
    # Umbrales de energía (kW)
    ENERGIA_MEDIA: float = 15.0
    ENERGIA_CRITICA: float = 20.0
    
    # Predicción
    PREDICTION_WINDOW_MINUTES: int = 60
    MOVING_AVERAGE_WINDOW: int = 10  # últimos 10 registros
    
    # Datos del edificio
    EDIFICIO: str = "A"
    PISOS: list = [1, 2, 3]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()