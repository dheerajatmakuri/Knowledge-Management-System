"""
Quick demo of vector search system with sample data.
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.database.migrations import DatabaseSession
from src.database.repository import ProfileRepository, KnowledgeSnippetRepository
from src.services.search_service import create_search_service

def create_sample_data():
    """Create sample profiles and snippets for testing."""
    print("\n📝 Creating sample data...")
    
    db_session = DatabaseSession('sqlite:///data/profiles.db')
    
    with db_session.get_session() as session:
        profile_repo = ProfileRepository(session)
        snippet_repo = KnowledgeSnippetRepository(session)
        
        # Sample profiles
        profiles = [
            {
                'name': 'Sarah Johnson',
                'title': 'Machine Learning Engineer',
                'bio': 'Passionate about deep learning and neural networks. Expertise in Python, TensorFlow, and PyTorch. Published researcher in computer vision.',
                'email': 'sarah.j@example.com',
                'source_url': 'https://example.com/sarah',
                'source_domain': 'example.com'
            },
            {
                'name': 'Michael Chen',
                'title': 'Data Scientist',
                'bio': 'Experienced in statistical analysis, data visualization, and predictive modeling. Skilled in R, Python, and SQL.',
                'email': 'michael.c@example.com',
                'source_url': 'https://example.com/michael',
                'source_domain': 'example.com'
            },
            {
                'name': 'Emily Rodriguez',
                'title': 'Software Engineer',
                'bio': 'Full-stack developer with expertise in React, Node.js, and cloud architecture. Focus on scalable web applications.',
                'email': 'emily.r@example.com',
                'source_url': 'https://example.com/emily',
                'source_domain': 'example.com'
            },
            {
                'name': 'David Kim',
                'title': 'AI Research Scientist',
                'bio': 'Ph.D. in Artificial Intelligence. Research focus on natural language processing and large language models.',
                'email': 'david.k@example.com',
                'source_url': 'https://example.com/david',
                'source_domain': 'example.com'
            },
            {
                'name': 'Jessica Taylor',
                'title': 'DevOps Engineer',
                'bio': 'Expert in CI/CD, Kubernetes, Docker, and cloud infrastructure. Strong background in automation and monitoring.',
                'email': 'jessica.t@example.com',
                'source_url': 'https://example.com/jessica',
                'source_domain': 'example.com'
            }
        ]
        
        for profile_data in profiles:
            try:
                profile = profile_repo.create(**profile_data)
                print(f"   ✅ Created profile: {profile.name}")
            except Exception as e:
                print(f"   ⚠️  Skipped {profile_data['name']}: {e}")
        
        # Sample knowledge snippets
        snippets = [
            {
                'title': 'Introduction to Machine Learning',
                'content': 'Machine learning is a subset of artificial intelligence that enables computers to learn from data without explicit programming. Key techniques include supervised learning, unsupervised learning, and reinforcement learning.',
                'content_type': 'article',
                'category': 'Technical',
                'source_url': 'https://example.com/ml-intro',
                'source_domain': 'example.com',
                'confidence_score': 0.95
            },
            {
                'title': 'Best Practices for Software Development',
                'content': 'Modern software development requires following best practices like code reviews, automated testing, continuous integration, and documentation. Version control with Git is essential for team collaboration.',
                'content_type': 'guide',
                'category': 'Technical',
                'source_url': 'https://example.com/dev-practices',
                'source_domain': 'example.com',
                'confidence_score': 0.90
            },
            {
                'title': 'Cloud Computing Fundamentals',
                'content': 'Cloud computing provides on-demand computing resources including servers, storage, and applications. Major providers include AWS, Azure, and Google Cloud. Benefits include scalability, cost-efficiency, and flexibility.',
                'content_type': 'article',
                'category': 'Technical',
                'source_url': 'https://example.com/cloud-basics',
                'source_domain': 'example.com',
                'confidence_score': 0.88
            },
            {
                'title': 'Data Science Career Guide',
                'content': 'Data science combines statistics, programming, and domain expertise. Essential skills include Python, R, SQL, machine learning, and data visualization. Communication skills are equally important for explaining insights.',
                'content_type': 'guide',
                'category': 'Business',
                'source_url': 'https://example.com/ds-career',
                'source_domain': 'example.com',
                'confidence_score': 0.85
            },
            {
                'title': 'Neural Networks Explained',
                'content': 'Neural networks are computing systems inspired by biological brains. They consist of layers of interconnected nodes that process information. Deep learning uses multiple layers to learn complex patterns in data.',
                'content_type': 'article',
                'category': 'Technical',
                'source_url': 'https://example.com/neural-nets',
                'source_domain': 'example.com',
                'confidence_score': 0.92
            }
        ]
        
        for snippet_data in snippets:
            try:
                snippet = snippet_repo.create_snippet(**snippet_data)
                print(f"   ✅ Created snippet: {snippet.title}")
            except Exception as e:
                print(f"   ⚠️  Skipped {snippet_data['title']}: {e}")
        
        session.commit()
    
    print("✅ Sample data created!")

def demo_search():
    """Demonstrate search functionality."""
    print("\n" + "="*60)
    print("🔍 Vector Search Demo")
    print("="*60)
    
    # Initialize search service
    db_session = DatabaseSession('sqlite:///data/profiles.db')
    search_service = create_search_service(db_session)
    
    # Index content
    print("\n📊 Indexing content...")
    stats = search_service.rebuild_index()
    print(f"   Indexed {stats['profiles']['indexed']} profiles")
    print(f"   Indexed {stats['snippets']['indexed']} snippets")
    print(f"   Total: {stats['total_indexed']} items")
    
    # Demo searches
    queries = [
        "machine learning and artificial intelligence",
        "software engineering and web development",
        "cloud computing and DevOps"
    ]
    
    for query in queries:
        print(f"\n🔍 Query: '{query}'")
        print("-" * 60)
        
        results = search_service.search(
            query=query,
            k=3,
            min_score=0.3,
            use_expansion=False
        )
        
        print(f"Found {len(results.results)} results in {results.search_time:.3f}s\n")
        
        for i, result in enumerate(results.results, 1):
            print(f"{i}. [{result.entity_type.upper()}] Score: {result.score:.3f}")
            if result.content:
                if result.entity_type == 'profile':
                    print(f"   Name: {result.content.get('name')}")
                    print(f"   Title: {result.content.get('title')}")
                    print(f"   Bio: {result.content.get('bio', '')[:80]}...")
                elif result.entity_type == 'snippet':
                    print(f"   Title: {result.content.get('title')}")
                    print(f"   Type: {result.content.get('content_type')}")
                    print(f"   Preview: {result.content.get('content', '')[:80]}...")
            print()

def main():
    print("\n" + "="*60)
    print("🚀 Vector Search System Demo")
    print("="*60)
    
    # Create sample data
    create_sample_data()
    
    # Demo search
    demo_search()
    
    print("\n" + "="*60)
    print("✅ Demo Complete!")
    print("="*60)
    print("\n💡 Try the interactive search:")
    print("   python examples/search_example.py")
    print("\n📚 Read the documentation:")
    print("   QUICKSTART_SEARCH.md")
    print("   docs/VECTOR_SEARCH.md")

if __name__ == "__main__":
    main()
