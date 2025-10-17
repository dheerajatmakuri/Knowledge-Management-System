"""
Demonstration of the Hybrid Search Engine.
Shows full-text, vector, and metadata filtering working together.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

# Load environment
load_dotenv()

from src.database.repository import DatabaseSession
from src.database.repository import ProfileRepository, KnowledgeSnippetRepository
from src.search.indexing import ContentVectorizationPipeline, EmbeddingIndexer
from src.search.vector_search import VectorSearch
from src.search.hybrid_search import HybridSearchEngine, HybridSearchConfig

console = Console()


def create_sample_data(session):
    """Create diverse sample data for demonstration."""
    from src.database.models import Profile, KnowledgeSnippet
    
    console.print("\n[yellow]Creating sample data...[/yellow]")
    
    # Profiles with various attributes
    profiles = [
        Profile(
            name="Dr. Sarah Chen",
            title="Machine Learning Research Scientist",
            bio="Expert in deep learning, computer vision, and neural architecture search. "
                "Published 50+ papers on transformer models and efficient ML systems. "
                "Focus on production ML and scalable AI infrastructure.",
            email="sarah.chen@research.ai",
            source_url="https://research.ai/sarah-chen",
            source_domain="research.ai",
            is_verified=True,
            confidence_score=0.95
        ),
        Profile(
            name="Michael Rodriguez",
            title="Full Stack Developer & DevOps Engineer",
            bio="Specializes in React, Node.js, and cloud infrastructure. "
                "Experience with Kubernetes, Docker, and CI/CD pipelines. "
                "Building scalable web applications with modern JavaScript.",
            email="m.rodriguez@webdev.com",
            source_url="https://webdev.com/mrodriguez",
            source_domain="webdev.com",
            is_verified=True,
            confidence_score=0.88
        ),
        Profile(
            name="Dr. Emily Thompson",
            title="Data Scientist & Statistical Analyst",
            bio="PhD in Statistics with focus on Bayesian methods and causal inference. "
                "Expert in R, Python, and statistical modeling. "
                "10+ years experience in healthcare analytics and A/B testing.",
            email="emily.t@stats.org",
            source_url="https://stats.org/emily-thompson",
            source_domain="stats.org",
            is_verified=False,
            confidence_score=0.72
        ),
        Profile(
            name="James Kim",
            title="AI/ML Engineer",
            bio="Building production ML systems with PyTorch and TensorFlow. "
                "Experience with NLP, recommendation systems, and MLOps. "
                "Previously at Google and Microsoft working on AI products.",
            email="james.kim@mltech.com",
            source_url="https://mltech.com/james",
            source_domain="mltech.com",
            is_verified=True,
            confidence_score=0.91
        ),
        Profile(
            name="Lisa Anderson",
            title="Cloud Architect & Security Specialist",
            bio="AWS and Azure certified architect. Expert in cloud security, "
                "infrastructure as code, and compliance. "
                "15+ years in enterprise IT and cybersecurity.",
            email="l.anderson@cloudsec.io",
            source_url="https://cloudsec.io/lisa",
            source_domain="cloudsec.io",
            is_verified=True,
            confidence_score=0.86
        )
    ]
    
    # Knowledge snippets with categories
    snippets = [
        KnowledgeSnippet(
            title="Transformer Architecture Explained",
            content="The transformer architecture revolutionized NLP with self-attention mechanisms. "
                    "Key components: multi-head attention, positional encoding, layer normalization. "
                    "Used in BERT, GPT, and modern LLMs.",
            content_type="technical",
            category="machine-learning",
            is_validated=True,
            confidence_score=0.92
        ),
        KnowledgeSnippet(
            title="React Hooks Best Practices",
            content="Modern React development using hooks: useState, useEffect, useMemo. "
                    "Avoid common pitfalls: dependency arrays, stale closures, unnecessary re-renders. "
                    "Custom hooks for reusable logic.",
            content_type="tutorial",
            category="web-development",
            is_validated=True,
            confidence_score=0.88
        ),
        KnowledgeSnippet(
            title="Bayesian A/B Testing",
            content="Bayesian approach to A/B testing provides probability distributions instead of p-values. "
                    "Better for early stopping decisions and continuous monitoring. "
                    "Use Beta-Binomial conjugate priors for conversion rates.",
            content_type="technical",
            category="statistics",
            is_validated=True,
            confidence_score=0.85
        ),
        KnowledgeSnippet(
            title="Kubernetes Production Deployment",
            content="Deploy applications on Kubernetes with: Deployments, Services, Ingress. "
                    "Implement health checks, resource limits, and auto-scaling. "
                    "Use Helm charts for reproducible deployments.",
            content_type="tutorial",
            category="devops",
            is_validated=False,
            confidence_score=0.75
        ),
        KnowledgeSnippet(
            title="Neural Architecture Search",
            content="Automated design of neural network architectures using reinforcement learning or evolution. "
                    "Methods: ENAS, DARTS, NAS-Bench. Trade-off between search cost and model performance.",
            content_type="research",
            category="machine-learning",
            is_validated=True,
            confidence_score=0.90
        )
    ]
    
    # Add to database
    for profile in profiles:
        session.add(profile)
    
    for snippet in snippets:
        session.add(snippet)
    
    session.commit()
    console.print(f"[green]✓[/green] Created {len(profiles)} profiles and {len(snippets)} snippets")


def demo_hybrid_search():
    """Demonstrate hybrid search capabilities."""
    console.print(Panel.fit(
        "[bold cyan]Hybrid Search Engine Demo[/bold cyan]\n"
        "Combining Full-Text, Vector Similarity, and Metadata Filtering",
        border_style="cyan"
    ))
    
    # Initialize
    db_path = "data/profiles.db"
    if not db_path.startswith('sqlite:///'):
        db_path = f'sqlite:///{db_path}'
    
    db_session = DatabaseSession(db_path)
    
    # Create sample data
    with db_session.get_session() as session:
        # Check if data exists
        from src.database.models import Profile
        count = session.query(Profile).count()
        if count < 5:
            create_sample_data(session)
    
    # Initialize components
    console.print("\n[yellow]Initializing hybrid search engine...[/yellow]")
    
    vectorizer = ContentVectorizationPipeline()
    vector_search = VectorSearch(
        dimension=vectorizer.config.dimension,
        backend='faiss',
        metric='cosine',
        use_gpu=False
    )
    
    # Index content
    console.print("[yellow]Building search indexes...[/yellow]")
    indexer = EmbeddingIndexer(vectorizer, db_session)
    
    stats = indexer.index_all()
    console.print(f"[green]✓[/green] Indexed {stats['total_indexed']} items in {stats['time_taken']:.2f}s")
    
    # Create hybrid search with custom config
    config = HybridSearchConfig(
        vector_weight=0.5,
        fulltext_weight=0.3,
        metadata_weight=0.2,
        fusion_method='weighted_sum',
        use_vector=True,
        use_fulltext=True,
        use_metadata=True
    )
    
    hybrid_search = HybridSearchEngine(
        db_session=db_session,
        vector_search=vector_search,
        vectorizer=vectorizer,
        config=config
    )
    
    console.print("[green]✓[/green] Hybrid search engine ready\n")
    
    # Demo 1: Pure semantic search
    console.print(Panel("[bold]Demo 1: Semantic Search[/bold]\nQuery: 'deep learning expert'", 
                       border_style="blue"))
    
    results = hybrid_search.search(
        query="deep learning expert",
        k=3,
        include_scores=True
    )
    
    display_results(results, show_scores=True)
    
    # Demo 2: Full-text + vector search
    console.print("\n" + Panel("[bold]Demo 2: Combined Search[/bold]\nQuery: 'React hooks tutorial'", 
                              border_style="blue"))
    
    results = hybrid_search.search(
        query="React hooks tutorial",
        k=3,
        include_scores=True
    )
    
    display_results(results, show_scores=True)
    
    # Demo 3: Search with metadata filters
    console.print("\n" + Panel("[bold]Demo 3: Filtered Search[/bold]\n"
                              "Query: 'machine learning'\nFilter: verified profiles only", 
                              border_style="blue"))
    
    results = hybrid_search.search(
        query="machine learning",
        k=3,
        entity_types=['profile'],
        filters={'is_verified': True, 'min_confidence': 0.85},
        include_scores=True
    )
    
    display_results(results, show_scores=True)
    
    # Demo 4: Search with facets
    console.print("\n" + Panel("[bold]Demo 4: Faceted Search[/bold]\n"
                              "Query: 'technical content'", 
                              border_style="blue"))
    
    results = hybrid_search.search(
        query="technical content",
        k=5,
        include_facets=True,
        facet_fields=['category', 'content_type', 'is_verified']
    )
    
    display_results(results)
    display_facets(results.filters_applied.get('facets', {}))
    
    # Demo 5: Different fusion methods
    console.print("\n" + Panel("[bold]Demo 5: Fusion Method Comparison[/bold]\n"
                              "Query: 'cloud infrastructure'", 
                              border_style="blue"))
    
    fusion_methods = ['weighted_sum', 'reciprocal_rank', 'max']
    
    for method in fusion_methods:
        hybrid_search.config.fusion_method = method
        results = hybrid_search.search(
            query="cloud infrastructure",
            k=3,
            include_scores=True
        )
        
        console.print(f"\n[cyan]Fusion Method: {method}[/cyan]")
        display_results_compact(results)
    
    # Demo 6: Dynamic weight adjustment
    console.print("\n" + Panel("[bold]Demo 6: Dynamic Weight Tuning[/bold]\n"
                              "Query: 'statistics and data analysis'", 
                              border_style="blue"))
    
    weight_configs = [
        (0.7, 0.2, 0.1, "Vector-focused"),
        (0.2, 0.7, 0.1, "Text-focused"),
        (0.3, 0.3, 0.4, "Metadata-focused")
    ]
    
    for v_weight, t_weight, m_weight, desc in weight_configs:
        hybrid_search.update_weights(vector=v_weight, fulltext=t_weight, metadata=m_weight)
        results = hybrid_search.search(
            query="statistics and data analysis",
            k=2,
            include_scores=True
        )
        
        console.print(f"\n[cyan]{desc} (v={v_weight}, t={t_weight}, m={m_weight})[/cyan]")
        display_results_compact(results)
    
    # Statistics
    console.print("\n" + Panel("[bold]Hybrid Search Statistics[/bold]", border_style="green"))
    stats = hybrid_search.get_statistics()
    
    stats_table = Table(show_header=True, box=box.ROUNDED)
    stats_table.add_column("Metric", style="cyan")
    stats_table.add_column("Value", style="green")
    
    stats_table.add_row("Vector Weight", f"{stats['config']['vector_weight']:.2f}")
    stats_table.add_row("Full-Text Weight", f"{stats['config']['fulltext_weight']:.2f}")
    stats_table.add_row("Metadata Weight", f"{stats['config']['metadata_weight']:.2f}")
    stats_table.add_row("Fusion Method", stats['config']['fusion_method'])
    stats_table.add_row("Vector Search", "✓" if stats['enabled_methods']['vector'] else "✗")
    stats_table.add_row("Full-Text Search", "✓" if stats['enabled_methods']['fulltext'] else "✗")
    stats_table.add_row("Metadata Filtering", "✓" if stats['enabled_methods']['metadata'] else "✗")
    
    console.print(stats_table)


def display_results(results, show_scores=False):
    """Display search results in a formatted table."""
    table = Table(show_header=True, box=box.ROUNDED)
    table.add_column("Rank", style="cyan", width=6)
    table.add_column("Type", style="magenta", width=10)
    table.add_column("Title/Name", style="green")
    table.add_column("Score", style="yellow", width=8)
    
    if show_scores:
        table.add_column("V", style="blue", width=6)  # Vector
        table.add_column("T", style="blue", width=6)  # Text
        table.add_column("M", style="blue", width=6)  # Metadata
    
    for result in results.results[:10]:
        content = result.content or {}
        title = content.get('title') or content.get('name', 'N/A')
        
        row = [
            str(result.rank),
            result.entity_type,
            title[:50],
            f"{result.score:.3f}"
        ]
        
        if show_scores and 'score_breakdown' in result.metadata:
            breakdown = result.metadata['score_breakdown']
            row.extend([
                f"{breakdown.get('vector', 0):.2f}",
                f"{breakdown.get('fulltext', 0):.2f}",
                f"{breakdown.get('metadata', 0):.2f}"
            ])
        
        table.add_row(*row)
    
    console.print(table)
    console.print(f"[dim]Total: {results.total_results} results in {results.search_time:.3f}s[/dim]")


def display_results_compact(results):
    """Display results in compact format."""
    for i, result in enumerate(results.results[:3], 1):
        content = result.content or {}
        title = content.get('title') or content.get('name', 'N/A')
        
        score_info = ""
        if 'score_breakdown' in result.metadata:
            breakdown = result.metadata['score_breakdown']
            score_info = f" (V:{breakdown.get('vector', 0):.2f} T:{breakdown.get('fulltext', 0):.2f} M:{breakdown.get('metadata', 0):.2f})"
        
        console.print(f"  {i}. [{result.entity_type}] {title[:40]} - {result.score:.3f}{score_info}")


def display_facets(facets):
    """Display facet counts."""
    if not facets:
        return
    
    console.print("\n[bold cyan]Facets:[/bold cyan]")
    
    for field, counts in facets.items():
        if counts:
            console.print(f"\n[yellow]{field}:[/yellow]")
            for value, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
                console.print(f"  • {value}: {count}")


if __name__ == "__main__":
    try:
        demo_hybrid_search()
        console.print("\n[bold green]✓ Hybrid search demo completed successfully![/bold green]")
    except Exception as e:
        console.print(f"\n[bold red]✗ Error: {e}[/bold red]")
        import traceback
        console.print(traceback.format_exc())
