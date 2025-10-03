"""
Tavily-powered general knowledge RAG service

This service uses Tavily Search API with LangChain for real-time
general knowledge queries. It combines search results with ChromaDB
for enhanced context and reliable sources.
"""

import asyncio
import logging
import re
from typing import Dict, Optional, Any

from langchain_tavily import TavilySearch
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import Settings

logger = logging.getLogger(__name__)


class TavilyKnowledgeService:
    """
    Tavily-powered general knowledge service
    
    Combines real-time search with ChromaDB for enhanced context.
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.tavily_search = None
        self.chroma_client = None
        self.collection = None
        self.embedding_model = None
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize Tavily, ChromaDB, and embedding model"""
        try:
            # Initialize Tavily Search
            api_key = self.settings.TAVILY_API_KEY
            if api_key and api_key != "test_api_key_for_development":
                self.tavily_search = TavilySearch(
                    tavily_api_key=self.settings.TAVILY_API_KEY,
                    max_results=5,
                    include_answer=True,
                    include_raw_content=False,
                    include_images=False,
                    search_depth="advanced"  # Better quality, costs 2 credits
                )
                logger.info("Tavily Search initialized successfully")
            else:
                logger.warning(
                    "Tavily API key not configured, "
                    "general knowledge search disabled"
                )
            
            # Initialize ChromaDB for caching and context enhancement
            # Use PersistentClient with unique directory to avoid conflicts
            import os
            tavily_db_path = os.path.join(
                os.path.dirname(self.settings.CHROMA_DB_PATH),
                "tavily_knowledge"
            )
            self.chroma_client = chromadb.PersistentClient(
                path=tavily_db_path,
                settings=ChromaSettings(
                    anonymized_telemetry=False
                )
            )
            
            # Get or create collection for general knowledge
            self.collection = self.chroma_client.get_or_create_collection(
                name="general_knowledge",
                metadata={
                    "description": (
                        "Cached general knowledge from Tavily searches"
                    )
                }
            )
            
            # Initialize embedding model for similarity search
            self.embedding_model = SentenceTransformer(
                self.settings.EMBEDDING_MODEL
            )
            
            logger.info("General knowledge service initialized successfully")
            
        except Exception as e:
            logger.error(
                f"Failed to initialize general knowledge service: {e}"
            )
            self.tavily_search = None
    
    def _is_general_knowledge_query(self, query: str) -> bool:
        """
        Detect if a query requires general knowledge lookup
        
        Args:
            query: User query to analyze
            
        Returns:
            bool: True if query needs general knowledge search
        """
        query_lower = query.lower().strip()
        
        # Patterns that indicate general knowledge queries
        knowledge_patterns = [
            r'\b(who is|who was|who are)\b',
            r'\b(what is|what are|what was|what were)\b',
            r'\b(when did|when was|when were|when do)\b',
            r'\b(where is|where are|where was|where were)\b',
            r'\b(why did|why do|why is|why are)\b',
            r'\b(how does|how do|how did|how to)\b',
            r'\b(tell me about|explain|describe)\b',
            r'\b(current|latest|recent|today|now)\b.*'
            r'\b(president|leader|ceo|news|events)\b',
            r'\b(facts about|information about|details about)\b',
            r'\b(capital of|population of|history of)\b',
            r'\b(definition of|meaning of)\b'
        ]
        
        # Check if query matches knowledge patterns
        for pattern in knowledge_patterns:
            if re.search(pattern, query_lower):
                return True
        
        # Topics that typically require general knowledge
        knowledge_topics = [
            'president', 'politics', 'government', 'election', 'country',
            'capital', 'history', 'biography', 'celebrity', 'company',
            'technology', 'science', 'geography', 'culture', 'sports',
            'entertainment', 'economics', 'finance', 'current events',
            'news', 'world', 'population', 'facts', 'statistics'
        ]
        
        # Check if query contains knowledge topics
        for topic in knowledge_topics:
            if topic in query_lower:
                return True
        
        return False
    
    async def retrieve_knowledge(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve general knowledge using Tavily search
        
        Args:
            query: Search query
            
        Returns:
            Dict with search results and metadata, or None if not applicable
        """
        if not self._is_general_knowledge_query(query):
            logger.debug(
                f"Query '{query}' not identified as general knowledge"
            )
            return None
        
        if not self.tavily_search:
            logger.warning("Tavily search not available")
            return None
        
        try:
            logger.info(f"Performing Tavily search for: {query}")
            
            # Check cache first
            cached_result = await self._check_cache(query)
            if cached_result:
                logger.info("Using cached general knowledge result")
                return cached_result
            
            # Perform Tavily search
            search_result = await asyncio.to_thread(
                self.tavily_search.invoke,
                {"query": query}
            )
            
            if not search_result:
                logger.warning(f"No results from Tavily for query: {query}")
                return None
            
            # Parse Tavily response
            if isinstance(search_result, str):
                # Parse JSON string response
                import json
                try:
                    search_data = json.loads(search_result)
                except json.JSONDecodeError:
                    logger.error("Failed to parse Tavily JSON response")
                    return None
            else:
                search_data = search_result
            
            knowledge_result = {
                "query": query,
                "answer": search_data.get("answer", ""),
                "sources": [],
                "content": [],
                "metadata": {
                    "provider": "tavily",
                    "response_time": search_data.get("response_time", 0),
                    "results_count": len(search_data.get("results", []))
                }
            }
            
            # Process search results
            for result in search_data.get("results", []):
                source = {
                    "type": "web",
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "content": result.get("content", ""),
                    "score": result.get("score", 0.0)
                }
                knowledge_result["sources"].append(source)
                knowledge_result["content"].append(result.get("content", ""))
            
            # Cache the result
            await self._cache_result(query, knowledge_result)
            
            logger.info(f"Retrieved {len(knowledge_result['sources'])} results from Tavily")
            return knowledge_result
            
        except Exception as e:
            logger.error(f"Error in Tavily search: {e}")
            return None
    
    async def _check_cache(self, query: str) -> Optional[Dict[str, Any]]:
        """Check ChromaDB cache for similar queries"""
        if not self.collection or not self.embedding_model:
            return None
        
        try:
            # Generate embedding for query
            query_embedding = self.embedding_model.encode([query])
            
            # Search for similar cached queries
            results = self.collection.query(
                query_embeddings=query_embedding.tolist(),
                n_results=1,
                where={"cached": True}
            )
            
            if results["distances"][0] and results["distances"][0][0] < 0.3:  # High similarity threshold
                # Return cached result
                cached_data = results["metadatas"][0][0]
                if "answer" in cached_data:
                    return {
                        "query": query,
                        "answer": cached_data["answer"],
                        "sources": cached_data.get("sources", []),
                        "content": cached_data.get("content", []),
                        "metadata": {
                            "provider": "tavily_cached",
                            "cache_hit": True
                        }
                    }
        except Exception as e:
            logger.debug(f"Cache check failed: {e}")
        
        return None
    
    async def _cache_result(self, query: str, result: Dict[str, Any]):
        """Cache search result in ChromaDB"""
        if not self.collection or not self.embedding_model:
            return
        
        try:
            # Generate embedding for query
            query_embedding = self.embedding_model.encode([query])
            
            # Store in ChromaDB
            self.collection.add(
                embeddings=query_embedding.tolist(),
                documents=[query],
                metadatas=[{
                    "cached": True,
                    "answer": result["answer"],
                    "sources": result["sources"][:3],  # Limit stored sources
                    "content": result["content"][:3],  # Limit stored content
                    "provider": "tavily"
                }],
                ids=[f"tavily_{hash(query)}"]
            )
            
            logger.debug(f"Cached Tavily result for query: {query}")
            
        except Exception as e:
            logger.debug(f"Failed to cache result: {e}")
    
    def get_search_stats(self) -> Dict[str, Any]:
        """Get statistics about the general knowledge service"""
        stats = {
            "tavily_available": self.tavily_search is not None,
            "chroma_available": self.collection is not None,
            "embedding_model": self.settings.EMBEDDING_MODEL if self.embedding_model else None
        }
        
        if self.collection:
            try:
                count = self.collection.count()
                stats["cached_queries"] = count
            except Exception as e:
                logger.debug(f"Failed to get cache count: {e}")
                stats["cached_queries"] = 0
        
        return stats