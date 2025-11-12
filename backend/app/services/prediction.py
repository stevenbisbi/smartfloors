from datetime import datetime, timedelta
from typing import List, Dict
import numpy as np
from app.database.mongodb import get_db
from app.config import settings
from app.models.sensor_data import Prediction

class PredictionService:
    
    @staticmethod
    async def get_historical_data(piso: int, minutes: int = 120) -> List[Dict]:
        """
        Obtiene datos históricos de un piso para los últimos N minutos
        """
        db = get_db()
        collection = db[settings.READINGS_COLLECTION]
        
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        cursor = collection.find({
            "piso": piso,
            "timestamp": {"$gte": cutoff_time}
        }).sort("timestamp", 1)
        
        data = await cursor.to_list(length=None)
        return data
    
    @staticmethod
    def moving_average_prediction(values: List[float], window: int = 10) -> float:
        """
        Predice el siguiente valor usando promedio móvil
        """
        if len(values) < window:
            window = len(values)
        
        if len(values) == 0:
            return 0.0
        
        recent_values = values[-window:]
        return np.mean(recent_values)
    
    @staticmethod
    def linear_trend_prediction(values: List[float], timestamps: List[datetime], 
                                minutes_ahead: int = 60) -> float:
        """
        Predice usando regresión lineal simple
        """
        if len(values) < 2:
            return values[-1] if values else 0.0
        
        # Convertir timestamps a minutos desde el primer timestamp
        base_time = timestamps[0]
        x = np.array([(t - base_time).total_seconds() / 60 for t in timestamps])
        y = np.array(values)
        
        # Calcular pendiente e intercepto
        if len(x) > 1:
            coefficients = np.polyfit(x, y, 1)
            slope, intercept = coefficients
            
            # Predecir para minutes_ahead minutos en el futuro
            future_x = x[-1] + minutes_ahead
            prediction = slope * future_x + intercept
            
            return float(prediction)
        
        return values[-1]
    
    @staticmethod
    async def predict_for_floor(piso: int) -> Prediction:
        """
        Genera predicción a +60 minutos para un piso específico
        """
        # Obtener datos históricos
        historical_data = await PredictionService.get_historical_data(piso, minutes=120)
        
        if not historical_data:
            raise ValueError(f"No hay datos históricos para el piso {piso}")
        
        # Extraer valores
        temps = [d["temp_C"] for d in historical_data]
        humedades = [d["humedad_pct"] for d in historical_data]
        energias = [d["energia_kW"] for d in historical_data]
        timestamps = [d["timestamp"] for d in historical_data]
        
        # Hacer predicciones usando promedio móvil y tendencia lineal
        # Usar el promedio de ambos métodos para mayor robustez
        temp_ma = PredictionService.moving_average_prediction(temps)
        temp_trend = PredictionService.linear_trend_prediction(temps, timestamps, 60)
        temp_pred = (temp_ma + temp_trend) / 2
        
        humedad_ma = PredictionService.moving_average_prediction(humedades)
        humedad_trend = PredictionService.linear_trend_prediction(humedades, timestamps, 60)
        humedad_pred = (humedad_ma + humedad_trend) / 2
        
        energia_ma = PredictionService.moving_average_prediction(energias)
        energia_trend = PredictionService.linear_trend_prediction(energias, timestamps, 60)
        energia_pred = (energia_ma + energia_trend) / 2
        
        # Calcular confianza basada en la cantidad de datos
        confianza = min(len(historical_data) / 60, 1.0)  # Máxima confianza con 60+ datos
        
        prediction = Prediction(
            piso=piso,
            timestamp_prediccion=datetime.now() + timedelta(minutes=60),
            temp_C_predicha=round(temp_pred, 2),
            humedad_pct_predicha=round(max(0, min(100, humedad_pred)), 2),
            energia_kW_predicha=round(max(0, energia_pred), 2),
            confianza=round(confianza, 2)
        )
        
        return prediction
    
    @staticmethod
    async def predict_all_floors() -> List[Prediction]:
        """
        Genera predicciones para todos los pisos
        """
        predictions = []
        for piso in settings.PISOS:
            try:
                pred = await PredictionService.predict_for_floor(piso)
                predictions.append(pred)
            except ValueError:
                # Si no hay datos, continuar con el siguiente piso
                continue
        
        return predictions