from datetime import datetime
from typing import List, Optional
from app.models.sensor_data import Alert, AlertLevel, AlertVariable
from app.config import settings
from app.services.prediction import PredictionService

class AnomalyDetectionService:
    
    @staticmethod
    def detect_temperature_anomaly(temp: float, temp_pred: Optional[float] = None) -> Optional[Alert]:
        """
        Detecta anomalías en temperatura
        """
        nivel = None
        recomendacion = ""
        
        if temp >= settings.TEMP_MAX_CRITICA or temp <= settings.TEMP_MIN_CRITICA:
            nivel = AlertLevel.CRITICA
            if temp >= settings.TEMP_MAX_CRITICA:
                recomendacion = f"Temperatura crítica alta ({temp}°C). Reducir setpoint a 24°C inmediatamente."
            else:
                recomendacion = f"Temperatura crítica baja ({temp}°C). Aumentar setpoint a 20°C inmediatamente."
        
        elif temp >= settings.TEMP_MAX_MEDIA or temp <= settings.TEMP_MIN_MEDIA:
            nivel = AlertLevel.MEDIA
            if temp >= settings.TEMP_MAX_MEDIA:
                recomendacion = f"Temperatura elevada ({temp}°C). Ajustar setpoint a 24°C en los próximos 15 min."
            else:
                recomendacion = f"Temperatura baja ({temp}°C). Aumentar setpoint a 22°C en los próximos 15 min."
        
        elif temp >= settings.TEMP_MAX_INFORMATIVA or temp <= settings.TEMP_MIN_INFORMATIVA:
            nivel = AlertLevel.INFORMATIVA
            recomendacion = f"Temperatura fuera del rango óptimo ({temp}°C). Monitorear evolución."
        
        # Verificar predicción
        if temp_pred and temp_pred >= settings.TEMP_MAX_MEDIA:
            if nivel is None or nivel == AlertLevel.INFORMATIVA:
                nivel = AlertLevel.MEDIA
                recomendacion = f"Predicción indica temperatura de {temp_pred:.1f}°C en 60 min. Ajustar setpoint preventivamente."
        
        if nivel:
            return Alert(
                timestamp=datetime.now(),
                piso=0,  # Se asigna luego
                variable=AlertVariable.TEMPERATURA,
                nivel=nivel,
                recomendacion=recomendacion,
                valor_actual=temp,
                valor_predicho=temp_pred
            )
        
        return None
    
    @staticmethod
    def detect_humidity_anomaly(humedad: float, humedad_pred: Optional[float] = None) -> Optional[Alert]:
        """
        Detecta anomalías en humedad
        """
        nivel = None
        recomendacion = ""
        
        if humedad >= settings.HUMEDAD_MAX_CRITICA or humedad <= settings.HUMEDAD_MIN_CRITICA:
            nivel = AlertLevel.CRITICA
            if humedad >= settings.HUMEDAD_MAX_CRITICA:
                recomendacion = f"Humedad crítica alta ({humedad}%). Incrementar ventilación urgentemente; revisar sistema HVAC."
            else:
                recomendacion = f"Humedad crítica baja ({humedad}%). Activar humidificadores; revisar sellos térmicos."
        
        elif humedad >= settings.HUMEDAD_MAX_MEDIA or humedad <= settings.HUMEDAD_MIN_MEDIA:
            nivel = AlertLevel.MEDIA
            if humedad >= settings.HUMEDAD_MAX_MEDIA:
                recomendacion = f"Humedad elevada ({humedad}%). Incrementar ventilación; revisar puertas/celosías."
            else:
                recomendacion = f"Humedad baja ({humedad}%). Considerar activar humidificadores."
        
        elif humedad >= settings.HUMEDAD_MAX_INFORMATIVA or humedad <= settings.HUMEDAD_MIN_INFORMATIVA:
            nivel = AlertLevel.INFORMATIVA
            recomendacion = f"Humedad fuera del rango óptimo ({humedad}%). Monitorear condiciones."
        
        if nivel:
            return Alert(
                timestamp=datetime.now(),
                piso=0,
                variable=AlertVariable.HUMEDAD,
                nivel=nivel,
                recomendacion=recomendacion,
                valor_actual=humedad,
                valor_predicho=humedad_pred
            )
        
        return None
    
    @staticmethod
    def detect_energy_anomaly(energia: float, energia_pred: Optional[float] = None) -> Optional[Alert]:
        """
        Detecta anomalías en consumo energético
        """
        nivel = None
        recomendacion = ""
        
        if energia >= settings.ENERGIA_CRITICA:
            nivel = AlertLevel.CRITICA
            recomendacion = f"Consumo crítico ({energia} kW). Redistribuir carga eléctrica inmediatamente."
        
        elif energia >= settings.ENERGIA_MEDIA:
            nivel = AlertLevel.MEDIA
            recomendacion = f"Consumo elevado ({energia} kW). Considerar redistribuir carga en la próxima hora."
        
        if energia_pred and energia_pred >= settings.ENERGIA_CRITICA:
            if nivel is None:
                nivel = AlertLevel.MEDIA
                recomendacion = f"Predicción indica consumo de {energia_pred:.1f} kW en 60 min. Planificar redistribución de carga."
        
        if nivel:
            return Alert(
                timestamp=datetime.now(),
                piso=0,
                variable=AlertVariable.ENERGIA,
                nivel=nivel,
                recomendacion=recomendacion,
                valor_actual=energia,
                valor_predicho=energia_pred
            )
        
        return None
    
    @staticmethod
    def detect_combined_risk(temp: float, energia: float, temp_pred: Optional[float] = None, 
                            energia_pred: Optional[float] = None) -> Optional[Alert]:
        """
        Detecta riesgo combinado de sobrecarga térmica
        """
        # Riesgo alto: temperatura alta + energía alta
        if temp >= settings.TEMP_MAX_MEDIA and energia >= settings.ENERGIA_MEDIA:
            nivel = AlertLevel.CRITICA
            recomendacion = f"Riesgo de sobrecarga térmica: temp {temp}°C + consumo {energia} kW. Reducir carga y ajustar HVAC urgentemente."
            
            return Alert(
                timestamp=datetime.now(),
                piso=0,
                variable=AlertVariable.RIESGO_COMBINADO,
                nivel=nivel,
                recomendacion=recomendacion,
                valor_actual=temp,
                valor_predicho=temp_pred
            )
        
        # Riesgo predictivo
        if temp_pred and energia_pred:
            if temp_pred >= settings.TEMP_MAX_MEDIA and energia_pred >= settings.ENERGIA_MEDIA:
                nivel = AlertLevel.MEDIA
                recomendacion = f"Predicción indica riesgo de sobrecarga en 60 min: temp {temp_pred:.1f}°C + consumo {energia_pred:.1f} kW. Acción preventiva recomendada."
                
                return Alert(
                    timestamp=datetime.now(),
                    piso=0,
                    variable=AlertVariable.RIESGO_COMBINADO,
                    nivel=nivel,
                    recomendacion=recomendacion,
                    valor_actual=temp,
                    valor_predicho=temp_pred
                )
        
        return None
    
    @staticmethod
    async def analyze_floor(piso: int) -> List[Alert]:
        """
        Analiza todas las anomalías para un piso específico
        """
        alerts = []
        
        # Obtener datos más recientes
        historical_data = await PredictionService.get_historical_data(piso, minutes=5)
        
        if not historical_data:
            return alerts
        
        latest = historical_data[-1]
        
        # Obtener predicción
        try:
            prediction = await PredictionService.predict_for_floor(piso)
            temp_pred = prediction.temp_C_predicha
            humedad_pred = prediction.humedad_pct_predicha
            energia_pred = prediction.energia_kW_predicha
        except:
            temp_pred = None
            humedad_pred = None
            energia_pred = None
        
        # Detectar anomalías
        temp_alert = AnomalyDetectionService.detect_temperature_anomaly(
            latest["temp_C"], temp_pred
        )
        if temp_alert:
            temp_alert.piso = piso
            alerts.append(temp_alert)
        
        humidity_alert = AnomalyDetectionService.detect_humidity_anomaly(
            latest["humedad_pct"], humedad_pred
        )
        if humidity_alert:
            humidity_alert.piso = piso
            alerts.append(humidity_alert)
        
        energy_alert = AnomalyDetectionService.detect_energy_anomaly(
            latest["energia_kW"], energia_pred
        )
        if energy_alert:
            energy_alert.piso = piso
            alerts.append(energy_alert)
        
        combined_alert = AnomalyDetectionService.detect_combined_risk(
            latest["temp_C"], latest["energia_kW"], temp_pred, energia_pred
        )
        if combined_alert:
            combined_alert.piso = piso
            alerts.append(combined_alert)
        
        return alerts