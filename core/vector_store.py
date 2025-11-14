"""
Vector Store Module
Handles storage and similarity search of embeddings
"""

import pickle
import os
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from sklearn.metrics.pairwise import cosine_similarity


class VectorStore:
    """Store and search embeddings using cosine similarity"""
    
    def __init__(self):
        """Initialize VectorStore"""
        self.embeddings = None  # numpy array of embeddings
        self.metadata = []  # List of vendor records
        self.dimension = None
        
    def add_embeddings(self, embeddings: List[List[float]], 
                      metadata: List[Dict[str, Any]]):
        """
        Add embeddings and their associated metadata
        
        Args:
            embeddings: List of embedding vectors
            metadata: List of vendor records (same length as embeddings)
        """
        if len(embeddings) != len(metadata):
            raise ValueError("Number of embeddings must match number of metadata items")
        
        # Convert to numpy array for efficient computation
        embeddings_array = np.array(embeddings)
        
        if self.embeddings is None:
            self.embeddings = embeddings_array
            self.metadata = list(metadata)
            self.dimension = embeddings_array.shape[1]
        else:
            # Append to existing embeddings
            self.embeddings = np.vstack([self.embeddings, embeddings_array])
            self.metadata.extend(metadata)
        
        print(f"✓ Added {len(embeddings)} embeddings. Total: {len(self.metadata)}")
    
    def search(self, query_embedding: List[float], top_k: int = 5, 
               threshold: Optional[float] = None) -> List[Tuple[Dict[str, Any], float]]:
        """
        Search for similar vectors using cosine similarity
        
        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            threshold: Minimum similarity score (0-1) - NOT USED HERE, applied after keyword boost
            
        Returns:
            List of tuples (metadata, similarity_score) sorted by similarity
        """
        if self.embeddings is None or len(self.embeddings) == 0:
            return []
        
        # Convert query to numpy array
        query_vector = np.array(query_embedding).reshape(1, -1)
        
        # Calculate cosine similarity
        similarities = cosine_similarity(query_vector, self.embeddings)[0]
        
        # Get top K indices (get more to allow for post-boost filtering)
        # Don't apply threshold here - it will be applied after keyword boosting
        top_indices = np.argsort(similarities)[::-1][:top_k * 3]  # Get 3x results for boost filtering
        
        # Build results WITHOUT applying match boost here
        # Match boost will be applied in query_engine AFTER keyword boosting
        results = []
        for idx in top_indices:
            similarity_score = float(similarities[idx])
            
            result = {
                **self.metadata[idx],
                'similarity_score': similarity_score  # Return raw score, boost applied later
            }
            results.append((result, similarity_score))
        
        return results
    
    def search_with_filter(self, query_embedding: List[float], 
                          filters: Dict[str, Any],
                          top_k: int = 5,
                          threshold: float = 0.0) -> List[Tuple[Dict[str, Any], float]]:
        """
        Search with metadata filters
        
        Args:
            query_embedding: Query vector
            filters: Dictionary of field:value pairs to filter by
            top_k: Number of results to return
            threshold: Minimum similarity threshold (0-1) - NOT USED, applied after boost
            
        Returns:
            Filtered results sorted by similarity
        """
        # First, get a larger set of results (get 3x more for filtering + boosting)
        all_results = self.search(query_embedding, top_k=min(len(self.metadata), top_k * 3), threshold=None)
        
        # Apply filters
        filtered_results = []
        for result, score in all_results:
            match = True
            for field, value in filters.items():
                if field in result:
                    # Handle case-insensitive string matching
                    if isinstance(value, str) and isinstance(result[field], str):
                        if value.lower() not in result[field].lower():
                            match = False
                            break
                    elif result[field] != value:
                        match = False
                        break
                else:
                    match = False
                    break
            
            if match:
                filtered_results.append((result, score))
        
        return filtered_results
    
    def get_all_metadata(self) -> List[Dict[str, Any]]:
        """
        Get all stored metadata
        
        Returns:
            List of all vendor records
        """
        return self.metadata
    
    def get_count(self) -> int:
        """
        Get number of stored embeddings
        
        Returns:
            Count of embeddings
        """
        return len(self.metadata) if self.metadata else 0
    
    def clear(self):
        """Clear all embeddings and metadata"""
        self.embeddings = None
        self.metadata = []
        self.dimension = None
        print("✓ Vector store cleared")
    
    def save(self, file_path: str):
        """
        Save vector store to disk
        
        Args:
            file_path: Path to save file
        """
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        data = {
            'embeddings': self.embeddings,
            'metadata': self.metadata,
            'dimension': self.dimension
        }
        
        with open(file_path, 'wb') as f:
            pickle.dump(data, f)
        
        print(f"✓ Saved vector store with {len(self.metadata)} items to {file_path}")
    
    def load(self, file_path: str):
        """
        Load vector store from disk
        
        Args:
            file_path: Path to load from
        """
        if not os.path.exists(file_path):
            print(f"No vector store found at {file_path}")
            return False
        
        with open(file_path, 'rb') as f:
            data = pickle.load(f)
        
        self.embeddings = data.get('embeddings')
        self.metadata = data.get('metadata', [])
        self.dimension = data.get('dimension')
        
        print(f"✓ Loaded vector store with {len(self.metadata)} items from {file_path}")
        return True
    
    def update_metadata(self, index: int, new_metadata: Dict[str, Any]):
        """
        Update metadata for a specific item
        
        Args:
            index: Index of item to update
            new_metadata: New metadata dictionary
        """
        if 0 <= index < len(self.metadata):
            self.metadata[index] = new_metadata
        else:
            raise IndexError(f"Index {index} out of range")
    
    def delete(self, index: int):
        """
        Delete an item from the vector store
        
        Args:
            index: Index of item to delete
        """
        if 0 <= index < len(self.metadata):
            self.embeddings = np.delete(self.embeddings, index, axis=0)
            del self.metadata[index]
        else:
            raise IndexError(f"Index {index} out of range")
