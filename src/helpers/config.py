from pydantic_settings import BaseSettings ,SettingsConfigDict
import os 


class Settings(BaseSettings):
    APPLICATION_NAME : str
    APP_VERSION : str
    OPENAI_API_KEY : str = ""  # Optional - can be empty for search-only mode
    FILE_ALLOWED_EXTENSIONS :list 
    FILE_MAX_SIZE :int   # 10 MB
    FILE_CHUNK_SIZE : int # 512000 #kb = half megabyte
    MONGODB_URl : str
    MONGODB_DB_NAME : str
    EMBEDDING_MODEL : str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION : int = 384
    EMBEDDING_BATCH_SIZE : int = 32
    EMBEDDING_DEVICE : str = "cpu"
    CHROMADB_PATH : str = "src/assets/chromadb"
    CHROMADB_COLLECTION_PREFIX : str = "project_"
    VECTOR_SEARCH_TOP_K : int = 5
    LLM_MODEL : str = "gpt-3.5-turbo"
    LLM_TEMPERATURE : float = 0.7
    LLM_MAX_TOKENS : int = 500
    RAG_CONTEXT_CHUNKS : int = 5
    RAG_SIMILARITY_THRESHOLD : float = 0.0  # Disabled by default - use all results
    
    class Config :
        env_file = os.path.join(os.path.dirname(__file__), "../assets/.env")

def get_settings():
    return Settings()