import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Direct import to avoid loading routes
from app.services.rag.tavily_knowledge import TavilyKnowledgeService
from app.config import settings

print("Testing Tavily Search directly...")
print(f"API Key present: {'Yes' if settings.TAVILY_API_KEY else 'No'}")

import asyncio

async def test():
    print("\nInitializing Tavily service...")
    tavily = TavilyKnowledgeService(settings)
    
    print("Searching for: 'who won the 2024 ballon d'or'")
    result = await tavily.retrieve_knowledge("who won the 2024 ballon d'or")
    
    if result:
        print(f"\nFound {len(result.get('sources', []))} sources")
        print(f"Content preview: {result.get('content', '')[:300]}...")
    else:
        print("\nNo results returned")

if __name__ == "__main__":
    asyncio.run(test())
