"""
Embedding Service

This module provides embedding generation and management capabilities
for the RAG (Retrieval-Augmented Generation) system.
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

import numpy as np
from sentence_transformers import SentenceTransformer
import torch
from loguru import logger

from app.config import settings
from app.core.exceptions import EmbeddingError
from app.utils.metrics import record_embedding_generation, record_embedding_batch


class EmbeddingModel(str, Enum):
    """Supported embedding models."""
    ALL_MINILM_L6_V2 = "all-MiniLM-L6-v2"
    ALL_MPNET_BASE_V2 = "all-mpnet-base-v2"
    MULTI_QA_MINILM_L6_COS_V1 = "multi-qa-MiniLM-L6-cos-v1"
    PARAPHRASE_MULTILINGUAL_MINILM_L12_V2 = "paraphrase-multilingual-MiniLM-L12-v2"


@dataclass
class EmbeddingRequest:
    """Embedding generation request."""
    texts: List[str]
    model: Optional[str] = None
    normalize: bool = True
    batch_size: int = 32


@dataclass
class EmbeddingResponse:
    """Embedding generation response."""
    embeddings: List[List[float]]
    model: str
    dimensions: int
    generation_time: float
    metadata: Dict[str, Any]


class EmbeddingService:
    """
    Service for generating and managing text embeddings.
    
    Supports multiple embedding models with batch processing and caching.
    """
    
    def __init__(self):
        """Initialize embedding service."""
        self.models: Dict[str, SentenceTransformer] = {}
        self.default_model = settings.EMBEDDING_MODEL
        self.device = self._get_device()
        self._load_models()
        
    def _get_device(self) -> str:
        """Get the best available device for embedding generation."""
        if torch.cuda.is_available() and settings.USE_GPU:
            return "cuda"
        elif torch.backends.mps.is_available() and settings.USE_MPS:
            return "mps"
        else:
            return "cpu"
    
    def _load_models(self):
        """Load embedding models."""
        try:
            # Load default model
            if self.default_model:
                self.models[self.default_model] = SentenceTransformer(
                    self.default_model, 
                    device=self.device
                )
                logger.info(f"Loaded embedding model: {self.default_model} on {self.device}")
            
            # Load additional models if specified
            additional_models = settings.ADDITIONAL_EMBEDDING_MODELS
            if additional_models:
                for model_name in additional_models:
                    if model_name not in self.models:
                        self.models[model_name] = SentenceTransformer(
                            model_name, 
                            device=self.device
                        )
                        logger.info(f"Loaded additional embedding model: {model_name}")
                        
        except Exception as e:
            logger.error(f"Failed to load embedding models: {e}")
            raise EmbeddingError(f"Model loading failed: {e}")
    
    async def generate_embeddings(
        self, 
        request: EmbeddingRequest
    ) -> EmbeddingResponse:
        """
        Generate embeddings for the given texts.
        
        Args:
            request: Embedding generation request
            
        Returns:
            EmbeddingResponse with embeddings and metadata
            
        Raises:
            EmbeddingError: If embedding generation fails
        """
        try:
            start_time = time.time()
            
            model_name = request.model or self.default_model
            if model_name not in self.models:
                raise EmbeddingError(f"Model {model_name} not loaded")
            
            model = self.models[model_name]
            
            # Generate embeddings
            embeddings = await self._generate_embeddings_async(
                model, 
                request.texts, 
                request.normalize, 
                request.batch_size
            )
            
            generation_time = time.time() - start_time
            
            # Record metrics
            await record_embedding_generation(
                request_id="embedding_" + str(hash(tuple(request.texts))),
                model=model_name, 
                text_length=len(request.texts), 
                duration=generation_time,
                success=True
            )
            
            logger.info(f"Generated embeddings for {len(request.texts)} texts in {generation_time:.2f}s")
            
            return EmbeddingResponse(
                embeddings=embeddings.tolist() if isinstance(embeddings, np.ndarray) else embeddings,
                model=model_name,
                dimensions=embeddings.shape[1] if hasattr(embeddings, 'shape') else len(embeddings[0]),
                generation_time=generation_time,
                metadata={
                    "device": self.device,
                    "normalized": request.normalize,
                    "batch_size": request.batch_size
                }
            )
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise EmbeddingError(f"Embedding generation failed: {e}")
    
    async def _generate_embeddings_async(
        self,
        model: SentenceTransformer,
        texts: List[str],
        normalize: bool = True,
        batch_size: int = 32
    ) -> np.ndarray:
        """
        Generate embeddings asynchronously.
        
        Args:
            model: SentenceTransformer model
            texts: List of texts to embed
            normalize: Whether to normalize embeddings
            batch_size: Batch size for processing
            
        Returns:
            Numpy array of embeddings
        """
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        
        def _generate():
            try:
                embeddings = model.encode(
                    texts,
                    batch_size=batch_size,
                    normalize_embeddings=normalize,
                    show_progress_bar=False
                )
                return embeddings
            except Exception as e:
                logger.error(f"Embedding generation in thread failed: {e}")
                raise
        
        return await loop.run_in_executor(None, _generate)
    
    async def generate_single_embedding(
        self, 
        text: str, 
        model: Optional[str] = None
    ) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            model: Model to use (defaults to default model)
            
        Returns:
            List of embedding values
        """
        request = EmbeddingRequest(texts=[text], model=model)
        response = await self.generate_embeddings(request)
        return response.embeddings[0]
    
    async def generate_batch_embeddings(
        self,
        texts: List[str],
        model: Optional[str] = None,
        batch_size: int = 32
    ) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts.
        
        Args:
            texts: List of texts to embed
            model: Model to use (defaults to default model)
            batch_size: Batch size for processing
            
        Returns:
            List of embedding lists
        """
        request = EmbeddingRequest(
            texts=texts,
            model=model,
            batch_size=batch_size
        )
        response = await self.generate_embeddings(request)
        return response.embeddings
    
    def compute_similarity(
        self, 
        embedding1: List[float], 
        embedding2: List[float]
    ) -> float:
        """
        Compute cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            
        Returns:
            Cosine similarity score
        """
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Normalize vectors
            vec1_norm = vec1 / np.linalg.norm(vec1)
            vec2_norm = vec2 / np.linalg.norm(vec2)
            
            # Compute cosine similarity
            similarity = np.dot(vec1_norm, vec2_norm)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Similarity computation failed: {e}")
            return 0.0
    
    def compute_similarities(
        self, 
        query_embedding: List[float], 
        document_embeddings: List[List[float]]
    ) -> List[float]:
        """
        Compute similarities between query and multiple documents.
        
        Args:
            query_embedding: Query embedding
            document_embeddings: List of document embeddings
            
        Returns:
            List of similarity scores
        """
        similarities = []
        for doc_embedding in document_embeddings:
            similarity = self.compute_similarity(query_embedding, doc_embedding)
            similarities.append(similarity)
        return similarities
    
    async def get_model_info(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get information about an embedding model.
        
        Args:
            model_name: Model name (defaults to default model)
            
        Returns:
            Model information
        """
        model_name = model_name or self.default_model
        
        if model_name not in self.models:
            return {"error": f"Model {model_name} not loaded"}
        
        model = self.models[model_name]
        
        # Test embedding to get dimensions
        test_text = "test"
        test_embedding = await self.generate_single_embedding(test_text, model_name)
        
        return {
            "model_name": model_name,
            "device": self.device,
            "dimensions": len(test_embedding),
            "max_sequence_length": model.max_seq_length,
            "loaded": True
        }
    
    def get_loaded_models(self) -> List[str]:
        """Get list of loaded model names."""
        return list(self.models.keys())
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of embedding service.
        
        Returns:
            Health status
        """
        try:
            # Test embedding generation
            test_text = "Health check test"
            test_embedding = await self.generate_single_embedding(test_text)
            
            # Test similarity computation
            test_embedding2 = await self.generate_single_embedding("Another test")
            similarity = self.compute_similarity(test_embedding, test_embedding2)
            
            return {
                "status": "healthy",
                "default_model": self.default_model,
                "loaded_models": self.get_loaded_models(),
                "device": self.device,
                "test_embedding": {
                    "success": True,
                    "dimensions": len(test_embedding),
                    "similarity_test": similarity > 0
                }
            }
            
        except Exception as e:
            logger.error(f"Embedding service health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def close(self):
        """Close embedding service and free resources."""
        try:
            # Clear models to free memory
            for model_name in list(self.models.keys()):
                del self.models[model_name]
            
            # Clear CUDA cache if using GPU
            if self.device == "cuda" and torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            logger.info("Embedding service closed")
            
        except Exception as e:
            logger.warning(f"Error closing embedding service: {e}") 