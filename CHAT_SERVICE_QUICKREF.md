# AI Chat Service - Quick Reference

## 🚀 Quick Start

```python
from src.services.chat_service import ChatService

# Initialize
service = ChatService()

# Ask a question
response = service.chat(
    "Who are the Python developers?",
    session_id="user_123"
)

# Get answer
print(response.message)

# Check confidence
print(f"Confidence: {response.confidence.value}")

# View sources
for citation in response.citations:
    print(f"- {citation.source_title} ({citation.relevance_score:.0%})")
```

---

## 📋 Core Capabilities

| Capability | Description | Status |
|------------|-------------|--------|
| **Knowledge Scope Enforcement** | Only answers from knowledge base | ✅ |
| **Source Attribution** | Provides citations for all claims | ✅ |
| **Uncertainty Communication** | Admits knowledge gaps honestly | ✅ |
| **Context Management** | Maintains conversation history | ✅ |
| **Response Validation** | Ensures quality and accuracy | ✅ |

---

## 🎯 Common Patterns

### Pattern 1: Simple Query
```python
service = ChatService()

response = service.chat("What technologies are most common?", "session_1")
print(response.message)
```

### Pattern 2: Multi-Turn Conversation
```python
service = ChatService()
session = "conv_001"

# Turn 1
r1 = service.chat("Find ML engineers", session)

# Turn 2 (uses context)
r2 = service.chat("What about their Python experience?", session)

# Turn 3 (builds on context)
r3 = service.chat("Show me the senior ones", session)
```

### Pattern 3: Check Response Quality
```python
response = service.chat("query", "session")

# Quality checks
if response.confidence in [ResponseConfidence.HIGH, ResponseConfidence.MEDIUM]:
    print("✅ High quality response")
else:
    print("⚠️ Low confidence - verify sources")

if response.knowledge_scope == KnowledgeScope.OUT_OF_SCOPE:
    print("❌ Question out of scope")
```

### Pattern 4: Access Citations
```python
response = service.chat("query", "session")

print(f"Based on {response.sources_count} sources:")
for i, citation in enumerate(response.citations, 1):
    print(f"{i}. {citation.source_title}")
    print(f"   Relevance: {citation.relevance_score:.0%}")
    if citation.source_url:
        print(f"   URL: {citation.source_url}")
```

### Pattern 5: Handle Uncertainty
```python
response = service.chat("query", "session")

if response.admitted_gaps:
    print("Knowledge gaps identified:")
    for gap in response.admitted_gaps:
        print(f"  - {gap}")

if response.suggestions:
    print("Alternative questions:")
    for suggestion in response.suggestions:
        print(f"  - {suggestion}")
```

---

## 🔧 Configuration Options

### Basic Init
```python
service = ChatService()  # Uses defaults
```

### Custom Configuration
```python
service = ChatService(
    openai_api_key="sk-...",      # API key
    model="gpt-4",                 # Model (gpt-4, gpt-3.5-turbo)
    max_tokens=1000,               # Max response length
    temperature=0.3                # Randomness (0-1, lower=focused)
)
```

### Environment Variables
```bash
export OPENAI_API_KEY=sk-...
export CHAT_MODEL=gpt-4
export CHAT_MAX_TOKENS=1000
export CHAT_TEMPERATURE=0.3
```

---

## 📊 Response Fields

### ChatResponse Object
```python
response = service.chat("query", "session")

# Main content
response.message                  # str: Answer text
response.citations               # List[Citation]: Sources
response.confidence              # ResponseConfidence: HIGH/MEDIUM/LOW/UNCERTAIN
response.knowledge_scope         # KnowledgeScope: IN/PARTIAL/OUT

# Metadata
response.sources_count           # int: Number of sources
response.query_intent           # str: Detected intent
response.processing_time        # float: Seconds
response.admitted_gaps          # List[str]: Knowledge gaps
response.suggestions            # List[str]: Alternative questions
```

### Citation Object
```python
citation = response.citations[0]

citation.source_id              # str: Unique ID
citation.source_type            # str: 'profile', 'content', 'snippet'
citation.source_title           # str: Human-readable title
citation.source_url             # str: URL (optional)
citation.relevance_score        # float: 0.0-1.0
citation.excerpt                # str: Text excerpt (optional)
```

---

## 🎨 Confidence Levels

| Level | Criteria | Meaning |
|-------|----------|---------|
| **HIGH** | 3+ sources, relevance ≥ 0.7 | Strong evidence |
| **MEDIUM** | 2+ sources, relevance ≥ 0.5 | Moderate evidence |
| **LOW** | 1+ sources, relevance ≥ 0.3 | Weak evidence |
| **UNCERTAIN** | Insufficient sources/relevance | No good answer |

---

## 🔍 Knowledge Scope

| Scope | Meaning | Response Type |
|-------|---------|---------------|
| **IN_SCOPE** | Information available | Full answer with citations |
| **PARTIAL_SCOPE** | Some information available | Partial answer with gaps |
| **OUT_OF_SCOPE** | No information available | "I don't know" + suggestions |

---

## 🛠️ Session Management

### Create Session
```python
session_id = f"user_{user_id}"
response = service.chat("query", session_id)
```

### Get History
```python
# All messages
history = service.get_conversation_history(session_id)

# Last N messages
history = service.get_conversation_history(session_id, last_n=5)
```

### Clear Session
```python
service.clear_conversation(session_id)
```

### Session Summary
```python
summary = service.get_session_summary(session_id)
print(f"Messages: {summary['message_count']}")
print(f"Started: {summary['started_at']}")
```

---

## 📈 Statistics

```python
stats = service.get_statistics()

print(f"Active sessions: {stats['active_sessions']}")
print(f"Model: {stats['model']}")
print(f"Temperature: {stats['temperature']}")
```

---

## 🚨 Error Handling

### Missing API Key
```python
try:
    service = ChatService()
except ValueError as e:
    print("Set OPENAI_API_KEY environment variable")
```

### API Errors
```python
try:
    response = service.chat("query", "session")
except Exception as e:
    logger.error(f"Chat error: {e}")
    # Provide fallback
```

---

## 💡 Tips & Best Practices

### 1. Use Meaningful Session IDs
```python
# Good
session_id = f"user_{user_id}_{date}"

# Bad
session_id = "default"
```

### 2. Check Confidence Before Display
```python
if response.confidence == ResponseConfidence.UNCERTAIN:
    print("⚠️ Answer not reliable - insufficient sources")
```

### 3. Display Citations
```python
# Always show sources to users
print(response.message)
print("\nSources:")
for i, c in enumerate(response.citations, 1):
    print(f"[{i}] {c.source_title}")
```

### 4. Handle Out-of-Scope Gracefully
```python
if response.knowledge_scope == KnowledgeScope.OUT_OF_SCOPE:
    print("This topic isn't in our knowledge base yet.")
    if response.suggestions:
        print("Try asking about:", response.suggestions[0])
```

### 5. Monitor Processing Time
```python
if response.processing_time > 5.0:
    logger.warning(f"Slow response: {response.processing_time}s")
```

---

## 🎯 Example Use Cases

### Use Case 1: Profile Search
```python
response = service.chat(
    "Find senior Python developers with ML experience",
    session_id="search_001"
)
```

### Use Case 2: Skill Inquiry
```python
response = service.chat(
    "What technologies does John Smith know?",
    session_id="inquiry_001"
)
```

### Use Case 3: Comparison
```python
response = service.chat(
    "Compare Python vs JavaScript developers in the system",
    session_id="compare_001"
)
```

### Use Case 4: List Query
```python
response = service.chat(
    "List all data scientists with NLP experience",
    session_id="list_001"
)
```

### Use Case 5: Follow-Up Questions
```python
session = "followup_001"

# Initial query
r1 = service.chat("Find React developers", session)

# Follow-ups that use context
r2 = service.chat("What's their experience level?", session)
r3 = service.chat("Do they know TypeScript too?", session)
```

---

## 🔗 Integration Snippets

### With Streamlit
```python
import streamlit as st
from src.services.chat_service import ChatService

service = ChatService()

user_input = st.text_input("Ask:")
if user_input:
    response = service.chat(user_input, st.session_state.session_id)
    st.write(response.message)
    
    with st.expander("Sources"):
        for c in response.citations:
            st.write(f"- {c.source_title}")
```

### With FastAPI
```python
from fastapi import FastAPI
from src.services.chat_service import ChatService

app = FastAPI()
service = ChatService()

@app.post("/chat")
def chat(query: str, session_id: str):
    response = service.chat(query, session_id)
    return {
        "message": response.message,
        "confidence": response.confidence.value,
        "sources": [c.to_dict() for c in response.citations]
    }
```

### With Command Line
```python
#!/usr/bin/env python
from src.services.chat_service import ChatService
import sys

service = ChatService()
query = " ".join(sys.argv[1:])
response = service.chat(query, "cli_session")

print(response.message)
print(f"\nSources: {response.sources_count}")
```

---

## 📊 Performance

| Metric | Value |
|--------|-------|
| Query Understanding | 1-3ms |
| Hybrid Search | 25-45ms |
| LLM Generation | 1-3s |
| Validation | <1ms |
| **Total** | **~1.5-3.5s** |

---

## 🎓 Learning Path

1. **Basic Usage** → Initialize service, ask simple questions
2. **Citations** → Access and display source references
3. **Context** → Build multi-turn conversations
4. **Validation** → Check confidence and scope
5. **Integration** → Connect to UI or API

---

## 📚 Related Docs

- Full Documentation: `docs/CHAT_SERVICE.md`
- Query Understanding: `docs/QUERY_UNDERSTANDING.md`
- Hybrid Search: `docs/HYBRID_SEARCH.md`
- System Architecture: `SYSTEM_ARCHITECTURE.md`

---

## 🎉 Quick Test

```python
from src.services.chat_service import ChatService

service = ChatService()
response = service.chat("What do you know?", "test")

print(f"✅ Service works!")
print(f"   Confidence: {response.confidence.value}")
print(f"   Scope: {response.knowledge_scope.value}")
print(f"   Time: {response.processing_time:.2f}s")
```

---

Copyright 2025 Amzur. All rights reserved.
