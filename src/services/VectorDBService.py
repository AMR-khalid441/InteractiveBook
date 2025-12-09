"""
Vector Database Service for ChromaDB integration.
Handles storing embeddings and performing similarity search.
"""
import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Optional, Dict, Any
from helpers import get_settings
import logging
import os

logger = logging.getLogger(__name__)


class VectorDBService:
    """
    Service for managing vector embeddings in ChromaDB.
    Provides methods for storing chunks with embeddings and performing similarity search.
    """
    
    _client_instance = None
    
    def __init__(self):
        """Initialize ChromaDB client with persistent storage."""
        self.settings = get_settings()
        self.chromadb_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            self.settings.CHROMADB_PATH.lstrip("src/")
        )
        
        # Ensure directory exists
        os.makedirs(self.chromadb_path, exist_ok=True)
        
        # Initialize ChromaDB client (singleton pattern)
        if VectorDBService._client_instance is None:
            try:
                logger.info(f"Initializing ChromaDB client at: {self.chromadb_path}")
                VectorDBService._client_instance = chromadb.PersistentClient(
                    path=self.chromadb_path,
                    settings=ChromaSettings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )
                logger.info("ChromaDB client initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing ChromaDB client: {e}", exc_info=True)
                raise RuntimeError(f"Failed to initialize ChromaDB client: {e}")
        
        self.client = VectorDBService._client_instance
        self.collection_prefix = self.settings.CHROMADB_COLLECTION_PREFIX
    
    def get_or_create_collection(self, project_id: str):
        """
        Get or create a ChromaDB collection for a project.
        
        Args:
            project_id: Project identifier
            
        Returns:
            chromadb.Collection: ChromaDB collection object
            
        Raises:
            RuntimeError: If collection creation fails
        """
        collection_name = f"{self.collection_prefix}{project_id}"
        
        try:
            # Try to get existing collection
            try:
                collection = self.client.get_collection(name=collection_name)
                logger.debug(f"Retrieved existing collection: {collection_name}")
                return collection
            except Exception:
                # Collection doesn't exist, create it
                logger.info(f"Creating new ChromaDB collection: {collection_name}")
                collection = self.client.create_collection(
                    name=collection_name,
                    metadata={"project_id": project_id}
                )
                logger.info(f"Collection {collection_name} created successfully")
                return collection
        except Exception as e:
            logger.error(f"Error getting/creating collection {collection_name}: {e}", exc_info=True)
            raise RuntimeError(f"Failed to get/create collection: {e}")
    
    def add_chunks(
        self,
        project_id: str,
        chunks: List,
        embeddings: List[List[float]],
        file_id: str
    ) -> int:
        """
        Add chunks with embeddings to ChromaDB.
        
        Args:
            project_id: Project identifier
            chunks: List of LangChain Document objects
            embeddings: List of embedding vectors (one per chunk)
            file_id: File identifier
            
        Returns:
            int: Number of chunks added
            
        Raises:
            ValueError: If inputs are invalid
            RuntimeError: If ChromaDB operation fails
        """
        if not chunks or len(chunks) == 0:
            logger.warning("No chunks provided to add_chunks")
            return 0
        
        if not embeddings or len(embeddings) == 0:
            logger.warning("No embeddings provided to add_chunks")
            return 0
        
        if len(chunks) != len(embeddings):
            logger.warning(
                f"Chunk count ({len(chunks)}) doesn't match embedding count ({len(embeddings)})"
            )
            # Use minimum length to avoid index errors
            min_length = min(len(chunks), len(embeddings))
            chunks = chunks[:min_length]
            embeddings = embeddings[:min_length]
        
        try:
            collection = self.get_or_create_collection(project_id)
            
            # Prepare data for ChromaDB
            ids = []
            documents = []
            metadatas = []
            embedding_vectors = []
            
            for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings), start=1):
                # Validate embedding dimensions
                if len(embedding) != self.settings.EMBEDDING_DIMENSION:
                    logger.warning(
                        f"Embedding dimension mismatch at chunk {idx}: "
                        f"expected {self.settings.EMBEDDING_DIMENSION}, got {len(embedding)}"
                    )
                    continue
                
                # Generate unique ID for this chunk
                chunk_id = f"chunk_{file_id}_{idx}"
                ids.append(chunk_id)
                
                # Store chunk text as document
                documents.append(chunk.page_content)
                
                # Prepare metadata
                metadata = {
                    "chunk_order": idx,
                    "file_id": file_id,
                    "project_id": project_id,
                }
                
                # Add chunk metadata if available
                if hasattr(chunk, 'metadata') and chunk.metadata:
                    # Convert ObjectId to string if present
                    chunk_metadata = {}
                    for key, value in chunk.metadata.items():
                        if hasattr(value, '__str__'):
                            chunk_metadata[key] = str(value)
                        else:
                            chunk_metadata[key] = value
                    metadata.update(chunk_metadata)
                
                metadatas.append(metadata)
                embedding_vectors.append(embedding)
            
            if not ids:
                logger.warning("No valid chunks to add after validation")
                return 0
            
            # Add to ChromaDB
            collection.add(
                ids=ids,
                embeddings=embedding_vectors,
                documents=documents,
                metadatas=metadatas
            )
            
            logger.info(
                f"Added {len(ids)} chunks to ChromaDB collection for project {project_id}"
            )
            return len(ids)
            
        except Exception as e:
            logger.error(f"Error adding chunks to ChromaDB: {e}", exc_info=True)
            raise RuntimeError(f"Failed to add chunks to ChromaDB: {e}")
    
    def search_similar(
        self,
        project_id: str,
        query_embedding: List[float],
        top_k: int = 5,
        file_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar chunks based on query embedding.
        
        Args:
            project_id: Project identifier
            query_embedding: Query embedding vector
            top_k: Number of results to return
            file_id: Optional file filter
            
        Returns:
            List[Dict]: List of similar chunks with metadata and distances
            
        Raises:
            ValueError: If query embedding is invalid
            RuntimeError: If search fails
        """
        if not query_embedding:
            raise ValueError("Query embedding cannot be empty")
        
        if len(query_embedding) != self.settings.EMBEDDING_DIMENSION:
            raise ValueError(
                f"Query embedding dimension mismatch: "
                f"expected {self.settings.EMBEDDING_DIMENSION}, got {len(query_embedding)}"
            )
        
        try:
            collection = self.get_or_create_collection(project_id)
            
            # Prepare where clause for file filter
            where_clause = None
            if file_id:
                where_clause = {"file_id": file_id}
            
            # Perform similarity search
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_clause
            )
            
            # Format results
            formatted_results = []
            if results['ids'] and len(results['ids'][0]) > 0:
                for i in range(len(results['ids'][0])):
                    result = {
                        "chunk_id": results['ids'][0][i],
                        "chunk_text": results['documents'][0][i] if results['documents'] else "",
                        "distance": results['distances'][0][i] if results['distances'] else None,
                        "metadata": results['metadatas'][0][i] if results['metadatas'] else {}
                    }
                    formatted_results.append(result)
            
            logger.info(
                f"Found {len(formatted_results)} similar chunks for project {project_id}"
            )
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching ChromaDB: {e}", exc_info=True)
            raise RuntimeError(f"Failed to search ChromaDB: {e}")
    
    def delete_chunks_by_file(self, project_id: str, file_id: str) -> int:
        """
        Delete chunks for a specific file from ChromaDB.
        
        Args:
            project_id: Project identifier
            file_id: File identifier
            
        Returns:
            int: Number of chunks deleted
            
        Raises:
            RuntimeError: If deletion fails
        """
        try:
            collection = self.get_or_create_collection(project_id)
            
            # Get all chunks for this file
            results = collection.get(
                where={"file_id": file_id}
            )
            
            if not results['ids']:
                logger.info(f"No chunks found for file {file_id} in project {project_id}")
                return 0
            
            # Delete chunks
            collection.delete(ids=results['ids'])
            
            deleted_count = len(results['ids'])
            logger.info(
                f"Deleted {deleted_count} chunks for file {file_id} from project {project_id}"
            )
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error deleting chunks from ChromaDB: {e}", exc_info=True)
            raise RuntimeError(f"Failed to delete chunks from ChromaDB: {e}")
    
    def get_collection_stats(self, project_id: str) -> Dict[str, Any]:
        """
        Get statistics about a ChromaDB collection.
        
        Args:
            project_id: Project identifier
            
        Returns:
            Dict: Collection statistics (count, files, etc.)
            
        Raises:
            RuntimeError: If stats retrieval fails
        """
        try:
            collection = self.get_or_create_collection(project_id)
            
            # Get all documents to calculate stats
            results = collection.get()
            
            count = len(results['ids']) if results['ids'] else 0
            
            # Get unique file IDs
            file_ids = set()
            if results['metadatas']:
                for metadata in results['metadatas']:
                    if metadata and 'file_id' in metadata:
                        file_ids.add(metadata['file_id'])
            
            stats = {
                "project_id": project_id,
                "collection_name": f"{self.collection_prefix}{project_id}",
                "total_chunks": count,
                "unique_files": len(file_ids),
                "file_ids": list(file_ids)
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}", exc_info=True)
            raise RuntimeError(f"Failed to get collection stats: {e}")

