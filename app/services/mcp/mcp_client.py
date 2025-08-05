"""
MCP Client for HealthLang AI

Handles communication with MCP servers for medical tools.
"""

import logging
from typing import Any, Dict, List, Optional
from contextlib import AsyncExitStack

# Conditional MCP import
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    ClientSession = None
    StdioServerParameters = None
    stdio_client = None

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class MCPClient:
    """MCP client for communicating with healthcare servers"""
    
    def __init__(self):
        if not MCP_AVAILABLE:
            raise ImportError("MCP module is not available. Please install the 'mcp' package.")
        
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
    
    async def list_tools(self) -> List[Dict[str, Any]]:
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
                    "inputSchema": tool.inputSchema
                })
            
            return tools
            
        except Exception as e:
            logger.error(f"Failed to get available tools: {e}")
            return []
    
    async def call_tool(self, tool_name: str, arguments: str) -> str:
        """Call a specific tool on the MCP server"""
        try:
            if not self.session:
                return f"Tool {tool_name} not available (no active session)"
            
            # Parse arguments if they're passed as a string
            if isinstance(arguments, str):
                try:
                    import json
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    arguments = {"query": arguments}
            
            # Call the tool
            response = await self.session.call_tool(tool_name, arguments)
            
            # Return the result
            if response.content:
                return response.content[0].text
            else:
                return f"Tool {tool_name} returned no content"
                
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name}: {e}")
            return f"Error calling tool {tool_name}: {str(e)}"
    
    async def medical_lookup(self, query: str) -> str:
        """Perform medical information lookup"""
        return await self.call_tool("medical_lookup", {"query": query})
    
    async def icd10_lookup(self, condition: str) -> str:
        """Look up ICD-10 codes for a condition"""
        return await self.call_tool("icd10_lookup", {"condition": condition})
    
    async def pubmed_search(self, query: str, max_results: int = 5) -> str:
        """Search PubMed for medical literature"""
        return await self.call_tool("pubmed_search", {
            "query": query,
            "max_results": max_results
        })
    
    async def drug_interaction_check(self, drugs: List[str]) -> str:
        """Check for drug interactions"""
        return await self.call_tool("drug_interaction_check", {"drugs": drugs})
    
    async def symptom_checker(self, symptoms: List[str], age: Optional[int] = None, gender: Optional[str] = None) -> str:
        """Check symptoms and suggest possible conditions"""
        args = {"symptoms": symptoms}
        if age:
            args["age"] = age
        if gender:
            args["gender"] = gender
        return await self.call_tool("symptom_checker", args)
    
    def is_connected(self) -> bool:
        """Check if the MCP client is connected"""
        return self.session is not None and self._initialized
    
    async def cleanup(self) -> None:
        """Cleanup MCP client resources"""
        try:
            if self.exit_stack:
                await self.exit_stack.aclose()
            self._initialized = False
            logger.info("MCP client cleaned up successfully")
        except Exception as e:
            logger.error(f"Failed to cleanup MCP client: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on MCP client"""
        try:
            if not self.is_connected():
                return {
                    "status": "disconnected",
                    "message": "MCP client is not connected"
                }
            
            # Try to list tools as a health check
            tools = await self.list_tools()
            
            return {
                "status": "healthy",
                "message": "MCP client is connected and responsive",
                "available_tools": len(tools),
                "tools": [tool["name"] for tool in tools]
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"MCP client health check failed: {str(e)}"
            } 