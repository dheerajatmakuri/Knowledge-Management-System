"""
Streamlit Chat Interface for Knowledge Management System

This module provides a rich conversational interface with:
- Message thread visualization with role-based styling
- Source citation display with metadata
- Knowledge scope indicators (IN/PARTIAL/OUT scope)
- Intelligent query suggestions based on context
- Response quality feedback with confidence levels

Author: Knowledge Management System
Date: 2025-10-16
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

import streamlit as st
from loguru import logger

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.services.chat_service import (
    ChatService,
    Message,
    ChatResponse,
    ResponseConfidence,
    KnowledgeScope,
    Citation
)


# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

def configure_page():
    """Configure Streamlit page settings and styling."""
    st.set_page_config(
        page_title="Knowledge Chat",
        page_icon="💬",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for enhanced styling
    st.markdown("""
    <style>
    /* Main chat container */
    .main-chat-container {
        max-width: 900px;
        margin: 0 auto;
    }
    
    /* Message styling */
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
        padding: 12px 16px;
        border-radius: 8px;
        margin: 8px 0;
    }
    
    .assistant-message {
        background-color: #f5f5f5;
        border-left: 4px solid #4caf50;
        padding: 12px 16px;
        border-radius: 8px;
        margin: 8px 0;
    }
    
    /* Scope indicators */
    .scope-in {
        background-color: #4caf50;
        color: white;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.85em;
        font-weight: bold;
    }
    
    .scope-partial {
        background-color: #ff9800;
        color: white;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.85em;
        font-weight: bold;
    }
    
    .scope-out {
        background-color: #f44336;
        color: white;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.85em;
        font-weight: bold;
    }
    
    /* Confidence indicators */
    .confidence-high {
        color: #4caf50;
        font-weight: bold;
    }
    
    .confidence-medium {
        color: #ff9800;
        font-weight: bold;
    }
    
    .confidence-low {
        color: #f44336;
        font-weight: bold;
    }
    
    .confidence-uncertain {
        color: #9e9e9e;
        font-weight: bold;
    }
    
    /* Citation styling */
    .citation-box {
        background-color: #fff3e0;
        border-left: 3px solid #ff9800;
        padding: 8px 12px;
        margin: 4px 0;
        border-radius: 4px;
        font-size: 0.9em;
    }
    
    /* Suggestion chips */
    .suggestion-chip {
        display: inline-block;
        background-color: #e8eaf6;
        color: #3f51b5;
        padding: 6px 12px;
        border-radius: 16px;
        margin: 4px;
        cursor: pointer;
        border: 1px solid #c5cae9;
        font-size: 0.9em;
    }
    
    .suggestion-chip:hover {
        background-color: #c5cae9;
    }
    
    /* Metadata text */
    .metadata-text {
        color: #757575;
        font-size: 0.85em;
        font-style: italic;
    }
    
    /* Quality score */
    .quality-score {
        font-size: 0.9em;
        color: #616161;
    }
    
    /* Divider */
    .custom-divider {
        border-top: 2px solid #e0e0e0;
        margin: 16px 0;
    }
    </style>
    """, unsafe_allow_html=True)


# ============================================================================
# SESSION STATE MANAGEMENT
# ============================================================================

def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if 'chat_service' not in st.session_state:
        st.session_state.chat_service = None
    
    if 'session_id' not in st.session_state:
        st.session_state.session_id = f"streamlit_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'chat_responses' not in st.session_state:
        st.session_state.chat_responses = []
    
    if 'feedback_given' not in st.session_state:
        st.session_state.feedback_given = set()
    
    if 'suggested_queries' not in st.session_state:
        st.session_state.suggested_queries = [
            "What are the latest AI developments?",
            "Explain machine learning basics",
            "Tell me about neural networks",
            "What is deep learning?"
        ]


def initialize_chat_service():
    """Initialize the chat service with proper configuration."""
    try:
        # Check for OpenAI API key
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            st.error("⚠️ OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
            st.info("💡 The chat service requires OpenAI API access for AI-powered responses.")
            return None
        
        # Initialize chat service
        chat_service = ChatService()
        logger.info("Chat service initialized successfully")
        return chat_service
        
    except Exception as e:
        logger.error(f"Failed to initialize chat service: {e}")
        st.error(f"❌ Failed to initialize chat service: {str(e)}")
        return None


# ============================================================================
# MESSAGE DISPLAY COMPONENTS
# ============================================================================

def display_scope_indicator(scope: KnowledgeScope) -> str:
    """Generate HTML for knowledge scope indicator."""
    scope_map = {
        KnowledgeScope.IN_SCOPE: ("IN SCOPE", "scope-in"),
        KnowledgeScope.PARTIAL_SCOPE: ("PARTIAL", "scope-partial"),
        KnowledgeScope.OUT_OF_SCOPE: ("OUT OF SCOPE", "scope-out")
    }
    
    label, css_class = scope_map.get(scope, ("UNKNOWN", "scope-out"))
    return f'<span class="{css_class}">{label}</span>'


def display_confidence_indicator(confidence: ResponseConfidence) -> str:
    """Generate HTML for confidence indicator."""
    confidence_map = {
        ResponseConfidence.HIGH: ("HIGH CONFIDENCE", "confidence-high", "✓"),
        ResponseConfidence.MEDIUM: ("MEDIUM CONFIDENCE", "confidence-medium", "~"),
        ResponseConfidence.LOW: ("LOW CONFIDENCE", "confidence-low", "!"),
        ResponseConfidence.UNCERTAIN: ("UNCERTAIN", "confidence-uncertain", "?")
    }
    
    label, css_class, icon = confidence_map.get(
        confidence, 
        ("UNKNOWN", "confidence-uncertain", "?")
    )
    return f'<span class="{css_class}">{icon} {label}</span>'


def display_citation(citation: Citation, index: int):
    """Display a single citation with metadata."""
    with st.expander(f"📚 Source {index + 1}: {citation.title or 'Untitled'}", expanded=False):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if citation.snippet:
                st.markdown(f"*\"{citation.snippet}\"*")
            
            if citation.url:
                st.markdown(f"🔗 [View Source]({citation.url})")
            
            if citation.author:
                st.caption(f"👤 Author: {citation.author}")
            
            if citation.published_date:
                st.caption(f"📅 Published: {citation.published_date}")
        
        with col2:
            if citation.relevance_score is not None:
                relevance_pct = citation.relevance_score * 100
                st.metric("Relevance", f"{relevance_pct:.1f}%")


def display_knowledge_gaps(gaps: List[str]):
    """Display identified knowledge gaps."""
    if gaps:
        st.warning("⚠️ **Knowledge Gaps Identified:**")
        for gap in gaps:
            st.markdown(f"- {gap}")


def display_response_metadata(response: ChatResponse):
    """Display response metadata and quality indicators."""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Knowledge Scope:**")
        st.markdown(display_scope_indicator(response.scope), unsafe_allow_html=True)
    
    with col2:
        st.markdown("**Confidence:**")
        st.markdown(display_confidence_indicator(response.confidence), unsafe_allow_html=True)
    
    with col3:
        if response.quality_score is not None:
            quality_pct = response.quality_score * 100
            st.metric("Quality Score", f"{quality_pct:.1f}%")


def display_message_thread():
    """Display the complete message thread with styling."""
    st.markdown("### 💬 Conversation")
    
    if not st.session_state.messages:
        st.info("👋 Start a conversation by asking a question below!")
        return
    
    # Display messages with their associated responses
    for idx, msg in enumerate(st.session_state.messages):
        if msg['role'] == 'user':
            # User message
            st.markdown(f"""
            <div class="user-message">
                <strong>👤 You:</strong><br/>
                {msg['content']}
                <div class="metadata-text">{msg.get('timestamp', '')}</div>
            </div>
            """, unsafe_allow_html=True)
            
        else:
            # Assistant message with full response details
            response_idx = msg.get('response_idx')
            if response_idx is not None and response_idx < len(st.session_state.chat_responses):
                response = st.session_state.chat_responses[response_idx]
                
                st.markdown(f"""
                <div class="assistant-message">
                    <strong>🤖 Assistant:</strong><br/>
                    {msg['content']}
                    <div class="metadata-text">{msg.get('timestamp', '')}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Response metadata
                with st.container():
                    display_response_metadata(response)
                    
                    # Citations
                    if response.citations:
                        st.markdown("**📚 Sources:**")
                        for idx, citation in enumerate(response.citations):
                            display_citation(citation, idx)
                    
                    # Knowledge gaps
                    if response.knowledge_gaps:
                        display_knowledge_gaps(response.knowledge_gaps)
                    
                    # Feedback section
                    feedback_key = f"feedback_{response_idx}"
                    if feedback_key not in st.session_state.feedback_given:
                        col1, col2, col3 = st.columns([1, 1, 4])
                        with col1:
                            if st.button("👍 Helpful", key=f"helpful_{response_idx}"):
                                st.session_state.feedback_given.add(feedback_key)
                                st.success("Thanks for your feedback!")
                                st.rerun()
                        with col2:
                            if st.button("👎 Not Helpful", key=f"not_helpful_{response_idx}"):
                                st.session_state.feedback_given.add(feedback_key)
                                st.info("Thanks for your feedback!")
                                st.rerun()
                    else:
                        st.caption("✓ Feedback received")
        
        # Divider between messages
        if idx < len(st.session_state.messages) - 1:
            st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)


# ============================================================================
# QUERY SUGGESTIONS
# ============================================================================

def generate_contextual_suggestions(chat_service: ChatService, session_id: str) -> List[str]:
    """Generate contextual query suggestions based on conversation history."""
    try:
        # Get conversation history
        conversation = chat_service.conversation_manager.get_history(session_id)
        
        if not conversation or len(conversation) < 2:
            # Default suggestions for new conversations
            return [
                "What topics are covered in the knowledge base?",
                "Explain a technical concept",
                "Find information about a specific subject",
                "Compare different approaches or ideas"
            ]
        
        # Get last assistant message to extract topics
        last_response = None
        for msg in reversed(conversation):
            if msg.role == "assistant":
                last_response = msg
                break
        
        if last_response:
            # Generate follow-up suggestions
            suggestions = [
                "Tell me more about this topic",
                "What are related concepts?",
                "Can you provide more examples?",
                "How does this compare to alternatives?"
            ]
            return suggestions
        
        return st.session_state.suggested_queries
        
    except Exception as e:
        logger.error(f"Error generating suggestions: {e}")
        return st.session_state.suggested_queries


def display_query_suggestions():
    """Display intelligent query suggestions as clickable chips."""
    if not st.session_state.chat_service:
        return
    
    st.markdown("### 💡 Suggested Questions")
    
    # Generate contextual suggestions
    suggestions = generate_contextual_suggestions(
        st.session_state.chat_service,
        st.session_state.session_id
    )
    
    # Display as columns of buttons
    cols = st.columns(2)
    for idx, suggestion in enumerate(suggestions[:4]):
        with cols[idx % 2]:
            if st.button(
                suggestion,
                key=f"suggestion_{idx}",
                use_container_width=True,
                type="secondary"
            ):
                # Set the suggestion as the user input
                st.session_state.user_input = suggestion
                st.rerun()


# ============================================================================
# CHAT INPUT HANDLING
# ============================================================================

def handle_chat_input(user_query: str):
    """Process user input and generate response."""
    if not user_query or not user_query.strip():
        return
    
    if not st.session_state.chat_service:
        st.error("❌ Chat service not initialized. Please check configuration.")
        return
    
    # Add user message to thread
    user_msg = {
        'role': 'user',
        'content': user_query,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    st.session_state.messages.append(user_msg)
    
    # Show processing indicator
    with st.spinner("🤔 Thinking..."):
        try:
            # Get response from chat service
            response = st.session_state.chat_service.chat(
                user_query=user_query,
                session_id=st.session_state.session_id
            )
            
            # Store response
            response_idx = len(st.session_state.chat_responses)
            st.session_state.chat_responses.append(response)
            
            # Add assistant message to thread
            assistant_msg = {
                'role': 'assistant',
                'content': response.response,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'response_idx': response_idx
            }
            st.session_state.messages.append(assistant_msg)
            
            logger.info(f"Response generated: {len(response.response)} chars, "
                       f"{len(response.citations)} citations, "
                       f"scope={response.scope.value}")
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            st.error(f"❌ Error: {str(e)}")


# ============================================================================
# SIDEBAR COMPONENTS
# ============================================================================

def display_sidebar():
    """Display sidebar with statistics and controls."""
    with st.sidebar:
        st.title("⚙️ Chat Settings")
        
        # Session info
        st.markdown("### 📊 Session Info")
        st.info(f"**Session ID:** `{st.session_state.session_id[:16]}...`")
        st.metric("Messages", len(st.session_state.messages))
        
        # Service statistics
        if st.session_state.chat_service:
            st.markdown("### 📈 Service Stats")
            stats = st.session_state.chat_service.get_statistics()
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Queries", stats.get('total_queries', 0))
            with col2:
                st.metric("Sessions", stats.get('total_sessions', 0))
            
            avg_time = stats.get('avg_processing_time', 0)
            if avg_time:
                st.metric("Avg Response Time", f"{avg_time:.2f}s")
            
            # Scope distribution
            st.markdown("**Scope Distribution:**")
            scope_dist = stats.get('scope_distribution', {})
            total_queries = stats.get('total_queries', 0)
            if scope_dist and total_queries > 0:
                for scope, count in scope_dist.items():
                    pct = (count / total_queries) * 100
                    st.progress(pct / 100, text=f"{scope}: {count} ({pct:.0f}%)")
        
        # Controls
        st.markdown("---")
        st.markdown("### 🎮 Controls")
        
        if st.button("🔄 New Conversation", use_container_width=True):
            st.session_state.session_id = f"streamlit_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            st.session_state.messages = []
            st.session_state.chat_responses = []
            st.session_state.feedback_given = set()
            st.success("✓ Started new conversation")
            st.rerun()
        
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.messages = []
            st.session_state.chat_responses = []
            st.session_state.feedback_given = set()
            st.success("✓ History cleared")
            st.rerun()
        
        # Export conversation
        if st.session_state.messages:
            st.markdown("---")
            st.markdown("### 💾 Export")
            if st.button("📥 Download Conversation", use_container_width=True):
                conversation_text = ""
                for msg in st.session_state.messages:
                    role = "You" if msg['role'] == 'user' else "Assistant"
                    conversation_text += f"{role} ({msg.get('timestamp', 'N/A')}):\n"
                    conversation_text += f"{msg['content']}\n\n"
                
                st.download_button(
                    label="💾 Save as Text",
                    data=conversation_text,
                    file_name=f"chat_{st.session_state.session_id}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
        
        # Help section
        st.markdown("---")
        st.markdown("### ℹ️ Help")
        with st.expander("How to use"):
            st.markdown("""
            **Getting Started:**
            1. Type your question in the chat input
            2. Click suggested questions for quick queries
            3. View sources and citations in responses
            
            **Understanding Indicators:**
            - 🟢 **IN SCOPE**: Complete answer available
            - 🟠 **PARTIAL**: Partial information available
            - 🔴 **OUT OF SCOPE**: No relevant information
            
            **Confidence Levels:**
            - ✓ **HIGH**: Strong confidence in answer
            - ~ **MEDIUM**: Moderate confidence
            - ! **LOW**: Low confidence, use caution
            - ? **UNCERTAIN**: Cannot provide reliable answer
            
            **Features:**
            - Source citations with relevance scores
            - Knowledge gap identification
            - Context-aware suggestions
            - Response quality feedback
            """)


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application entry point."""
    # Configure page
    configure_page()
    
    # Initialize session state
    initialize_session_state()
    
    # Initialize chat service if needed
    if st.session_state.chat_service is None:
        st.session_state.chat_service = initialize_chat_service()
    
    # Display sidebar
    display_sidebar()
    
    # Main content area
    st.title("💬 Knowledge Chat")
    st.markdown("*Ask questions and get answers grounded in collected knowledge*")
    
    # Check if service is ready
    if not st.session_state.chat_service:
        st.warning("⚠️ Chat service is not available. Please configure OpenAI API key.")
        st.info("""
        **Setup Instructions:**
        1. Get an API key from [OpenAI](https://platform.openai.com/api-keys)
        2. Set environment variable: `OPENAI_API_KEY=your_key_here`
        3. Restart the application
        """)
        return
    
    # Display message thread
    display_message_thread()
    
    # Display query suggestions
    st.markdown("---")
    display_query_suggestions()
    
    # Chat input at the bottom
    st.markdown("---")
    
    # Check if there's a suggested query to use
    suggested_input = st.session_state.get('user_input', '')
    if suggested_input:
        del st.session_state.user_input
    
    # Chat input form
    with st.form(key="chat_form", clear_on_submit=True):
        user_query = st.text_area(
            "Your Question:",
            value=suggested_input,
            placeholder="Type your question here... (e.g., 'What are the key concepts in machine learning?')",
            height=100,
            key="query_input"
        )
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            submit_button = st.form_submit_button(
                "💬 Send Message",
                use_container_width=True,
                type="primary"
            )
        with col2:
            st.form_submit_button("🔄 Clear", use_container_width=True)
        
        if submit_button and user_query:
            handle_chat_input(user_query)
            st.rerun()
    
    # Footer
    st.markdown("---")
    st.caption("🤖 Powered by OpenAI GPT-4 | 🔍 Hybrid Search | 💡 Query Understanding")


if __name__ == "__main__":
    main()
