"""
Async MCP HTTP client for HealthLang AI
"""
import os
from typing import Optional, Dict, Any

import httpx

from app.core.exceptions import MCPClientError
from app.config import settings


MCP_BASE_URL = getattr(settings, "MCP_BASE_URL", os.getenv(
    "MCP_BASE_URL", "https://healthcare-mcp.onrender.com"
))
MCP_API_KEY = getattr(settings, "MCP_API_KEY", os.getenv("MCP_API_KEY", ""))


async def mcp_get(
    endpoint: str,
    params: Optional[Dict[str, Any]] = None,
) -> Dict:
    headers = {"X-API-Key": MCP_API_KEY} if MCP_API_KEY else {}
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                f"{MCP_BASE_URL}{endpoint}",
                params=params,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as e:
            raise MCPClientError(
                message=f"MCP GET {endpoint} failed: {e}",
                status_code=e.response.status_code,
                details={"endpoint": endpoint, "params": params},
            ) from e
        except httpx.RequestError as e:
            raise MCPClientError(
                message=f"MCP GET {endpoint} network error: {e}",
                status_code=502,
                details={"endpoint": endpoint, "params": params},
            ) from e
        except ValueError as e:  # JSON parse error
            raise MCPClientError(
                message=f"MCP GET {endpoint} unexpected error: {e}",
                status_code=502,
                details={"endpoint": endpoint},
            ) from e

        if isinstance(data, dict) and data.get("status") == "error":
            raise MCPClientError(
                message=data.get("error_message", "Unknown MCP error"),
                status_code=502,
                details={"endpoint": endpoint, "payload": data},
            )
        return data


async def mcp_post(
    endpoint: str,
    json: Optional[Dict[str, Any]] = None,
) -> Dict:
    headers = {"X-API-Key": MCP_API_KEY} if MCP_API_KEY else {}
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{MCP_BASE_URL}{endpoint}",
                json=json,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as e:
            raise MCPClientError(
                message=f"MCP POST {endpoint} failed: {e}",
                status_code=e.response.status_code,
                details={"endpoint": endpoint, "json": json},
            ) from e
        except httpx.RequestError as e:
            raise MCPClientError(
                message=f"MCP POST {endpoint} network error: {e}",
                status_code=502,
                details={"endpoint": endpoint, "json": json},
            ) from e
        except ValueError as e:
            raise MCPClientError(
                message=f"MCP POST {endpoint} unexpected error: {e}",
                status_code=502,
                details={"endpoint": endpoint},
            ) from e

        if isinstance(data, dict) and data.get("status") == "error":
            raise MCPClientError(
                message=data.get("error_message", "Unknown MCP error"),
                status_code=502,
                details={"endpoint": endpoint, "payload": data},
            )
        return data


# Tool-specific wrappers


async def fda_drug_lookup(drug_name: str, search_type: str = "general"):
    return await mcp_get(
        "/api/fda",
        {"drug_name": drug_name, "search_type": search_type},
    )


async def pubmed_search(
    query: str,
    max_results: int = 5,
    date_range: int = 5,
):
    return await mcp_get(
        "/api/pubmed",
        {
            "query": query,
            "max_results": max_results,
            "date_range": date_range,
        },
    )


async def health_topics(query: str, max_results: int = 10):
    return await mcp_get(
        "/api/health-topics",
        {"query": query, "max_results": max_results},
    )


async def clinical_trials_search(
    query: str,
    status: str = "all",
    max_results: int = 10,
):
    return await mcp_get(
        "/api/clinical-trials",
        {"query": query, "status": status, "max_results": max_results},
    )


async def medical_terminology_lookup(term: str, category: str = "all"):
    return await mcp_get("/api/icd10", {"term": term, "category": category})


async def medrxiv_search(query: str, max_results: int = 10):
    return await mcp_get(
        "/api/medrxiv",
        {"query": query, "max_results": max_results},
    )


async def calculate_bmi(weight: float, height: float):
    return await mcp_get("/api/bmi", {"weight": weight, "height": height})


async def ncbi_bookshelf_search(query: str, max_results: int = 10):
    return await mcp_get(
        "/api/bookshelf",
        {"query": query, "max_results": max_results},
    )


async def extract_dicom_metadata(file_path: str):
    # For file upload, use mcp_post with appropriate file handling
    return await mcp_post("/api/dicom/metadata", {"file_path": file_path})


async def usage_analytics(period: str = "day", tool: str = "all"):
    return await mcp_get("/api/usage", {"period": period, "tool": tool})
