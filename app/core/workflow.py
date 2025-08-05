"""
HealthLang AI Workflow

Orchestrates translation and medical reasoning without LangGraph dependencies.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, TypedDict
from contextlib import AsyncExitStack

import httpx
from langchain_core.messages import HumanMessage, AIMessage

from app.config import settings
from app.utils.logger import get_logger

# Conditional MCP import
try:
    from app.services.mcp import MCPClient
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    MCPClient = None

logger = get_logger(__name__)

# State definition for the workflow
class WorkflowState(TypedDict):
    """State for the HealthLang workflow"""
    messages: List[Any]
    original_query: str
    detected_language: str
    translated_query: Optional[str]
    medical_response: Optional[str]
    final_response: Optional[str]
    error: Optional[str]
    metadata: Dict[str, Any]


class HealthLangWorkflow:
    """Main workflow orchestrator for HealthLang AI"""
    
    def __init__(self):
        if MCP_AVAILABLE and settings.MCP_ENABLED:
            self.mcp_client = MCPClient()
        else:
            self.mcp_client = None
        
    async def _detect_language(self, query: str) -> str:
        """Detect the language of the input query"""
        try:
            # Simple language detection (can be enhanced with proper language detection)
            yoruba_keywords = [
                "ni", "ti", "si", "fun", "lori", "ninu", "lati", "bi", "pe", "ki",
                "mo", "o", "a", "won", "wa", "e", "yin", "mi", "re", "wa"
            ]
            
            # Check for Yoruba characters and common words
            yoruba_chars = set("ọọẹẹṣṣ")
            query_chars = set(query.lower())
            
            has_yoruba_chars = bool(yoruba_chars.intersection(query_chars))
            has_yoruba_words = any(word in query.lower() for word in yoruba_keywords)
            
            detected_language = "yo" if (has_yoruba_chars or has_yoruba_words) else "en"
            
            logger.info(f"Detected language: {detected_language} for query: {query[:50]}...")
            return detected_language
            
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return "en"  # Default to English
    
    def _should_translate(self, detected_language: str) -> bool:
        """Determine if translation is needed"""
        return detected_language == "yo"
    
    async def _translate_to_english(self, query: str) -> str:
        """Translate query to English if needed"""
        try:
            if not self._should_translate(await self._detect_language(query)):
                return query
            
            # Call translation service
            translated = await self._call_translation_service(query, "yo", "en")
            logger.info(f"Translated query: {query[:50]}... -> {translated[:50]}...")
            return translated
            
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return query  # Return original if translation fails
    
    async def _medical_reasoning(self, query: str) -> str:
        """Perform medical reasoning on the query"""
        try:
            # Get MCP tools
            mcp_tools = await self._get_mcp_tools()
            
            # Call medical reasoning service
            response = await self._call_medical_reasoning(query, mcp_tools)
            logger.info(f"Medical reasoning completed for query: {query[:50]}...")
            return response
            
        except Exception as e:
            logger.error(f"Medical reasoning failed: {e}")
            return f"Sorry, I encountered an error while processing your medical query: {str(e)}"
    
    async def _translate_response(self, response: str, target_language: str) -> str:
        """Translate response to target language if needed"""
        try:
            if target_language == "en":
                return response
            
            # Call translation service
            translated = await self._call_translation_service(response, "en", target_language)
            logger.info("Response translation completed")
            return translated
            
        except Exception as e:
            logger.error(f"Response translation failed: {e}")
            return response  # Return original if translation fails
    
    async def _format_response(self, original_query: str, response: str, target_language: str) -> str:
        """Format the final response"""
        try:
            if target_language == "yo":
                formatted_response = f"""**Ọrọ ibeere:** {original_query}
**Idahun:** {response}
**Alaye:** Idahun yii ti ṣe ni ede Yoruba lati inu idahun ti o wa ni ede Gẹẹsi."""
            else:
                formatted_response = f"""**Query:** {original_query}
**Response:** {response}
**Note:** This response was translated from English to {target_language}."""
            
            logger.info("Response formatting completed")
            return formatted_response
            
        except Exception as e:
            logger.error(f"Response formatting failed: {e}")
            return response
    
    async def _call_translation_service(self, text: str, source_language: str, target_language: str) -> str:
        """Call the translation service"""
        try:
            # Import here to avoid circular imports
            from app.services.translation.translator import TranslationService
            
            translator = TranslationService()
            await translator.initialize()
            
            result = await translator.translate(
                text=text,
                source_language=source_language,
                target_language=target_language
            )
            
            return result.translated_text
            
        except Exception as e:
            logger.error(f"Translation service call failed: {e}")
            raise
    
    async def _call_medical_reasoning(self, query: str, mcp_tools: List[Dict]) -> str:
        """Call the medical reasoning service (XAI Grok API or Groq fallback) with MCP tools"""
        try:
            # Try XAI Grok API first
            prompt = f"""You are a medical AI assistant. Answer the following medical question accurately and comprehensively.

Available medical tools: {json.dumps(mcp_tools, indent=2)}

Question: {query}

Provide a detailed, accurate medical response. If you need to use any tools, specify which ones and how to use them."""

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.XAI_GROK_BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.XAI_GROK_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": settings.MEDICAL_MODEL_NAME,
                        "messages": [
                            {"role": "system", "content": prompt},
                            {"role": "user", "content": query}
                        ],
                        "temperature": settings.TEMPERATURE,
                        "max_tokens": settings.MAX_TOKENS,
                        "top_p": settings.TOP_P
                    },
                    timeout=settings.LLM_TIMEOUT
                )
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            logger.warning(f"XAI API returned status {e.response.status_code}, falling back to Groq")
            # Fallback to Groq API
            return await self._call_groq_medical_reasoning(query, mcp_tools)
        except Exception as e:
            logger.warning(f"XAI API failed, falling back to Groq: {e}")
            # Fallback to Groq API
            return await self._call_groq_medical_reasoning(query, mcp_tools)
    
    async def _call_groq_medical_reasoning(self, query: str, mcp_tools: List[Dict]) -> str:
        """Fallback medical reasoning using Groq API"""
        try:
            from langchain_groq import ChatGroq
            
            prompt = f"""You are a medical AI assistant. Answer the following medical question accurately and comprehensively.

Available medical tools: {json.dumps(mcp_tools, indent=2)}

Question: {query}

Provide a detailed, accurate medical response. If you need to use any tools, specify which ones and how to use them."""

            llm = ChatGroq(
                model=settings.MEDICAL_MODEL_NAME,
                groq_api_key=settings.GROQ_API_KEY,
                temperature=settings.TEMPERATURE,
                max_tokens=settings.MAX_TOKENS
            )
            
            response = await llm.ainvoke([HumanMessage(content=prompt)])
            return response.content
            
        except Exception as e:
            logger.error(f"Groq medical reasoning failed: {e}")
            return f"Sorry, I encountered an error while processing your medical query: {str(e)}"
    
    async def _get_mcp_tools(self) -> List[Dict]:
        """Get available MCP tools"""
        try:
            if self.mcp_client and hasattr(self.mcp_client, 'is_connected') and self.mcp_client.is_connected():
                return await self.mcp_client.list_tools()
            else:
                return []
        except Exception as e:
            logger.warning(f"Failed to get MCP tools: {e}")
            return []
    
    async def _call_mcp_tool(self, tool_name: str, arguments: str) -> str:
        """Call an MCP tool"""
        try:
            if self.mcp_client and hasattr(self.mcp_client, 'is_connected') and self.mcp_client.is_connected():
                return await self.mcp_client.call_tool(tool_name, arguments)
            else:
                return f"Tool {tool_name} not available (MCP not connected)"
        except Exception as e:
            logger.error(f"MCP tool call failed: {e}")
            return f"Error calling tool {tool_name}: {str(e)}"
    
    async def initialize(self) -> None:
        """Initialize the workflow"""
        try:
            logger.info("Initializing HealthLang workflow...")
            if self.mcp_client:
                await self.mcp_client.initialize()
            logger.info("HealthLang workflow initialized successfully")
        except Exception as e:
            logger.warning(f"Workflow initialization failed (continuing without MCP): {e}")
    
    async def cleanup(self) -> None:
        """Cleanup resources"""
        try:
            if self.mcp_client:
                await self.mcp_client.cleanup()
        except Exception as e:
            logger.error(f"Workflow cleanup failed: {e}")
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """Process a medical query through the complete workflow"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Step 1: Detect language
            detected_language = await self._detect_language(query)
            
            # Step 2: Translate to English if needed
            translated_query = await self._translate_to_english(query)
            
            # Step 3: Medical reasoning
            medical_response = await self._medical_reasoning(translated_query)
            
            # Step 4: Translate response back if needed
            final_response = await self._translate_response(medical_response, detected_language)
            
            # Step 5: Format response
            formatted_response = await self._format_response(query, final_response, detected_language)
            
            processing_time = asyncio.get_event_loop().time() - start_time
            
            return {
                "request_id": f"req_{int(start_time * 1000)}",
                "original_query": query,
                "response": formatted_response,
                "processing_time": processing_time,
                "timestamp": asyncio.get_event_loop().time(),
                "metadata": {
                    "original_language": detected_language,
                    "translation_used": detected_language == "yo",
                    "processing_steps": 5,
                    "error": None
                },
                "success": True,
                "error": None
            }
            
        except Exception as e:
            processing_time = asyncio.get_event_loop().time() - start_time
            logger.error(f"Query processing failed: {e}")
            
            return {
                "request_id": f"req_{int(start_time * 1000)}",
                "original_query": query,
                "response": f"Sorry, I encountered an error while processing your query: {str(e)}",
                "processing_time": processing_time,
                "timestamp": asyncio.get_event_loop().time(),
                "metadata": {
                    "original_language": "unknown",
                    "translation_used": False,
                    "processing_steps": 0,
                    "error": str(e)
                },
                "success": False,
                "error": str(e)
            } 