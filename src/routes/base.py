from fastapi import FastAPI , APIRouter  , Depends
from helpers import get_settings ,Settings 
base_router = APIRouter(
    prefix="/api/v1" , 
    tags= ["api_v1"]

)

@base_router.get("/welcome")

async def welcome (app_settings:Settings= Depends(get_settings)):
    app_settings = get_settings()

    return{"status" : "running",
           "name ": app_settings.APPLICATION_NAME , 
           "version" : app_settings.APP_VERSION , 
           "open_api_key" : app_settings.OPENAI_API_KEY }
