from fastapi import APIRouter, Query
from typing import List, Optional
from app.models.sensor_data import Alert, AlertLevel
from app.database.mongodb import get_db
from app.config import settings
from app.services.anomaly_detection import AnomalyDetectionService
from datetime import datetime

router = APIRouter()

@router.post("/alerts/generate")
async def generate_alerts():
    """
    Genera alertas analizando las condiciones actuales de todos los pisos
    """
    db = get_db()
    alerts_collection = db[settings.ALERTS_COLLECTION]
    
    all_alerts = []
    
    for piso in settings.PISOS:
        alerts = await AnomalyDetectionService.analyze_floor(piso)
        
        if alerts:
            # Guardar alertas en la base de datos
            alerts_dict = [alert.model_dump() for alert in alerts]
            if alerts_dict:
                await alerts_collection.insert_many(alerts_dict)
            
            all_alerts.extend(alerts)
    
    return {
        "message": f"{len(all_alerts)} alertas generadas",
        "alerts": all_alerts
    }

@router.get("/alerts", response_model=List[Alert])
async def get_alerts(
    piso: Optional[int] = Query(None, description="Filtrar por piso (1-3)"),
    nivel: Optional[AlertLevel] = Query(None, description="Filtrar por nivel de alerta"),
    limit: int = Query(50, description="Número máximo de alertas a retornar")
):
    """
    Obtiene alertas con filtros opcionales por piso y nivel
    """
    db = get_db()
    alerts_collection = db[settings.ALERTS_COLLECTION]
    
    query = {}
    if piso:
        query["piso"] = piso
    if nivel:
        query["nivel"] = nivel.value
    
    cursor = alerts_collection.find(query).sort("timestamp", -1).limit(limit)
    alerts = await cursor.to_list(length=limit)
    
    # Convertir ObjectId y datetime para JSON
    from datetime import datetime
    for alert in alerts:
        alert.pop("_id", None)
        if isinstance(alert.get("timestamp"), datetime):
            alert["timestamp"] = alert["timestamp"].isoformat()
    
    return alerts

@router.get("/alerts/active")
async def get_active_alerts(minutes: int = Query(60, description="Alertas de los últimos N minutos")):
    """
    Obtiene alertas activas de los últimos N minutos
    """
    db = get_db()
    alerts_collection = db[settings.ALERTS_COLLECTION]
    
    from datetime import timedelta
    cutoff_time = datetime.now() - timedelta(minutes=minutes)
    
    cursor = alerts_collection.find({
        "timestamp": {"$gte": cutoff_time}
    }).sort("timestamp", -1)
    
    alerts = await cursor.to_list(length=None)
    
    for alert in alerts:
        alert.pop("_id", None)
    
    # Agrupar por piso
    alerts_by_floor = {1: [], 2: [], 3: []}
    for alert in alerts:
        if alert["piso"] in alerts_by_floor:
            alerts_by_floor[alert["piso"]].append(alert)
    
    return {
        "total_alerts": len(alerts),
        "by_floor": alerts_by_floor,
        "alerts": alerts
    }

@router.delete("/alerts/clear")
async def clear_alerts():
    """
    Elimina todas las alertas (usar solo para testing)
    """
    db = get_db()
    alerts_collection = db[settings.ALERTS_COLLECTION]
    
    result = await alerts_collection.delete_many({})
    
    return {
        "message": "Alertas eliminadas",
        "deleted_count": result.deleted_count
    }