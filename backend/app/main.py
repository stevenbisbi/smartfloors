from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database.mongodb import connect_db, close_db
from app.routes import ingestion, predictions, alerts, dashboard
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        await connect_db()
        logger.info("✅ Conectado a MongoDB")
    except Exception as e:
        logger.error(f"❌ Error conectando a MongoDB: {e}")
    yield
    # Shutdown
    await close_db()
    logger.info("❌ Desconectado de MongoDB")

app = FastAPI(
    title="SmartFloors API",
    description="Sistema de monitoreo y alertas para edificios inteligentes",
    version="1.0.0",
    lifespan=lifespan
)

# CORS para permitir requests desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(ingestion.router, prefix="/api", tags=["Ingestion"])
app.include_router(predictions.router, prefix="/api", tags=["Predictions"])
app.include_router(alerts.router, prefix="/api", tags=["Alerts"])
app.include_router(dashboard.router, prefix="/api", tags=["Dashboard"])

@app.get("/")
def root():
    return {
        "status": "SmartFloors MVP running",
        "version": "1.0.0",
        "endpoints": {
            "ingestion": "/api/data",
            "predictions": "/api/predictions/{piso}",
            "alerts": "/api/alerts",
            "dashboard": "/api/dashboard"
        }
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Manejador de errores global
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Error no manejado: {exc}")
    import traceback
    traceback.print_exc()
    
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc),
            "type": type(exc).__name__
        }
    )