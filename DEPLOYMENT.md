# DecisionAI Deployment Guide

## 🚀 Quick Deployment Steps

### 1️⃣ Push to GitHub

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - DecisionAI with Vector DB"

# Create repository on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/decisionai.git
git branch -M main
git push -u origin main
```

---

## 2️⃣ Deploy Backend to Render

### Option A: Using render.yaml (Automated)

1. Go to [https://render.com](https://render.com)
2. Sign up / Login
3. Click **"New +"** → **"Blueprint"**
4. Connect your GitHub repository
5. Render will detect `render.yaml` automatically
6. Add environment variables:
   - `GROQ_API_KEY` - Your Groq API key
   - `TAVILY_API_KEY` - Your Tavily API key
   - `AWS_ACCESS_KEY_ID` - Your AWS access key
   - `AWS_SECRET_ACCESS_KEY` - Your AWS secret key
   - `AWS_REGION` - us-east-1 (or your region)
7. Click **"Apply"**

### Option B: Manual Setup

1. Go to [https://render.com](https://render.com)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure:
   - **Name**: decisionai-backend
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt && python setup_vector_db.py`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
5. Add Environment Variables (same as above)
6. Click **"Create Web Service"**

### ✅ Test Backend

Once deployed, visit: `https://decisionai-backend.onrender.com/`

You should see:
```json
{
  "message": "Decision AI Backend API is running",
  "version": "2.0.0",
  "agent_configured": true
}
```

**Save your backend URL**: `https://YOUR-APP-NAME.onrender.com`

---

## 3️⃣ Create Frontend with Vercel v0

### Step 1: Design with v0

1. Go to [https://v0.dev](https://v0.dev)
2. Use this prompt:

```
Create a modern AI chat interface for DecisionAI with:

1. Clean, professional design with gradient background
2. Chat interface with:
   - Message input at bottom
   - Chat history showing user and AI messages
   - Loading indicator while AI is thinking
   - Source citations display (if available)
3. Header with logo and "DecisionAI" title
4. Reset conversation button
5. Responsive design (mobile + desktop)
6. Dark mode compatible
7. Use shadcn/ui components
8. Tailwind CSS styling

The interface should:
- Send messages to backend API: POST /agent/chat
- Display AI responses with markdown support
- Show sources if available
- Have a clean, ChatGPT-like interface
```

3. v0 will generate React/Next.js code
4. Copy the generated code

### Step 2: Configure API Endpoint

In your v0 generated code, update the API endpoint:

```typescript
// Replace this:
const API_URL = 'http://localhost:8000';

// With your Render backend URL:
const API_URL = 'https://YOUR-APP-NAME.onrender.com';
```

### Step 3: Deploy to Vercel

1. Download the v0 generated code
2. Create a new repository on GitHub
3. Push the frontend code:
```bash
git init
git add .
git commit -m "DecisionAI frontend"
git remote add origin https://github.com/YOUR_USERNAME/decisionai-frontend.git
git push -u origin main
```

4. Go to [https://vercel.com](https://vercel.com)
5. Click **"Add New Project"**
6. Import your frontend repository
7. Vercel will auto-detect Next.js
8. Add Environment Variable:
   - `NEXT_PUBLIC_API_URL` = `https://YOUR-RENDER-APP.onrender.com`
9. Click **"Deploy"**

---

## 4️⃣ Post-Deployment Setup

### Update CORS (if needed)

If you face CORS issues, update `backend/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://YOUR-VERCEL-APP.vercel.app",
        "http://localhost:3000"  # for local development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Redeploy backend after changes.

---

## 📊 What Gets Deployed

### ✅ Included in Deployment:
- Backend API (`backend/`)
- AI Agent (`agent/`)
- Vector database setup (`vector_db/`)
- Business tools and DynamoDB integration
- Document processing scripts

### ❌ Excluded (in .gitignore):
- `.env` (environment variables - add manually in Render)
- `__pycache__/` (Python cache)
- `vector_db/chroma_data/` (generated on first run)
- `business_documents/` (demo documents)
- Demo guides (DEMONSTRATION_GUIDE.md, etc.)

---

## 🔐 Environment Variables Required

### Render Backend:
```
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_REGION=us-east-1
```

### Vercel Frontend:
```
NEXT_PUBLIC_API_URL=https://your-render-app.onrender.com
```

---

## 🧪 Testing Deployment

### Test Backend:
```bash
curl https://YOUR-RENDER-APP.onrender.com/
```

### Test Agent:
```bash
curl -X POST https://YOUR-RENDER-APP.onrender.com/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How many users do we have in Berlin?"}'
```

### Test Frontend:
1. Visit your Vercel URL
2. Type: "Should we expand to Netherlands?"
3. Check if AI responds with data + sources

---

## 🐛 Troubleshooting

### Backend Issues:

**Issue**: "Groq Agent not configured"
- **Fix**: Add `GROQ_API_KEY` in Render environment variables

**Issue**: "Vector database not available"
- **Fix**: Ensure `python setup_vector_db.py` runs in build command

**Issue**: "DynamoDB connection failed"
- **Fix**: Verify AWS credentials in Render environment variables

### Frontend Issues:

**Issue**: CORS error
- **Fix**: Update CORS origins in `backend/main.py`

**Issue**: API not responding
- **Fix**: Check if Render backend URL is correct in frontend

**Issue**: "Network request failed"
- **Fix**: Render free tier sleeps after inactivity - first request takes ~30s

---

## 📈 Free Tier Limitations

### Render (Free):
- ✅ 750 hours/month free
- ⚠️ Sleeps after 15 min inactivity
- ⚠️ First request after sleep: 30-60 seconds
- ✅ Auto-deploys on git push

### Vercel (Free):
- ✅ Unlimited deployments
- ✅ 100 GB bandwidth/month
- ✅ Instant wake up (no sleep)
- ✅ Auto-deploys on git push

### Recommendation:
For production, upgrade to paid plans to avoid cold starts.

---

## 🚀 Deployment Checklist

- [ ] Create `.env.example` (template without actual keys)
- [ ] Update `.gitignore` (exclude sensitive files)
- [ ] Create `requirements.txt` (Python dependencies)
- [ ] Test locally before deploying
- [ ] Push to GitHub
- [ ] Deploy backend to Render
- [ ] Add environment variables to Render
- [ ] Test backend endpoint
- [ ] Generate frontend with v0
- [ ] Update API URL in frontend
- [ ] Deploy frontend to Vercel
- [ ] Test full application
- [ ] Share URLs with team 🎉

---

## 📝 URLs After Deployment

**Backend API**: `https://YOUR-RENDER-APP.onrender.com`
**Frontend**: `https://YOUR-VERCEL-APP.vercel.app`
**GitHub Repo**: `https://github.com/YOUR-USERNAME/decisionai`

---

## 🎉 You're Done!

Your DecisionAI is now live and accessible worldwide!

**Next Steps:**
- Share the Vercel URL with your team
- Monitor usage in Render dashboard
- Set up custom domain (optional)
- Upgrade to paid plans for production use
