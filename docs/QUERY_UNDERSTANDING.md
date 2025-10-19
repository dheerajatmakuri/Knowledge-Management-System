# Query Understanding System - Documentation

## Overview

The **Query Understanding System** analyzes natural language queries to extract intent, entities, and optimize search strategies. It processes user questions and formulates the best approach for retrieving relevant information.

## Architecture

```
User Query
    │
    ▼
┌────────────────────────────────────────────┐
│     Query Understanding Engine             │
├────────────────────────────────────────────┤
│                                            │
│  ┌──────────────┐   ┌──────────────┐     │
│  │   Intent     │   │   Entity     │     │
│  │ Classifier   │   │  Extractor   │     │
│  └──────┬───────┘   └──────┬───────┘     │
│         │                   │             │
│         └────────┬──────────┘             │
│                  │                         │
│         ┌────────▼────────┐               │
│         │  Query Expander │               │
│         └────────┬────────┘               │
│                  │                         │
│         ┌────────▼────────┐               │
│         │    Strategy     │               │
│         │   Optimizer     │               │
│         └────────┬────────┘               │
│                  │                         │
│         ┌────────▼────────┐               │
│         │   Context       │               │
│         │  Preservation   │               │
│         └─────────────────┘               │
└────────────────────────────────────────────┘
```

## Components

### 1. Intent Classifier

**Purpose:** Classifies user query intent using pattern matching

**Supported Intents:**
- **SEARCH** - General search query
- **FIND_PERSON** - Looking for a specific person
- **FIND_KNOWLEDGE** - Looking for tutorials/documentation
- **COMPARE** - Comparing two or more entities
- **LIST** - List all matching items
- **FILTER** - Filter by specific attributes
- **RECOMMEND** - Get recommendations
- **EXPLAIN** - Explanation or how-to query
- **QUESTION** - Direct yes/no question
- **UNKNOWN** - Cannot determine intent

**Pattern Examples:**
```python
FIND_PERSON:
- "Find a senior machine learning engineer"
- "Who is an expert in React?"
- "Show me data scientists"

FIND_KNOWLEDGE:
- "How to implement neural networks"
- "What is the difference between REST and GraphQL?"
- "Tutorial on Docker"

COMPARE:
- "Compare Python vs Java"
- "Which is better: AWS or Azure?"
- "Pros and cons of React"

LIST:
- "List all verified developers"
- "Show all tutorials about web development"

FILTER:
- "Only senior engineers from Google"
- "Verified profiles with AI expertise"

RECOMMEND:
- "Recommend the best resources for learning React"
- "What should I learn for data science?"

EXPLAIN:
- "Explain how transformers work"
- "Why is Kubernetes important?"

QUESTION:
- "Is Python good for web development?"
- "Can I use TensorFlow with JavaScript?"
```

### 2. Entity Extractor

**Purpose:** Extracts named entities and key terms from queries

**Supported Entity Types:**
- **PERSON** - People names (from quoted text)
- **SKILL** - Technical skills (e.g., "machine learning", "data analysis")
- **TECHNOLOGY** - Technologies and tools (e.g., "Python", "React", "Docker")
- **ROLE** - Job titles/roles (e.g., "engineer", "data scientist")
- **COMPANY** - Company names (e.g., "Google", "Microsoft")
- **LOCATION** - Geographic locations
- **DOMAIN** - Technical domains (e.g., "AI", "web development")
- **CATEGORY** - Content categories
- **DATE** - Temporal references
- **NUMBER** - Numeric values

**Knowledge Base:**
- 46+ technologies (Python, React, Docker, TensorFlow, AWS, etc.)
- 26+ roles (engineer, developer, scientist, architect, etc.)
- 30+ skills (machine learning, web development, DevOps, etc.)
- 14+ domains (AI, data science, cybersecurity, etc.)
- 14+ companies (Google, Microsoft, Amazon, etc.)

**Example:**
```python
Query: "Find senior ML engineers with TensorFlow and PyTorch from Google"

Extracted Entities:
- "senior" → ROLE (confidence: 0.90)
- "ML engineer" → ROLE (confidence: 0.90)
- "TensorFlow" → TECHNOLOGY (confidence: 0.90)
- "PyTorch" → TECHNOLOGY (confidence: 0.90)
- "Google" → COMPANY (confidence: 0.90)
```

### 3. Query Expander

**Purpose:** Expands queries with synonyms and related terms

**Expansion Sources:**
- **Synonyms** - Alternative terms with same meaning
- **Related Terms** - Conceptually related terminology

**Synonym Groups:**
```python
'engineer' → ['developer', 'programmer', 'coder']
'machine learning' → ['ml', 'deep learning', 'ai']
'data science' → ['data analysis', 'analytics']
'python' → ['py', 'python3']
'database' → ['db', 'sql', 'nosql']
```

**Related Terms:**
```python
'react' → ['javascript', 'frontend', 'ui']
'docker' → ['container', 'kubernetes', 'devops']
'tensorflow' → ['machine learning', 'neural network', 'ai']
'aws' → ['cloud', 'ec2', 's3', 'lambda']
```

**Example:**
```python
Query: "machine learning engineer with Python"

Expansion Terms:
- 'deep learning'
- 'ml'
- 'developer'
- 'python3'
- 'programmer'
```

### 4. Search Strategy Optimizer

**Purpose:** Formulates optimized search strategy based on understanding

**Strategy Components:**
- **search_methods** - Which methods to use (vector, fulltext, metadata)
- **weights** - Weight distribution across methods
- **filters** - Metadata filters to apply
- **entity_types** - Entity types to search
- **k** - Number of results
- **min_score** - Score threshold
- **expansion_terms** - Query expansion terms
- **boost_fields** - Field boosting factors
- **rerank** - Whether to apply reranking

**Intent-Based Optimization:**

| Intent | Vector Weight | Fulltext Weight | Metadata Weight | K | Notes |
|--------|---------------|-----------------|-----------------|---|-------|
| FIND_PERSON | 0.4 | 0.4 | 0.2 | 15 | Balanced search |
| FIND_KNOWLEDGE | 0.6 | 0.3 | 0.1 | 10 | Semantic focus |
| COMPARE | 0.7 | 0.2 | 0.1 | 20 | High semantic, rerank |
| LIST | 0.3 | 0.3 | 0.4 | 50 | Metadata focus |
| FILTER | 0.2 | 0.3 | 0.5 | 20 | Metadata dominant |
| RECOMMEND | 0.8 | 0.1 | 0.1 | 10 | High semantic, rerank |
| EXPLAIN | 0.6 | 0.3 | 0.1 | 5 | Knowledge search |

**Entity-Based Adjustments:**
```python
# Technical entities → Boost vector search
if has_TECHNOLOGY_entities:
    vector_weight += 0.1
    
# Verification keywords → Add filters
if "verified" in query:
    filters['is_verified'] = True
    
# Quality keywords → Raise threshold
if "best" or "top" or "expert" in query:
    min_score = 0.5
    filters['min_confidence'] = 0.7
```

### 5. Context Preservation

**Purpose:** Maintains conversation context across queries

**Tracked Information:**
- **previous_queries** - Last 10 queries
- **previous_intents** - Intent history
- **previous_entities** - Extracted entities across queries
- **session_data** - Session-specific data
- **user_preferences** - User preferences

**Use Cases:**
- Follow-up questions
- Pronoun resolution ("show me the ones from Google")
- Progressive refinement
- Personalization

**Example Context:**
```python
Session: user_123

Query 1: "Find machine learning engineers"
  Intent: SEARCH
  Entities: ['machine learning engineer']
  
Query 2: "Who has Python experience?"
  Intent: SEARCH
  Entities: ['Python']
  Context: Referring to ML engineers from Query 1
  
Query 3: "Show me the ones from Google"
  Intent: SEARCH
  Entities: ['Google']
  Context: Referring to Python ML engineers from Query 1+2
```

## API Reference

### QueryUnderstandingEngine

```python
from src.search.query_understanding import QueryUnderstandingEngine

# Initialize
engine = QueryUnderstandingEngine()

# Understand query
result = engine.understand(
    query="Find senior ML engineers with Python",
    session_id="user_123",  # Optional: for context preservation
    preserve_context=True   # Optional: enable context tracking
)

# Access results
print(f"Intent: {result.intent.value} ({result.intent_confidence})")
print(f"Entities: {[e.text for e in result.entities]}")
print(f"Expansions: {result.expanded_terms}")
print(f"Strategy: {result.search_strategy}")
```

### QueryUnderstanding Result

```python
@dataclass
class QueryUnderstanding:
    original_query: str           # Original user query
    normalized_query: str         # Normalized query text
    intent: QueryIntent           # Classified intent
    intent_confidence: float      # Intent confidence (0-1)
    entities: List[Entity]        # Extracted entities
    expanded_terms: List[str]     # Query expansion terms
    search_strategy: SearchStrategy  # Optimized strategy
    context_preserved: QueryContext  # Session context
    processing_time: float        # Processing time (seconds)
    metadata: Dict[str, Any]      # Additional metadata
```

### SearchStrategy

```python
@dataclass
class SearchStrategy:
    search_methods: List[str]         # ['vector', 'fulltext', 'metadata']
    weights: Dict[str, float]         # Method weights
    filters: Dict[str, Any]           # Metadata filters
    entity_types: List[str]           # Entity types to search
    k: int                            # Number of results
    min_score: float                  # Score threshold
    expansion_terms: List[str]        # Expansion terms
    boost_fields: Dict[str, float]    # Field boosting
    rerank: bool                      # Rerank results
```

## Usage Examples

### Basic Query Understanding

```python
engine = QueryUnderstandingEngine()

result = engine.understand("Find Python developers with React experience")

print(f"Intent: {result.intent.value}")
# Output: Intent: find_person

print(f"Entities:")
for entity in result.entities:
    print(f"  - {entity.text} ({entity.entity_type.value})")
# Output:
#   - Python (technology)
#   - developer (role)
#   - React (technology)

print(f"Strategy Weights: {result.search_strategy.weights}")
# Output: {'vector': 0.5, 'fulltext': 0.3, 'metadata': 0.2}
```

### With Context Preservation

```python
session_id = "user_123"

# First query
result1 = engine.understand(
    "Find machine learning engineers",
    session_id=session_id
)

# Follow-up query (uses context)
result2 = engine.understand(
    "Who has Python experience?",
    session_id=session_id
)

# Check context
context = engine.get_session_context(session_id)
print(f"Previous queries: {context.previous_queries}")
print(f"Total entities: {len(context.previous_entities)}")
```

### Integration with Hybrid Search

```python
from app_hybrid_search import ProductionHybridSearchService

# Initialize both systems
understanding_engine = QueryUnderstandingEngine()
search_service = ProductionHybridSearchService()

# User query
user_query = "Find senior data scientists with NLP experience"

# Understand query
understanding = understanding_engine.understand(user_query)

# Apply optimized strategy
search_service.update_search_config(
    vector_weight=understanding.search_strategy.weights['vector'],
    fulltext_weight=understanding.search_strategy.weights['fulltext'],
    metadata_weight=understanding.search_strategy.weights['metadata']
)

# Execute search
results = search_service.search(
    query=understanding.normalized_query + " " + " ".join(understanding.expanded_terms),
    k=understanding.search_strategy.k,
    entity_types=understanding.search_strategy.entity_types,
    filters=understanding.search_strategy.filters,
    min_score=understanding.search_strategy.min_score
)
```

### Custom Intent Handling

```python
result = engine.understand(query)

if result.intent == QueryIntent.COMPARE:
    # Comparison query - get more results and rerank
    k = 20
    rerank = True
    
elif result.intent == QueryIntent.RECOMMEND:
    # Recommendation - high semantic weight
    weights = {'vector': 0.8, 'fulltext': 0.1, 'metadata': 0.1}
    
elif result.intent == QueryIntent.FILTER:
    # Filter query - apply strict filters
    filters = result.search_strategy.filters
    filters['is_verified'] = True
```

## Performance Metrics

Based on testing with diverse queries:

| Metric | Value |
|--------|-------|
| Processing time | 1-5ms per query |
| Intent classification accuracy | ~75-90% |
| Entity extraction recall | ~85% |
| Known technologies | 46+ |
| Known roles | 26+ |
| Synonym groups | 12+ |

## Best Practices

### 1. Always Preserve Context for Conversations

```python
# Good - maintains context
session_id = f"user_{user_id}"
result = engine.understand(query, session_id=session_id)

# Bad - no context
result = engine.understand(query)  # Each query is independent
```

### 2. Use Expanded Terms in Search

```python
# Combine original and expanded terms
full_query = result.normalized_query
if result.expanded_terms:
    full_query += " " + " ".join(result.expanded_terms[:3])

search_results = search_service.search(full_query)
```

### 3. Apply Strategy Filters

```python
# Use extracted filters
filters = result.search_strategy.filters

# Add custom filters based on business logic
if user.is_premium:
    filters['is_verified'] = True

results = search_service.search(query, filters=filters)
```

### 4. Handle Low Confidence Intents

```python
if result.intent_confidence < 0.6:
    # Use default search strategy
    logger.warning(f"Low intent confidence: {result.intent_confidence}")
    # Fallback to balanced weights
```

### 5. Clear Old Contexts

```python
# Clear context after session ends
engine.clear_session_context(session_id)

# Or periodically clean up
for session_id in old_sessions:
    engine.clear_session_context(session_id)
```

## Troubleshooting

### Issue: Wrong Intent Classification

**Problem:** Intent is misclassified

**Solutions:**
1. Check query against pattern examples
2. Add more specific patterns to `IntentClassifier`
3. Use intent confidence to detect ambiguous queries
4. Implement feedback loop to improve patterns

### Issue: Missing Entities

**Problem:** Important entities not extracted

**Solutions:**
1. Add terms to entity dictionaries
2. Check for typos or variations
3. Use quoted strings for names: `"John Smith"`
4. Expand synonym/related term dictionaries

### Issue: Poor Expansions

**Problem:** Expansion terms not relevant

**Solutions:**
1. Review synonym dictionary for accuracy
2. Limit max_expansions parameter
3. Filter expansions by relevance
4. Build domain-specific expansion rules

### Issue: Incorrect Strategy

**Problem:** Search strategy doesn't match query

**Solutions:**
1. Review intent classification
2. Check entity extraction
3. Adjust strategy optimizer rules
4. Override strategy for specific intents

## Statistics and Monitoring

```python
# Get system statistics
stats = engine.get_statistics()

print(f"Active sessions: {stats['active_sessions']}")
print(f"Total queries: {stats['total_queries_in_context']}")
print(f"Intent patterns: {stats['intent_patterns']}")
print(f"Known technologies: {stats['known_technologies']}")
print(f"Known roles: {stats['known_roles']}")
print(f"Synonym groups: {stats['synonym_groups']}")
```

## Future Enhancements

1. **Machine Learning Intent Classification**
   - Train ML model on query corpus
   - Improve accuracy beyond pattern matching
   
2. **Advanced NER**
   - Use spaCy or transformer-based NER
   - Extract complex entities
   
3. **Query Reformulation**
   - Automatic query rewriting
   - Spelling correction
   
4. **Personalization**
   - User-specific entity preferences
   - Learning from search history
   
5. **Multi-language Support**
   - Support non-English queries
   - Cross-language entity matching

## License

Copyright 2025 Amzur. All rights reserved.
