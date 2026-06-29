from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from typing import List, Optional
from agent.groq_agent import GroqAgent

# Load environment variables
load_dotenv()

app = FastAPI(title="Decision AI API", version="2.0.0")

# Initialize Groq Agent
groq_agent = None
try:
    groq_agent = GroqAgent()
    print("✅ Groq Agent initialized with Business Intelligence tools")
except Exception as e:
    print(f"⚠️  Groq Agent initialization failed: {str(e)}")
    print("   Agent endpoints will not be available")

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Decision AI Backend API is running",
        "version": "2.0.0",
        "agent_configured": groq_agent is not None,
        "features": {
            "business_intelligence": True,
            "database_tables": ["users", "sales", "feature_requests", "tasks", "decisions", "competitors"]
        }
    }

# ========== AGENT CHAT ENDPOINT ==========

class ChatMessage(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    sources: Optional[List[dict]] = None

@app.post("/agent/chat", response_model=ChatResponse)
async def agent_chat(chat_message: ChatMessage):
    """
    Send message to Groq Agent
    Agent will use business intelligence tools as needed
    """
    if not groq_agent:
        raise HTTPException(
            status_code=503,
            detail="Groq Agent not configured. Please set GROQ_API_KEY in .env file"
        )
    
    try:
        print(f"\n💬 User query: {chat_message.message}")
        
        # Run agent
        response = groq_agent.run(chat_message.message)
        
        # Extract sources if last search exists
        sources = None
        last_search = groq_agent.get_last_search()
        if last_search and last_search.get("success"):
            sources = [
                {
                    "title": result.get("title"),
                    "url": result.get("url"),
                    "score": result.get("score")
                }
                for result in last_search.get("results", [])
            ]
        
        return ChatResponse(
            response=response,
            conversation_id="default",
            sources=sources
        )
        
    except Exception as e:
        print(f"❌ Error in agent chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agent/reset")
async def reset_agent():
    """Reset agent conversation"""
    if not groq_agent:
        raise HTTPException(
            status_code=503,
            detail="Groq Agent not configured"
        )
    
    groq_agent.reset_conversation()
    return {"message": "Conversation reset successfully"}
