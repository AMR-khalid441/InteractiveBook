from pydantic import BaseModel , Field , ConfigDict
from typing import Optional
from bson.objectid import ObjectId

class DataChunk(BaseModel):
        model_config = ConfigDict(arbitrary_types_allowed=True)
        _id : Optional[ObjectId] = None
        chunk_text : str = Field(... , min_length = 1)
        chunk_order : int = Field(... , gt=0)
        chunk_project_id : ObjectId
        