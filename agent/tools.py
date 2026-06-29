"""
Tools for Groq Agent
Includes web search, social media search, and DynamoDB CRUD operations
"""

from tavily import TavilyClient
import os
from dotenv import load_dotenv
from typing import Dict, List, Optional
from decimal import Decimal
import requests
from datetime import datetime
from agent.business_tools import BUSINESS_TOOL_FUNCTIONS
from agent.business_tool_definitions import BUSINESS_TOOL_DEFINITIONS
from agent.document_search_tools import search_documents, DOCUMENT_SEARCH_TOOLS

load_dotenv()

# Initialize Tavily client
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
tavily_client = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None


def convert_decimals(obj):
    """Convert Decimal objects to float for JSON serialization"""
    if isinstance(obj, list):
        return [convert_decimals(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_decimals(value) for key, value in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj)
    return obj


def summarize_large_data(data: Dict) -> Dict:
    """
    Intelligently summarize large data responses to fit context window
    
    Args:
        data: Tool response data
        
    Returns:
        Summarized version with key insights
    """
    if not data.get("success"):
        return data
    
    # If data has many items, create summary statistics
    if "sales" in data and len(data["sales"]) > 5:
        sales = data["sales"]
        total_revenue = sum(float(s.get("monthly_revenue", 0)) for s in sales)
        total_users = sum(int(s.get("active_users", 0)) for s in sales)
        avg_growth = sum(float(s.get("yearly_growth", 0)) for s in sales) / len(sales)
        
        # Keep only top 5 by revenue
        top_5 = sorted(sales, key=lambda x: x.get("monthly_revenue", 0), reverse=True)[:5]
        
        return {
            "success": True,
            "summary": {
                "total_countries": len(sales),
                "total_monthly_revenue": round(total_revenue, 2),
                "total_users": total_users,
                "average_growth": round(avg_growth, 1)
            },
            "top_5_countries": top_5,
            "note": f"Showing top 5 of {len(sales)} countries by revenue"
        }
    
    if "users" in data and len(data["users"]) > 10:
        users = data["users"]
        active_count = len([u for u in users if u.get("active")])
        
        # Group by plan
        plan_breakdown = {}
        for u in users:
            plan = u.get("plan", "Unknown")
            plan_breakdown[plan] = plan_breakdown.get(plan, 0) + 1
        
        # Group by city
        city_breakdown = {}
        for u in users:
            city = u.get("city", "Unknown")
            city_breakdown[city] = city_breakdown.get(city, 0) + 1
        
        return {
            "success": True,
            "count": len(users),
            "active_count": active_count,
            "active_percentage": round((active_count/len(users))*100, 1),
            "by_plan": plan_breakdown,
            "by_city": city_breakdown,
            "note": "Aggregated statistics for efficiency"
        }
    
    if "features" in data and len(data["features"]) > 8:
        features = data["features"]
        top_8 = features[:8]  # Already sorted by votes
        
        return {
            "success": True,
            "count": len(features),
            "top_features": top_8,
            "total_votes": sum(f.get("votes", 0) for f in features),
            "note": f"Showing top 8 of {len(features)} features"
        }
    
    if "tasks" in data and len(data["tasks"]) > 10:
        tasks = data["tasks"]
        
        status_breakdown = {}
        dept_breakdown = {}
        for t in tasks:
            status = t.get("status", "Unknown")
            dept = t.get("department", "Unknown")
            status_breakdown[status] = status_breakdown.get(status, 0) + 1
            dept_breakdown[dept] = dept_breakdown.get(dept, 0) + 1
        
        return {
            "success": True,
            "total_tasks": len(tasks),
            "by_status": status_breakdown,
            "by_department": dept_breakdown,
            "sample_tasks": tasks[:5],
            "note": "Summary with 5 sample tasks"
        }
    
    if "decisions" in data and len(data["decisions"]) > 8:
        decisions = data["decisions"]
        
        status_breakdown = {}
        for d in decisions:
            status = d.get("status", "Unknown")
            status_breakdown[status] = status_breakdown.get(status, 0) + 1
        
        avg_confidence = sum(float(d.get("confidence", 0)) for d in decisions) / len(decisions)
        
        return {
            "success": True,
            "total_decisions": len(decisions),
            "by_status": status_breakdown,
            "average_confidence": round(avg_confidence, 1),
            "recent_decisions": decisions[:5],
            "note": "Summary with 5 most recent decisions"
        }
    
    if "competitors" in data and len(data["competitors"]) > 8:
        competitors = data["competitors"]
        top_8 = competitors[:8]  # Already sorted by market share
        
        return {
            "success": True,
            "total_competitors": len(competitors),
            "top_competitors": top_8,
            "note": f"Showing top 8 of {len(competitors)} competitors"
        }
    
    # If data is small enough, return as-is
    return data


def web_search(query: str, max_results: int = 3) -> Dict:
    """
    Search the web using Tavily API
    
    Args:
        query: Search query
        max_results: Number of results to return
        
    Returns:
        Dict with answer and results
    """
    if not tavily_client:
        return {
            "success": False,
            "error": "Tavily API not configured"
        }
    
    try:
        print(f"🔍 Web search: {query}")
        
        response = tavily_client.search(
            query=query,
            search_depth="advanced",
            max_results=max_results,
            include_answer=True
        )
        
        # Extract results - only keep high-quality matches (score > 0.85)
        results = []
        for result in response.get("results", []):
            score = float(result.get("score", 0.0))
            
            # Only include high-quality results
            if score >= 0.85:
                # Truncate content to 300 chars to save context
                content = result.get("content", "")[:300]
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "content": content,
                    "score": score
                })
        
        # Limit to top 3 highest quality
        results = results[:3]
        
        answer = response.get("answer") or "No AI summary available"
        
        # Truncate answer if too long (keep under 500 chars)
        if len(answer) > 500:
            answer = answer[:500] + "..."
        
        return {
            "success": True,
            "query": query,
            "answer": answer,
            "results": results,
            "results_count": len(results)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def search_hacker_news(query: str, max_results: int = 10) -> Dict:
    """
    Search Hacker News for tech discussions, product launches, and developer opinions.
    No API key required - completely free!
    
    Args:
        query: Search query (e.g., "AI resume tools", "career tech startups")
        max_results: Number of results to return (default: 10, max: 20)
        
    Returns:
        Dict with HN stories, points, comments, and URLs
    """
    try:
        print(f"🔍 Hacker News search: {query}")
        
        # Use Algolia HN Search API (free, no auth needed)
        url = "http://hn.algolia.com/api/v1/search"
        params = {
            "query": query,
            "tags": "story",
            "hitsPerPage": min(max_results, 20)
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        hits = data.get('hits', [])
        
        if not hits:
            return {
                "success": True,
                "query": query,
                "results": [],
                "count": 0,
                "message": "No results found on Hacker News"
            }
        
        # Format results
        results = []
        for hit in hits:
            # Skip stories without URLs (Ask HN, Show HN with no link)
            if not hit.get('url'):
                continue
                
            results.append({
                "title": hit.get('title', 'No title'),
                "url": hit.get('url', ''),
                "hn_url": f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}",
                "points": hit.get('points', 0),
                "comments": hit.get('num_comments', 0),
                "author": hit.get('author', 'unknown'),
                "created_at": hit.get('created_at', '')
            })
        
        # Sort by relevance (points + comments as proxy)
        results.sort(key=lambda x: x['points'] + x['comments'], reverse=True)
        results = results[:max_results]
        
        # Generate summary
        if results:
            top_result = results[0]
            summary = f"Found {len(results)} HN discussions. Top result: '{top_result['title']}' ({top_result['points']} points, {top_result['comments']} comments)"
        else:
            summary = "No relevant discussions found"
        
        return {
            "success": True,
            "query": query,
            "summary": summary,
            "results": results,
            "count": len(results),
            "source": "Hacker News"
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"HN API request failed: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"HN search failed: {str(e)}"
        }


def search_stackoverflow(query: str, tags: Optional[List[str]] = None, max_results: int = 10) -> Dict:
    """
    Search Stack Overflow for technical discussions and solutions.
    FREE - No API key needed! Uses official Stack Exchange API.
    
    Args:
        query: Search query (e.g., "Python career automation", "AI interview tools")
        tags: Optional list of tags to filter (e.g., ["python", "ai", "career"])
        max_results: Number of results (default: 10, max: 30)
        
    Returns:
        Dict with Stack Overflow questions, answers, votes, and acceptance
    """
    try:
        print(f"🔍 Stack Overflow search: {query}")
        
        # Use Stack Exchange API v2.3 (no auth required for read-only)
        url = "https://api.stackexchange.com/2.3/search/advanced"
        
        params = {
            "order": "desc",
            "sort": "relevance",
            "q": query,
            "site": "stackoverflow",
            "pagesize": min(max_results, 30),
            "filter": "withbody"  # Include question body
        }
        
        # Add tags filter if provided
        if tags:
            params["tagged"] = ";".join(tags)
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        items = data.get('items', [])
        
        if not items:
            return {
                "success": True,
                "query": query,
                "results": [],
                "count": 0,
                "message": "No results found on Stack Overflow"
            }
        
        # Format results
        results = []
        for item in items:
            title = item.get('title', 'No title')
            question_id = item.get('question_id', '')
            score = item.get('score', 0)
            answer_count = item.get('answer_count', 0)
            view_count = item.get('view_count', 0)
            is_answered = item.get('is_answered', False)
            tags_list = item.get('tags', [])
            creation_date = datetime.fromtimestamp(item.get('creation_date', 0)).strftime('%Y-%m-%d')
            link = item.get('link', '')
            
            # Quality indicator based on score and answers
            if score > 5 and answer_count > 2:
                quality = "high"
            elif score > 0 and answer_count > 0:
                quality = "medium"
            else:
                quality = "low"
            
            results.append({
                "title": title,
                "url": link,
                "score": score,
                "answers": answer_count,
                "views": view_count,
                "is_answered": is_answered,
                "tags": tags_list,
                "created": creation_date,
                "quality": quality
            })
        
        # Sort by relevance (score + answers)
        results.sort(key=lambda x: x['score'] + x['answers'], reverse=True)
        results = results[:max_results]
        
        # Generate summary
        answered_count = sum(1 for r in results if r['is_answered'])
        total_score = sum(r['score'] for r in results)
        
        summary = f"Found {len(results)} Stack Overflow questions ({answered_count} answered, {total_score} total score)"
        
        return {
            "success": True,
            "query": query,
            "summary": summary,
            "results": results,
            "count": len(results),
            "answered_rate": f"{round((answered_count/len(results))*100)}%" if results else "0%",
            "source": "Stack Overflow"
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Stack Overflow API request failed: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Stack Overflow search failed: {str(e)}"
        }


def search_google_news(query: str, max_results: int = 10, period: str = "7d", country: str = "US") -> Dict:
    """
    Search Google News for latest news articles and trends.
    FREE - No API key needed! Uses GNews library.
    
    Args:
        query: Search query (e.g., "AI career market", "tech hiring trends")
        max_results: Number of articles (default: 10, max: 20)
        period: Time period - "1h", "24h", "7d", "30d" (default: "7d")
        country: Country code - "US", "GB", "IN", etc. (default: "US")
        
    Returns:
        Dict with news articles, sources, dates, and URLs
    """
    try:
        print(f"🔍 Google News search: {query}")
        
        # Import GNews
        try:
            from gnews import GNews
        except ImportError:
            return {
                "success": False,
                "error": "GNews library not installed. Run: pip3 install gnews"
            }
        
        # Initialize GNews client
        google_news = GNews(
            language='en',
            country=country,
            period=period,
            max_results=min(max_results, 20)
        )
        
        # Search for news
        articles = google_news.get_news(query)
        
        if not articles:
            return {
                "success": True,
                "query": query,
                "results": [],
                "count": 0,
                "message": "No news articles found"
            }
        
        # Format results
        results = []
        for article in articles:
            title = article.get('title', 'No title')
            description = article.get('description', '')[:200]  # Truncate
            url = article.get('url', '')
            published_date = article.get('published date', 'Unknown')
            publisher = article.get('publisher', {}).get('title', 'Unknown')
            
            results.append({
                "title": title,
                "description": description,
                "url": url,
                "published": published_date,
                "source": publisher
            })
        
        # Generate summary
        sources = list(set(r['source'] for r in results))
        summary = f"Found {len(results)} news articles from {len(sources)} sources"
        
        return {
            "success": True,
            "query": query,
            "summary": summary,
            "results": results,
            "count": len(results),
            "period": period,
            "sources": sources[:5],  # Top 5 sources
            "source": "Google News"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Google News search failed: {str(e)}"
        }


# Tool definitions for Groq function calling
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for external market data, trends, competitor insights, and current information. Use for questions requiring external market analysis, industry trends, or general knowledge. Returns AI-generated answer and top 3 high-quality results (score > 0.85).",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query (e.g., 'France market analysis 2026', 'hiring trends Europe', 'competitor pricing strategy')"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Number of results to return (default: 3, max: 3)",
                        "default": 3
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_hacker_news",
            "description": "Search Hacker News for tech discussions, product launches, startup trends, and developer opinions. FREE - no API key needed. Best for: SaaS products, tech trends, developer sentiment, startup strategies. Returns stories with points, comments, and URLs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (e.g., 'AI resume tools', 'career tech startups', 'SaaS pricing strategies')"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Number of results (default: 10, max: 20)",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_stackoverflow",
            "description": "Search Stack Overflow for technical discussions, developer opinions, and solutions. FREE - no API key needed. Best for: technical product validation, developer pain points, implementation feedback, tool comparisons. Returns questions with scores, answers, and tags.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (e.g., 'Python automation tools', 'AI career platforms', 'resume parser libraries')"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional: filter by tags (e.g., ['python', 'ai', 'automation'])"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Number of results (default: 10, max: 30)",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_google_news",
            "description": "Search Google News for latest news articles, market trends, and current events. FREE - no API key needed. Best for: industry news, competitor announcements, market trends, hiring news, regulatory changes. Returns recent articles with sources and dates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (e.g., 'AI hiring trends', 'tech layoffs 2026', 'France tech market')"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Number of articles (default: 10, max: 20)",
                        "default": 10
                    },
                    "period": {
                        "type": "string",
                        "enum": ["1h", "24h", "7d", "30d"],
                        "description": "Time period (default: '7d' for last 7 days)",
                        "default": "7d"
                    },
                    "country": {
                        "type": "string",
                        "description": "Country code for localized news (e.g., 'US', 'GB', 'FR', 'IN'). Default: 'US'",
                        "default": "US"
                    }
                },
                "required": ["query"]
            }
        }
    }
]

# Add business tools and document search to definitions
TOOL_DEFINITIONS.extend(BUSINESS_TOOL_DEFINITIONS)
TOOL_DEFINITIONS.extend(DOCUMENT_SEARCH_TOOLS)

# Map function names to actual functions
TOOL_FUNCTIONS = {
    "web_search": web_search,
    "search_hacker_news": search_hacker_news,
    "search_stackoverflow": search_stackoverflow,
    "search_google_news": search_google_news,
    "search_documents": search_documents
}

# Add business tool functions
TOOL_FUNCTIONS.update(BUSINESS_TOOL_FUNCTIONS)
