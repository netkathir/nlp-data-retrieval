"""
Pinecone Vector Store Module
Handles storage and retrieval of embeddings using Pinecone vector database
"""

from pinecone import Pinecone, ServerlessSpec
import numpy as np
from typing import List, Dict, Any, Tuple
import time
import config

class PineconeVectorStore:
    """Manages embeddings storage in Pinecone vector database"""
    
    def __init__(self):
        """Initialize Pinecone connection"""
        if not config.PINECONE_API_KEY:
            raise ValueError("Pinecone API key is required. Set PINECONE_API_KEY in .env file")
        
        # Initialize Pinecone
        self.pc = Pinecone(api_key=config.PINECONE_API_KEY)
        self.index_name = config.PINECONE_INDEX_NAME
        self.dimension = 3072  # text-embedding-3-large dimensions
        
        # Create or connect to index
        self._initialize_index()
        
        # Connect to index
        self.index = self.pc.Index(self.index_name)
        
        print(f"✅ Connected to Pinecone index: {self.index_name}")
    
    def _initialize_index(self):
        """Create Pinecone index if it doesn't exist"""
        existing_indexes = [index.name for index in self.pc.list_indexes()]
        
        if self.index_name not in existing_indexes:
            print(f"📊 Creating new Pinecone index: {self.index_name}")
            self.pc.create_index(
                name=self.index_name,
                dimension=self.dimension,
                metric='cosine',  # Use cosine similarity
                spec=ServerlessSpec(
                    cloud='aws',
                    region=config.PINECONE_ENVIRONMENT
                )
            )
            # Wait for index to be ready
            while not self.pc.describe_index(self.index_name).status['ready']:
                time.sleep(1)
            print(f"✅ Index created successfully")
        else:
            print(f"✅ Using existing Pinecone index: {self.index_name}")
    
    def upsert_embeddings(self, embeddings: np.ndarray, metadata: List[Dict[str, Any]], 
                          db_fingerprint: str = None) -> None:
        """
        Store embeddings in Pinecone
        
        Args:
            embeddings: Numpy array of embeddings (n_samples, dimension)
            metadata: List of metadata dicts for each embedding
            db_fingerprint: Database fingerprint for change detection (stored in special vector)
        """
        print(f"📤 Uploading {len(embeddings)} embeddings to Pinecone...")
        
        # Prepare vectors for upsert
        vectors = []
        for idx, (embedding, meta) in enumerate(zip(embeddings, metadata)):
            vector_id = f"vendor_{idx}"
            
            # Filter metadata - Pinecone only accepts string, number, boolean, or list of strings
            filtered_meta = {"index": idx}
            for key, value in meta.items():
                if value is None:
                    continue
                if isinstance(value, (str, int, float, bool)):
                    filtered_meta[key] = value
                elif isinstance(value, list):
                    # Handle list of dicts (like notes_raw) - serialize as JSON string
                    if value and isinstance(value[0], dict):
                        import json
                        filtered_meta[f"{key}_json"] = json.dumps(value)
                    # Include lists of simple types
                    elif all(isinstance(v, (str, int, float, bool)) for v in value):
                        filtered_meta[key] = value
                # Skip other complex types
            
            vectors.append({
                "id": vector_id,
                "values": embedding.tolist(),
                "metadata": filtered_meta
            })
        
        # Add database fingerprint as a special metadata-only vector
        if db_fingerprint:
            # Create a small random vector (Pinecone requires non-zero values)
            fingerprint_vector = [0.001] * self.dimension
            vectors.append({
                "id": "_db_fingerprint",
                "values": fingerprint_vector,
                "metadata": {
                    "type": "fingerprint",
                    "db_fingerprint": db_fingerprint,
                    "vendor_count": len(metadata),
                    "timestamp": time.time()
                }
            })
        
        # Upsert in batches of 100
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            self.index.upsert(vectors=batch)
            print(f"  Uploaded {min(i + batch_size, len(vectors))}/{len(vectors)} vectors")
        
        print(f"✅ Successfully uploaded {len(embeddings)} embeddings to Pinecone")
    
    def query(self, query_embedding: np.ndarray, top_k: int = 5, 
              filter_dict: Dict[str, Any] = None) -> Tuple[List[int], np.ndarray, List[Dict[str, Any]]]:
        """
        Query Pinecone for similar vectors
        
        Args:
            query_embedding: Query vector (dimension,)
            top_k: Number of results to return
            filter_dict: Optional metadata filters
            
        Returns:
            Tuple of (indices, similarities, metadata_list)
        """
        # Query Pinecone (get extra to account for fingerprint vector)
        results = self.index.query(
            vector=query_embedding.tolist(),
            top_k=top_k + 1,  # Get one extra in case fingerprint is returned
            include_metadata=True,
            filter=filter_dict
        )
        
        # Extract indices, scores, and metadata (skip fingerprint vector)
        indices = []
        similarities = []
        metadata_list = []
        
        for match in results['matches']:
            # Skip the fingerprint vector
            if match['id'] == '_db_fingerprint':
                continue
            
            indices.append(match['metadata']['index'])
            similarities.append(match['score'])
            # Return full metadata from Pinecone
            metadata_list.append(match['metadata'])
            
            # Stop once we have enough results
            if len(indices) >= top_k:
                break
        
        return indices, np.array(similarities), metadata_list
    
    def get_stats(self) -> Dict[str, Any]:
        """Get Pinecone index statistics"""
        stats = self.index.describe_index_stats()
        return {
            "total_vectors": stats.get('total_vector_count', 0),
            "dimension": stats.get('dimension', 0),
            "index_name": self.index_name
        }
    
    def delete_all(self):
        """Delete all vectors from the index"""
        print(f"🗑️  Deleting all vectors from {self.index_name}...")
        self.index.delete(delete_all=True)
        print(f"✅ All vectors deleted")
    
    def check_exists(self) -> bool:
        """Check if embeddings exist in Pinecone"""
        stats = self.get_stats()
        return stats['total_vectors'] > 0
    
    def get_db_fingerprint(self) -> Tuple[str, int]:
        """
        Retrieve database fingerprint from Pinecone
        
        Returns:
            Tuple of (fingerprint_hash, vendor_count) or (None, 0) if not found
        """
        try:
            # Fetch the special fingerprint vector
            result = self.index.fetch(ids=["_db_fingerprint"])
            
            if result and '_db_fingerprint' in result['vectors']:
                metadata = result['vectors']['_db_fingerprint']['metadata']
                vendor_count = int(metadata.get('vendor_count', 0))  # Convert to int
                return metadata.get('db_fingerprint'), vendor_count
        except Exception as e:
            print(f"⚠️  Could not retrieve fingerprint from Pinecone: {e}")
        
        return None, 0
