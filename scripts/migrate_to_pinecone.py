#!/usr/bin/env python3
"""
Migrate embeddings from local cache to Pinecone
Run this once to upload your existing embeddings to Pinecone
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from core.vector_store import VectorStore
from core.pinecone_store import PineconeVectorStore
import pickle
import numpy as np

def migrate_to_pinecone():
    """Migrate local embeddings cache to Pinecone"""
    
    print("🚀 Pinecone Migration Tool")
    print("=" * 60)
    
    # Check if Pinecone is enabled
    if not config.USE_PINECONE:
        print("❌ Pinecone is not enabled in config")
        print("   Set USE_PINECONE=True in .env file")
        return False
    
    # Check if local cache exists
    cache_path = config.EMBEDDINGS_CACHE_PATH
    if not os.path.exists(cache_path):
        print(f"❌ No local cache found at: {cache_path}")
        print("   Generate embeddings first by running the application")
        return False
    
    print(f"✅ Found local cache: {cache_path}")
    
    # Load local cache
    print(f"📂 Loading embeddings from local cache...")
    try:
        with open(cache_path, 'rb') as f:
            cache_data = pickle.load(f)
        
        embeddings = cache_data['embeddings']
        metadata = cache_data['metadata']
        
        print(f"✅ Loaded {len(embeddings)} embeddings")
        print(f"   Dimension: {embeddings.shape[1]}")
        
    except Exception as e:
        print(f"❌ Error loading cache: {e}")
        return False
    
    # Initialize Pinecone
    print(f"\n🔌 Connecting to Pinecone...")
    try:
        pinecone_store = PineconeVectorStore()
    except Exception as e:
        print(f"❌ Failed to connect to Pinecone: {e}")
        return False
    
    # Check if embeddings already exist in Pinecone
    stats = pinecone_store.get_stats()
    print(f"\n📊 Current Pinecone stats:")
    print(f"   Index: {stats['index_name']}")
    print(f"   Vectors: {stats['total_vectors']}")
    print(f"   Dimension: {stats['dimension']}")
    
    if stats['total_vectors'] > 0:
        print(f"\n⚠️  Pinecone index already contains {stats['total_vectors']} vectors")
        response = input("   Delete existing and re-upload? (yes/no): ").strip().lower()
        if response == 'yes':
            pinecone_store.delete_all()
        else:
            print("   Skipping migration")
            return True
    
    # Upload to Pinecone
    print(f"\n📤 Uploading embeddings to Pinecone...")
    try:
        pinecone_store.upsert_embeddings(embeddings, metadata)
        print(f"✅ Migration complete!")
        
        # Verify
        stats = pinecone_store.get_stats()
        print(f"\n✅ Final Pinecone stats:")
        print(f"   Vectors: {stats['total_vectors']}")
        print(f"   Index: {stats['index_name']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error uploading to Pinecone: {e}")
        return False

if __name__ == "__main__":
    print("\n")
    success = migrate_to_pinecone()
    print("\n")
    
    if success:
        print("🎉 Migration successful!")
        print("   Your embeddings are now stored in Pinecone")
        print("   The application will use Pinecone for vector search")
    else:
        print("❌ Migration failed")
        print("   Check the error messages above")
    
    print("\n")
