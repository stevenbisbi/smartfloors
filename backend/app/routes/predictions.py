from fastapi import APIRouter, HTTPException
from typing import List
from app.models.sensor_data import Prediction
from app.services.prediction import PredictionService

router = APIRouter()

@router.get("/predictions/{piso}", response_model=Prediction)
async def get_prediction(piso: int):
    """
    Obtiene la predicción a +60 minutos para un piso específico
    """
    if piso not in [1, 2, 3]:
        raise HTTPException(status_code=400, detail="El piso debe ser 1, 2 o 3")
    
    try:
        prediction = await PredictionService.predict_for_floor(piso)
        return prediction
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/predictions", response_model=List[Prediction])
async def get_all_predictions():
    """
    Obtiene las predicciones a +60 minutos para todos los pisos
    """
    predictions = await PredictionService.predict_all_floors()
    
    if not predictions:
        raise HTTPException(
            status_code=404, 
            detail="No hay suficientes datos históricos para generar predicciones"
        )
    
    return predictions