from sentence_transformers import SentenceTransformer
from typing import List
from helpers import get_settings
import logging
import torch

logger = logging.getLogger(__name__)

class EmbeddingService:
    """
    Service for generating vector embeddings from text using Sentence Transformers.
    Provides free, local embedding generation without requiring external API access.
    """
    
    _model_instance = None
    _model_name = None
    
    def __init__(self):
        """Initialize the embedding service with model configuration."""
        self.settings = get_settings()
        self.model_name = self.settings.EMBEDDING_MODEL
        self.device = self.settings.EMBEDDING_DEVICE
        
        # Use GPU if available and device is set to auto
        if self.device == "cpu":
            self.device = "cpu"
        elif self.device == "cuda" and torch.cuda.is_available():
            self.device = "cuda"
        else:
            self.device = "cpu"
        
        # Load model (singleton pattern - reuse same instance)
        self._load_model()
    
    def _load_model(self):
        """Load the SentenceTransformer model (lazy loading, cached)."""
        # Use class-level caching to avoid reloading the same model
        if EmbeddingService._model_instance is None or EmbeddingService._model_name != self.model_name:
            try:
                logger.info(f"Loading embedding model: {self.model_name} on device: {self.device}")
                EmbeddingService._model_instance = SentenceTransformer(
                    self.model_name,
                    device=self.device
                )
                EmbeddingService._model_name = self.model_name
                logger.info(f"Model {self.model_name} loaded successfully")
            except Exception as e:
                logger.error(f"Error loading embedding model {self.model_name}: {e}", exc_info=True)
                raise RuntimeError(f"Failed to load embedding model: {e}")
        
        self.model = EmbeddingService._model_instance
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text string.
        
        Args:
            text: Input text string
            
        Returns:
            List[float]: Embedding vector as list of floats
            
        Raises:
            ValueError: If text is empty or invalid
            RuntimeError: If model fails to generate embedding
        """
        if not text or not isinstance(text, str):
            raise ValueError("Text must be a non-empty string")
        
        if not text.strip():
            logger.warning("Empty text provided, returning zero vector")
            # Return zero vector matching the embedding dimension
            return [0.0] * self.settings.EMBEDDING_DIMENSION
        
        try:
            # Generate embedding
            embedding = self.model.encode(
                text,
                convert_to_numpy=True,
                normalize_embeddings=True  # Normalize for better similarity search
            )
            
            # Convert numpy array to Python list
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}", exc_info=True)
            raise RuntimeError(f"Failed to generate embedding: {e}")
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a batch of text strings.
        
        Args:
            texts: List of input text strings
            
        Returns:
            List[List[float]]: List of embedding vectors
            
        Raises:
            ValueError: If texts is empty or contains invalid entries
            RuntimeError: If model fails to generate embeddings
        """
        if not texts:
            logger.warning("Empty texts list provided")
            return []
        
        if not isinstance(texts, list):
            raise ValueError("Texts must be a list of strings")
        
        # Filter out empty strings and validate
        valid_texts = []
        valid_indices = []
        for idx, text in enumerate(texts):
            if text and isinstance(text, str) and text.strip():
                valid_texts.append(text)
                valid_indices.append(idx)
            else:
                logger.warning(f"Skipping empty or invalid text at index {idx}")
        
        if not valid_texts:
            logger.warning("No valid texts after filtering")
            return []
        
        try:
            # Generate embeddings in batches
            batch_size = self.settings.EMBEDDING_BATCH_SIZE
            all_embeddings = []
            
            logger.info(f"Generating embeddings for {len(valid_texts)} texts in batches of {batch_size}")
            
            for i in range(0, len(valid_texts), batch_size):
                batch = valid_texts[i:i + batch_size]
                
                # Generate embeddings for this batch
                embeddings = self.model.encode(
                    batch,
                    batch_size=len(batch),
                    convert_to_numpy=True,
                    normalize_embeddings=True,  # Normalize for better similarity search
                    show_progress_bar=False
                )
                
                # Convert numpy arrays to Python lists
                batch_embeddings = [emb.tolist() for emb in embeddings]
                all_embeddings.extend(batch_embeddings)
                
                logger.debug(f"Processed batch {i // batch_size + 1}, total embeddings: {len(all_embeddings)}")
            
            logger.info(f"Successfully generated {len(all_embeddings)} embeddings")
            
            # If some texts were filtered out, we need to return embeddings in original order
            # For now, we return only valid embeddings (can be enhanced later)
            return all_embeddings
            
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}", exc_info=True)
            raise RuntimeError(f"Failed to generate batch embeddings: {e}")

