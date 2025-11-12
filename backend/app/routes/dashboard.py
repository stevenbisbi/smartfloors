from fastapi import APIRouter, Query
from typing import List, Dict
from app.models.sensor_data import FloorStatus, DashboardData, AlertLevel
from app.database.mongodb import get_db
from app.config import settings
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/dashboard", response_model=DashboardData)
async def get_dashboard_data():
    """
    Obtiene todos los datos necesarios para el dashboard
    """
    db = get_db()
    readings_collection = db[settings.READINGS_COLLECTION]
    alerts_collection = db[settings.ALERTS_COLLECTION]
    
    pisos_status = []
    
    # Obtener estado de cada piso
    for piso in settings.PISOS:
        # Obtener última lectura
        latest_reading = await readings_collection.find_one(
            {"piso": piso},
            sort=[("timestamp", -1)]
        )
        
        if not latest_reading:
            continue
        
        # Contar alertas activas de la última hora
        cutoff_time = datetime.now() - timedelta(hours=1)
        alertas_activas = await alerts_collection.count_documents({
            "piso": piso,
            "timestamp": {"$gte": cutoff_time}
        })
        
        # Obtener alerta más crítica
        critical_alert = await alerts_collection.find_one(
            {
                "piso": piso,
                "timestamp": {"$gte": cutoff_time}
            },
            sort=[("timestamp", -1)]
        )
        
        # Determinar estado del piso
        if critical_alert:
            estado = AlertLevel(critical_alert["nivel"])
            resumen = critical_alert["recomendacion"][:80] + "..."
        else:
            estado = AlertLevel.OK
            resumen = "Condiciones normales"
        
        floor_status = FloorStatus(
            piso=piso,
            estado=estado,
            resumen=resumen,
            temp_actual=latest_reading["temp_C"],
            humedad_actual=latest_reading["humedad_pct"],
            energia_actual=latest_reading["energia_kW"],
            alertas_activas=alertas_activas
        )
        
        pisos_status.append(floor_status)
    
    # Obtener últimas 20 alertas
    cursor = alerts_collection.find().sort("timestamp", -1).limit(20)
    alertas_recientes = await cursor.to_list(length=20)
    
    # Serializar alertas
    for alert in alertas_recientes:
        alert.pop("_id", None)
        if isinstance(alert.get("timestamp"), datetime):
            alert["timestamp"] = alert["timestamp"].isoformat()
    
    return DashboardData(
        timestamp=datetime.now(),
        pisos=pisos_status,
        alertas_recientes=alertas_recientes
    )

@router.get("/dashboard/trends/{piso}")
async def get_floor_trends(
    piso: int,
    hours: int = Query(4, description="Horas de datos históricos")
):
    """
    Obtiene las tendencias de temperatura, humedad y energía de un piso
    """
    db = get_db()
    readings_collection = db[settings.READINGS_COLLECTION]
    
    cutoff_time = datetime.now() - timedelta(hours=hours)
    
    cursor = readings_collection.find({
        "piso": piso,
        "timestamp": {"$gte": cutoff_time}
    }).sort("timestamp", 1)
    
    readings = await cursor.to_list(length=None)
    
    if not readings:
        return {
            "piso": piso,
            "data": [],
            "message": "No hay datos disponibles"
        }
    
    # Formatear datos para gráficos
    trends = []
    for reading in readings:
        trends.append({
            "timestamp": reading["timestamp"].isoformat(),
            "temp_C": reading["temp_C"],
            "humedad_pct": reading["humedad_pct"],
            "energia_kW": reading["energia_kW"]
        })
    
    return {
        "piso": piso,
        "count": len(trends),
        "data": trends
    }

@router.get("/dashboard/summary")
async def get_summary():
    """
    Obtiene un resumen general del sistema
    """
    db = get_db()
    readings_collection = db[settings.READINGS_COLLECTION]
    alerts_collection = db[settings.ALERTS_COLLECTION]
    
    # Total de lecturas
    total_readings = await readings_collection.count_documents({})
    
    # Alertas por nivel en la última hora
    cutoff_time = datetime.now() - timedelta(hours=1)
    
    alertas_criticas = await alerts_collection.count_documents({
        "nivel": AlertLevel.CRITICA.value,
        "timestamp": {"$gte": cutoff_time}
    })
    
    alertas_medias = await alerts_collection.count_documents({
        "nivel": AlertLevel.MEDIA.value,
        "timestamp": {"$gte": cutoff_time}
    })
    
    alertas_informativas = await alerts_collection.count_documents({
        "nivel": AlertLevel.INFORMATIVA.value,
        "timestamp": {"$gte": cutoff_time}
    })
    
    # Última lectura de cada piso
    latest_by_floor = {}
    for piso in settings.PISOS:
        latest = await readings_collection.find_one(
            {"piso": piso},
            sort=[("timestamp", -1)]
        )
        if latest:
            latest_by_floor[f"piso_{piso}"] = {
                "timestamp": latest["timestamp"].isoformat(),
                "temp_C": latest["temp_C"],
                "humedad_pct": latest["humedad_pct"],
                "energia_kW": latest["energia_kW"]
            }
    
    return {
        "total_readings": total_readings,
        "alerts_last_hour": {
            "criticas": alertas_criticas,
            "medias": alertas_medias,
            "informativas": alertas_informativas,
            "total": alertas_criticas + alertas_medias + alertas_informativas
        },
        "latest_readings": latest_by_floor,
        "timestamp": datetime.now().isoformat()
    }