"""
Query Understanding System - Demonstration
Shows intent classification, entity extraction, query expansion, and search optimization.
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.tree import Tree

from src.search.query_understanding import (
    QueryUnderstandingEngine,
    QueryIntent,
    EntityType
)

console = Console()


def demo_query_understanding():
    """Demonstrate query understanding capabilities."""
    console.print(Panel.fit(
        "[bold cyan]Query Understanding System Demo[/bold cyan]\n"
        "Intent Classification | Entity Extraction | Query Expansion | Strategy Optimization",
        border_style="cyan"
    ))
    
    # Initialize engine
    console.print("\n[yellow]Initializing query understanding engine...[/yellow]")
    engine = QueryUnderstandingEngine()
    console.print("[green][OK][/green] Engine initialized\n")
    
    # Test queries covering different intents
    test_queries = [
        # Find person queries
        "Find a senior machine learning engineer with Python experience",
        "Who is an expert in React and Node.js?",
        "Show me data scientists working on NLP",
        
        # Find knowledge queries
        "How to implement a neural network in TensorFlow",
        "What is the difference between REST and GraphQL?",
        "Tutorial on Docker containerization",
        
        # Compare queries
        "Compare Python vs Java for machine learning",
        "Which is better: AWS or Azure?",
        
        # List queries
        "List all verified developers with cloud experience",
        "Show all tutorials about web development",
        
        # Filter queries
        "Only senior engineers from Google",
        "Verified profiles with AI expertise",
        
        # Recommend queries
        "Recommend the best resources for learning React",
        "What should I learn for becoming a data scientist?",
        
        # Explain queries
        "Explain how transformers work in NLP",
        "Why is Kubernetes important for DevOps?",
        
        # Question queries
        "Is Python good for web development?",
        "Can I use TensorFlow with JavaScript?"
    ]
    
    session_id = "demo_session_001"
    
    for idx, query in enumerate(test_queries, 1):
        console.print(f"\n[bold blue]Query {idx}:[/bold blue] {query}")
        console.print("=" * 80)
        
        # Understand query
        result = engine.understand(
            query=query,
            session_id=session_id,
            preserve_context=True
        )
        
        # Display results
        display_understanding_result(result)
        
        # Add separator between queries
        if idx < len(test_queries):
            console.print()
    
    # Show statistics
    console.print("\n" + "=" * 80)
    console.print(Panel("[bold]Query Understanding Statistics[/bold]", border_style="green"))
    
    stats = engine.get_statistics()
    stats_table = Table(show_header=True, box=box.ROUNDED)
    stats_table.add_column("Metric", style="cyan")
    stats_table.add_column("Value", style="green")
    
    stats_table.add_row("Active Sessions", str(stats['active_sessions']))
    stats_table.add_row("Total Queries in Context", str(stats['total_queries_in_context']))
    stats_table.add_row("Intent Patterns", str(stats['intent_patterns']))
    stats_table.add_row("Known Technologies", str(stats['known_technologies']))
    stats_table.add_row("Known Roles", str(stats['known_roles']))
    stats_table.add_row("Synonym Groups", str(stats['synonym_groups']))
    
    console.print(stats_table)
    
    # Show context
    context = engine.get_session_context(session_id)
    if context and context.previous_queries:
        console.print("\n[bold cyan]Session Context:[/bold cyan]")
        console.print(f"  Recent queries: {len(context.previous_queries)}")
        console.print(f"  Recent intents: {[i.value for i in context.previous_intents[-5:]]}")
        console.print(f"  Extracted entities: {len(context.previous_entities)}")


def display_understanding_result(result):
    """Display query understanding result in formatted output."""
    
    # Intent
    intent_color = "green" if result.intent_confidence > 0.7 else "yellow"
    console.print(
        f"  [bold]Intent:[/bold] [{intent_color}]{result.intent.value}[/{intent_color}] "
        f"(confidence: {result.intent_confidence:.2f})"
    )
    
    # Entities
    if result.entities:
        console.print(f"  [bold]Entities:[/bold] {len(result.entities)} found")
        for entity in result.entities:
            entity_color = {
                EntityType.PERSON: "magenta",
                EntityType.SKILL: "blue",
                EntityType.TECHNOLOGY: "cyan",
                EntityType.ROLE: "yellow",
                EntityType.COMPANY: "green",
                EntityType.DOMAIN: "red"
            }.get(entity.entity_type, "white")
            
            console.print(
                f"    - [{entity_color}]{entity.text}[/{entity_color}] "
                f"({entity.entity_type.value}, {entity.confidence:.2f})"
            )
    else:
        console.print("  [bold]Entities:[/bold] [dim]None extracted[/dim]")
    
    # Expanded terms
    if result.expanded_terms:
        console.print(f"  [bold]Expansions:[/bold] {', '.join(result.expanded_terms)}")
    else:
        console.print("  [bold]Expansions:[/bold] [dim]None[/dim]")
    
    # Search strategy
    strategy = result.search_strategy
    console.print(f"  [bold]Strategy:[/bold]")
    console.print(f"    Methods: {', '.join(strategy.search_methods)}")
    console.print(
        f"    Weights: V={strategy.weights.get('vector', 0):.1f} "
        f"T={strategy.weights.get('fulltext', 0):.1f} "
        f"M={strategy.weights.get('metadata', 0):.1f}"
    )
    
    if strategy.entity_types:
        console.print(f"    Entity Types: {', '.join(strategy.entity_types)}")
    
    if strategy.filters:
        console.print(f"    Filters: {strategy.filters}")
    
    console.print(f"    K={strategy.k}, Min Score={strategy.min_score:.2f}")
    
    if strategy.rerank:
        console.print("    [cyan]⚡ Reranking enabled[/cyan]")
    
    # Processing time
    console.print(f"  [dim]Processing time: {result.processing_time*1000:.1f}ms[/dim]")


def demo_specific_examples():
    """Demonstrate specific use cases."""
    console.print("\n" + "=" * 80)
    console.print(Panel.fit(
        "[bold cyan]Specific Use Case Examples[/bold cyan]",
        border_style="cyan"
    ))
    
    engine = QueryUnderstandingEngine()
    
    examples = [
        {
            'title': "Complex Technical Query",
            'query': "Find senior ML engineers with TensorFlow and PyTorch experience from Google or Microsoft",
            'description': "Multi-entity extraction with filtering"
        },
        {
            'title': "Learning Path Query",
            'query': "How do I learn web development with React, Node.js, and MongoDB?",
            'description': "Knowledge search with multiple technologies"
        },
        {
            'title': "Comparison Query",
            'query': "Compare AWS Lambda vs Azure Functions for serverless computing",
            'description': "Comparative analysis intent"
        },
        {
            'title': "Filtered List Query",
            'query': "List all verified data scientists with at least 5 years experience",
            'description': "List intent with quality filters"
        }
    ]
    
    for example in examples:
        console.print(f"\n[bold green]{example['title']}[/bold green]")
        console.print(f"[dim]{example['description']}[/dim]")
        console.print(f"[bold]Query:[/bold] {example['query']}")
        console.print()
        
        result = engine.understand(example['query'])
        
        # Create tree visualization
        tree = Tree(f"[bold cyan]Query Understanding[/bold cyan]")
        
        # Intent branch
        intent_branch = tree.add(f"[yellow]Intent:[/yellow] {result.intent.value} ({result.intent_confidence:.2f})")
        
        # Entities branch
        if result.entities:
            entities_branch = tree.add(f"[blue]Entities ({len(result.entities)})[/blue]")
            for entity in result.entities:
                entities_branch.add(f"{entity.text} -> {entity.entity_type.value}")
        
        # Expansion branch
        if result.expanded_terms:
            expansion_branch = tree.add(f"[green]Expansions ({len(result.expanded_terms)})[/green]")
            for term in result.expanded_terms:
                expansion_branch.add(term)
        
        # Strategy branch
        strategy_branch = tree.add("[magenta]Search Strategy[/magenta]")
        strategy_branch.add(f"Weights: {result.search_strategy.weights}")
        if result.search_strategy.entity_types:
            strategy_branch.add(f"Entity Types: {result.search_strategy.entity_types}")
        if result.search_strategy.filters:
            strategy_branch.add(f"Filters: {result.search_strategy.filters}")
        
        console.print(tree)


def demo_context_preservation():
    """Demonstrate context preservation across queries."""
    console.print("\n" + "=" * 80)
    console.print(Panel.fit(
        "[bold cyan]Context Preservation Demo[/bold cyan]\n"
        "Tracking query history and maintaining context",
        border_style="cyan"
    ))
    
    engine = QueryUnderstandingEngine()
    session_id = "context_demo"
    
    conversation = [
        "Find machine learning engineers",
        "Who has Python experience?",
        "Show me the ones from Google",
        "What about TensorFlow experts?",
        "Recommend someone senior"
    ]
    
    console.print("[bold]Simulated Conversation:[/bold]\n")
    
    for idx, query in enumerate(conversation, 1):
        console.print(f"[cyan]User {idx}:[/cyan] {query}")
        
        result = engine.understand(
            query=query,
            session_id=session_id,
            preserve_context=True
        )
        
        console.print(f"  Intent: {result.intent.value}")
        console.print(f"  Entities: {[e.text for e in result.entities]}")
        console.print(f"  Strategy: {result.search_strategy.entity_types or 'General'}")
        
        # Show context accumulation
        context = engine.get_session_context(session_id)
        console.print(f"  [dim]Context: {len(context.previous_queries)} queries, "
                     f"{len(context.previous_entities)} entities[/dim]")
        console.print()
    
    # Final context summary
    console.print("[bold green]Final Context Summary:[/bold green]")
    context = engine.get_session_context(session_id)
    
    summary_table = Table(show_header=True, box=box.SIMPLE)
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="green")
    
    summary_table.add_row("Total Queries", str(len(context.previous_queries)))
    summary_table.add_row("Unique Intents", str(len(set(context.previous_intents))))
    summary_table.add_row("Total Entities", str(len(context.previous_entities)))
    summary_table.add_row(
        "Entity Types",
        str(len(set(e.entity_type for e in context.previous_entities)))
    )
    
    console.print(summary_table)


if __name__ == "__main__":
    try:
        # Main demo
        demo_query_understanding()
        
        # Specific examples
        demo_specific_examples()
        
        # Context preservation
        demo_context_preservation()
        
        console.print("\n[bold green][SUCCESS] Query understanding demo completed successfully![/bold green]")
    
    except Exception as e:
        console.print(f"\n[bold red][ERROR] Error: {e}[/bold red]")
        import traceback
        console.print(traceback.format_exc())
