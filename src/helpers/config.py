from pydantic_settings import BaseSettings ,SettingsConfigDict
import os 


class Settings(BaseSettings):
    APPLICATION_NAME : str
    APP_VERSION : str
    OPENAI_API_KEY : str
    FILE_ALLOWED_EXTENSIONS :list 
    FILE_MAX_SIZE :int   # 10 MB
    FILE_CHUNK_SIZE : int # 512000 #kb = half megabyte
    MONGODB_URl : str
    MONGODB_DB_NAME : str
    
    class Config :
        env_file = os.path.join(os.path.dirname(__file__), "../assets/.env")

def get_settings():
    return Settings()