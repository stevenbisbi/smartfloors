from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum

class SensorReading(BaseModel):
    timestamp: datetime
    edificio: str = Field(default="A")
    piso: int = Field(ge=1, le=3, description="Número de piso (1-3)")
    temp_C: float = Field(description="Temperatura en grados Celsius")
    humedad_pct: float = Field(ge=0, le=100, description="Humedad relativa en porcentaje")
    energia_kW: float = Field(ge=0, description="Consumo de energía en kW")

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2025-11-11T14:30:00",
                "edificio": "A",
                "piso": 2,
                "temp_C": 24.5,
                "humedad_pct": 55.0,
                "energia_kW": 12.3
            }
        }

class AlertLevel(str, Enum):
    OK = "OK"
    INFORMATIVA = "Informativa"
    MEDIA = "Media"
    CRITICA = "Crítica"

class AlertVariable(str, Enum):
    TEMPERATURA = "temperatura"
    HUMEDAD = "humedad"
    ENERGIA = "energia"
    RIESGO_COMBINADO = "riesgo_combinado"

class Alert(BaseModel):
    timestamp: datetime
    piso: int
    variable: AlertVariable
    nivel: AlertLevel
    recomendacion: str
    valor_actual: Optional[float] = None
    valor_predicho: Optional[float] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2025-11-11T14:30:00",
                "piso": 2,
                "variable": "temperatura",
                "nivel": "Media",
                "recomendacion": "Ajustar temperatura del Piso 2 a 24 °C en los próximos 15 min.",
                "valor_actual": 28.5,
                "valor_predicho": 29.2
            }
        }

class Prediction(BaseModel):
    piso: int
    timestamp_prediccion: datetime
    temp_C_predicha: float
    humedad_pct_predicha: float
    energia_kW_predicha: float
    confianza: float = Field(ge=0, le=1, description="Nivel de confianza de la predicción")

class FloorStatus(BaseModel):
    piso: int
    estado: AlertLevel
    resumen: str
    temp_actual: float
    humedad_actual: float
    energia_actual: float
    alertas_activas: int

class DashboardData(BaseModel):
    timestamp: datetime
    pisos: List[FloorStatus]
    alertas_recientes: List[Alert]