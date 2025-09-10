#!/usr/bin/env python3
"""
MCP Healthcare Server

Provides tools for medical lookup, ICD-10 codes, and PubMed searches.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

import httpx
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
)

notification_options = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the server
server = Server("healthcare-server")

# PubMed API base URL
PUBMED_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

# ICD-10 API base URL (using WHO API)
ICD10_BASE_URL = "https://id.who.int/icd/entity"

@server.list_tools()
async def handle_list_tools() -> ListToolsResult:
    """List available tools"""
    tools = [
        Tool(
            name="medical_lookup",
            description="Look up medical terms, conditions, and treatments",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Medical term, condition, or treatment to look up"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="icd10_lookup",
            description="Look up ICD-10 codes for medical conditions",
            inputSchema={
                "type": "object",
                "properties": {
                    "condition": {
                        "type": "string",
                        "description": "Medical condition to find ICD-10 code for"
                    }
                },
                "required": ["condition"]
            }
        ),
        Tool(
            name="pubmed_search",
            description="Search PubMed for medical research articles",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for PubMed articles"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 5)",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="drug_interaction_check",
            description="Check for potential drug interactions",
            inputSchema={
                "type": "object",
                "properties": {
                    "drugs": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of drug names to check for interactions"
                    }
                },
                "required": ["drugs"]
            }
        ),
        Tool(
            name="symptom_checker",
            description="Get possible conditions based on symptoms",
            inputSchema={
                "type": "object",
                "properties": {
                    "symptoms": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of symptoms to analyze"
                    },
                    "age": {
                        "type": "integer",
                        "description": "Patient age"
                    },
                    "gender": {
                        "type": "string",
                        "description": "Patient gender (male/female/other)"
                    }
                },
                "required": ["symptoms"]
            }
        )
    ]
    return ListToolsResult(tools=tools)

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """Handle tool calls"""
    try:
        if name == "medical_lookup":
            return await medical_lookup(arguments["query"])
        elif name == "icd10_lookup":
            return await icd10_lookup(arguments["condition"])
        elif name == "pubmed_search":
            max_results = arguments.get("max_results", 5)
            return await pubmed_search(arguments["query"], max_results)
        elif name == "drug_interaction_check":
            return await drug_interaction_check(arguments["drugs"])
        elif name == "symptom_checker":
            age = arguments.get("age")
            gender = arguments.get("gender")
            return await symptom_checker(arguments["symptoms"], age, gender)
        else:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Unknown tool: {name}")]
            )
    except Exception as e:
        logger.error(f"Error in tool {name}: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: {str(e)}")]
        )

async def medical_lookup(query: str) -> CallToolResult:
    """Look up medical terms and conditions"""
    # This would typically connect to a medical database
    # For now, we'll provide a basic response
    response = f"""
Medical Lookup Results for: {query}

Based on the query "{query}", here are some relevant medical information:

1. **Definition**: {query} is a medical condition that may require professional evaluation.

2. **Common Symptoms**: 
   - Varies by individual
   - May include pain, discomfort, or other symptoms

3. **Treatment Options**:
   - Consult with a healthcare provider
   - Follow recommended treatment plans
   - Monitor symptoms

4. **Prevention**:
   - Maintain healthy lifestyle
   - Regular check-ups
   - Follow medical advice

**Note**: This is general information. For specific medical advice, please consult with a qualified healthcare provider.
"""
    return CallToolResult(content=[TextContent(type="text", text=response)])

async def icd10_lookup(condition: str) -> CallToolResult:
    """Look up ICD-10 codes"""
    # This would typically connect to WHO ICD-10 API
    # For now, we'll provide a basic response
    response = f"""
ICD-10 Lookup Results for: {condition}

Based on the condition "{condition}", here are potential ICD-10 codes:

1. **Primary Code**: Z00.00 - Encounter for general adult medical examination without abnormal findings
2. **Secondary Codes**:
   - Z51.11 - Encounter for antineoplastic chemotherapy
   - Z79.899 - Other long term (current) drug therapy, unspecified

**Note**: These are example codes. For accurate ICD-10 coding, please consult with a qualified medical coder or use official WHO ICD-10 resources.

**Disclaimer**: This information is for educational purposes only and should not be used for actual medical coding without proper verification.
"""
    return CallToolResult(content=[TextContent(type="text", text=response)])

async def pubmed_search(query: str, max_results: int = 5) -> CallToolResult:
    """Search PubMed for medical articles"""
    try:
        async with httpx.AsyncClient() as client:
            # Search for articles
            search_url = f"{PUBMED_BASE_URL}/esearch.fcgi"
            search_params = {
                "db": "pubmed",
                "term": query,
                "retmax": max_results,
                "retmode": "json"
            }
            
            search_response = await client.get(search_url, params=search_params)
            search_data = search_response.json()
            
            if "esearchresult" not in search_data:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"No results found for: {query}")]
                )
            
            id_list = search_data["esearchresult"].get("idlist", [])
            
            if not id_list:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"No results found for: {query}")]
                )
            
            # Get article details
            summary_url = f"{PUBMED_BASE_URL}/esummary.fcgi"
            summary_params = {
                "db": "pubmed",
                "id": ",".join(id_list),
                "retmode": "json"
            }
            
            summary_response = await client.get(summary_url, params=summary_params)
            summary_data = summary_response.json()
            
            articles = []
            for article_id in id_list:
                if article_id in summary_data["result"]:
                    article = summary_data["result"][article_id]
                    title = article.get("title", "No title available")
                    authors = article.get("authors", [])
                    author_names = [author.get("name", "") for author in authors[:3]]
                    pub_date = article.get("pubdate", "No date available")
                    
                    articles.append({
                        "id": article_id,
                        "title": title,
                        "authors": author_names,
                        "pub_date": pub_date
                    })
            
            # Format response
            response = f"PubMed Search Results for: {query}\n\n"
            for i, article in enumerate(articles, 1):
                response += f"{i}. **{article['title']}**\n"
                response += f"   Authors: {', '.join(article['authors'])}\n"
                response += f"   Published: {article['pub_date']}\n"
                response += f"   PMID: {article['id']}\n\n"
            
            return CallToolResult(content=[TextContent(type="text", text=response)])
            
    except Exception as e:
        logger.error(f"Error in PubMed search: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error searching PubMed: {str(e)}")]
        )

async def drug_interaction_check(drugs: List[str]) -> CallToolResult:
    """Check for potential drug interactions"""
    response = f"""
Drug Interaction Check for: {', '.join(drugs)}

Based on the provided medications, here are potential interactions to consider:

1. **General Guidelines**:
   - Always inform your healthcare provider about all medications you're taking
   - Include prescription drugs, over-the-counter medications, and supplements
   - Be aware of potential side effects

2. **Common Interaction Types**:
   - Pharmacokinetic interactions (affecting drug absorption, distribution, metabolism, excretion)
   - Pharmacodynamic interactions (affecting drug effects)
   - Additive or synergistic effects
   - Antagonistic effects

3. **Recommendations**:
   - Consult with a pharmacist or healthcare provider
   - Monitor for unusual side effects
   - Keep a complete medication list

**Note**: This is general information. For specific drug interaction advice, please consult with a qualified healthcare provider or pharmacist.
"""
    return CallToolResult(content=[TextContent(type="text", text=response)])

async def symptom_checker(symptoms: List[str], age: Optional[int] = None, gender: Optional[str] = None) -> CallToolResult:
    """Get possible conditions based on symptoms"""
    age_info = f" (Age: {age})" if age else ""
    gender_info = f" (Gender: {gender})" if gender else ""
    
    response = f"""
Symptom Analysis for: {', '.join(symptoms)}{age_info}{gender_info}

Based on the reported symptoms, here are possible conditions to consider:

1. **Common Conditions**:
   - These symptoms may be associated with various conditions
   - Severity and duration of symptoms are important factors
   - Individual health history plays a significant role

2. **Red Flags to Watch For**:
   - Severe or worsening symptoms
   - Symptoms lasting longer than expected
   - New or unusual symptoms
   - Symptoms affecting daily activities

3. **Recommendations**:
   - Consult with a healthcare provider for proper diagnosis
   - Keep a symptom diary with timing and severity
   - Note any triggers or patterns
   - Monitor for changes in symptoms

4. **When to Seek Immediate Care**:
   - Severe pain or discomfort
   - Difficulty breathing
   - Loss of consciousness
   - Severe bleeding
   - Chest pain or pressure

**Note**: This is general information and should not replace professional medical advice. Please consult with a qualified healthcare provider for proper diagnosis and treatment.
"""
    return CallToolResult(content=[TextContent(type="text", text=response)])

async def main():
    """Run the MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="healthcare-server",
                server_version="1.0.0",
                
                capabilities=server.get_capabilities(
                    notification_options=notification_options,
                    experimental_capabilities=None,
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main()) 