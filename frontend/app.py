import streamlit as st
import requests
import time

# Configure page
st.set_page_config(page_title="Decision AI Agent", page_icon="🤖", layout="wide")

# Backend API URL
BACKEND_URL = "http://localhost:8000"

# Initialize session state for conversation history
if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_sources" not in st.session_state:
    st.session_state.last_sources = None

# App title
st.title("🤖 Decision AI Agent")
st.caption("Powered by Groq AI with Web Search & Database")

# Sidebar
with st.sidebar:
    st.markdown("## ℹ️ About")
    st.markdown("""
    This AI agent can:
    - 🔍 Search the web for information
    - 💾 Save searches to database (with permission)
    - 📚 Retrieve search history
    - 📊 Show statistics
    - 🗑️ Delete searches (with confirmation)
    """)
    
    st.markdown("### 💡 Try asking:")
    st.markdown("""
    - Who is Elon Musk?
    - What is quantum computing?
    - Save this to database
    - Show my search history
    - What are my database stats?
    """)
    
    if st.button("🔄 Reset Conversation"):
        try:
            response = requests.post(f"{BACKEND_URL}/agent/reset", timeout=5)
            if response.status_code == 200:
                st.session_state.messages = []
                st.session_state.last_sources = None
                st.success("Conversation reset!")
                st.rerun()
        except:
            st.error("Failed to reset conversation")
    
    st.markdown("---")
    
    # Check backend status
    try:
        status = requests.get(f"{BACKEND_URL}/", timeout=2)
        if status.status_code == 200:
            data = status.json()
            st.success("✅ Backend connected")
            
            if data.get("agent_configured"):
                st.success("✅ Agent ready")
            else:
                st.warning("⚠️ Agent not configured")
            
            if data.get("dynamodb_configured"):
                st.success("✅ Database connected")
            else:
                st.info("ℹ️ Database not configured")
        else:
            st.error("❌ Backend error")
    except:
        st.error("❌ Backend offline")

# Display conversation history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Display sources if available
        if message["role"] == "assistant" and message.get("sources"):
            st.markdown("---")
            st.markdown("**📚 References:**")
            for idx, source in enumerate(message["sources"], 1):
                st.markdown(f"{idx}. [{source['title']}]({source['url']}) - *Score: {source['score']:.2f}*")

# Chat input
if prompt := st.chat_input("Ask me anything..."):
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Display assistant response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        try:
            # Show thinking status
            message_placeholder.markdown("🤔 Thinking...")
            
            # Send to agent
            response = requests.post(
                f"{BACKEND_URL}/agent/chat",
                json={"message": prompt},
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                agent_response = data["response"]
                sources = data.get("sources")
                
                # Display response
                message_placeholder.markdown(agent_response)
                
                # Display sources if available
                if sources and len(sources) > 0:
                    st.markdown("---")
                    st.markdown("**📚 References:**")
                    for idx, source in enumerate(sources, 1):
                        st.markdown(f"{idx}. [{source['title']}]({source['url']}) - *Score: {source['score']:.2f}*")
                
                # Add to chat history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": agent_response,
                    "sources": sources
                })
                
            else:
                error_detail = response.json().get("detail", "Unknown error")
                if "GROQ_API_KEY" in error_detail:
                    message_placeholder.error("""
                    ⚠️ **Groq API key not configured!**
                    
                    Setup Instructions:
                    1. Get free API key from https://console.groq.com
                    2. Add to `.env` file: `GROQ_API_KEY=your_key_here`
                    3. Restart the backend server
                    """)
                else:
                    message_placeholder.error(f"❌ Error: {error_detail}")
                    
        except requests.exceptions.Timeout:
            message_placeholder.error("⏱️ Request timed out. The agent might be processing a complex query.")
        except requests.exceptions.ConnectionError:
            message_placeholder.error("""
            ⚠️ **Cannot connect to backend**
            
            Make sure the backend is running:
            ```
            uvicorn backend.main:app --reload
            ```
            """)
        except Exception as e:
            message_placeholder.error(f"❌ An error occurred: {str(e)}")
