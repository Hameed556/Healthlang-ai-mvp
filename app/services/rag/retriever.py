"""
RAG Retriever Service

This module provides the main RAG (Retrieval-Augmented Generation) retrieval
service that orchestrates document retrieval, embedding generation, and search.
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum

from loguru import logger

from app.config import settings
from app.core.exceptions import RAGError, RetrievalError
from app.services.rag.embeddings import EmbeddingService, EmbeddingRequest
from app.services.rag.vector_store import VectorStore, SearchRequest, Document
from app.services.rag.document_processor import DocumentProcessor, ProcessingOptions
from app.utils.metrics import record_rag_retrieval, record_rag_indexing


class RetrievalStrategy(str, Enum):
    """RAG retrieval strategies."""
    SEMANTIC = "semantic"
    HYBRID = "hybrid"
    KEYWORD = "keyword"
    DENSE = "dense"


@dataclass
class RetrievalRequest:
    """RAG retrieval request."""
    query: str
    collection_name: str = "medical_docs"
    top_k: int = 10
    similarity_threshold: float = 0.5
    strategy: RetrievalStrategy = RetrievalStrategy.SEMANTIC
    filter_metadata: Optional[Dict[str, Any]] = None
    include_metadata: bool = True
    rerank_results: bool = False


@dataclass
class RetrievedDocument:
    """Retrieved document with relevance information."""
    document: Document
    similarity_score: float
    rank: int
    retrieval_method: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrievalResponse:
    """RAG retrieval response."""
    documents: List[RetrievedDocument]
    query: str
    total_results: int
    retrieval_time: float
    strategy: RetrievalStrategy
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IndexingRequest:
    """Document indexing request."""
    documents: List[Document]
    collection_name: str = "medical_docs"
    processing_options: Optional[ProcessingOptions] = None
    embedding_model: Optional[str] = None
    batch_size: int = 32


@dataclass
class IndexingResponse:
    """Document indexing response."""
    indexed_documents: int
    collection_name: str
    indexing_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class RAGRetriever:
    """
    Main RAG retrieval service.
    
    Orchestrates document indexing, embedding generation, and similarity search.
    """
    
    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: VectorStore,
        document_processor: DocumentProcessor
    ):
        """
        Initialize RAG retriever.
        
        Args:
            embedding_service: Service for generating embeddings
            vector_store: Service for vector storage and search
            document_processor: Service for document processing
        """
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.document_processor = document_processor
        
    async def retrieve(
        self, 
        request: RetrievalRequest
    ) -> RetrievalResponse:
        """
        Retrieve relevant documents for a query.
        
        Args:
            request: Retrieval request
            
        Returns:
            RetrievalResponse with relevant documents
            
        Raises:
            RetrievalError: If retrieval fails
        """
        try:
            start_time = time.time()
            
            # Generate query embedding
            query_embedding = await self.embedding_service.generate_single_embedding(
                request.query
            )
            
            # Perform vector search
            search_request = SearchRequest(
                query_embedding=query_embedding,
                collection_name=request.collection_name,
                top_k=request.top_k,
                similarity_threshold=request.similarity_threshold,
                filter_metadata=request.filter_metadata
            )
            
            search_response = await self.vector_store.search(search_request)
            
            # Convert to retrieved documents
            retrieved_docs = []
            for result in search_response.results:
                retrieved_doc = RetrievedDocument(
                    document=result.document,
                    similarity_score=result.similarity_score,
                    rank=result.rank,
                    retrieval_method="vector_search",
                    metadata={
                        "search_time": search_response.search_time,
                        "collection": request.collection_name
                    }
                )
                retrieved_docs.append(retrieved_doc)
            
            # Apply reranking if requested
            if request.rerank_results:
                retrieved_docs = await self._rerank_documents(
                    request.query, 
                    retrieved_docs
                )
            
            retrieval_time = time.time() - start_time
            
            # Record metrics
            await record_rag_retrieval(
                request.strategy.value,
                len(retrieved_docs),
                retrieval_time
            )
            
            logger.info(f"RAG retrieval completed in {retrieval_time:.2f}s, found {len(retrieved_docs)} documents")
            
            return RetrievalResponse(
                documents=retrieved_docs,
                query=request.query,
                total_results=len(retrieved_docs),
                retrieval_time=retrieval_time,
                strategy=request.strategy,
                metadata={
                    "embedding_model": self.embedding_service.default_model,
                    "vector_store": self.vector_store.store_type.value,
                    "similarity_threshold": request.similarity_threshold
                }
            )
            
        except Exception as e:
            logger.error(f"RAG retrieval failed: {e}")
            raise RetrievalError(f"RAG retrieval failed: {e}")
    
    async def index_documents(
        self, 
        request: IndexingRequest
    ) -> IndexingResponse:
        """
        Index documents for retrieval.
        
        Args:
            request: Indexing request
            
        Returns:
            IndexingResponse with indexing results
            
        Raises:
            RAGError: If indexing fails
        """
        try:
            start_time = time.time()
            
            # Set default processing options if not provided
            if not request.processing_options:
                request.processing_options = ProcessingOptions()
            
            # Process documents
            processed_chunks = []
            
            for document in request.documents:
                # Process document into chunks
                processed = await self.document_processor.process_document(
                    document, 
                    request.processing_options
                )
                
                # Generate embeddings for chunks
                chunk_texts = [chunk.content for chunk in processed.chunks]
                chunk_embeddings = await self.embedding_service.generate_batch_embeddings(
                    chunk_texts,
                    model=request.embedding_model,
                    batch_size=request.batch_size
                )
                
                # Add embeddings to chunks
                for chunk, embedding in zip(processed.chunks, chunk_embeddings):
                    chunk.embedding = embedding
                    processed_chunks.append(chunk)
            
            # Insert chunks into vector store
            inserted_ids = await self.vector_store.insert_documents(
                processed_chunks,
                collection_name=request.collection_name
            )
            
            indexing_time = time.time() - start_time
            
            # Record metrics
            await record_rag_indexing(
                request.collection_name,
                len(inserted_ids),
                indexing_time
            )
            
            logger.info(f"Indexed {len(inserted_ids)} document chunks in {indexing_time:.2f}s")
            
            return IndexingResponse(
                indexed_documents=len(inserted_ids),
                collection_name=request.collection_name,
                indexing_time=indexing_time,
                metadata={
                    "embedding_model": request.embedding_model or self.embedding_service.default_model,
                    "chunking_strategy": request.processing_options.chunking_strategy.value,
                    "chunk_size": request.processing_options.chunk_size
                }
            )
            
        except Exception as e:
            logger.error(f"Document indexing failed: {e}")
            raise RAGError(f"Document indexing failed: {e}")
    
    async def _rerank_documents(
        self, 
        query: str, 
        documents: List[RetrievedDocument]
    ) -> List[RetrievedDocument]:
        """
        Rerank retrieved documents using additional criteria.
        
        Args:
            query: Original query
            documents: Retrieved documents
            
        Returns:
            Reranked documents
        """
        try:
            # Simple reranking based on multiple factors
            for doc in documents:
                # Calculate additional relevance scores
                content_length_score = self._calculate_length_score(doc.document.content)
                metadata_score = self._calculate_metadata_score(doc.document.metadata, query)
                
                # Combine scores (simple weighted average)
                combined_score = (
                    doc.similarity_score * 0.6 +
                    content_length_score * 0.2 +
                    metadata_score * 0.2
                )
                
                doc.similarity_score = combined_score
                doc.metadata.update({
                    "original_similarity": doc.similarity_score,
                    "length_score": content_length_score,
                    "metadata_score": metadata_score
                })
            
            # Sort by new combined score
            documents.sort(key=lambda x: x.similarity_score, reverse=True)
            
            # Update ranks
            for i, doc in enumerate(documents):
                doc.rank = i + 1
            
            return documents
            
        except Exception as e:
            logger.warning(f"Document reranking failed: {e}")
            return documents
    
    def _calculate_length_score(self, content: str) -> float:
        """Calculate score based on content length."""
        # Prefer medium-length content (not too short, not too long)
        length = len(content)
        
        if length < 50:
            return 0.3  # Too short
        elif length < 500:
            return 1.0  # Ideal length
        elif length < 2000:
            return 0.8  # Good length
        else:
            return 0.5  # Too long
    
    def _calculate_metadata_score(self, metadata: Dict[str, Any], query: str) -> float:
        """Calculate score based on metadata relevance."""
        score = 0.5  # Base score
        
        # Check if query terms appear in metadata
        query_terms = query.lower().split()
        
        for key, value in metadata.items():
            if isinstance(value, str):
                value_lower = value.lower()
                for term in query_terms:
                    if term in value_lower:
                        score += 0.1
        
        # Check for specific metadata fields
        if 'topics' in metadata:
            topics = metadata['topics']
            if isinstance(topics, list):
                for topic in topics:
                    if topic.lower() in query.lower():
                        score += 0.2
        
        if 'language' in metadata:
            # Prefer documents in the same language as query
            # This is a simplified check - in practice, you'd detect query language
            score += 0.1
        
        return min(1.0, score)
    
    async def search_similar_documents(
        self, 
        document_id: str, 
        collection_name: str = "medical_docs",
        top_k: int = 5
    ) -> List[RetrievedDocument]:
        """
        Find documents similar to a given document.
        
        Args:
            document_id: ID of the reference document
            collection_name: Collection to search in
            top_k: Number of similar documents to return
            
        Returns:
            List of similar documents
        """
        try:
            # Get the reference document
            # Note: This would require implementing document retrieval by ID
            # For now, we'll use a placeholder approach
            
            # TODO: Implement document retrieval by ID
            logger.warning("Document retrieval by ID not yet implemented")
            return []
            
        except Exception as e:
            logger.error(f"Similar document search failed: {e}")
            return []
    
    async def get_collection_stats(self, collection_name: str = "medical_docs") -> Dict[str, Any]:
        """
        Get statistics for a collection.
        
        Args:
            collection_name: Collection name
            
        Returns:
            Collection statistics
        """
        try:
            # Get vector store stats
            vector_stats = await self.vector_store.get_collection_stats(collection_name)
            
            # Get embedding model info
            embedding_info = await self.embedding_service.get_model_info()
            
            return {
                "collection_name": collection_name,
                "vector_store_stats": vector_stats,
                "embedding_model": embedding_info,
                "supported_strategies": [strategy.value for strategy in RetrievalStrategy]
            }
            
        except Exception as e:
            logger.error(f"Collection stats retrieval failed: {e}")
            return {"error": str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of RAG retriever.
        
        Returns:
            Health status
        """
        try:
            # Check component health
            embedding_health = await self.embedding_service.health_check()
            vector_health = await self.vector_store.health_check()
            processor_health = await self.document_processor.health_check()
            
            # Test basic retrieval
            test_request = RetrievalRequest(
                query="test query",
                top_k=1
            )
            
            test_response = await self.retrieve(test_request)
            
            return {
                "status": "healthy",
                "components": {
                    "embedding_service": embedding_health,
                    "vector_store": vector_health,
                    "document_processor": processor_health
                },
                "test_retrieval": {
                    "success": True,
                    "documents_found": len(test_response.documents),
                    "retrieval_time": test_response.retrieval_time
                }
            }
            
        except Exception as e:
            logger.error(f"RAG retriever health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def close(self):
        """Close RAG retriever and its components."""
        try:
            await self.embedding_service.close()
            await self.vector_store.close()
            
            logger.info("RAG retriever closed")
            
        except Exception as e:
            logger.warning(f"Error closing RAG retriever: {e}") 