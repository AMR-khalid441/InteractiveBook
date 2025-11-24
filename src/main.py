from routes import base_router , data_router
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from helpers import get_settings
app = FastAPI()

@app.on_event("startup")
async def start_db_client():
    settings = get_settings()
    app.mongo_connection = AsyncIOMotorClient(settings.MONGODB_URl)
    app.db_client = app.mongo_connection[settings.MONGODB_DB_NAME]

@app.on_event("shutdown")
async def shutdown_db_client():
    try:
        if hasattr(app, 'mongo_connection'):
            mongo_conn = getattr(app, 'mongo_connection', None)
            if mongo_conn is not None:
                await mongo_conn.close()
    except Exception as e:
        pass  # Ignore shutdown errors

app.include_router(base_router)
app.include_router(data_router)
