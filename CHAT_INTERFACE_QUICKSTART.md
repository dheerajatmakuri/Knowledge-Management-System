# Chat Interface Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Prerequisites
- Python 3.10+
- OpenAI API key
- Project dependencies installed

### Step 1: Set Up Environment

```bash
# Navigate to project directory
cd knowledge-management-system

# Activate virtual environment (if using one)
# Windows PowerShell:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Set OpenAI API key
# Windows PowerShell:
$env:OPENAI_API_KEY = "sk-your-key-here"
# Linux/Mac:
export OPENAI_API_KEY="sk-your-key-here"
```

### Step 2: Install Dependencies

```bash
# Install Streamlit if not already installed
pip install streamlit

# Verify all dependencies
pip install -r requirements.txt
```

### Step 3: Launch Interface

```bash
streamlit run src/ui/chat_interface.py
```

The interface will automatically open at `http://localhost:8501` 🎉

---

## 💬 Using the Chat Interface

### Basic Usage

1. **Type Your Question**
   - Use the text area at the bottom
   - Example: "What are the key concepts in machine learning?"

2. **Send Message**
   - Click "💬 Send Message" button
   - Or press Ctrl+Enter (in text area)

3. **View Response**
   - See AI-generated answer
   - Check knowledge scope indicator
   - Review confidence level
   - Explore source citations

### Understanding Indicators

#### Knowledge Scope
- 🟢 **IN SCOPE**: Complete answer available from knowledge base
- 🟠 **PARTIAL**: Some information available, gaps identified
- 🔴 **OUT OF SCOPE**: No relevant information in knowledge base

#### Confidence Levels
- ✓ **HIGH**: Strong confidence (85-100%)
- ~ **MEDIUM**: Moderate confidence (70-85%)
- ! **LOW**: Limited confidence (50-70%)
- ? **UNCERTAIN**: Cannot provide reliable answer (<50%)

### Features at a Glance

#### 💡 Smart Suggestions
- Click any suggestion chip for instant query
- Suggestions adapt based on conversation
- Perfect for exploring topics

#### 📚 Source Citations
- Click to expand each citation
- View snippets, URLs, authors, dates
- Check relevance scores
- Access original sources

#### 👍👎 Feedback
- Rate responses as helpful or not helpful
- Helps improve the system
- Feedback recorded per response

#### 🎮 Controls (Sidebar)
- **New Conversation**: Start fresh with new session
- **Clear History**: Remove messages, keep session
- **Download**: Export conversation as text file

---

## 🎯 Example Conversations

### Example 1: Basic Question

**Query:** "What is machine learning?"

**Expected Response:**
- Scope: IN SCOPE (if ML content exists)
- Confidence: HIGH
- Citations: 2-5 relevant sources
- Quality Score: 85-95%

**What You'll See:**
- Clear definition of machine learning
- Key concepts and applications
- Source citations with links
- Related suggestions for follow-up

### Example 2: Follow-Up Question

**Initial:** "What is machine learning?"
**Follow-Up:** "How does it differ from traditional programming?"

**Expected Response:**
- Context from previous question preserved
- Comparative analysis
- Examples highlighting differences
- Citations from both topics

### Example 3: Out of Scope Query

**Query:** "What's the weather today?"

**Expected Response:**
- Scope: OUT OF SCOPE
- Confidence: UNCERTAIN
- Message: "I don't have information about current weather..."
- Suggestion to ask knowledge-related questions

### Example 4: Partial Knowledge

**Query:** "What are the latest developments in quantum computing?"

**Expected Response:**
- Scope: PARTIAL SCOPE
- Confidence: MEDIUM
- Some information provided
- Knowledge gaps identified
- Suggestion to add more sources

---

## 📊 Understanding the UI

### Main Chat Area

```
┌────────────────────────────────────┐
│  💬 Conversation                   │
│                                    │
│  ┌────────────────────────┐        │
│  │ 👤 You:                │        │
│  │ What is machine...     │        │
│  │ [2024-10-16 14:30:00] │        │
│  └────────────────────────┘        │
│                                    │
│  ┌────────────────────────┐        │
│  │ 🤖 Assistant:          │        │
│  │ Machine learning is... │        │
│  │                        │        │
│  │ Scope: [IN SCOPE]      │        │
│  │ Confidence: [HIGH]     │        │
│  │ Quality: 92%           │        │
│  │                        │        │
│  │ 📚 Sources:            │        │
│  │ > Source 1 (Expand)    │        │
│  │ > Source 2 (Expand)    │        │
│  │                        │        │
│  │ [👍 Helpful] [👎 Not]  │        │
│  └────────────────────────┘        │
└────────────────────────────────────┘
```

### Sidebar Stats

```
┌─────────────────┐
│ 📊 Session Info │
│ Session: abc123 │
│ Messages: 8     │
│                 │
│ 📈 Service Stats│
│ Total: 150      │
│ Avg Time: 2.3s  │
│                 │
│ Scope Dist:     │
│ IN: 70%    ████ │
│ PARTIAL: 20% ██ │
│ OUT: 10%     █  │
└─────────────────┘
```

---

## 🔧 Troubleshooting

### Problem: Interface Won't Start

**Error:** `ModuleNotFoundError: No module named 'streamlit'`

**Solution:**
```bash
pip install streamlit
```

### Problem: API Key Error

**Error:** "OpenAI API key not found"

**Solution:**
```bash
# Check if key is set
echo $env:OPENAI_API_KEY  # PowerShell
echo $OPENAI_API_KEY      # Linux/Mac

# Set the key
$env:OPENAI_API_KEY = "sk-..."  # PowerShell
export OPENAI_API_KEY="sk-..."  # Linux/Mac
```

### Problem: No Citations Displayed

**Cause:** No content in knowledge base

**Solution:**
1. Run web scraper to collect content
2. Check database has content:
```bash
python -c "from src.database.models import Content; from src.database.repository import Repository; repo = Repository(); print(f'Content: {len(repo.get_all_content())}')"
```

### Problem: Slow Responses

**Causes:**
- Using GPT-4 (slower but higher quality)
- Large knowledge base
- Network latency

**Solutions:**
1. **Use faster model:**
```python
# Edit chat_service.py
self.model = "gpt-3.5-turbo"  # Instead of "gpt-4"
```

2. **Reduce search results:**
```python
# Edit chat_service.py
max_results=3  # Instead of 5
```

3. **Check internet speed:**
```bash
# Test OpenAI API
curl https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Problem: Port Already in Use

**Error:** `OSError: [Errno 98] Address already in use`

**Solution:**
```bash
# Use different port
streamlit run src/ui/chat_interface.py --server.port 8502

# Or kill existing process
# Windows:
taskkill /F /IM streamlit.exe
# Linux/Mac:
pkill -f streamlit
```

---

## ⚙️ Configuration Tips

### Custom Port

```bash
streamlit run src/ui/chat_interface.py --server.port 8080
```

### Auto-Reload on Changes

```bash
streamlit run src/ui/chat_interface.py --server.runOnSave true
```

### Disable Usage Stats

Create `.streamlit/config.toml`:
```toml
[browser]
gatherUsageStats = false
```

### Custom Theme

Create `.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#FF6B6B"
backgroundColor = "#1a1a1a"
secondaryBackgroundColor = "#2d2d2d"
textColor = "#ffffff"
font = "sans serif"
```

---

## 🎓 Pro Tips

### 1. Use Specific Questions
**Good:** "What are the key differences between supervised and unsupervised learning?"
**Better:** "Compare supervised and unsupervised learning with examples"

### 2. Leverage Suggestions
- Click suggestions after responses for natural flow
- Suggestions are context-aware
- Save time typing follow-ups

### 3. Check Citations
- Always verify source relevance
- Higher relevance scores = better matches
- Click URLs to read full context

### 4. Provide Feedback
- Help improve response quality
- Feedback trains the system
- Rate honestly for best results

### 5. Start New Conversations
- Use "New Conversation" for unrelated topics
- Keeps context focused
- Improves suggestion quality

### 6. Export Important Chats
- Download conversations for reference
- Text format works everywhere
- Preserves all Q&A pairs

---

## 📚 Additional Resources

### Documentation
- **Full Documentation:** `docs/CHAT_INTERFACE.md`
- **Chat Service Docs:** `docs/CHAT_SERVICE.md`
- **Query Understanding:** `docs/QUERY_UNDERSTANDING.md`

### Quick References
- **Chat Service:** `CHAT_SERVICE_QUICKREF.md`
- **Query Understanding:** `QUERY_UNDERSTANDING_QUICKREF.md`

### Implementation Details
- **Architecture:** `SYSTEM_ARCHITECTURE.md`
- **Visual Guide:** `CHAT_SERVICE_VISUAL.md`

---

## 🚨 Important Notes

### API Costs
- GPT-4 costs ~$0.03 per 1K tokens (input)
- GPT-4 costs ~$0.06 per 1K tokens (output)
- Average query: ~1,500 tokens total
- **Estimated cost: $0.05-0.10 per query**

**Tips to reduce costs:**
- Use gpt-3.5-turbo (10x cheaper)
- Reduce max_results in search
- Keep queries focused

### Privacy
- Conversations stored locally in session
- OpenAI processes queries (check their privacy policy)
- No conversation data persisted to disk (unless exported)
- Citations may link to external sources

### Rate Limits
- OpenAI free tier: 3 RPM (requests per minute)
- OpenAI pay-as-you-go: 3,500 RPM
- Interface has no built-in rate limiting
- Add delays between queries if needed

---

## ✅ Checklist Before Starting

- [ ] Python 3.10+ installed
- [ ] Virtual environment activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] OpenAI API key obtained
- [ ] API key set in environment
- [ ] Content in knowledge base (run scraper if needed)
- [ ] Port 8501 available (or choose different port)

---

## 🎉 You're Ready!

Run this command to start:

```bash
streamlit run src/ui/chat_interface.py
```

Then open your browser to `http://localhost:8501` and start chatting!

---

## 🆘 Need Help?

### Common Commands

```bash
# Start interface
streamlit run src/ui/chat_interface.py

# Start with custom port
streamlit run src/ui/chat_interface.py --server.port 8080

# Check Streamlit version
streamlit --version

# View Streamlit config
streamlit config show

# Clear Streamlit cache
streamlit cache clear
```

### Debug Mode

```bash
# Run with verbose logging
LOG_LEVEL=DEBUG streamlit run src/ui/chat_interface.py
```

### Check Dependencies

```bash
# Verify all imports work
python -c "from src.ui.chat_interface import main; print('✓ All imports successful')"
```

---

**Happy Chatting! 💬✨**