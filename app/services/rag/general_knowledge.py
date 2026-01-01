"""
General Knowledge RAG Service

This module provides RAG capabilities for general knowledge queries by scraping
reliable sources like Wikipedia, BBC News, Reuters, etc.
"""

import asyncio
import aiohttp
import re
import time
import hashlib
from typing import List, Optional
from dataclasses import dataclass
from urllib.parse import quote
from bs4 import BeautifulSoup
from loguru import logger

from app.services.rag.retriever import (
    RAGRetriever, RetrievalResponse
)
from app.services.rag.vector_store import Document
from app.services.medical.llm_client import LLMClient, LLMRequest


@dataclass
class KnowledgeSource:
    """Configuration for a knowledge source."""
    name: str
    base_url: str
    search_endpoint: str
    scrape_endpoint: str
    reliability_score: float
    rate_limit: float = 1.0  # seconds between requests


class GeneralKnowledgeRAG:
    """
    RAG service for general knowledge queries using reliable web sources.
    """
    
    def __init__(self, rag_retriever: RAGRetriever):
        """Initialize general knowledge RAG service."""
        self.rag_retriever = rag_retriever
        self.collection_name = "general_knowledge"
        self.llm_client = LLMClient()
        
        # Configure reliable sources
        self.knowledge_sources = [
            KnowledgeSource(
                name="Wikipedia",
                base_url="https://en.wikipedia.org",
                search_endpoint="/w/api.php?action=opensearch&format=json&search={query}&limit=5",
                scrape_endpoint="/wiki/{title}",
                reliability_score=0.9,
                rate_limit=1.0
            ),
            KnowledgeSource(
                name="BBC News",
                base_url="https://www.bbc.com",
                search_endpoint="/search?q={query}&sa_f=search-product&scope=all",
                scrape_endpoint="",  # Will extract from search results
                reliability_score=0.85,
                rate_limit=2.0
            ),
            # Add more sources as needed
        ]
    
    async def _is_general_knowledge_query(self, query: str) -> bool:
        """
        Detect if a query is asking for general knowledge using LLM.
        
        Args:
            query: User query
            
        Returns:
            True if query is asking for general knowledge
        """
        try:
            system_prompt = """You are a query classifier. Determine if the given query is asking for GENERAL KNOWLEDGE (facts about world events, people, places, current affairs, definitions, history, geography, politics, etc.) or NOT GENERAL KNOWLEDGE.

General knowledge queries include:
- Questions about current events, news, leaders, countries
- Historical facts and dates
- Definitions and explanations of non-medical terms
- Geography, capitals, populations
- General world facts and information
- "Who is", "What is", "When did", "Where is" questions about non-medical topics

NOT general knowledge:
- Medical/health questions
- Personal advice
- Mathematical calculations
- Programming/technical questions
- Casual conversation

Respond with ONLY one word: GENERAL or NOT_GENERAL"""
            
            request = LLMRequest(
                prompt=f"Query: {query}\n\nClassify this query:",
                system_prompt=system_prompt,
                max_tokens=10,
                temperature=0.1
            )
            
            response = await self.llm_client.generate(request)
            classification = response.content.strip().upper()
            
            is_general = "GENERAL" in classification and "NOT_GENERAL" not in classification
            logger.info(f"LLM classified query '{query}' as {'GENERAL' if is_general else 'NOT_GENERAL'} knowledge")
            
            return is_general
            
        except Exception as e:
            logger.warning(f"LLM classification failed, using keyword fallback: {e}")
            # Fallback to simple keyword detection
            return self._is_general_knowledge_query_fallback(query)
    
    def _is_general_knowledge_query_fallback(self, query: str) -> bool:
        """
        Fallback keyword-based detection for general knowledge queries.
        
        Args:
            query: User query
            
        Returns:
            True if query appears to be general knowledge
        """
        query_lower = query.lower()
        
        # Simple patterns for fallback
        general_patterns = [
            r'\b(who is|what is|when did|where is)\b',
            r'\b(president|capital|population|leader)\b',
            r'\b(current|latest|news)\b',
        ]
        
        for pattern in general_patterns:
            if re.search(pattern, query_lower):
                return True
        
        return False
    
    async def retrieve_knowledge(self, query: str) -> Optional[RetrievalResponse]:
        """
        Retrieve general knowledge for a query using Wikipedia API.
        
        Args:
            query: User query
            
        Returns:
            RetrievalResponse with general knowledge or None if not applicable
        """
        if not await self._is_general_knowledge_query(query):
            logger.info(f"Query '{query}' not identified as general knowledge")
            return None
            
        try:
            logger.info(f"Retrieving general knowledge for: {query}")
            
            # Use Wikipedia API for current, reliable information
            wikipedia_docs = await self._get_wikipedia_knowledge(query)
            
            if wikipedia_docs:
                # Create a RetrievalResponse with the Wikipedia documents
                response = RetrievalResponse(
                    documents=wikipedia_docs,
                    query=query,
                    collection_name=self.collection_name,
                    total_results=len(wikipedia_docs),
                    metadata={
                        'source': 'wikipedia_api',
                        'retrieval_method': 'api_search',
                        'timestamp': time.time()
                    }
                )
                
                logger.info(f"Retrieved {len(wikipedia_docs)} Wikipedia documents for general knowledge")
                return response
            
            logger.info("No Wikipedia knowledge found for query")
            return None
            
        except Exception as e:
            logger.error(f"General knowledge retrieval failed: {e}")
            return None
    
    async def _get_wikipedia_knowledge(self, query: str) -> List[Document]:
        """Get knowledge from Wikipedia API."""
        documents = []
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
                # Search Wikipedia
                search_url = "https://en.wikipedia.org/w/api.php"
                search_params = {
                    'action': 'query',
                    'list': 'search',
                    'srsearch': query,
                    'format': 'json',
                    'srlimit': 3,
                    'srprop': 'snippet'
                }
                
                logger.info(f"Searching Wikipedia API for: {query}")
                
                async with session.get(search_url, params=search_params) as response:
                    if response.status == 200:
                        data = await response.json()
                        search_results = data.get('query', {}).get('search', [])
                        
                        logger.info(f"Found {len(search_results)} search results")
                        
                        # Get content for each result
                        for result in search_results:
                            page_title = result['title']
                            
                            # Get page extract
                            content_params = {
                                'action': 'query',
                                'format': 'json',
                                'titles': page_title,
                                'prop': 'extracts|info',
                                'exintro': True,
                                'explaintext': True,
                                'exchars': 1000,
                                'inprop': 'url'
                            }
                            
                            async with session.get(search_url, params=content_params) as content_response:
                                if content_response.status == 200:
                                    content_data = await content_response.json()
                                    pages = content_data.get('query', {}).get('pages', {})
                                    
                                    for page_id, page_info in pages.items():
                                        extract = page_info.get('extract', '')
                                        page_url = page_info.get('fullurl', f"https://en.wikipedia.org/wiki/{quote(page_title)}")
                                        
                                        if extract and len(extract.strip()) > 50:
                                            doc = Document(
                                                content=extract,
                                                metadata={
                                                    'title': page_title,
                                                    'url': page_url,
                                                    'source': 'Wikipedia',
                                                    'type': 'general_knowledge',
                                                    'reliability_score': 0.9,
                                                    'timestamp': time.time()
                                                },
                                                doc_id=f"wiki_{page_title.replace(' ', '_')}"
                                            )
                                            documents.append(doc)
                                            logger.info(f"Retrieved Wikipedia article: {page_title}")
                                            break
                    else:
                        logger.error(f"Wikipedia search failed with status: {response.status}")
            
            return documents
            
        except Exception as e:
            logger.error(f"Error retrieving Wikipedia knowledge: {e}")
            return []
    
    async def _scrape_fresh_knowledge(self, query: str) -> List[Document]:
        """
        Scrape fresh knowledge from reliable sources.
        
        Args:
            query: Search query
            
        Returns:
            List of scraped documents
        """
        documents = []
        
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'HealthLang-AI/1.0 (Educational Purpose)'}
        ) as session:
            
            # Scrape from each knowledge source
            for source in self.knowledge_sources:
                try:
                    if source.name == "Wikipedia":
                        docs = await self._scrape_wikipedia(session, query, source)
                        documents.extend(docs)
                    
                    # Add rate limiting
                    await asyncio.sleep(source.rate_limit)
                    
                except Exception as e:
                    logger.warning(f"Failed to scrape from {source.name}: {e}")
                    continue
        
        return documents[:10]  # Limit to top 10 documents
    
    async def _scrape_wikipedia(
        self, 
        session: aiohttp.ClientSession, 
        query: str, 
        source: KnowledgeSource
    ) -> List[Document]:
        """
        Scrape Wikipedia for relevant articles.
        
        Args:
            session: HTTP session
            query: Search query
            source: Wikipedia source configuration
            
        Returns:
            List of Wikipedia documents
        """
        documents = []
        
        try:
            # Search for relevant articles
            search_url = source.base_url + source.search_endpoint.format(query=quote(query))
            
            async with session.get(search_url) as response:
                if response.status == 200:
                    search_results = await response.json()
                    
                    # Extract article titles from search results
                    if len(search_results) >= 2 and len(search_results[1]) > 0:
                        titles = search_results[1][:3]  # Top 3 results
                        
                        # Scrape each article
                        for title in titles:
                            try:
                                article_url = source.base_url + source.scrape_endpoint.format(title=quote(title))
                                article_doc = await self._scrape_wikipedia_article(session, article_url, title, source)
                                
                                if article_doc:
                                    documents.append(article_doc)
                                
                                # Rate limiting between articles
                                await asyncio.sleep(0.5)
                                
                            except Exception as e:
                                logger.warning(f"Failed to scrape Wikipedia article '{title}': {e}")
                                continue
        
        except Exception as e:
            logger.error(f"Wikipedia search failed: {e}")
        
        return documents
    
    async def _scrape_wikipedia_article(
        self,
        session: aiohttp.ClientSession,
        url: str,
        title: str,
        source: KnowledgeSource
    ) -> Optional[Document]:
        """
        Scrape a single Wikipedia article.
        
        Args:
            session: HTTP session
            url: Article URL
            title: Article title
            source: Source configuration
            
        Returns:
            Document with article content or None
        """
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    html_content = await response.text()
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # Extract main content
                    content_div = soup.find('div', {'id': 'mw-content-text'})
                    if not content_div:
                        return None
                    
                    # Remove unwanted elements
                    for element in content_div.find_all(['script', 'style', 'table', 'div.navbox']):
                        element.decompose()
                    
                    # Extract paragraphs
                    paragraphs = content_div.find_all('p')
                    text_content = ' '.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
                    
                    # Clean up text
                    text_content = re.sub(r'\[.*?\]', '', text_content)  # Remove citation markers
                    text_content = re.sub(r'\s+', ' ', text_content).strip()
                    
                    if len(text_content) < 100:  # Skip very short articles
                        return None
                    
                    return Document(
                        content=text_content[:5000],  # Limit content length
                        metadata={
                            'title': title,
                            'source': source.name,
                            'url': url,
                            'reliability_score': source.reliability_score,
                            'scraped_at': time.time(),
                            'type': 'general_knowledge'
                        },
                        doc_id=f"wiki_{hashlib.md5(url.encode()).hexdigest()}"
                    )
        
        except Exception as e:
            logger.error(f"Failed to scrape Wikipedia article {url}: {e}")
            return None
    
    async def _index_documents(self, documents: List[Document]) -> None:
        """
        Index documents in the vector store.
        
        Args:
            documents: Documents to index
        """
        try:
            from app.services.rag.document_processor import ProcessingOptions
            
            # Process documents for indexing
            processing_options = ProcessingOptions(
                chunk_size=800,
                chunk_overlap=100,
                include_metadata=True,
                clean_text=True
            )
            
            # Index documents using the existing RAG retriever
            processed_docs = []
            for doc in documents:
                processed_doc = await self.rag_retriever.document_processor.process_document(
                    doc, processing_options
                )
                processed_docs.extend(processed_doc.chunks)
            
            # Store in vector database
            if processed_docs:
                await self.rag_retriever.vector_store.add_documents(
                    processed_docs, 
                    collection_name=self.collection_name
                )
                
                logger.info(f"Indexed {len(processed_docs)} document chunks for general knowledge")
        
        except Exception as e:
            logger.error(f"Failed to index general knowledge documents: {e}")


def hashlib_md5_hash(text: str) -> str:
    """Generate MD5 hash for text."""
    return hashlib.md5(text.encode()).hexdigest()