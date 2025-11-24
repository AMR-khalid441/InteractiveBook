from pydantic import BaseModel , Field , validator , ConfigDict
from typing import Optional
from bson.objectid import ObjectId

class project(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    _id : Optional[ObjectId] = None
    project_id : str = Field(... , min_length= 1)

    @validator('project_id')
    def validate_project_id(cls, value):
        if not value.isalnum():
            raise ValueError("project id must be alpha numeric")
        return value
        