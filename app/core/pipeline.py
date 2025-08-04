"""
Main processing pipeline for HealthLang AI MVP
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

from app.config import settings
from app.core.exceptions import (
    HealthLangException,
    TranslationError,
    MedicalAnalysisError,
    RAGError,
)
from app.services.translation.translator import TranslationService
from app.services.medical.llm_client import LLMClient
from app.services.rag.vector_store import VectorStore
from app.services.rag.retriever import RAGRetriever
from app.services.medical.medical_analyzer import MedicalAnalyzer
from app.services.medical.response_formatter import ResponseFormatter
from app.utils.logger import get_logger
from app.utils.metrics import record_pipeline_metrics
from app.utils.cache import Cache

logger = get_logger(__name__)


@dataclass
class QueryContext:
    """Context for processing a medical query"""
    original_text: str
    source_language: str
    target_language: str
    translated_text: Optional[str] = None
    retrieved_documents: Optional[List[Dict[str, Any]]] = None
    medical_analysis: Optional[Dict[str, Any]] = None
    final_response: Optional[str] = None
    processing_time: Optional[float] = None
    request_id: Optional[str] = None
    timestamp: Optional[datetime] = None


class MedicalQueryPipeline:
    """
    Main pipeline for processing medical queries with translation and RAG
    """
    
    def __init__(self):
        self.translation_service: Optional[TranslationService] = None
        self.llm_client: Optional[LLMClient] = None
        self.vector_store: Optional[VectorStore] = None
        self.retriever: Optional[RAGRetriever] = None
        self.medical_analyzer: Optional[MedicalAnalyzer] = None
        self.response_formatter: Optional[ResponseFormatter] = None
        self.cache: Optional[Cache] = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize all pipeline components"""
        if self._initialized:
            return
        
        logger.info("Initializing MedicalQueryPipeline...")
        
        try:
            # Initialize services
            self.translation_service = TranslationService()
            await self.translation_service.initialize()
            
            self.llm_client = LLMClient()
            await self.llm_client.initialize()
            
            self.vector_store = VectorStore()
            await self.vector_store.initialize()
            
            self.retriever = RAGRetriever(self.vector_store)
            await self.retriever.initialize()
            
            self.medical_analyzer = MedicalAnalyzer(self.llm_client)
            await self.medical_analyzer.initialize()
            
            self.response_formatter = ResponseFormatter()
            await self.response_formatter.initialize()
            
            self.cache = Cache()
            await self.cache.initialize()
            
            self._initialized = True
            logger.info("MedicalQueryPipeline initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize MedicalQueryPipeline: {e}")
            raise HealthLangException(f"Pipeline initialization failed: {e}")
    
    async def cleanup(self) -> None:
        """Cleanup pipeline resources"""
        logger.info("Cleaning up MedicalQueryPipeline...")
        
        cleanup_tasks = []
        
        if self.translation_service:
            cleanup_tasks.append(self.translation_service.cleanup())
        if self.llm_client:
            cleanup_tasks.append(self.llm_client.cleanup())
        if self.vector_store:
            cleanup_tasks.append(self.vector_store.cleanup())
        if self.retriever:
            cleanup_tasks.append(self.retriever.cleanup())
        if self.medical_analyzer:
            cleanup_tasks.append(self.medical_analyzer.cleanup())
        if self.response_formatter:
            cleanup_tasks.append(self.response_formatter.cleanup())
        if self.cache:
            cleanup_tasks.append(self.cache.cleanup())
        
        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        
        self._initialized = False
        logger.info("MedicalQueryPipeline cleanup completed")
    
    async def process_query(
        self,
        text: str,
        source_language: str = "en",
        target_language: Optional[str] = None,
        request_id: Optional[str] = None,
        use_cache: bool = True,
        translate_response: bool = False,
    ) -> Dict[str, Any]:
        """
        Process a medical query through the complete pipeline
        
        Args:
            text: The input text (medical question)
            source_language: Source language code (en, yo)
            target_language: Target language code (en, yo) - if None, matches source_language
            request_id: Unique request identifier
            use_cache: Whether to use caching
            translate_response: Whether to translate the response (optional translation)
            
        Returns:
            Dictionary containing the processed response
        """
        if not self._initialized:
            await self.initialize()
        
        start_time = datetime.now()
        
        # Set target language to match source if not specified
        if target_language is None:
            target_language = source_language
        
        context = QueryContext(
            original_text=text,
            source_language=source_language,
            target_language=target_language,
            request_id=request_id,
            timestamp=start_time,
        )
        
        try:
            logger.info(f"Processing query: {text[:100]}... (ID: {request_id})")
            
            # Check cache first
            if use_cache:
                cached_result = await self._check_cache(context)
                if cached_result:
                    logger.info(f"Cache hit for request {request_id}")
                    return cached_result
            
            # Step 1: Language detection and translation (only if different languages)
            await self._translate_query(context)
            
            # Step 2: RAG retrieval (if enabled)
            if settings.RAG_ENABLED:
                await self._retrieve_relevant_documents(context)
            
            # Step 3: Medical analysis
            await self._analyze_medical_query(context)
            
            # Step 4: Response formatting and optional translation
            await self._format_response(context, translate_response)
            
            # Step 5: Cache the result
            if use_cache:
                await self._cache_result(context)
            
            # Calculate processing time
            context.processing_time = (datetime.now() - start_time).total_seconds()
            
            # Record metrics
            await record_pipeline_metrics(context)
            
            logger.info(f"Query processed successfully in {context.processing_time:.2f}s (ID: {request_id})")
            
            return self._build_response(context)
            
        except Exception as e:
            logger.error(f"Error processing query (ID: {request_id}): {e}", exc_info=True)
            context.processing_time = (datetime.now() - start_time).total_seconds()
            raise
    
    async def _check_cache(self, context: QueryContext) -> Optional[Dict[str, Any]]:
        """Check if result exists in cache"""
        cache_key = self._generate_cache_key(context)
        return await self.cache.get(cache_key)
    
    async def _cache_result(self, context: QueryContext) -> None:
        """Cache the processing result"""
        cache_key = self._generate_cache_key(context)
        result = self._build_response(context)
        await self.cache.set(cache_key, result, ttl=settings.CACHE_TTL)
    
    def _generate_cache_key(self, context: QueryContext) -> str:
        """Generate cache key for the query"""
        import hashlib
        key_data = f"{context.original_text}:{context.source_language}:{context.target_language}"
        return f"medical_query:{hashlib.md5(key_data.encode()).hexdigest()}"
    
    async def _translate_query(self, context: QueryContext) -> None:
        """Translate the query if needed"""
        try:
            if context.source_language != context.target_language:
                logger.debug(f"Translating from {context.source_language} to {context.target_language}")
                context.translated_text = await self.translation_service.translate(
                    text=context.original_text,
                    source_language=context.source_language,
                    target_language=context.target_language,
                )
            else:
                context.translated_text = context.original_text
                
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            raise TranslationError(f"Failed to translate query: {e}")
    
    async def _retrieve_relevant_documents(self, context: QueryContext) -> None:
        """Retrieve relevant medical documents using RAG"""
        try:
            query_text = context.translated_text or context.original_text
            logger.debug(f"Retrieving documents for query: {query_text[:100]}...")
            
            context.retrieved_documents = await self.retriever.retrieve(
                query=query_text,
                max_docs=settings.MAX_RETRIEVAL_DOCS,
                similarity_threshold=settings.SIMILARITY_THRESHOLD,
            )
            
            logger.debug(f"Retrieved {len(context.retrieved_documents)} documents")
            
        except Exception as e:
            logger.error(f"Document retrieval failed: {e}")
            raise RAGError(f"Failed to retrieve relevant documents: {e}")
    
    async def _analyze_medical_query(self, context: QueryContext) -> None:
        """Analyze the medical query using LLM"""
        try:
            query_text = context.translated_text or context.original_text
            logger.debug(f"Analyzing medical query: {query_text[:100]}...")
            
            # Prepare context for LLM
            llm_context = self._prepare_llm_context(context)
            
            context.medical_analysis = await self.medical_analyzer.analyze(
                query=query_text,
                context=llm_context,
                max_tokens=settings.MAX_TOKENS,
                temperature=settings.TEMPERATURE,
                top_p=settings.TOP_P,
            )
            
            logger.debug("Medical analysis completed")
            
        except Exception as e:
            logger.error(f"Medical analysis failed: {e}")
            raise MedicalAnalysisError(f"Failed to analyze medical query: {e}")
    
    def _prepare_llm_context(self, context: QueryContext) -> str:
        """Prepare context for LLM including retrieved documents"""
        if not context.retrieved_documents:
            return ""
        
        context_parts = []
        for i, doc in enumerate(context.retrieved_documents, 1):
            context_parts.append(f"Document {i}: {doc.get('content', '')}")
        
        return "\n\n".join(context_parts)
    
    async def _format_response(self, context: QueryContext, translate_response: bool = False) -> None:
        """Format and optionally translate the final response"""
        try:
            if not context.medical_analysis:
                raise MedicalAnalysisError("No medical analysis available for response formatting")
            
            # Format the response in the source language first
            formatted_response = await self.response_formatter.format(
                analysis=context.medical_analysis,
                target_language=context.source_language,
            )
            
            # Apply optional translation if requested
            if translate_response and context.target_language != context.source_language:
                logger.debug(f"Translating response from {context.source_language} to {context.target_language}")
                context.final_response = await self.translation_service.translate(
                    text=formatted_response,
                    source_language=context.source_language,
                    target_language=context.target_language,
                )
            else:
                # Keep response in the same language as the query
                context.final_response = formatted_response
            
            logger.debug("Response formatting completed")
            
        except Exception as e:
            logger.error(f"Response formatting failed: {e}")
            raise HealthLangException(f"Failed to format response: {e}")
    
    def _build_response(self, context: QueryContext) -> Dict[str, Any]:
        """Build the final response dictionary"""
        return {
            "request_id": context.request_id,
            "original_query": context.original_text,
            "source_language": context.source_language,
            "target_language": context.target_language,
            "translated_query": context.translated_text,
            "response": context.final_response,
            "processing_time": context.processing_time,
            "timestamp": context.timestamp.isoformat() if context.timestamp else None,
            "metadata": {
                "rag_enabled": settings.RAG_ENABLED,
                "documents_retrieved": len(context.retrieved_documents) if context.retrieved_documents else 0,
                "model_used": settings.MEDICAL_MODEL_NAME,
                "cache_hit": False,  # TODO: Track cache hits
            },
            "sources": [
                {
                    "title": doc.get("title", "Unknown"),
                    "url": doc.get("url", ""),
                    "relevance_score": doc.get("score", 0.0),
                }
                for doc in (context.retrieved_documents or [])
            ],
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all pipeline components"""
        health_status = {
            "status": "healthy",
            "components": {},
            "timestamp": datetime.now().isoformat(),
        }
        
        try:
            # Check translation service
            if self.translation_service:
                health_status["components"]["translation"] = await self.translation_service.health_check()
            else:
                health_status["components"]["translation"] = {"status": "not_initialized"}
            
            # Check LLM client
            if self.llm_client:
                health_status["components"]["llm"] = await self.llm_client.health_check()
            else:
                health_status["components"]["llm"] = {"status": "not_initialized"}
            
            # Check vector store
            if self.vector_store:
                health_status["components"]["vector_store"] = await self.vector_store.health_check()
            else:
                health_status["components"]["vector_store"] = {"status": "not_initialized"}
            
            # Check cache
            if self.cache:
                health_status["components"]["cache"] = await self.cache.health_check()
            else:
                health_status["components"]["cache"] = {"status": "not_initialized"}
            
            # Overall status
            all_healthy = all(
                comp.get("status") == "healthy" 
                for comp in health_status["components"].values()
            )
            
            if not all_healthy:
                health_status["status"] = "degraded"
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)
        
        return health_status 