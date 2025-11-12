from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

class MongoDB:
    client: AsyncIOMotorClient = None
    db = None

db_instance = MongoDB()

async def connect_db():
    """Conectar a MongoDB"""
    try:
        db_instance.client = AsyncIOMotorClient(settings.MONGODB_URL, serverSelectionTimeoutMS=5000)
        db_instance.db = db_instance.client[settings.DATABASE_NAME]
        
        # Verificar conexión
        await db_instance.client.admin.command('ping')
        print(f"✅ Conectado exitosamente a MongoDB: {settings.DATABASE_NAME}")
        
        # Crear índices para optimizar consultas
        readings_collection = db_instance.db[settings.READINGS_COLLECTION]
        await readings_collection.create_index([("timestamp", -1)])
        await readings_collection.create_index([("piso", 1)])
        await readings_collection.create_index([("timestamp", -1), ("piso", 1)])
        
        alerts_collection = db_instance.db[settings.ALERTS_COLLECTION]
        await alerts_collection.create_index([("timestamp", -1)])
        await alerts_collection.create_index([("piso", 1)])
        await alerts_collection.create_index([("nivel", 1)])
        
    except Exception as e:
        print(f"❌ Error conectando a MongoDB: {e}")
        print(f"Verifica que MongoDB esté corriendo en: {settings.MONGODB_URL}")
        raise

async def close_db():
    """Cerrar conexión a MongoDB"""
    if db_instance.client:
        db_instance.client.close()

def get_db():
    """Obtener instancia de la base de datos"""
    return db_instance.db