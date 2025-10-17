"""
Query Understanding System - Analyzes user questions and optimizes search strategies.

Processes natural language queries to:
- Classify intent
- Extract entities
- Expand queries
- Preserve context
- Optimize search strategy
"""

from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
import re
from enum import Enum
from loguru import logger


class QueryIntent(Enum):
    """Types of query intents."""
    SEARCH = "search"                    # General search
    FIND_PERSON = "find_person"         # Looking for a person
    FIND_KNOWLEDGE = "find_knowledge"   # Looking for knowledge/tutorial
    COMPARE = "compare"                 # Comparing entities
    LIST = "list"                       # List all matching items
    FILTER = "filter"                   # Filter by attributes
    RECOMMEND = "recommend"             # Get recommendations
    EXPLAIN = "explain"                 # Explanation/how-to
    QUESTION = "question"               # Direct question
    UNKNOWN = "unknown"                 # Cannot determine


class EntityType(Enum):
    """Types of entities that can be extracted."""
    PERSON = "person"
    SKILL = "skill"
    TECHNOLOGY = "technology"
    ROLE = "role"
    COMPANY = "company"
    LOCATION = "location"
    DOMAIN = "domain"
    CATEGORY = "category"
    DATE = "date"
    NUMBER = "number"


@dataclass
class Entity:
    """Extracted entity from query."""
    text: str
    entity_type: EntityType
    confidence: float
    start: int
    end: int
    normalized: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QueryContext:
    """Context information for query understanding."""
    previous_queries: List[str] = field(default_factory=list)
    previous_intents: List[QueryIntent] = field(default_factory=list)
    previous_entities: List[Entity] = field(default_factory=list)
    session_data: Dict[str, Any] = field(default_factory=dict)
    user_preferences: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchStrategy:
    """Optimized search strategy based on query understanding."""
    search_methods: List[str]  # ['vector', 'fulltext', 'metadata']
    weights: Dict[str, float]  # Method weights
    filters: Dict[str, Any]    # Metadata filters
    entity_types: List[str]    # Entity types to search
    k: int                     # Number of results
    min_score: float           # Minimum score threshold
    expansion_terms: List[str] # Query expansion terms
    boost_fields: Dict[str, float]  # Field boosting
    rerank: bool               # Whether to rerank results


@dataclass
class QueryUnderstanding:
    """Complete query understanding result."""
    original_query: str
    normalized_query: str
    intent: QueryIntent
    intent_confidence: float
    entities: List[Entity]
    expanded_terms: List[str]
    search_strategy: SearchStrategy
    context_preserved: QueryContext
    processing_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class IntentClassifier:
    """Classifies query intent based on patterns and keywords."""
    
    def __init__(self):
        """Initialize intent classifier with pattern rules."""
        self.intent_patterns = {
            QueryIntent.FIND_PERSON: [
                r'\b(who is|find|show|search for)\b.*\b(person|people|expert|engineer|developer|scientist)\b',
                r'\b(looking for|need|want)\b.*\b(someone|anyone|developer|engineer|expert)\b',
                r'\bprofile.*\b(with|having|who has)\b',
                r'\b(list|show|find) all\b.*\b(people|persons|developers|engineers|experts)\b'
            ],
            QueryIntent.FIND_KNOWLEDGE: [
                r'\b(how to|how do|how can)\b',
                r'\b(what is|what are|explain|describe)\b',
                r'\b(tutorial|guide|learn|documentation|docs)\b',
                r'\b(example|sample|demo)\b.*\b(of|for)\b',
                r'\b(introduction to|basics of|getting started with)\b'
            ],
            QueryIntent.COMPARE: [
                r'\b(compare|versus|vs|difference between)\b',
                r'\b(better|best|which)\b.*\b(or|vs|versus)\b',
                r'\badvantages? of\b',
                r'\b(pros and cons|trade-?offs)\b'
            ],
            QueryIntent.LIST: [
                r'^(list|show|display|get) all\b',
                r'\ball\b.*\b(with|having|who)\b',
                r'\bevery\b.*\b(that|who|with)\b'
            ],
            QueryIntent.FILTER: [
                r'\b(filter|refine|narrow)\b',
                r'\b(only|just|exclusively)\b.*\b(with|having|from)\b',
                r'\bverified\b',
                r'\b(senior|junior|lead|principal)\b'
            ],
            QueryIntent.RECOMMEND: [
                r'\b(recommend|suggest|advice)\b',
                r'\bwhat should\b',
                r'\bbest\b.*\b(for|to)\b',
                r'\bsuitable for\b'
            ],
            QueryIntent.EXPLAIN: [
                r'\b(why|explain|describe|tell me about)\b',
                r'\b(understand|clarify)\b',
                r'\bwhat does\b.*\bmean\b',
                r'\b(definition of|meaning of)\b'
            ],
            QueryIntent.QUESTION: [
                r'^(is|are|do|does|can|could|would|should|will)\b',
                r'\?\s*$'  # Ends with question mark
            ]
        }
        
        # Compile patterns
        self.compiled_patterns = {
            intent: [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
            for intent, patterns in self.intent_patterns.items()
        }
    
    def classify(self, query: str) -> Tuple[QueryIntent, float]:
        """
        Classify query intent.
        
        Args:
            query: User query
        
        Returns:
            Tuple of (intent, confidence)
        """
        query_lower = query.lower().strip()
        
        # Check each intent
        intent_scores = {}
        
        for intent, patterns in self.compiled_patterns.items():
            matches = sum(1 for pattern in patterns if pattern.search(query_lower))
            if matches > 0:
                # Higher confidence with more pattern matches
                confidence = min(0.95, 0.6 + (matches * 0.15))
                intent_scores[intent] = confidence
        
        # Return best match
        if intent_scores:
            best_intent = max(intent_scores.items(), key=lambda x: x[1])
            return best_intent[0], best_intent[1]
        
        # Default to search with low confidence
        return QueryIntent.SEARCH, 0.4


class EntityExtractor:
    """Extracts named entities and key terms from queries."""
    
    def __init__(self):
        """Initialize entity extractor with keyword dictionaries."""
        # Technology keywords
        self.technologies = {
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'ruby', 'go', 'rust',
            'react', 'angular', 'vue', 'node.js', 'django', 'flask', 'spring', 'express',
            'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'pandas', 'numpy',
            'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'jenkins', 'git', 'terraform',
            'sql', 'nosql', 'mongodb', 'postgresql', 'mysql', 'redis', 'elasticsearch',
            'html', 'css', 'sass', 'webpack', 'babel', 'graphql', 'rest', 'api'
        }
        
        # Role/job titles
        self.roles = {
            'engineer', 'developer', 'programmer', 'scientist', 'analyst', 'architect',
            'manager', 'director', 'lead', 'senior', 'junior', 'principal', 'staff',
            'software engineer', 'data scientist', 'machine learning engineer', 'ml engineer',
            'data engineer', 'devops engineer', 'full stack', 'frontend', 'backend',
            'ai researcher', 'research scientist', 'cloud architect', 'security engineer'
        }
        
        # Skills
        self.skills = {
            'machine learning', 'deep learning', 'nlp', 'computer vision', 'data analysis',
            'web development', 'mobile development', 'cloud computing', 'devops', 'cicd',
            'data engineering', 'mlops', 'software engineering', 'system design',
            'algorithms', 'data structures', 'databases', 'distributed systems',
            'microservices', 'api design', 'testing', 'debugging', 'optimization'
        }
        
        # Domains
        self.domains = {
            'artificial intelligence', 'machine learning', 'data science', 'web development',
            'mobile development', 'cloud computing', 'cybersecurity', 'blockchain',
            'iot', 'robotics', 'fintech', 'healthcare', 'e-commerce', 'education'
        }
        
        # Companies
        self.companies = {
            'google', 'microsoft', 'amazon', 'facebook', 'meta', 'apple', 'netflix',
            'uber', 'airbnb', 'tesla', 'openai', 'anthropic', 'deepmind', 'nvidia'
        }
        
        # Combine all for faster lookup
        self.all_keywords = {
            **{k: EntityType.TECHNOLOGY for k in self.technologies},
            **{k: EntityType.ROLE for k in self.roles},
            **{k: EntityType.SKILL for k in self.skills},
            **{k: EntityType.DOMAIN for k in self.domains},
            **{k: EntityType.COMPANY for k in self.companies}
        }
    
    def extract(self, query: str) -> List[Entity]:
        """
        Extract entities from query.
        
        Args:
            query: User query
        
        Returns:
            List of extracted entities
        """
        entities = []
        query_lower = query.lower()
        
        # Extract multi-word entities first (longer matches take precedence)
        sorted_keywords = sorted(self.all_keywords.keys(), key=len, reverse=True)
        
        matched_spans = set()
        
        for keyword in sorted_keywords:
            # Find all occurrences
            start = 0
            while True:
                pos = query_lower.find(keyword, start)
                if pos == -1:
                    break
                
                end = pos + len(keyword)
                
                # Check if this span overlaps with existing matches
                span = (pos, end)
                if not any(pos < e < end or pos < s < end for s, e in matched_spans):
                    entity_type = self.all_keywords[keyword]
                    
                    entities.append(Entity(
                        text=query[pos:end],
                        entity_type=entity_type,
                        confidence=0.9,
                        start=pos,
                        end=end,
                        normalized=keyword
                    ))
                    
                    matched_spans.add(span)
                
                start = pos + 1
        
        # Sort by position
        entities.sort(key=lambda e: e.start)
        
        # Extract quoted strings as potential person names
        quoted_pattern = r'"([^"]+)"'
        for match in re.finditer(quoted_pattern, query):
            text = match.group(1)
            if not any(e.start <= match.start() < e.end for e in entities):
                entities.append(Entity(
                    text=text,
                    entity_type=EntityType.PERSON,
                    confidence=0.7,
                    start=match.start(),
                    end=match.end(),
                    normalized=text.lower()
                ))
        
        return entities


class QueryExpander:
    """Expands queries with synonyms and related terms."""
    
    def __init__(self):
        """Initialize query expander with synonym dictionaries."""
        self.synonyms = {
            'engineer': ['developer', 'programmer', 'coder'],
            'developer': ['engineer', 'programmer'],
            'scientist': ['researcher', 'analyst'],
            'expert': ['specialist', 'professional', 'guru'],
            'machine learning': ['ml', 'deep learning', 'ai'],
            'artificial intelligence': ['ai', 'machine learning', 'ml'],
            'web development': ['web dev', 'frontend', 'backend', 'full stack'],
            'data science': ['data analysis', 'analytics', 'data engineering'],
            'python': ['py', 'python3'],
            'javascript': ['js', 'node', 'typescript'],
            'database': ['db', 'sql', 'nosql', 'data store'],
            'cloud': ['aws', 'azure', 'gcp', 'cloud computing']
        }
        
        self.related_terms = {
            'react': ['javascript', 'frontend', 'ui', 'component'],
            'docker': ['container', 'kubernetes', 'devops', 'deployment'],
            'tensorflow': ['machine learning', 'deep learning', 'neural network', 'ai'],
            'aws': ['cloud', 'amazon', 'ec2', 's3', 'lambda'],
            'nlp': ['natural language', 'text processing', 'language model'],
            'api': ['rest', 'graphql', 'endpoint', 'web service']
        }
    
    def expand(self, query: str, entities: List[Entity], max_expansions: int = 5) -> List[str]:
        """
        Expand query with synonyms and related terms.
        
        Args:
            query: Original query
            entities: Extracted entities
            max_expansions: Maximum expansion terms to add
        
        Returns:
            List of expansion terms
        """
        expansions = set()
        query_lower = query.lower()
        
        # Expand based on entities
        for entity in entities:
            normalized = entity.normalized or entity.text.lower()
            
            # Add synonyms
            if normalized in self.synonyms:
                expansions.update(self.synonyms[normalized][:2])
            
            # Add related terms
            if normalized in self.related_terms:
                expansions.update(self.related_terms[normalized][:2])
        
        # Expand based on query terms
        words = re.findall(r'\b\w+\b', query_lower)
        for word in words:
            if word in self.synonyms:
                expansions.add(self.synonyms[word][0])
            if word in self.related_terms:
                expansions.add(self.related_terms[word][0])
        
        # Remove terms already in query
        expansions = {term for term in expansions if term not in query_lower}
        
        # Return limited set
        return list(expansions)[:max_expansions]


class SearchStrategyOptimizer:
    """Optimizes search strategy based on query understanding."""
    
    def optimize(self,
                 query: str,
                 intent: QueryIntent,
                 entities: List[Entity],
                 context: QueryContext) -> SearchStrategy:
        """
        Optimize search strategy based on query understanding.
        
        Args:
            query: User query
            intent: Classified intent
            entities: Extracted entities
            context: Query context
        
        Returns:
            Optimized search strategy
        """
        # Default strategy
        strategy = SearchStrategy(
            search_methods=['vector', 'fulltext', 'metadata'],
            weights={'vector': 0.5, 'fulltext': 0.3, 'metadata': 0.2},
            filters={},
            entity_types=[],
            k=10,
            min_score=0.3,
            expansion_terms=[],
            boost_fields={},
            rerank=False
        )
        
        # Optimize based on intent
        if intent == QueryIntent.FIND_PERSON:
            strategy.entity_types = ['profile']
            strategy.weights = {'vector': 0.4, 'fulltext': 0.4, 'metadata': 0.2}
            strategy.k = 15
            strategy.boost_fields = {'name': 2.0, 'title': 1.5}
        
        elif intent == QueryIntent.FIND_KNOWLEDGE:
            strategy.entity_types = ['snippet', 'content']
            strategy.weights = {'vector': 0.6, 'fulltext': 0.3, 'metadata': 0.1}
            strategy.k = 10
            strategy.boost_fields = {'title': 1.5, 'content': 1.0}
        
        elif intent == QueryIntent.COMPARE:
            strategy.weights = {'vector': 0.7, 'fulltext': 0.2, 'metadata': 0.1}
            strategy.k = 20
            strategy.rerank = True
        
        elif intent == QueryIntent.LIST:
            strategy.weights = {'vector': 0.3, 'fulltext': 0.3, 'metadata': 0.4}
            strategy.k = 50
            strategy.min_score = 0.2
        
        elif intent == QueryIntent.FILTER:
            strategy.weights = {'vector': 0.2, 'fulltext': 0.3, 'metadata': 0.5}
            strategy.k = 20
        
        elif intent == QueryIntent.RECOMMEND:
            strategy.weights = {'vector': 0.8, 'fulltext': 0.1, 'metadata': 0.1}
            strategy.k = 10
            strategy.rerank = True
        
        elif intent == QueryIntent.EXPLAIN:
            strategy.entity_types = ['snippet', 'content']
            strategy.weights = {'vector': 0.6, 'fulltext': 0.3, 'metadata': 0.1}
            strategy.k = 5
        
        # Apply entity-based filters
        for entity in entities:
            if entity.entity_type == EntityType.ROLE:
                if not strategy.entity_types:
                    strategy.entity_types = ['profile']
            
            elif entity.entity_type == EntityType.SKILL or entity.entity_type == EntityType.TECHNOLOGY:
                # Boost semantic search for technical queries
                strategy.weights['vector'] = min(0.8, strategy.weights['vector'] + 0.1)
                strategy.weights['fulltext'] = max(0.1, strategy.weights['fulltext'] - 0.05)
        
        # Check for verification keywords
        query_lower = query.lower()
        if 'verified' in query_lower or 'authentic' in query_lower:
            strategy.filters['is_verified'] = True
        
        # Check for seniority keywords
        if any(word in query_lower for word in ['senior', 'lead', 'principal', 'staff']):
            strategy.filters['min_confidence'] = 0.8
        
        # Check for quality keywords
        if any(word in query_lower for word in ['best', 'top', 'excellent', 'expert']):
            strategy.min_score = 0.5
            strategy.filters['min_confidence'] = 0.7
        
        return strategy


class QueryUnderstandingEngine:
    """
    Main query understanding engine that orchestrates all components.
    """
    
    def __init__(self):
        """Initialize query understanding engine."""
        self.intent_classifier = IntentClassifier()
        self.entity_extractor = EntityExtractor()
        self.query_expander = QueryExpander()
        self.strategy_optimizer = SearchStrategyOptimizer()
        
        # Context tracking
        self.contexts: Dict[str, QueryContext] = {}
        
        logger.success("Query understanding engine initialized")
    
    def understand(self,
                   query: str,
                   session_id: Optional[str] = None,
                   preserve_context: bool = True) -> QueryUnderstanding:
        """
        Understand and analyze a user query.
        
        Args:
            query: User query
            session_id: Session identifier for context preservation
            preserve_context: Whether to preserve context across queries
        
        Returns:
            Complete query understanding result
        """
        import time
        start_time = time.time()
        
        logger.info(f"Understanding query: '{query}'")
        
        # Get or create context
        if session_id and preserve_context:
            context = self.contexts.get(session_id, QueryContext())
        else:
            context = QueryContext()
        
        # Normalize query
        normalized_query = self._normalize_query(query)
        
        # Classify intent
        intent, intent_confidence = self.intent_classifier.classify(normalized_query)
        logger.debug(f"Intent: {intent.value} (confidence: {intent_confidence:.2f})")
        
        # Extract entities
        entities = self.entity_extractor.extract(normalized_query)
        logger.debug(f"Extracted {len(entities)} entities")
        
        # Expand query
        expansion_terms = self.query_expander.expand(normalized_query, entities)
        logger.debug(f"Expansion terms: {expansion_terms}")
        
        # Optimize search strategy
        search_strategy = self.strategy_optimizer.optimize(
            normalized_query,
            intent,
            entities,
            context
        )
        search_strategy.expansion_terms = expansion_terms
        
        # Update context
        if preserve_context and session_id:
            context.previous_queries.append(query)
            context.previous_intents.append(intent)
            context.previous_entities.extend(entities)
            
            # Keep only recent history
            if len(context.previous_queries) > 10:
                context.previous_queries = context.previous_queries[-10:]
                context.previous_intents = context.previous_intents[-10:]
                context.previous_entities = context.previous_entities[-20:]
            
            self.contexts[session_id] = context
        
        processing_time = time.time() - start_time
        
        result = QueryUnderstanding(
            original_query=query,
            normalized_query=normalized_query,
            intent=intent,
            intent_confidence=intent_confidence,
            entities=entities,
            expanded_terms=expansion_terms,
            search_strategy=search_strategy,
            context_preserved=context,
            processing_time=processing_time,
            metadata={
                'entity_count': len(entities),
                'expansion_count': len(expansion_terms),
                'has_context': len(context.previous_queries) > 0
            }
        )
        
        logger.info(f"Query understanding completed in {processing_time:.3f}s")
        
        return result
    
    def _normalize_query(self, query: str) -> str:
        """
        Normalize query text.
        
        Args:
            query: Original query
        
        Returns:
            Normalized query
        """
        # Remove extra whitespace
        normalized = ' '.join(query.split())
        
        # Remove special characters but keep important ones
        normalized = re.sub(r'[^\w\s\-\.@\+\#]', ' ', normalized)
        
        # Remove extra whitespace again
        normalized = ' '.join(normalized.split())
        
        return normalized.strip()
    
    def get_session_context(self, session_id: str) -> Optional[QueryContext]:
        """Get context for a session."""
        return self.contexts.get(session_id)
    
    def clear_session_context(self, session_id: str):
        """Clear context for a session."""
        if session_id in self.contexts:
            del self.contexts[session_id]
            logger.info(f"Cleared context for session: {session_id}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get query understanding statistics."""
        return {
            'active_sessions': len(self.contexts),
            'total_queries_in_context': sum(
                len(ctx.previous_queries) for ctx in self.contexts.values()
            ),
            'intent_patterns': len(self.intent_classifier.intent_patterns),
            'known_technologies': len(self.entity_extractor.technologies),
            'known_roles': len(self.entity_extractor.roles),
            'synonym_groups': len(self.query_expander.synonyms)
        }
