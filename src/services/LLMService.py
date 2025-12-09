"""
LLM Service for OpenAI integration.
Handles LLM API calls and prompt building for RAG.
"""
from openai import OpenAI
from typing import Optional, List, Dict
from helpers import get_settings
import logging

logger = logging.getLogger(__name__)


class LLMService:
    """
    Service for interacting with OpenAI LLM API.
    Provides methods for generating responses and building RAG prompts.
    """
    
    _client_instance = None
    
    def __init__(self):
        """Initialize OpenAI client with API key from settings."""
        self.settings = get_settings()
        self.api_key = getattr(self.settings, 'OPENAI_API_KEY', '') or ""
        self.model = self.settings.LLM_MODEL
        self.temperature = self.settings.LLM_TEMPERATURE
        self.max_tokens = self.settings.LLM_MAX_TOKENS
        
        # Initialize availability flag
        self._is_available = False
        self.client = None
        
        # Check if API key is configured
        if not self.api_key or self.api_key.strip() == "":
            logger.warning("OpenAI API key is not configured - LLM features will be unavailable")
            return
        
        # Initialize OpenAI client (singleton pattern)
        if LLMService._client_instance is None:
            try:
                logger.info(f"Initializing OpenAI client with model: {self.model}")
                LLMService._client_instance = OpenAI(api_key=self.api_key)
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing OpenAI client: {e}", exc_info=True)
                self.client = None
                self._is_available = False
                return
        
        self.client = LLMService._client_instance
        self._is_available = True
    
    def is_available(self) -> bool:
        """Check if LLM service is available (API key configured)."""
        return self._is_available and self.client is not None
    
    def generate_response(
        self,
        prompt: str,
        system_message: Optional[str] = None
    ) -> str:
        """
        Generate LLM response from a prompt.
        
        Args:
            prompt: User prompt/question
            system_message: Optional system message to set behavior
            
        Returns:
            str: Generated response text
            
        Raises:
            ValueError: If prompt is empty
            RuntimeError: If API call fails
        """
        if not self.is_available():
            raise ValueError("OpenAI API key is not configured. Please set OPENAI_API_KEY in your .env file.")
        
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")
        
        # Default system message for RAG
        if system_message is None:
            system_message = (
                "You are a helpful assistant that answers questions based on the provided context. "
                "Answer using only the information from the context. If the context doesn't contain "
                "enough information, say so. Cite your sources when referencing specific information."
            )
        
        try:
            logger.info(f"Generating response with model: {self.model}")
            logger.debug(f"Prompt length: {len(prompt)} characters")
            
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            answer = response.choices[0].message.content.strip()
            logger.info(f"Generated response: {len(answer)} characters")
            
            return answer
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error generating LLM response: {error_msg}", exc_info=True)
            
            # Handle specific OpenAI errors
            if "rate_limit" in error_msg.lower() or "429" in error_msg:
                raise RuntimeError("OpenAI API rate limit exceeded. Please try again later.")
            elif "invalid_api_key" in error_msg.lower() or "401" in error_msg:
                raise RuntimeError("Invalid OpenAI API key. Please check your configuration.")
            elif "insufficient_quota" in error_msg.lower():
                raise RuntimeError("OpenAI API quota exceeded. Please check your account.")
            else:
                raise RuntimeError(f"Failed to generate LLM response: {error_msg}")
    
    def build_rag_prompt(
        self,
        query: str,
        context_chunks: List[str],
        sources: List[Dict]
    ) -> str:
        """
        Build RAG prompt with query and context chunks.
        
        Args:
            query: User's question/query
            context_chunks: List of context chunk texts
            sources: List of source metadata dicts (file_id, chunk_order, etc.)
            
        Returns:
            str: Formatted prompt with context and query
        """
        if not context_chunks:
            return f"Question: {query}\n\nI don't have any relevant context to answer this question."
        
        prompt_parts = ["You are a helpful assistant that answers questions based on the provided context.\n"]
        prompt_parts.append("\nContext:\n")
        
        for idx, (chunk_text, source) in enumerate(zip(context_chunks, sources), start=1):
            file_id = source.get("file_id", "unknown")
            chunk_order = source.get("chunk_order", 0)
            similarity = source.get("distance")
            
            prompt_parts.append(f"\n[Context {idx}]\n{chunk_text}\n")
            prompt_parts.append(f"Source: {file_id}, chunk {chunk_order}")
            if similarity is not None:
                prompt_parts.append(f" (similarity: {1 - similarity:.2f})")
            prompt_parts.append("\n")
        
        prompt_parts.append(f"\nQuestion: {query}\n\n")
        prompt_parts.append(
            "Answer the question using only the information from the context above. "
            "If the context doesn't contain enough information, say so. "
            "Cite your sources when referencing specific information (e.g., 'According to Context 1...')."
        )
        
        return "".join(prompt_parts)
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for a text string.
        Rough estimation: ~4 characters per token for English text.
        
        Args:
            text: Input text
            
        Returns:
            int: Estimated token count
        """
        if not text:
            return 0
        
        # Rough estimation: 1 token ≈ 4 characters for English
        # This is a simple heuristic, actual tokenization varies
        return len(text) // 4

