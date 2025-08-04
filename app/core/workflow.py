"""
LangGraph Workflow for HealthLang AI

Orchestrates translation and medical reasoning with MCP tools.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, TypedDict
from contextlib import AsyncExitStack

import httpx
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from app.config import settings
from app.services.mcp import MCPClient
from app.utils.logger import get_logger

logger = get_logger(__name__)

# State definition for the workflow
class WorkflowState(TypedDict):
    """State for the LangGraph workflow"""
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
        self.graph = self._build_graph()
        self.mcp_client = MCPClient()
        
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        
        # Create the workflow graph
        workflow = StateGraph(WorkflowState)
        
        # Add nodes
        workflow.add_node("detect_language", self._detect_language)
        workflow.add_node("translate_to_english", self._translate_to_english)
        workflow.add_node("medical_reasoning", self._medical_reasoning)
        workflow.add_node("translate_response", self._translate_response)
        workflow.add_node("format_response", self._format_response)
        
        # Define the workflow edges
        workflow.set_entry_point("detect_language")
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "detect_language",
            self._should_translate,
            {
                "translate": "translate_to_english",
                "skip": "medical_reasoning"
            }
        )
        
        workflow.add_edge("translate_to_english", "medical_reasoning")
        workflow.add_edge("medical_reasoning", "translate_response")
        workflow.add_edge("translate_response", "format_response")
        workflow.add_edge("format_response", END)
        
        return workflow.compile()
    
    async def _detect_language(self, state: WorkflowState) -> WorkflowState:
        """Detect the language of the input query"""
        try:
            query = state["original_query"]
            
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
            
            state["detected_language"] = detected_language
            state["messages"].append(
                AIMessage(content=f"Detected language: {detected_language}")
            )
            
            logger.info(f"Detected language: {detected_language} for query: {query[:50]}...")
            
        except Exception as e:
            logger.error(f"Error in language detection: {e}")
            state["error"] = f"Language detection failed: {str(e)}"
            state["detected_language"] = "en"  # Default to English
            
        return state
    
    def _should_translate(self, state: WorkflowState) -> str:
        """Determine if translation is needed"""
        detected_language = state.get("detected_language", "en")
        return "translate" if detected_language == "yo" else "skip"
    
    async def _translate_to_english(self, state: WorkflowState) -> WorkflowState:
        """Translate Yoruba query to English"""
        try:
            query = state["original_query"]
            
            # Use Groq + Llama-4-Maverick for translation
            translated_query = await self._call_translation_service(
                text=query,
                source_language="yo",
                target_language="en"
            )
            
            state["translated_query"] = translated_query
            state["messages"].append(
                AIMessage(content=f"Translated to English: {translated_query}")
            )
            
            logger.info(f"Translated query: {query[:50]}... -> {translated_query[:50]}...")
            
        except Exception as e:
            logger.error(f"Error in translation: {e}")
            state["error"] = f"Translation failed: {str(e)}"
            state["translated_query"] = state["original_query"]  # Fallback to original
            
        return state
    
    async def _medical_reasoning(self, state: WorkflowState) -> WorkflowState:
        """Perform medical reasoning using Grok API and MCP tools"""
        try:
            # Use the translated query if available, otherwise use original
            query = state.get("translated_query") or state["original_query"]
            
            # Perform medical reasoning with Grok API
            medical_response = await self._call_medical_reasoning(
                query=query,
                mcp_tools=await self._get_mcp_tools()
            )
            
            state["medical_response"] = medical_response
            state["messages"].append(
                AIMessage(content=f"Medical reasoning completed")
            )
            
            logger.info(f"Medical reasoning completed for query: {query[:50]}...")
            
        except Exception as e:
            logger.error(f"Error in medical reasoning: {e}")
            state["error"] = f"Medical reasoning failed: {str(e)}"
            state["medical_response"] = "Unable to process medical query at this time."
            
        return state
    
    async def _translate_response(self, state: WorkflowState) -> WorkflowState:
        """Translate the medical response back to the original language if needed"""
        try:
            detected_language = state.get("detected_language", "en")
            medical_response = state.get("medical_response", "")
            
            if detected_language == "yo" and medical_response:
                # Translate response back to Yoruba
                translated_response = await self._call_translation_service(
                    text=medical_response,
                    source_language="en",
                    target_language="yo"
                )
                
                state["final_response"] = translated_response
            else:
                # Keep response in English
                state["final_response"] = medical_response
            
            state["messages"].append(
                AIMessage(content="Response translation completed")
            )
            
            logger.info("Response translation completed")
            
        except Exception as e:
            logger.error(f"Error in response translation: {e}")
            state["error"] = f"Response translation failed: {str(e)}"
            state["final_response"] = state.get("medical_response", "Translation failed")
            
        return state
    
    async def _format_response(self, state: WorkflowState) -> WorkflowState:
        """Format the final response with metadata"""
        try:
            final_response = state.get("final_response", "")
            original_query = state["original_query"]
            detected_language = state.get("detected_language", "en")
            
            # Add metadata
            metadata = {
                "original_language": detected_language,
                "translation_used": detected_language == "yo",
                "processing_steps": len(state["messages"]),
                "error": state.get("error")
            }
            
            state["metadata"] = metadata
            
            # Format the response
            if detected_language == "yo":
                formatted_response = f"""
**Ọrọ ibeere:** {original_query}

**Idahun:** {final_response}

**Alaye:** Idahun yii ti ṣe ni ede Yoruba lati inu idahun ti o wa ni ede Gẹẹsi.
"""
            else:
                formatted_response = f"""
**Original Query:** {original_query}

**Response:** {final_response}

**Note:** This response was generated using medical reasoning and research tools.
"""
            
            state["final_response"] = formatted_response
            
            logger.info("Response formatting completed")
            
        except Exception as e:
            logger.error(f"Error in response formatting: {e}")
            state["error"] = f"Response formatting failed: {str(e)}"
            
        return state
    
    async def _call_translation_service(self, text: str, source_language: str, target_language: str) -> str:
        """Call the translation service (Groq + Llama-4-Maverick)"""
        try:
            async with httpx.AsyncClient() as client:
                # Prepare the prompt for translation
                if source_language == "yo" and target_language == "en":
                    prompt = f"""
Translate the following Yoruba text to English. Provide only the English translation without any explanations:

Yoruba: {text}
English:"""
                else:
                    prompt = f"""
Translate the following English text to Yoruba. Provide only the Yoruba translation without any explanations:

English: {text}
Yoruba:"""
                
                # Call Groq API with Llama-4-Maverick
                response = await client.post(
                    f"{settings.GROQ_BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": settings.TRANSLATION_MODEL,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.1,
                        "max_tokens": 1000
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    translated_text = result["choices"][0]["message"]["content"].strip()
                    return translated_text
                else:
                    raise Exception(f"Translation API error: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Translation service error: {e}")
            raise Exception(f"Translation failed: {str(e)}")
    
    async def _call_medical_reasoning(self, query: str, mcp_tools: List[Dict]) -> str:
        """Call the medical reasoning service with fallback to Groq"""
        try:
            # Prepare the prompt for medical reasoning
            prompt = f"""
You are a medical AI assistant. Analyze the following medical query and provide a comprehensive response using available medical tools and knowledge.

Query: {query}

Available tools: {[tool['name'] for tool in mcp_tools]}

Please provide a detailed, medically-informed response. Include relevant medical information, potential considerations, and recommendations. Always include appropriate medical disclaimers.
"""
            
            # Try XAI Grok API first
            if settings.XAI_GROK_API_KEY and settings.XAI_GROK_API_KEY != "test_api_key_for_development":
                try:
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
                                    {"role": "user", "content": prompt}
                                ],
                                "temperature": 0.1,
                                "max_tokens": 2000,
                                "tools": mcp_tools
                            },
                            timeout=60
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            medical_response = result["choices"][0]["message"]["content"]
                            
                            # Handle tool calls if any
                            if "tool_calls" in result["choices"][0]["message"]:
                                tool_calls = result["choices"][0]["message"]["tool_calls"]
                                for tool_call in tool_calls:
                                    tool_result = await self._call_mcp_tool(
                                        tool_call["function"]["name"],
                                        tool_call["function"]["arguments"]
                                    )
                                    medical_response += f"\n\nTool Result: {tool_result}"
                            
                            return medical_response
                        else:
                            logger.warning(f"XAI API returned status {response.status_code}, falling back to Groq")
                            raise Exception(f"XAI API error: {response.status_code}")
                            
                except Exception as xai_error:
                    logger.warning(f"XAI API failed, falling back to Groq: {xai_error}")
                    # Continue to fallback
            else:
                logger.info("XAI API key not configured, using Groq fallback")
            
            # Fallback to Groq API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.GROQ_BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": settings.GROQ_MODEL,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.1,
                        "max_tokens": 2000
                    },
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    medical_response = result["choices"][0]["message"]["content"]
                    return medical_response
                else:
                    raise Exception(f"Groq API error: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Medical reasoning service error: {e}")
            raise Exception(f"Medical reasoning failed: {str(e)}")
    
    async def _get_mcp_tools(self) -> List[Dict]:
        """Get available MCP tools"""
        if not settings.MCP_ENABLED or not self.mcp_client:
            return []
        
        try:
            return await self.mcp_client.get_available_tools()
        except Exception as e:
            logger.error(f"Error getting MCP tools: {e}")
            return []
    
    async def _call_mcp_tool(self, tool_name: str, arguments: str) -> str:
        """Call an MCP tool"""
        try:
            if not self.mcp_client:
                return f"MCP client not available for tool {tool_name}"
            
            # Parse arguments if they're a string
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    arguments = {"query": arguments}
            
            return await self.mcp_client.call_tool(tool_name, arguments)
        except Exception as e:
            logger.error(f"Error calling MCP tool {tool_name}: {e}")
            return f"Error calling tool {tool_name}: {str(e)}"
    
    async def initialize(self) -> None:
        """Initialize the workflow and MCP client"""
        try:
            if settings.MCP_ENABLED:
                # Initialize MCP client connection (optional)
                logger.info("Initializing MCP client...")
                try:
                    await self.mcp_client.initialize()
                    logger.info("MCP client initialized successfully")
                except Exception as mcp_error:
                    logger.warning(f"MCP client initialization failed (continuing without MCP): {mcp_error}")
                    # Continue without MCP - it's optional for basic functionality
            
            logger.info("HealthLang workflow initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize workflow: {e}")
            raise
    
    async def cleanup(self) -> None:
        """Cleanup workflow resources"""
        try:
            if self.mcp_client:
                # Cleanup MCP client
                logger.info("Cleaning up MCP client...")
                await self.mcp_client.cleanup()
                logger.info("MCP client cleaned up")
            
            logger.info("HealthLang workflow cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during workflow cleanup: {e}")
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """Process a medical query through the workflow"""
        try:
            # Initialize the workflow state
            initial_state = WorkflowState(
                messages=[],
                original_query=query,
                detected_language="",
                translated_query=None,
                medical_response=None,
                final_response=None,
                error=None,
                metadata={}
            )
            
            # Run the workflow
            final_state = await self.graph.ainvoke(initial_state)
            
            return {
                "success": True,
                "response": final_state.get("final_response", ""),
                "metadata": final_state.get("metadata", {}),
                "error": final_state.get("error")
            }
            
        except Exception as e:
            logger.error(f"Workflow error: {e}")
            return {
                "success": False,
                "response": "An error occurred while processing your query.",
                "error": str(e),
                "metadata": {}
            } 