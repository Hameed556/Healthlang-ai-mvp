"""
MCP Client for HealthLang AI

Handles communication with MCP servers for medical tools.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class MCPClient:
    """MCP client for communicating with healthcare servers"""
    
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the MCP client and connect to servers"""
        if self._initialized:
            return
        
        try:
            if not settings.MCP_ENABLED:
                logger.info("MCP is disabled, skipping initialization")
                return
            
            logger.info("Initializing MCP client...")
            
            # Connect to healthcare server
            await self._connect_to_healthcare_server()
            
            self._initialized = True
            logger.info("MCP client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize MCP client: {e}")
            raise
    
    async def _connect_to_healthcare_server(self) -> None:
        """Connect to the healthcare MCP server"""
        try:
            server_path = settings.MCP_HEALTHCARE_SERVER_PATH
            
            # Validate server path
            if not server_path.endswith('.py'):
                raise ValueError("Healthcare server must be a Python file")
            
            # Create server parameters
            server_params = StdioServerParameters(
                command="python",
                args=[server_path],
                env=None
            )
            
            # Connect to server
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            self.stdio, self.write = stdio_transport
            
            # Create session
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(self.stdio, self.write)
            )
            
            # Initialize session
            await self.session.initialize()
            
            # List available tools
            response = await self.session.list_tools()
            tools = response.tools
            
            logger.info(f"Connected to healthcare server with tools: {[tool.name for tool in tools]}")
            
        except Exception as e:
            logger.error(f"Failed to connect to healthcare server: {e}")
            raise
    
    async def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools from the MCP server"""
        try:
            if not self.session:
                return []
            
            response = await self.session.list_tools()
            tools = []
            
            for tool in response.tools:
                tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                })
            
            return tools
            
        except Exception as e:
            logger.error(f"Error getting available tools: {e}")
            return []
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Call a tool on the MCP server"""
        try:
            if not self.session:
                raise Exception("MCP session not initialized")
            
            # Call the tool
            result = await self.session.call_tool(tool_name, arguments)
            
            # Extract content from result
            if result.content:
                return result.content[0].text
            else:
                return "No result returned from tool"
                
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            raise Exception(f"Tool call failed: {str(e)}")
    
    async def medical_lookup(self, query: str) -> str:
        """Look up medical information"""
        try:
            return await self.call_tool("medical_lookup", {"query": query})
        except Exception as e:
            logger.error(f"Medical lookup failed: {e}")
            return f"Medical lookup failed: {str(e)}"
    
    async def icd10_lookup(self, condition: str) -> str:
        """Look up ICD-10 codes"""
        try:
            return await self.call_tool("icd10_lookup", {"condition": condition})
        except Exception as e:
            logger.error(f"ICD-10 lookup failed: {e}")
            return f"ICD-10 lookup failed: {str(e)}"
    
    async def pubmed_search(self, query: str, max_results: int = 5) -> str:
        """Search PubMed for medical articles"""
        try:
            return await self.call_tool("pubmed_search", {
                "query": query,
                "max_results": max_results
            })
        except Exception as e:
            logger.error(f"PubMed search failed: {e}")
            return f"PubMed search failed: {str(e)}"
    
    async def drug_interaction_check(self, drugs: List[str]) -> str:
        """Check for drug interactions"""
        try:
            return await self.call_tool("drug_interaction_check", {"drugs": drugs})
        except Exception as e:
            logger.error(f"Drug interaction check failed: {e}")
            return f"Drug interaction check failed: {str(e)}"
    
    async def symptom_checker(self, symptoms: List[str], age: Optional[int] = None, gender: Optional[str] = None) -> str:
        """Check symptoms and get potential conditions"""
        try:
            args = {"symptoms": symptoms}
            if age:
                args["age"] = age
            if gender:
                args["gender"] = gender
            
            return await self.call_tool("symptom_checker", args)
        except Exception as e:
            logger.error(f"Symptom checker failed: {e}")
            return f"Symptom checker failed: {str(e)}"
    
    async def cleanup(self) -> None:
        """Cleanup MCP client resources"""
        try:
            if self.exit_stack:
                await self.exit_stack.aclose()
            
            self._initialized = False
            logger.info("MCP client cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during MCP client cleanup: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on MCP client"""
        try:
            if not self._initialized:
                return {"status": "not_initialized"}
            
            if not self.session:
                return {"status": "no_session"}
            
            # Try to list tools as a health check
            tools = await self.get_available_tools()
            
            return {
                "status": "healthy",
                "tools_available": len(tools),
                "tool_names": [tool["name"] for tool in tools]
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            } 