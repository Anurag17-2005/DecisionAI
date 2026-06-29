"""
Groq Agent with Function Calling
Capable of web search and DynamoDB CRUD operations
"""

import os
import json
from groq import Groq
from dotenv import load_dotenv
from typing import List, Dict, Optional
from agent.tools import TOOL_DEFINITIONS, TOOL_FUNCTIONS

load_dotenv()


def truncate_tool_result(result: Dict, max_length: int = 2000) -> Dict:
    """
    Truncate large tool results to fit context window
    
    Args:
        result: Tool function result
        max_length: Maximum characters for result
        
    Returns:
        Truncated or summarized result
    """
    result_str = json.dumps(result)
    
    if len(result_str) <= max_length:
        return result
    
    # If too large, try to summarize
    if not result.get("success"):
        return result
    
    # For sales data
    if "sales" in result and isinstance(result["sales"], list):
        sales = result["sales"]
        if len(sales) > 5:
            total_rev = sum(s.get("monthly_revenue", 0) for s in sales)
            total_users = sum(s.get("active_users", 0) for s in sales)
            top_5 = sorted(sales, key=lambda x: x.get("monthly_revenue", 0), reverse=True)[:5]
            
            return {
                "success": True,
                "summary": f"{len(sales)} countries",
                "total_revenue": round(total_rev, 2),
                "total_users": total_users,
                "top_5": top_5
            }
    
    # For users data
    if "users" in result and isinstance(result["users"], list):
        users = result["users"]
        if len(users) > 8:
            active = len([u for u in users if u.get("active")])
            plans = {}
            for u in users:
                plan = u.get("plan", "Unknown")
                plans[plan] = plans.get(plan, 0) + 1
            
            return {
                "success": True,
                "total_users": len(users),
                "active_users": active,
                "by_plan": plans,
                "sample": users[:3]
            }
    
    # For features
    if "features" in result and isinstance(result["features"], list):
        features = result["features"]
        if len(features) > 5:
            return {
                "success": True,
                "total_features": len(features),
                "top_5": features[:5]
            }
    
    # For tasks
    if "tasks" in result and isinstance(result["tasks"], list):
        tasks = result["tasks"]
        if len(tasks) > 8:
            status_count = {}
            for t in tasks:
                status = t.get("status", "Unknown")
                status_count[status] = status_count.get(status, 0) + 1
            
            return {
                "success": True,
                "total_tasks": len(tasks),
                "by_status": status_count,
                "sample": tasks[:3]
            }
    
    # For decisions
    if "decisions" in result and isinstance(result["decisions"], list):
        decisions = result["decisions"]
        if len(decisions) > 5:
            return {
                "success": True,
                "total_decisions": len(decisions),
                "top_5": decisions[:5]
            }
    
    # For competitors
    if "competitors" in result and isinstance(result["competitors"], list):
        competitors = result["competitors"]
        if len(competitors) > 5:
            return {
                "success": True,
                "total_competitors": len(competitors),
                "top_5": competitors[:5]
            }
    
    # Generic truncation - just return success and count
    return {
        "success": True,
        "note": "Result truncated due to size",
        "preview": str(result)[:500]
    }


class GroqAgent:
    """AI Agent powered by Groq with function calling capabilities"""
    
    def __init__(self, model: str = "qwen/qwen3-32b"):
        """
        Initialize Groq Agent
        
        Args:
            model: Groq model to use
        """
        self.api_key = os.getenv("GROQ_API_KEY")
        
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        self.client = Groq(api_key=self.api_key)
        self.model = model
        self.conversation_history = []
        self.last_search_data = None  # Store last search for easy insertion
        
        # System prompt - optimized to fit token limits
        self.system_prompt = """You are a Business Intelligence AI analyzing internal data + external intelligence.

**Data Sources:**
1. Internal (DynamoDB): users, sales, features, tasks, decisions, competitors
2. External: web_search, search_hacker_news, search_stackoverflow, search_google_news

**Response Rules:**
✅ ALWAYS cite sources with links: [Title](URL)
✅ Group by source: "From Google News:", "From Hacker News:", etc.
✅ Use internal data when available
✅ Be concise (200 words max)
✅ Format: **Internal Data:** / **From [Source]:** / **Recommendation:**

**Decision Types:**
- Internal only: "How many users in Germany?" → query_users(country="Germany")
- External only: "Latest AI news?" → search_google_news("AI trends")
- Strategic (BOTH): "Should we expand to France?" → query_sales + search_google_news + web_search

**Example Multi-Source Response:**
**Internal Data:**
• Current revenue: €21K/month

**From Google News:**
• [Market grows 15%](url) - Strong sector

**From Hacker News:**
• [Discussion title](url) - Positive (89 points)

**Recommendation:**
✅ Expand based on data + market validation

**Critical:** For "should we" questions, use internal data + multiple external sources."""
        
        self.conversation_history.append({
            "role": "system",
            "content": self.system_prompt
        })
        
        print(f"✅ Groq Agent initialized with model: {self.model}")
    
    def run(self, user_message: str, max_iterations: int = 5) -> str:
        """
        Run the agent with user message
        
        Args:
            user_message: User's input message
            max_iterations: Max function calling iterations
            
        Returns:
            Agent's response
        """
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        print(f"\n{'='*60}")
        print(f"💬 User: {user_message}")
        print(f"{'='*60}")
        
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            # Call Groq API
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.conversation_history,
                    tools=TOOL_DEFINITIONS,
                    tool_choice="auto",
                    temperature=0.7,
                    max_tokens=800  # Increased for better responses with data
                )
                
                assistant_message = response.choices[0].message
                
                # Check if agent wants to call a function
                if assistant_message.tool_calls:
                    # Add assistant's function call to history
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": assistant_message.content or "",
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": tc.type,
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments
                                }
                            }
                            for tc in assistant_message.tool_calls
                        ]
                    })
                    
                    # Execute each tool call
                    for tool_call in assistant_message.tool_calls:
                        function_name = tool_call.function.name
                        function_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
                        
                        print(f"\n🔧 Tool: {function_name}")
                        if function_args:
                            print(f"   Args: {json.dumps(function_args, indent=2)[:100]}...")
                        
                        # Execute the function
                        if function_name in TOOL_FUNCTIONS:
                            # Handle None/null arguments
                            if function_args is None:
                                function_args = {}
                            
                            function_result = TOOL_FUNCTIONS[function_name](**function_args)
                            
                            # Truncate large results to prevent context overflow
                            function_result = truncate_tool_result(function_result)
                            
                            # Store search data for later insertion
                            if function_name == "web_search" and function_result.get("success"):
                                self.last_search_data = function_result
                            
                            print(f"   ✅ Success")
                            
                            # Add function result to conversation
                            self.conversation_history.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": json.dumps(function_result)
                            })
                        else:
                            print(f"   ❌ Unknown function: {function_name}")
                    
                    # Continue to next iteration to get final response
                    continue
                
                else:
                    # No more function calls - return final response
                    final_response = assistant_message.content
                    
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": final_response
                    })
                    
                    print(f"\n🤖 Agent responded")
                    print(f"{'='*60}\n")
                    
                    return final_response
            
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                print(f"\n❌ {error_msg}")
                return error_msg
        
        return "Max iterations reached. Please try again."
    
    def reset_conversation(self):
        """Reset conversation history"""
        self.conversation_history = [{
            "role": "system",
            "content": self.system_prompt
        }]
        self.last_search_data = None
        print("🔄 Conversation reset")
    
    def get_last_search(self) -> Optional[Dict]:
        """Get the last search data"""
        return self.last_search_data
