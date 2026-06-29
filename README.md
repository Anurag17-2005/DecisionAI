# AI-Powered Web Search Application

A modern AI agent application with web search and database management, powered by Groq AI, Tavily API, and AWS DynamoDB.

## 🌟 Features

- 🤖 **AI Agent** - Groq-powered conversational agent
- 🔍 **Web Search** - Real-time search via Tavily API  
- 🗣️ **Social Media Search** - Hacker News, Stack Overflow & Google News
- 💾 **Database** - Business intelligence data in AWS DynamoDB
- 💬 **Chat Interface** - ChatGPT-style UI
- 🛡️ **Permission-Based** - Agent asks before DB operations
- 📚 **Source References** - Links to all sources
- 📊 **Multi-Source Intelligence** - 4 external + 6 internal data sources

## 📁 Project Structure

```
Decision AI/
├── agent/          # AI Agent (Groq)
├── backend/        # FastAPI Backend
├── frontend/       # Streamlit UI
├── tests/          # Test Scripts
└── docs/           # Documentation
```

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for details.

## 🚀 Installation

### 1. Clone and Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get Tavily API Key

1. Sign up at [https://tavily.com](https://tavily.com)
2. Get your free API key from the dashboard

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your Tavily API key:
```
TAVILY_API_KEY=your_actual_api_key_here
```

## 🎯 Running the Application

### Step 1: Start the Backend (FastAPI)

Open a terminal and run:
```bash
uvicorn backend.main:app --reload
```

The backend will start on `http://localhost:8000`

You should see:
- ✅ Backend API is running
- ✅ Tavily client initialized

### Step 2: Start the Frontend (Streamlit)

Open a **new terminal** and run:
```bash
streamlit run frontend/app.py
```

The frontend will open in your browser at `http://localhost:8501`

## 💻 Usage

1. Enter your search query in the search bar
2. Click the "🔍 Search" button
3. View the AI-generated summary at the top
4. Explore detailed sources below with clickable links
5. Check the backend terminal to see API activity

### Example Queries

- "What is quantum computing?"
- "Latest developments in AI"
- "How does photosynthesis work?"
- "Best practices for Python programming"

## 🔧 API Configuration

### Search Depth Options

Edit `backend/main.py` to adjust search behavior:

```python
response = tavily_client.search(
    query=search_query.query,
    search_depth="advanced",   # or "basic" (advanced recommended for AI answers)
    max_results=5,             # adjust number of results (1-10)
    include_answer=True        # explicitly request AI answer generation
)
```

- **basic**: Faster, good for general queries, may not include AI-generated answers
- **advanced**: More comprehensive, includes AI-generated summaries (recommended, currently in use)

**Note**: If you experience `"answer": null` issues, ensure you're using `search_depth="advanced"`.

## 🛠️ Tech Stack

- **Frontend**: Streamlit 1.28.1
- **Backend**: FastAPI 0.104.1
- **Search API**: Tavily Python SDK 0.3.3
- **Server**: Uvicorn 0.24.0

## 📝 API Endpoints

### `GET /`
Health check endpoint
- Returns backend status and Tavily configuration status

### `POST /search`
Perform web search
- **Input**: `{"query": "search term"}`
- **Output**: 
```json
{
  "query": "search term",
  "answer": "AI-generated summary",
  "results": [
    {
      "title": "Result title",
      "content": "Content snippet",
      "url": "https://...",
      "score": 0.95
    }
  ]
}
```

## 🐛 Troubleshooting

### Backend won't start
- Check if port 8000 is available
- Verify `.env` file exists with API key

### "Tavily API key not configured" error
- Ensure `.env` file is in the project root (not in backend/ folder)
- Verify `TAVILY_API_KEY` is set correctly
- Restart the backend server after adding the key

### "Cannot connect to backend" in frontend
- Make sure backend is running on port 8000
- Check for any error messages in backend terminal

### Search times out
- Check your internet connection
- Try with `search_depth="basic"` for faster results
- Verify Tavily API key is valid

### `'NoneType' object is not subscriptable` error
- This has been fixed! The backend now uses `search_depth="advanced"` 
- Properly handles cases where Tavily returns `null` for the answer
- See `TROUBLESHOOTING.md` for detailed explanation

## 📋 Terminal Output

When you perform a search, the backend terminal displays detailed information:

```
================================================================================
🔍 Search Query: your search query
================================================================================
📡 Calling Tavily API...

📊 Processing 5 results:
--------------------------------------------------------------------------------

1. 📄 Result Title
   🔗 URL: https://example.com
   📊 Score: 0.95
   📝 Content: Brief content snippet...

[... more results ...]

--------------------------------------------------------------------------------
💡 AI-GENERATED ANSWER:
--------------------------------------------------------------------------------
Full AI-generated summary displayed here
--------------------------------------------------------------------------------

✅ Successfully processed 5 results
================================================================================
```

This makes it easy to see exactly what Tavily returned and verify the search is working correctly!

## 📄 License

This project is open source and available for educational purposes.

## 🤝 Contributing

Feel free to submit issues and enhancement requests!
