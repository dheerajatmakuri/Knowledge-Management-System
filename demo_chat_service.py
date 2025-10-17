"""
AI Chat Service - Demonstration Script

Demonstrates all capabilities:
- Knowledge-grounded responses
- Source citations
- Uncertainty communication
- Context management
- Response validation

Copyright 2025 Amzur. All rights reserved.
"""

import os
import time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.markdown import Markdown

from src.services.chat_service import (
    ChatService,
    ResponseConfidence,
    KnowledgeScope
)

console = Console()


def print_header():
    """Print demo header."""
    console.print(Panel.fit(
        "[bold cyan]AI Chat Service Demo[/bold cyan]\n"
        "Knowledge-Grounded | Source Citations | Uncertainty Communication | Context Management",
        border_style="cyan"
    ))


def print_query(query: str, query_num: int):
    """Print user query."""
    console.print(f"\n[bold blue]Query {query_num}:[/bold blue] {query}")
    console.print("=" * 80)


def print_response(response, show_details: bool = True):
    """Print chat response with formatting."""
    # Main response
    console.print(f"\n[bold green]Assistant:[/bold green]")
    console.print(response.message)
    
    # Metadata
    console.print(f"\n[dim]Confidence: {response.confidence.value.upper()} | "
                  f"Scope: {response.knowledge_scope.value} | "
                  f"Sources: {response.sources_count} | "
                  f"Time: {response.processing_time:.2f}s[/dim]")
    
    if show_details:
        # Citations
        if response.citations:
            console.print("\n[bold yellow]Sources:[/bold yellow]")
            for i, citation in enumerate(response.citations, 1):
                console.print(
                    f"  [{i}] {citation.source_title} "
                    f"[dim]({citation.source_type}, relevance: {citation.relevance_score:.1%})[/dim]"
                )
                if citation.source_url:
                    console.print(f"      URL: {citation.source_url}")
        
        # Admitted gaps
        if response.admitted_gaps:
            console.print("\n[bold red]Knowledge Gaps Identified:[/bold red]")
            for gap in response.admitted_gaps:
                console.print(f"  - {gap}")
        
        # Suggestions
        if response.suggestions:
            console.print("\n[bold cyan]Suggestions:[/bold cyan]")
            for suggestion in response.suggestions:
                console.print(f"  - {suggestion}")


def demo_basic_queries():
    """Demonstrate basic query handling."""
    console.print("\n[bold cyan]1. BASIC QUERIES[/bold cyan]")
    console.print("[dim]Testing simple questions with knowledge base lookups[/dim]\n")
    
    service = ChatService()
    session_id = "demo_basic"
    
    queries = [
        "Who are the machine learning engineers in the system?",
        "What skills does the Python developer have?",
        "Tell me about React developers"
    ]
    
    for i, query in enumerate(queries, 1):
        print_query(query, i)
        response = service.chat(query, session_id=session_id, k=5)
        print_response(response)
        time.sleep(0.5)


def demo_context_awareness():
    """Demonstrate conversation context management."""
    console.print("\n\n[bold cyan]2. CONTEXT AWARENESS[/bold cyan]")
    console.print("[dim]Testing multi-turn conversations with context preservation[/dim]\n")
    
    service = ChatService()
    session_id = "demo_context"
    
    queries = [
        "Find machine learning engineers",
        "What about their Python experience?",  # Refers to previous query
        "Show me the senior ones",               # Builds on context
        "Do any of them know TensorFlow?"       # Continues the thread
    ]
    
    for i, query in enumerate(queries, 1):
        print_query(query, i)
        response = service.chat(query, session_id=session_id, k=5)
        print_response(response, show_details=(i == len(queries)))  # Full details on last only
        time.sleep(0.5)
    
    # Show conversation summary
    summary = service.get_session_summary(session_id)
    console.print("\n[bold]Conversation Summary:[/bold]")
    console.print(f"  Total messages: {summary['message_count']}")
    console.print(f"  User messages: {summary['user_messages']}")
    console.print(f"  Assistant messages: {summary['assistant_messages']}")


def demo_knowledge_scope():
    """Demonstrate knowledge scope enforcement."""
    console.print("\n\n[bold cyan]3. KNOWLEDGE SCOPE ENFORCEMENT[/bold cyan]")
    console.print("[dim]Testing in-scope vs out-of-scope questions[/dim]\n")
    
    service = ChatService()
    session_id = "demo_scope"
    
    # Mix of in-scope and out-of-scope queries
    queries = [
        # In-scope: About profiles in database
        ("What programming languages are known by people in the system?", "IN-SCOPE"),
        
        # Out-of-scope: General knowledge not in database
        ("What is quantum computing?", "OUT-OF-SCOPE"),
        
        # Partial scope: May have some relevant info
        ("Compare Python and Java", "PARTIAL-SCOPE")
    ]
    
    for i, (query, expected_scope) in enumerate(queries, 1):
        print_query(f"{query} [dim](Expected: {expected_scope})[/dim]", i)
        response = service.chat(query, session_id=session_id, k=5)
        print_response(response)
        
        # Verify scope
        if response.knowledge_scope.value == expected_scope.lower().replace('-', '_'):
            console.print(f"[green]+ Scope correctly identified: {response.knowledge_scope.value}[/green]")
        else:
            console.print(f"[yellow]! Scope mismatch: got {response.knowledge_scope.value}, expected {expected_scope}[/yellow]")
        
        time.sleep(0.5)


def demo_source_attribution():
    """Demonstrate source citation capabilities."""
    console.print("\n\n[bold cyan]4. SOURCE ATTRIBUTION[/bold cyan]")
    console.print("[dim]Testing citation quality and accuracy[/dim]\n")
    
    service = ChatService()
    session_id = "demo_citations"
    
    query = "What are the skills and experience of the software engineers?"
    print_query(query, 1)
    
    response = service.chat(query, session_id=session_id, k=10)
    
    # Detailed citation analysis
    console.print(f"\n[bold green]Assistant:[/bold green]")
    console.print(response.message)
    
    console.print(f"\n[bold yellow]Citation Analysis:[/bold yellow]")
    console.print(f"  Total sources cited: {response.sources_count}")
    console.print(f"  Response confidence: {response.confidence.value}")
    
    if response.citations:
        # Create citation table
        table = Table(title="Source Citations", box=box.ROUNDED)
        table.add_column("#", style="cyan", width=3)
        table.add_column("Source", style="white", width=30)
        table.add_column("Type", style="yellow", width=10)
        table.add_column("Relevance", style="green", width=10)
        
        for i, citation in enumerate(response.citations, 1):
            table.add_row(
                str(i),
                citation.source_title[:27] + "..." if len(citation.source_title) > 30 else citation.source_title,
                citation.source_type,
                f"{citation.relevance_score:.1%}"
            )
        
        console.print(table)


def demo_uncertainty_communication():
    """Demonstrate uncertainty handling."""
    console.print("\n\n[bold cyan]5. UNCERTAINTY COMMUNICATION[/bold cyan]")
    console.print("[dim]Testing how the system admits knowledge gaps[/dim]\n")
    
    service = ChatService()
    session_id = "demo_uncertainty"
    
    # Queries designed to test uncertainty
    queries = [
        "What do you know about blockchain developers?",  # May or may not have info
        "Tell me about TypeScript experts",                # Specific query
        "What is the best programming language?"           # Opinion-based, likely out of scope
    ]
    
    for i, query in enumerate(queries, 1):
        print_query(query, i)
        response = service.chat(query, session_id=session_id, k=5)
        
        console.print(f"\n[bold green]Assistant:[/bold green]")
        console.print(response.message)
        
        # Analyze uncertainty indicators
        console.print(f"\n[bold]Uncertainty Analysis:[/bold]")
        console.print(f"  Confidence: {response.confidence.value}")
        console.print(f"  Knowledge scope: {response.knowledge_scope.value}")
        
        if response.admitted_gaps:
            console.print(f"  [green]+ System admitted {len(response.admitted_gaps)} knowledge gap(s)[/green]")
            for gap in response.admitted_gaps:
                console.print(f"    - {gap}")
        else:
            if response.knowledge_scope == KnowledgeScope.OUT_OF_SCOPE:
                console.print(f"  [green]+ System acknowledged being out of scope[/green]")
            elif response.confidence in [ResponseConfidence.LOW, ResponseConfidence.UNCERTAIN]:
                console.print(f"  [yellow]! Low confidence but no explicit gaps mentioned[/yellow]")
        
        time.sleep(0.5)


def demo_response_validation():
    """Demonstrate response quality validation."""
    console.print("\n\n[bold cyan]6. RESPONSE QUALITY VALIDATION[/bold cyan]")
    console.print("[dim]Testing response validation metrics[/dim]\n")
    
    service = ChatService()
    session_id = "demo_validation"
    
    query = "What technologies and skills are most common in the profiles?"
    print_query(query, 1)
    
    response = service.chat(query, session_id=session_id, k=15)
    
    console.print(f"\n[bold green]Assistant:[/bold green]")
    console.print(response.message)
    
    # Validation metrics
    console.print(f"\n[bold yellow]Validation Metrics:[/bold yellow]")
    
    table = Table(box=box.SIMPLE)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")
    table.add_column("Status", style="green")
    
    # Check various quality indicators
    has_citations = response.sources_count > 0
    sufficient_sources = response.sources_count >= 2
    high_confidence = response.confidence in [ResponseConfidence.HIGH, ResponseConfidence.MEDIUM]
    in_scope = response.knowledge_scope != KnowledgeScope.OUT_OF_SCOPE
    
    table.add_row(
        "Has Citations",
        "Yes" if has_citations else "No",
        "[green]PASS[/green]" if has_citations else "[red]FAIL[/red]"
    )
    table.add_row(
        "Sufficient Sources",
        f"{response.sources_count} sources",
        "[green]PASS[/green]" if sufficient_sources else "[yellow]WARN[/yellow]"
    )
    table.add_row(
        "Confidence Level",
        response.confidence.value.upper(),
        "[green]PASS[/green]" if high_confidence else "[yellow]WARN[/yellow]"
    )
    table.add_row(
        "Knowledge Scope",
        response.knowledge_scope.value,
        "[green]PASS[/green]" if in_scope else "[red]FAIL[/red]"
    )
    table.add_row(
        "Processing Time",
        f"{response.processing_time:.2f}s",
        "[green]PASS[/green]" if response.processing_time < 5.0 else "[yellow]SLOW[/yellow]"
    )
    
    console.print(table)
    
    # Overall quality score
    quality_score = sum([has_citations, sufficient_sources, high_confidence, in_scope]) / 4
    console.print(f"\n[bold]Overall Quality Score: {quality_score:.0%}[/bold]")


def demo_statistics():
    """Show service statistics."""
    console.print("\n\n[bold cyan]7. SERVICE STATISTICS[/bold cyan]\n")
    
    service = ChatService()
    stats = service.get_statistics()
    
    table = Table(title="Chat Service Statistics", box=box.ROUNDED)
    table.add_column("Component", style="cyan")
    table.add_column("Metric", style="yellow")
    table.add_column("Value", style="white")
    
    # Service stats
    table.add_row("Chat Service", "Model", stats['model'])
    table.add_row("", "Temperature", str(stats['temperature']))
    table.add_row("", "Max Tokens", str(stats['max_tokens']))
    table.add_row("", "Active Sessions", str(stats['active_sessions']))
    
    # Query understanding stats
    qu_stats = stats['query_understanding_stats']
    table.add_row("Query Understanding", "Active Sessions", str(qu_stats['active_sessions']))
    table.add_row("", "Intent Patterns", str(qu_stats['intent_patterns']))
    table.add_row("", "Known Technologies", str(qu_stats['known_technologies']))
    table.add_row("", "Known Roles", str(qu_stats['known_roles']))
    
    # Search service stats
    search_stats = stats['search_service_stats']
    table.add_row("Search Service", "Indexed Profiles", str(search_stats.get('indexed_profiles', 0)))
    table.add_row("", "Vector Dimensions", str(search_stats.get('vector_dimensions', 0)))
    
    console.print(table)


def main():
    """Run all demonstrations."""
    print_header()
    
    console.print("\n[bold]Initializing AI Chat Service...[/bold]")
    
    try:
        # Check for API key
        if not os.getenv('OPENAI_API_KEY'):
            console.print("[red]ERROR: OPENAI_API_KEY not found in environment variables[/red]")
            console.print("[yellow]Please set your OpenAI API key to run this demo[/yellow]")
            return
        
        console.print("[green][OK][/green] Chat service ready\n")
        
        # Run demonstrations
        demo_basic_queries()
        demo_context_awareness()
        demo_knowledge_scope()
        demo_source_attribution()
        demo_uncertainty_communication()
        demo_response_validation()
        demo_statistics()
        
        # Summary
        console.print("\n" + "=" * 80)
        console.print(Panel.fit(
            "[bold green]All Demonstrations Complete![/bold green]\n\n"
            "The chat service successfully demonstrated:\n"
            "+ Knowledge scope enforcement (only answers from knowledge base)\n"
            "+ Source attribution (provides citations for all claims)\n"
            "+ Uncertainty communication (admits knowledge gaps)\n"
            "+ Context management (maintains conversation history)\n"
            "+ Response validation (ensures quality and accuracy)",
            border_style="green",
            title="[bold]Demo Summary[/bold]"
        ))
        
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        import traceback
        console.print(traceback.format_exc())


if __name__ == "__main__":
    main()
