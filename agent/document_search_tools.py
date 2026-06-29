#!/usr/bin/env python3
"""
Document Search Tools for AI Agent
Provides semantic search capabilities over business documents
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vector_db.chroma_manager import ChromaManager

# Initialize ChromaDB manager
try:
    chroma_manager = ChromaManager()
    VECTOR_DB_AVAILABLE = True
    print("✅ Vector database initialized")
except Exception as e:
    print(f"⚠️ Vector database not available: {e}")
    VECTOR_DB_AVAILABLE = False
    chroma_manager = None

def search_documents(query: str, max_results: int = 3) -> dict:
    """
    Search internal business documents for relevant information.
    
    Args:
        query: The search query (e.g., "expansion strategy", "hiring budget")
        max_results: Maximum number of results to return (default: 3)
    
    Returns:
        Dictionary with search results containing relevant document excerpts
    """
    if not VECTOR_DB_AVAILABLE or not chroma_manager:
        return {
            "success": False,
            "error": "Document search is not available. Vector database not initialized."
        }
    
    try:
        results = chroma_manager.search(query, n_results=max_results)
        
        if not results:
            return {
                "success": True,
                "results_count": 0,
                "message": "No relevant documents found for this query.",
                "results": []
            }
        
        # Format results
        formatted_results = []
        for i, result in enumerate(results, 1):
            formatted_results.append({
                "rank": i,
                "document": result['metadata']['filename'],
                "excerpt": result['text'],
                "relevance_score": 1 - result['distance'] if result['distance'] else None
            })
        
        return {
            "success": True,
            "results_count": len(formatted_results),
            "query": query,
            "results": formatted_results
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Search failed: {str(e)}"
        }


def get_vector_db_stats() -> dict:
    """
    Get statistics about the document database.
    
    Returns:
        Dictionary with database statistics
    """
    if not VECTOR_DB_AVAILABLE or not chroma_manager:
        return {
            "available": False,
            "message": "Vector database not initialized"
        }
    
    try:
        stats = chroma_manager.get_collection_stats()
        return {
            "available": True,
            "total_chunks": stats['total_chunks'],
            "collection_name": stats['collection_name'],
            "status": "operational"
        }
    except Exception as e:
        return {
            "available": False,
            "error": str(e)
        }

# Tool definitions for Groq agent
DOCUMENT_SEARCH_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_documents",
            "description": "Search internal company documents (strategy plans, policies, financial reports, product roadmaps, etc.) for relevant information. Use this when you need information about company strategy, policies, budgets, plans, or internal guidelines.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query describing what information you're looking for (e.g., 'expansion strategy for Netherlands', 'hiring budget 2026', 'product roadmap AI features')"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of document excerpts to return (default: 3, max: 10)",
                        "default": 3
                    }
                },
                "required": ["query"]
            }
        }
    }
]

if __name__ == "__main__":
    # Test the search function
    print("Testing document search...")
    
    test_queries = [
        "What is our expansion strategy?",
        "What is the hiring budget?",
        "What features are users requesting?"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: {query}")
        result = search_documents(query, max_results=2)
        
        if result['success']:
            print(f"✅ Found {result['results_count']} results")
            for r in result['results']:
                print(f"   {r['rank']}. {r['document']}")
                print(f"      {r['excerpt'][:100]}...")
        else:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
