from .BaseDataModel import BaseDataModel
from .db_schemas import DataChunk
from .enums import DataBaseEnum
from bson.objectid import ObjectId
from typing import List, Optional

class ChunkModel(BaseDataModel):

    def __init__(self, db_client):
        super().__init__(db_client)
        self.collection = self.db_client[DataBaseEnum.COLLECTION_CHUNK_NAME.value]
    
    async def save_chunks(self, chunks: list, project_id: ObjectId, file_id: str, embeddings: Optional[List[List[float]]] = None) -> int:
        """
        Save multiple chunks to MongoDB with optional embeddings.
        
        Args:
            chunks: List of LangChain Document objects
            project_id: ObjectId of the project
            file_id: String identifier of the source file
            embeddings: Optional list of embedding vectors (one per chunk)
            
        Returns:
            int: Number of chunks saved
        """
        if not chunks or len(chunks) == 0:
            return 0
        
        chunk_documents = []
        for idx, chunk in enumerate(chunks, start=1):
            chunk_doc = DataChunk(
                chunk_text=chunk.page_content,
                chunk_order=idx,
                chunk_project_id=project_id,
                file_id=file_id,
                metadata=chunk.metadata if hasattr(chunk, 'metadata') else None,
                embedding=embeddings[idx - 1] if embeddings and idx <= len(embeddings) else None
            )
            chunk_dict = chunk_doc.model_dump()
            chunk_documents.append(chunk_dict)
        
        if chunk_documents:
            result = await self.collection.insert_many(chunk_documents)
            return len(result.inserted_ids)
        return 0
    
    async def get_chunks_by_project(self, project_id: ObjectId, limit: int = 100) -> List[DataChunk]:
        """
        Get chunks for a project.
        
        Args:
            project_id: ObjectId of the project
            limit: Maximum number of chunks to return
            
        Returns:
            List[DataChunk]: List of DataChunk objects
        """
        cursor = self.collection.find(
            {"chunk_project_id": project_id}
        ).sort("chunk_order", 1).limit(limit)
        
        chunks = []
        async for doc in cursor:
            chunks.append(DataChunk(**doc))
        return chunks
    
    async def get_chunks_by_file(self, project_id: ObjectId, file_id: str) -> List[DataChunk]:
        """
        Get chunks for a specific file.
        
        Args:
            project_id: ObjectId of the project
            file_id: String identifier of the file
            
        Returns:
            List[DataChunk]: List of DataChunk objects
        """
        cursor = self.collection.find({
            "chunk_project_id": project_id,
            "file_id": file_id
        }).sort("chunk_order", 1)
        
        chunks = []
        async for doc in cursor:
            chunks.append(DataChunk(**doc))
        return chunks
    
    async def delete_chunks_by_file(self, project_id: ObjectId, file_id: str) -> int:
        """
        Delete all chunks for a specific file.
        
        Args:
            project_id: ObjectId of the project
            file_id: String identifier of the file
            
        Returns:
            int: Number of chunks deleted
        """
        result = await self.collection.delete_many({
            "chunk_project_id": project_id,
            "file_id": file_id
        })
        return result.deleted_count

