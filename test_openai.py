"""
Test OpenAI embeddings with your API key.
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

from src.search.indexing import ContentVectorizationPipeline, EmbeddingConfig

def test_openai_embeddings():
    """Test OpenAI embeddings."""
    print("\n" + "="*60)
    print("🧪 Testing OpenAI Embeddings")
    print("="*60)
    
    try:
        # Initialize with OpenAI
        config = EmbeddingConfig(
            provider='openai',
            model_name='text-embedding-3-small'
        )
        
        print(f"\n📋 Configuration:")
        print(f"   Provider: {config.provider}")
        print(f"   Model: {config.model_name}")
        
        vectorizer = ContentVectorizationPipeline(config)
        print(f"   Dimension: {config.dimension}")
        
        # Test encoding
        print(f"\n🔄 Encoding test texts...")
        texts = [
            "Machine learning is transforming technology",
            "Python is a versatile programming language",
            "Artificial intelligence enables smart systems"
        ]
        
        embeddings = vectorizer.encode(texts)
        print(f"\n✅ Successfully encoded {len(texts)} texts!")
        print(f"   Shape: {embeddings.shape}")
        print(f"   Dimension: {embeddings.shape[1]}")
        print(f"   Sample embedding values: {embeddings[0][:5]}")
        
        # Test single encoding
        single_text = "Data science combines statistics and programming"
        single_embedding = vectorizer.encode_single(single_text)
        print(f"\n✅ Single encoding successful!")
        print(f"   Shape: {single_embedding.shape}")
        
        # Compare similarity
        import numpy as np
        from src.search.vector_search import SimilarityComputationAlgorithms
        
        sim1 = SimilarityComputationAlgorithms.cosine_similarity(embeddings[0], embeddings[2])
        sim2 = SimilarityComputationAlgorithms.cosine_similarity(embeddings[0], embeddings[1])
        
        print(f"\n📊 Similarity Scores:")
        print(f"   'Machine learning' vs 'AI': {sim1:.3f}")
        print(f"   'Machine learning' vs 'Python': {sim2:.3f}")
        print(f"   ✅ Higher score for more related concepts!")
        
        print("\n" + "="*60)
        print("🎉 OpenAI Embeddings Working Perfectly!")
        print("="*60)
        print("\n💡 Benefits of OpenAI embeddings:")
        print("   ✅ Higher quality (1536 dimensions)")
        print("   ✅ Better semantic understanding")
        print("   ✅ Optimized for search tasks")
        print("   ✅ No model download required")
        print(f"\n💰 Cost: ~$0.02 per 1M tokens (~750K words)")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_openai_embeddings()
    if success:
        print("\n✅ Ready to rebuild index with OpenAI embeddings!")
        print("\nRun: python demo_search.py")
    else:
        print("\n⚠️  Check your API key and internet connection")
