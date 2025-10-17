"""
AI Chat Service with Knowledge-Grounded Responses

This service provides intelligent conversational AI that:
- Only answers based on collected knowledge (no hallucination)
- Provides source citations for every claim
- Admits knowledge gaps honestly
- Maintains conversation context
- Validates response quality

Features:
- Knowledge scope enforcement (RAG pattern)
- Source attribution and citations
- Uncertainty communication
- Context thread management
- Response quality validation
- Conversation history tracking

Copyright 2025 Amzur. All rights reserved.
"""

import os
import json
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from loguru import logger
from openai import OpenAI

from src.search.query_understanding import QueryUnderstandingEngine, QueryContext
from app_hybrid_search import ProductionHybridSearchService


class ResponseConfidence(Enum):
    """Confidence level of the response."""
    HIGH = "high"           # Strong evidence from multiple sources
    MEDIUM = "medium"       # Evidence from single source or partial match
    LOW = "low"            # Weak evidence or inference
    UNCERTAIN = "uncertain" # Insufficient information


class KnowledgeScope(Enum):
    """Scope of knowledge available."""
    IN_SCOPE = "in_scope"           # Question answerable from knowledge base
    PARTIAL_SCOPE = "partial_scope" # Partial information available
    OUT_OF_SCOPE = "out_of_scope"   # No relevant information found


@dataclass
class Citation:
    """Source citation for a claim."""
    source_id: str
    source_type: str  # 'profile', 'content', 'snippet'
    source_title: str
    source_url: Optional[str] = None
    relevance_score: float = 0.0
    excerpt: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'source_id': self.source_id,
            'source_type': self.source_type,
            'source_title': self.source_title,
            'source_url': self.source_url,
            'relevance_score': self.relevance_score,
            'excerpt': self.excerpt
        }


@dataclass
class Message:
    """Chat message with metadata."""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    citations: List[Citation] = field(default_factory=list)
    confidence: Optional[ResponseConfidence] = None
    query_context: Optional[QueryContext] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'citations': [c.to_dict() for c in self.citations],
            'confidence': self.confidence.value if self.confidence else None,
            'metadata': self.metadata
        }


@dataclass
class ChatResponse:
    """Complete chat response with metadata."""
    message: str
    citations: List[Citation]
    confidence: ResponseConfidence
    knowledge_scope: KnowledgeScope
    sources_count: int
    query_intent: Optional[str] = None
    processing_time: float = 0.0
    admitted_gaps: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'message': self.message,
            'citations': [c.to_dict() for c in self.citations],
            'confidence': self.confidence.value,
            'knowledge_scope': self.knowledge_scope.value,
            'sources_count': self.sources_count,
            'query_intent': self.query_intent,
            'processing_time': self.processing_time,
            'admitted_gaps': self.admitted_gaps,
            'suggestions': self.suggestions,
            'metadata': self.metadata
        }


class ConversationManager:
    """Manages conversation context and history."""
    
    def __init__(self, max_history: int = 10):
        """
        Initialize conversation manager.
        
        Args:
            max_history: Maximum number of messages to keep in history
        """
        self.conversations: Dict[str, List[Message]] = {}
        self.max_history = max_history
        logger.info(f"Conversation manager initialized with max_history={max_history}")
    
    def add_message(self, session_id: str, message: Message) -> None:
        """Add message to conversation history."""
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        self.conversations[session_id].append(message)
        
        # Trim history if needed
        if len(self.conversations[session_id]) > self.max_history:
            self.conversations[session_id] = self.conversations[session_id][-self.max_history:]
        
        logger.debug(f"Added message to session {session_id}, total messages: {len(self.conversations[session_id])}")
    
    def get_history(self, session_id: str, last_n: Optional[int] = None) -> List[Message]:
        """Get conversation history for a session."""
        history = self.conversations.get(session_id, [])
        if last_n:
            return history[-last_n:]
        return history
    
    def get_context_string(self, session_id: str, last_n: int = 5) -> str:
        """Get conversation context as formatted string for LLM."""
        history = self.get_history(session_id, last_n)
        if not history:
            return ""
        
        context_parts = []
        for msg in history:
            context_parts.append(f"{msg.role.upper()}: {msg.content}")
        
        return "\n".join(context_parts)
    
    def clear_session(self, session_id: str) -> None:
        """Clear conversation history for a session."""
        if session_id in self.conversations:
            del self.conversations[session_id]
            logger.info(f"Cleared session {session_id}")
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary statistics for a session."""
        history = self.get_history(session_id)
        return {
            'session_id': session_id,
            'message_count': len(history),
            'user_messages': sum(1 for m in history if m.role == 'user'),
            'assistant_messages': sum(1 for m in history if m.role == 'assistant'),
            'started_at': history[0].timestamp.isoformat() if history else None,
            'last_activity': history[-1].timestamp.isoformat() if history else None
        }


class KnowledgeScopeValidator:
    """Validates if questions are within knowledge scope."""
    
    def __init__(self, min_sources: int = 1, min_relevance: float = 0.3):
        """
        Initialize scope validator.
        
        Args:
            min_sources: Minimum number of sources required
            min_relevance: Minimum relevance score threshold
        """
        self.min_sources = min_sources
        self.min_relevance = min_relevance
        logger.info(f"Knowledge scope validator initialized with min_sources={min_sources}, min_relevance={min_relevance}")
    
    def validate_scope(self, search_results: List[Any]) -> Tuple[KnowledgeScope, int]:
        """
        Validate if search results are sufficient to answer question.
        
        Args:
            search_results: Results from hybrid search
            
        Returns:
            Tuple of (scope, valid_sources_count)
        """
        if not search_results:
            return KnowledgeScope.OUT_OF_SCOPE, 0
        
        # Filter results by relevance
        relevant_results = [r for r in search_results if r.score >= self.min_relevance]
        
        if len(relevant_results) >= self.min_sources:
            # Strong evidence - multiple relevant sources
            if len(relevant_results) >= 3 and relevant_results[0].score >= 0.6:
                return KnowledgeScope.IN_SCOPE, len(relevant_results)
            # Some evidence - fewer sources or lower relevance
            else:
                return KnowledgeScope.PARTIAL_SCOPE, len(relevant_results)
        else:
            return KnowledgeScope.OUT_OF_SCOPE, len(relevant_results)


class ResponseValidator:
    """Validates response quality and accuracy."""
    
    def __init__(self):
        """Initialize response validator."""
        logger.info("Response validator initialized")
    
    def calculate_confidence(
        self,
        knowledge_scope: KnowledgeScope,
        sources_count: int,
        top_relevance: float,
        response_has_citations: bool
    ) -> ResponseConfidence:
        """
        Calculate confidence level for response.
        
        Args:
            knowledge_scope: Scope of knowledge available
            sources_count: Number of sources used
            top_relevance: Highest relevance score
            response_has_citations: Whether response includes citations
            
        Returns:
            Confidence level
        """
        if knowledge_scope == KnowledgeScope.OUT_OF_SCOPE:
            return ResponseConfidence.UNCERTAIN
        
        if not response_has_citations:
            return ResponseConfidence.LOW
        
        # High confidence: multiple sources, high relevance
        if sources_count >= 3 and top_relevance >= 0.7:
            return ResponseConfidence.HIGH
        
        # Medium confidence: some sources, moderate relevance
        elif sources_count >= 2 and top_relevance >= 0.5:
            return ResponseConfidence.MEDIUM
        
        # Low confidence: few sources or low relevance
        elif sources_count >= 1 and top_relevance >= 0.3:
            return ResponseConfidence.LOW
        
        else:
            return ResponseConfidence.UNCERTAIN
    
    def validate_citations(self, response: str, citations: List[Citation]) -> bool:
        """
        Validate that response has proper citations.
        
        Args:
            response: Response text
            citations: List of citations
            
        Returns:
            True if citations are present and valid
        """
        # Check if citations exist
        if not citations:
            return False
        
        # Check if response is substantive (not just "I don't know")
        if len(response.split()) < 10:
            return False
        
        # Check if citations have required fields
        for citation in citations:
            if not citation.source_title or not citation.source_type:
                return False
        
        return True
    
    def extract_gaps(self, response: str) -> List[str]:
        """
        Extract admitted knowledge gaps from response.
        
        Args:
            response: Response text
            
        Returns:
            List of identified gaps
        """
        gaps = []
        gap_phrases = [
            "i don't have information",
            "i don't know",
            "not available in",
            "cannot find",
            "no information about",
            "insufficient data",
            "beyond my knowledge"
        ]
        
        response_lower = response.lower()
        for phrase in gap_phrases:
            if phrase in response_lower:
                # Extract sentence containing the gap
                sentences = response.split('.')
                for sentence in sentences:
                    if phrase in sentence.lower():
                        gaps.append(sentence.strip())
                        break
        
        return gaps


class ChatService:
    """
    AI Chat Service with knowledge-grounded responses.
    
    Features:
    - Knowledge scope enforcement (only answers from knowledge base)
    - Source attribution (provides citations for all claims)
    - Uncertainty communication (admits when it doesn't know)
    - Context management (maintains conversation history)
    - Response validation (ensures quality and accuracy)
    """
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        model: str = "gpt-4",
        max_tokens: int = 1000,
        temperature: float = 0.3
    ):
        """
        Initialize chat service.
        
        Args:
            openai_api_key: OpenAI API key (reads from env if not provided)
            model: OpenAI model to use
            max_tokens: Maximum tokens in response
            temperature: Temperature for generation (lower = more focused)
        """
        # Initialize OpenAI client
        self.api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        # Initialize components
        self.query_understanding = QueryUnderstandingEngine()
        self.search_service = ProductionHybridSearchService()
        self.conversation_manager = ConversationManager(max_history=20)
        self.scope_validator = KnowledgeScopeValidator(min_sources=1, min_relevance=0.3)
        self.response_validator = ResponseValidator()
        
        logger.success(f"Chat service initialized with model={model}")
    
    def _create_system_prompt(self) -> str:
        """Create system prompt for the LLM."""
        return """You are a knowledgeable AI assistant with access to a curated knowledge base. Your role is to:

1. KNOWLEDGE SCOPE ENFORCEMENT:
   - ONLY answer questions using information from the provided search results
   - DO NOT use any external knowledge or training data
   - If information is not in the search results, clearly state that you don't have that information

2. SOURCE ATTRIBUTION:
   - ALWAYS cite your sources using [Source: <title>] format
   - Provide specific references for each claim you make
   - Quote relevant excerpts when appropriate

3. UNCERTAINTY COMMUNICATION:
   - If you're unsure or have incomplete information, say so explicitly
   - Indicate confidence levels (e.g., "Based on available information..." or "I'm not certain, but...")
   - Admit knowledge gaps honestly rather than guessing

4. RESPONSE QUALITY:
   - Be concise but informative
   - Structure responses clearly with bullet points or paragraphs as appropriate
   - Prioritize accuracy over completeness
   - If multiple sources disagree, mention the disagreement

5. CONTEXT AWARENESS:
   - Consider the conversation history
   - Reference previous messages when relevant
   - Maintain consistency across the conversation

Remember: It's better to say "I don't have information about that" than to provide unsupported claims."""
    
    def _format_search_results(self, results: List[Any]) -> str:
        """Format search results for inclusion in prompt."""
        if not results:
            return "No relevant information found in the knowledge base."
        
        formatted = ["=== SEARCH RESULTS FROM KNOWLEDGE BASE ===\n"]
        
        for idx, result in enumerate(results[:5], 1):  # Top 5 results
            formatted.append(f"\n--- Source {idx} (Relevance: {result.score:.2%}) ---")
            formatted.append(f"Title: {result.title}")
            formatted.append(f"Type: {result.entity_type}")
            
            # Add content/description
            content = getattr(result, 'description', None) or getattr(result, 'content', '')
            if content:
                # Truncate if too long
                if len(content) > 500:
                    content = content[:500] + "..."
                formatted.append(f"Content: {content}")
            
            # Add source URL if available
            url = getattr(result, 'url', None) or getattr(result, 'profile_url', None)
            if url:
                formatted.append(f"URL: {url}")
            
            formatted.append("")
        
        return "\n".join(formatted)
    
    def _create_citations(self, results: List[Any]) -> List[Citation]:
        """Create citations from search results."""
        citations = []
        
        for result in results[:5]:  # Top 5 sources
            citation = Citation(
                source_id=str(getattr(result, 'id', '')),
                source_type=result.entity_type,
                source_title=result.title,
                source_url=getattr(result, 'url', None) or getattr(result, 'profile_url', None),
                relevance_score=result.score,
                excerpt=None  # Could extract relevant excerpt
            )
            citations.append(citation)
        
        return citations
    
    def _call_llm(
        self,
        user_query: str,
        search_context: str,
        conversation_context: str
    ) -> str:
        """
        Call OpenAI LLM with knowledge-grounded prompt.
        
        Args:
            user_query: User's question
            search_context: Formatted search results
            conversation_context: Previous conversation
            
        Returns:
            LLM response
        """
        messages = [
            {"role": "system", "content": self._create_system_prompt()}
        ]
        
        # Add conversation context if available
        if conversation_context:
            messages.append({
                "role": "system",
                "content": f"=== PREVIOUS CONVERSATION ===\n{conversation_context}\n"
            })
        
        # Add search context
        messages.append({
            "role": "system",
            "content": search_context
        })
        
        # Add user query
        messages.append({
            "role": "user",
            "content": user_query
        })
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            raise
    
    def chat(
        self,
        user_query: str,
        session_id: str = "default",
        k: int = 10
    ) -> ChatResponse:
        """
        Process user query and generate knowledge-grounded response.
        
        Args:
            user_query: User's question
            session_id: Session identifier for conversation tracking
            k: Number of search results to retrieve
            
        Returns:
            ChatResponse with answer, citations, and metadata
        """
        start_time = time.time()
        logger.info(f"Processing chat query: '{user_query}' for session {session_id}")
        
        # Add user message to history
        user_message = Message(role="user", content=user_query)
        self.conversation_manager.add_message(session_id, user_message)
        
        # Step 1: Understand query
        query_context = self.query_understanding.understand(
            query=user_query,
            session_id=session_id,
            preserve_context=True
        )
        logger.debug(f"Query intent: {query_context.intent.value}, confidence: {query_context.intent_confidence:.2f}")
        
        # Step 2: Search knowledge base
        expanded_query = f"{query_context.normalized_query} {' '.join(query_context.expanded_terms[:3])}"
        
        search_results = self.search_service.search(
            query=expanded_query,
            vector_weight=query_context.search_strategy.weights['vector'],
            fulltext_weight=query_context.search_strategy.weights['fulltext'],
            metadata_weight=query_context.search_strategy.weights['metadata'],
            k=k,
            min_score=query_context.search_strategy.min_score,
            entity_types=query_context.search_strategy.entity_types,
            filters=query_context.search_strategy.filters
        )
        
        logger.info(f"Found {len(search_results)} search results")
        

        # General role/title direct answer logic
        import re
        # Try to extract a role/title from the user query
        match = re.search(r"who is (the |a |an )?(?P<role>[\w\s\-&]+?)( at| of| for| in|\?|$)", user_query.lower())
        if match:
            role_query = match.group("role").strip()
            logger.info(f"[DEBUG] User asked for role: '{role_query}'")
            if role_query and len(role_query) > 2:
                matched_leaders = []
                for r in search_results:
                    title = (getattr(r, 'title', '') or getattr(r, 'role', '')).lower()
                    name = getattr(r, 'name', '')
                    logger.info(f"[DEBUG] Checking leader: {name} | title: {title}")
                    # Fuzzy match: role_query must be in title (ignore punctuation, case)
                    def normalize(s):
                        return re.sub(r'[^a-z0-9 ]', '', s.lower())
                    if title and normalize(role_query) in normalize(title):
                        matched_leaders.append(f"{name}: {title}")
                logger.info(f"[DEBUG] Matched leaders: {matched_leaders}")
                if matched_leaders:
                    response_text = f"The {role_query.title()}(s) found:\n" + "\n".join(f"- {c}" for c in matched_leaders)
                    citations = self._create_citations(search_results)
                    confidence = ResponseConfidence.HIGH
                    admitted_gaps = []
                    suggestions = []
                    processing_time = time.time() - start_time
                    chat_response = ChatResponse(
                        message=response_text,
                        citations=citations,
                        confidence=confidence,
                        knowledge_scope=KnowledgeScope.IN_SCOPE,
                        sources_count=len(citations),
                        query_intent=query_context.intent.value,
                        processing_time=processing_time,
                        admitted_gaps=admitted_gaps,
                        suggestions=suggestions,
                        metadata={
                            'entities_extracted': len(query_context.entities),
                            'query_expanded': len(query_context.expanded_terms) > 0,
                            'search_results_count': len(search_results)
                        }
                    )
                    assistant_message = Message(
                        role="assistant",
                        content=response_text,
                        citations=citations,
                        confidence=confidence,
                        query_context=query_context,
                        metadata=chat_response.metadata
                    )
                    self.conversation_manager.add_message(session_id, assistant_message)
                    logger.success(f"Chat response (role direct) generated in {processing_time:.2f}s with confidence: {confidence.value}")
                    return chat_response

        # Step 3: Validate knowledge scope
        knowledge_scope, valid_sources = self.scope_validator.validate_scope(search_results)
        logger.debug(f"Knowledge scope: {knowledge_scope.value}, valid sources: {valid_sources}")
        
        # Step 4: Generate response based on scope
        if knowledge_scope == KnowledgeScope.OUT_OF_SCOPE:
            # No relevant information found
            response_text = self._generate_out_of_scope_response(user_query)
            citations = []
            confidence = ResponseConfidence.UNCERTAIN
            admitted_gaps = [f"No information found about: {user_query}"]
            suggestions = self._generate_suggestions(query_context)
        
        else:
            # Generate knowledge-grounded response
            search_context = self._format_search_results(search_results)
            conversation_context = self.conversation_manager.get_context_string(session_id, last_n=5)
            
            response_text = self._call_llm(user_query, search_context, conversation_context)
            citations = self._create_citations(search_results)
            
            # Validate response
            has_citations = self.response_validator.validate_citations(response_text, citations)
            top_relevance = search_results[0].score if search_results else 0.0
            
            confidence = self.response_validator.calculate_confidence(
                knowledge_scope=knowledge_scope,
                sources_count=len(citations),
                top_relevance=top_relevance,
                response_has_citations=has_citations
            )
            
            admitted_gaps = self.response_validator.extract_gaps(response_text)
            suggestions = []
        
        # Create response
        processing_time = time.time() - start_time
        
        chat_response = ChatResponse(
            message=response_text,
            citations=citations,
            confidence=confidence,
            knowledge_scope=knowledge_scope,
            sources_count=len(citations),
            query_intent=query_context.intent.value,
            processing_time=processing_time,
            admitted_gaps=admitted_gaps,
            suggestions=suggestions,
            metadata={
                'entities_extracted': len(query_context.entities),
                'query_expanded': len(query_context.expanded_terms) > 0,
                'search_results_count': len(search_results)
            }
        )
        
        # Add assistant message to history
        assistant_message = Message(
            role="assistant",
            content=response_text,
            citations=citations,
            confidence=confidence,
            query_context=query_context,
            metadata=chat_response.metadata
        )
        self.conversation_manager.add_message(session_id, assistant_message)
        
        logger.success(f"Chat response generated in {processing_time:.2f}s with confidence: {confidence.value}")
        
        return chat_response
    
    def _generate_out_of_scope_response(self, query: str) -> str:
        """Generate response when question is out of scope."""
        return f"""I don't have information about "{query}" in my knowledge base.

My knowledge is limited to the content that has been collected and indexed in the system. To get an answer to your question, you could:

1. Try rephrasing your question with different keywords
2. Ask about related topics that might be in the knowledge base
3. Check if new content about this topic can be added to the system

Is there something else I can help you with based on the available knowledge?"""
    
    def _generate_suggestions(self, query_context: QueryContext) -> List[str]:
        """Generate alternative question suggestions."""
        suggestions = []
        
        if query_context.entities:
            # Suggest questions about extracted entities
            for entity in query_context.entities[:3]:
                suggestions.append(f"Tell me about {entity.text}")
        
        if query_context.expanded_terms:
            # Suggest questions with expanded terms
            term = query_context.expanded_terms[0]
            suggestions.append(f"What do you know about {term}?")
        
        return suggestions[:3]
    
    def get_conversation_history(
        self,
        session_id: str,
        last_n: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history for a session.
        
        Args:
            session_id: Session identifier
            last_n: Number of recent messages to retrieve
            
        Returns:
            List of message dictionaries
        """
        messages = self.conversation_manager.get_history(session_id, last_n)
        return [msg.to_dict() for msg in messages]
    
    def clear_conversation(self, session_id: str) -> None:
        """Clear conversation history for a session."""
        self.conversation_manager.clear_session(session_id)
        logger.info(f"Cleared conversation for session {session_id}")
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary of a conversation session."""
        return self.conversation_manager.get_session_summary(session_id)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get service statistics."""
        return {
            'active_sessions': len(self.conversation_manager.conversations),
            'model': self.model,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'query_understanding_stats': self.query_understanding.get_statistics(),
            'search_service_stats': self.search_service.get_statistics()
        }


def create_chat_service(
    openai_api_key: Optional[str] = None,
    model: str = "gpt-4"
) -> ChatService:
    """
    Create and initialize chat service.
    
    Args:
        openai_api_key: OpenAI API key
        model: OpenAI model to use
        
    Returns:
        Initialized ChatService
    """
    return ChatService(openai_api_key=openai_api_key, model=model)


if __name__ == "__main__":
    # Example usage
    from rich.console import Console
    from rich.panel import Panel
    
    console = Console()
    
    try:
        # Initialize service
        console.print("[yellow]Initializing chat service...[/yellow]")
        service = create_chat_service()
        console.print("[green][OK][/green] Chat service ready\n")
        
        # Example conversation
        session_id = "demo_session"
        
        queries = [
            "Who are the machine learning engineers in the knowledge base?",
            "Tell me more about their Python experience",
            "What about React developers?"
        ]
        
        for query in queries:
            console.print(f"\n[bold blue]User:[/bold blue] {query}")
            
            # Get response
            response = service.chat(query, session_id=session_id)
            
            # Display response
            console.print(f"\n[bold green]Assistant:[/bold green] {response.message}")
            console.print(f"\n[dim]Confidence: {response.confidence.value} | Sources: {response.sources_count} | Time: {response.processing_time:.2f}s[/dim]")
            
            # Display citations
            if response.citations:
                console.print("\n[bold]Sources:[/bold]")
                for i, citation in enumerate(response.citations[:3], 1):
                    console.print(f"  {i}. {citation.source_title} ({citation.relevance_score:.1%})")
        
        # Show statistics
        console.print("\n" + "=" * 80)
        stats = service.get_statistics()
        console.print(f"[bold]Statistics:[/bold]")
        console.print(f"  Active sessions: {stats['active_sessions']}")
        console.print(f"  Model: {stats['model']}")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        import traceback
        console.print(traceback.format_exc())
