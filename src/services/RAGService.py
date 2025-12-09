"""
RAG Service for orchestrating the complete RAG pipeline.
Combines vector search with LLM to generate context-aware responses.
"""
from typing import List, Dict, Any, Optional
from helpers import get_settings
from services import EmbeddingService, VectorDBService, LLMService
import logging

logger = logging.getLogger(__name__)


class RAGService:
    """
    Service for orchestrating the RAG (Retrieval-Augmented Generation) pipeline.
    Combines vector similarity search with LLM to generate intelligent responses.
    """
    
    def __init__(self):
        """Initialize all required services for RAG pipeline."""
        self.settings = get_settings()
        self.embedding_service = EmbeddingService()
        self.vector_db_service = VectorDBService()
        
        # Initialize LLM service (may not be available if API key missing)
        try:
            self.llm_service = LLMService()
            self.llm_available = self.llm_service.is_available()
            if not self.llm_available:
                logger.warning("LLM service is not available - chat will return search results only")
        except Exception as e:
            logger.warning(f"LLM service initialization failed: {e} - chat will return search results only")
            self.llm_service = None
            self.llm_available = False
        
        self.context_chunks = self.settings.RAG_CONTEXT_CHUNKS
        self.similarity_threshold = self.settings.RAG_SIMILARITY_THRESHOLD
        
        logger.info(f"RAGService initialized (LLM available: {self.llm_available})")
    
    def retrieve_context(
        self,
        project_id: str,
        query: str,
        top_k: Optional[int] = None,
        file_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant context chunks for a query.
        
        Args:
            project_id: Project identifier
            query: User query/question
            top_k: Number of chunks to retrieve (overrides default)
            file_id: Optional file filter
            
        Returns:
            List[Dict]: List of relevant chunks with metadata
        """
        if not query or not query.strip():
            logger.warning("Empty query provided")
            return []
        
        try:
            # Generate query embedding
            logger.info(f"Generating embedding for query: '{query[:50]}...'")
            query_embedding = self.embedding_service.generate_embedding(query.strip())
            
            # Determine top_k
            search_top_k = top_k if top_k is not None else self.context_chunks
            
            # Search for similar chunks
            logger.info(f"Searching for {search_top_k} similar chunks in project {project_id}")
            results = self.vector_db_service.search_similar(
                project_id=project_id,
                query_embedding=query_embedding,
                top_k=search_top_k,
                file_id=file_id
            )
            logger.info(f"VectorDB returned {len(results)} results before filtering")
            
            # Filter by similarity threshold if configured (threshold > 0)
            # Note: ChromaDB uses cosine distance (0-2 range, lower is better)
            # For cosine distance: similarity ≈ 1 - distance (but distance can be > 1)
            if self.similarity_threshold > 0 and results:
                filtered_results = []
                for result in results:
                    distance = result.get("distance")
                    if distance is None:
                        logger.warning(f"Distance is None for chunk {result.get('chunk_id', 'unknown')}, defaulting to 1.0")
                        distance = 1.0
                    # For cosine distance: convert to similarity score
                    # Distance 0 = perfect match (similarity 1.0)
                    # Distance 1 = orthogonal (similarity 0.0)
                    # Distance 2 = opposite (similarity -1.0)
                    similarity = max(0.0, min(1.0, 1.0 - distance))  # Clamp to 0-1 range
                    
                    if similarity >= self.similarity_threshold:
                        result["similarity"] = similarity
                        result["distance"] = distance  # Keep original distance
                        filtered_results.append(result)
                    else:
                        logger.debug(f"Filtered out chunk with similarity {similarity:.3f} (threshold: {self.similarity_threshold}, distance: {distance:.3f})")
                
                results = filtered_results
                logger.info(f"Filtered to {len(results)} chunks above similarity threshold {self.similarity_threshold}")
            else:
                # No threshold filtering - add similarity scores for all results
                for result in results:
                    distance = result.get("distance")
                    if distance is None:
                        logger.warning(f"Distance is None for chunk {result.get('chunk_id', 'unknown')}, defaulting to 1.0")
                        distance = 1.0
                    # ChromaDB uses cosine distance: 0 = identical, 1 = orthogonal, 2 = opposite
                    # Convert to similarity: similarity = 1 - distance (clamped to 0-1)
                    similarity = max(0.0, min(1.0, 1.0 - distance))
                    result["similarity"] = similarity
                    result["distance"] = distance  # Keep original distance for debugging
                    logger.debug(f"Chunk similarity: {similarity:.3f} (distance: {distance:.3f})")
                logger.info(f"Using all {len(results)} retrieved chunks (no similarity threshold)")
            
            logger.info(f"Retrieved {len(results)} relevant chunks")
            return results
            
        except Exception as e:
            logger.error(f"Error retrieving context: {e}", exc_info=True)
            raise RuntimeError(f"Failed to retrieve context: {str(e)}")
    
    def format_sources(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Format chunk metadata as source citations.
        
        Args:
            chunks: List of chunk dictionaries from vector search
            
        Returns:
            List[Dict]: Formatted source citations
        """
        sources = []
        for idx, chunk in enumerate(chunks, start=1):
            metadata = chunk.get("metadata", {})
            source = {
                "source_index": idx,
                "file_id": metadata.get("file_id", "unknown"),
                "chunk_order": metadata.get("chunk_order", 0),
                "chunk_text": chunk.get("chunk_text", "")[:200] + "..." if len(chunk.get("chunk_text", "")) > 200 else chunk.get("chunk_text", ""),
                "similarity": chunk.get("similarity", 0.0) if "similarity" in chunk else (max(0.0, 1.0 - chunk.get("distance", 1.0)) if chunk.get("distance") is not None else 0.0)
            }
            sources.append(source)
        
        return sources
    
    def generate_answer(
        self,
        project_id: str,
        query: str,
        file_id: Optional[str] = None,
        top_k: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Complete RAG pipeline: retrieve context and generate answer.
        
        Args:
            project_id: Project identifier
            query: User query/question
            file_id: Optional file filter
            top_k: Optional override for number of context chunks
            
        Returns:
            Dict: Answer, sources, and metadata
            
        Raises:
            RuntimeError: If RAG pipeline fails
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        try:
            # Step 1: Retrieve relevant context
            logger.info(f"Starting RAG pipeline for query: '{query[:50]}...'")
            chunks = self.retrieve_context(
                project_id=project_id,
                query=query,
                top_k=top_k,
                file_id=file_id
            )
            
            if not chunks:
                logger.warning(f"No relevant chunks found for query: '{query}'")
                logger.warning("This might be due to:")
                logger.warning("1. No documents processed for this project")
                logger.warning("2. Similarity threshold too high (if enabled)")
                logger.warning("3. Query embedding mismatch with document embeddings")
                return {
                    "answer": "I couldn't find any relevant information in the documents to answer your question. Please try rephrasing your query or ensure documents have been processed.",
                    "sources": [],
                    "query": query,
                    "chunks_retrieved": 0,
                    "debug_info": "No chunks retrieved. Check if documents were processed and embeddings were stored."
                }
            
            # Step 2: Format sources
            sources = self.format_sources(chunks)
            
            # Step 3: Extract chunk texts for prompt
            context_texts = [chunk.get("chunk_text", "") for chunk in chunks]
            
            # Step 4: Check if LLM is available before building prompt
            if not self.llm_available or self.llm_service is None:
                logger.warning("LLM not available - returning search results only")
                return {
                    "answer": None,
                    "search_results": sources,
                    "query": query,
                    "chunks_retrieved": len(chunks),
                    "error": "OpenAI API key is not configured. Please set OPENAI_API_KEY in your .env file to enable AI chat responses."
                }
            
            # Step 5: Build RAG prompt
            logger.info("Building RAG prompt with context")
            prompt = self.llm_service.build_rag_prompt(
                query=query,
                context_chunks=context_texts,
                sources=sources
            )
            
            # Step 6: Generate answer using LLM
            logger.info("Generating answer using LLM")
            try:
                answer = self.llm_service.generate_response(prompt)
            except Exception as e:
                logger.error(f"LLM generation failed: {e}", exc_info=True)
                # Graceful degradation: return search results without LLM answer
                logger.warning("Falling back to search results only (LLM unavailable)")
                return {
                    "answer": None,
                    "search_results": sources,
                    "sources": sources,  # Include sources in both fields for consistency
                    "query": query,
                    "chunks_retrieved": len(chunks),
                    "error": f"LLM generation failed: {str(e)}",
                    "warning": "LLM generation failed, returning search results only"
                }
            
            logger.info("RAG pipeline completed successfully")
            
            return {
                "answer": answer,
                "sources": sources,
                "search_results": sources,  # Include for consistency
                "query": query,
                "chunks_retrieved": len(chunks)
            }
            
        except Exception as e:
            logger.error(f"Error in RAG pipeline: {e}", exc_info=True)
            raise RuntimeError(f"RAG pipeline failed: {str(e)}")

