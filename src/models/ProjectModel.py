from .BaseDataModel import BaseDataModel
from .db_schemas import project 
from .enums import DataBaseEnum

class ProjectModel(BaseDataModel):

    def __init__(self, db_client):
        super().__init__(db_client)
        self.collection = self.db_client[DataBaseEnum.COLLECTION_PROJECT_NAME.value]
    async def create_project(self , project: project):

        result = await self.collection.insert_one(project.model_dump())
        project._id = result.inserted_id
        return project
    async def get_project_or_create_one(self , project_id:str):
        
        record = await self.collection.find_one({
            "project_id" : project_id
        })

        if record is None :
            # create new project
            new_project = project(project_id = project_id)
            new_project = await self.create_project(project=new_project)

            return new_project 
        
        # Load existing project and ensure _id is set
        existing_project = project(**record)
        if '_id' in record and record['_id'] is not None:
            existing_project._id = record['_id']
        return existing_project
    
    async def get_all_projects(self , page: int =1  , page_size:int=10):
        total_documents = await self.collection.count_documents({})
        total_pages = total_documents // page_size

        if total_documents % page_size > 0 :
            total_pages+=1

        cursor = self.collection.find().skip((page-1)*page_size).limit(page_size)
        projects =[]
        async for document in cursor :
            proj = project(**document)
            if '_id' in document and document['_id'] is not None:
                proj._id = document['_id']
            projects.append(proj)

        return projects , total_pages



    