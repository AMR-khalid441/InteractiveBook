from pydantic import BaseModel
from typing import Optional

class ProcessRequest(BaseModel):
    file_id: str
    chunk_size: Optional[int] = 1000  # Match endpoint default
    overlap_size: Optional[int] = 200  # Match endpoint default
    do_reset: Optional[int] = 0

class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5
    file_id: Optional[str] = None

class ChatRequest(BaseModel):
    query: str
    file_id: Optional[str] = None  # Optional file filter
    top_k: Optional[int] = None  # Override default context chunks
    
