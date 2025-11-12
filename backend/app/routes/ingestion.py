from fastapi import APIRouter, HTTPException, status
from typing import List
from app.models.sensor_data import SensorReading
from app.database.mongodb import get_db
from app.config import settings
from datetime import datetime

router = APIRouter()

@router.post("/data", status_code=status.HTTP_201_CREATED)
async def ingest_data(reading: SensorReading):
    """
    Ingesta un registro individual de datos del sensor
    """
    try:
        db = get_db()
        collection = db[settings.READINGS_COLLECTION]
        
        # Convertir a diccionario
        reading_dict = reading.model_dump()
        
        # Si timestamp es string, convertir a datetime
        if isinstance(reading_dict['timestamp'], str):
            reading_dict['timestamp'] = datetime.fromisoformat(reading_dict['timestamp'].replace('Z', '+00:00'))
        
        result = await collection.insert_one(reading_dict)
        
        # Retornar respuesta simple sin ObjectId
        return {
            "message": "Datos ingresados correctamente",
            "id": str(result.inserted_id),
            "piso": reading.piso,
            "timestamp": reading.timestamp.isoformat() if isinstance(reading.timestamp, datetime) else reading.timestamp
        }
    except Exception as e:
        print(f"❌ Error en ingest_data: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al ingestar datos: {str(e)}"
        )

@router.post("/data/batch", status_code=status.HTTP_201_CREATED)
async def ingest_data_batch(readings: List[SensorReading]):
    """
    Ingesta múltiples registros de datos de sensores
    """
    try:
        db = get_db()
        collection = db[settings.READINGS_COLLECTION]
        
        readings_dict = []
        for reading in readings:
            reading_dict = reading.model_dump()
            # Convertir timestamp si es necesario
            if isinstance(reading_dict['timestamp'], str):
                reading_dict['timestamp'] = datetime.fromisoformat(reading_dict['timestamp'].replace('Z', '+00:00'))
            readings_dict.append(reading_dict)
        
        result = await collection.insert_many(readings_dict)
        
        return {
            "message": f"{len(result.inserted_ids)} registros ingresados correctamente",
            "count": len(result.inserted_ids),
            "ids": [str(id) for id in result.inserted_ids]
        }
    except Exception as e:
        print(f"❌ Error en ingest_data_batch: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al ingestar datos en lote: {str(e)}"
        )

@router.get("/data/latest")
async def get_latest_readings(piso: int = None, limit: int = 10):
    """
    Obtiene las últimas lecturas de sensores
    """
    db = get_db()
    collection = db[settings.READINGS_COLLECTION]
    
    query = {}
    if piso:
        query["piso"] = piso
    
    cursor = collection.find(query).sort("timestamp", -1).limit(limit)
    readings = await cursor.to_list(length=limit)
    
    # Serializar documentos (convertir ObjectId y datetime)
    serialized_readings = []
    for reading in readings:
        reading["_id"] = str(reading["_id"])
        if isinstance(reading.get("timestamp"), datetime):
            reading["timestamp"] = reading["timestamp"].isoformat()
        serialized_readings.append(reading)
    
    return {
        "count": len(serialized_readings),
        "readings": serialized_readings
    }

@router.delete("/data/clear")
async def clear_all_data():
    """
    Limpia todos los datos (usar solo para testing)
    """
    db = get_db()
    readings_collection = db[settings.READINGS_COLLECTION]
    alerts_collection = db[settings.ALERTS_COLLECTION]
    
    readings_result = await readings_collection.delete_many({})
    alerts_result = await alerts_collection.delete_many({})
    
    return {
        "message": "Datos eliminados",
        "readings_deleted": readings_result.deleted_count,
        "alerts_deleted": alerts_result.deleted_count
    }