"""
Vector Store Module
Handles storage and similarity search of embeddings
Supports both local storage (pickle) and Pinecone vector database
"""

import pickle
import os
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from sklearn.metrics.pairwise import cosine_similarity
import config

# Import Pinecone store if enabled
if config.USE_PINECONE:
    from core.pinecone_store import PineconeVectorStore


class VectorStore:
    """Store and search embeddings using cosine similarity (local) or Pinecone (cloud)"""
    
    def __init__(self):
        """Initialize VectorStore with Pinecone or local storage"""
        self.embeddings = None  # numpy array of embeddings (for local storage)
        self.metadata = []  # List of vendor records (for local storage)
        self.dimension = None
        
        # Get storage mode from config
        self.storage_mode = config.STORAGE_MODE  # "pinecone_only", "local_only", or "hybrid"
        
        # Initialize Pinecone if enabled
        self.use_pinecone = config.USE_PINECONE and self.storage_mode in ["pinecone_only", "hybrid"]
        self.pinecone_store = None
        
        if self.use_pinecone:
            try:
                self.pinecone_store = PineconeVectorStore()
                if self.storage_mode == "pinecone_only":
                    print(f"✅ Using Pinecone ONLY (cloud storage, no local cache)")
                else:
                    print(f"✅ Using Pinecone + local cache (hybrid mode)")
            except Exception as e:
                print(f"⚠️  Failed to initialize Pinecone: {e}")
                print(f"   Falling back to local storage")
                self.use_pinecone = False
                self.storage_mode = "local_only"
        else:
            print(f"✅ Using local storage only")
        
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
        
        # Store in Pinecone if enabled
        if self.use_pinecone and self.pinecone_store:
            self.pinecone_store.upsert_embeddings(embeddings_array, metadata)
            # Also keep in memory for quick access
            self.metadata = list(metadata)
            self.embeddings = embeddings_array
            self.dimension = embeddings_array.shape[1]
        else:
            # Local storage only
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
        Search for similar vectors using cosine similarity (local) or Pinecone (cloud)
        
        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            threshold: Minimum similarity score (0-1) - NOT USED HERE, applied after keyword boost
            
        Returns:
            List of tuples (metadata, similarity_score) sorted by similarity
        """
        # Convert query to numpy array
        query_vector = np.array(query_embedding).reshape(1, -1)
        
        # Use Pinecone if enabled
        if self.use_pinecone and self.pinecone_store:
            try:
                # Query Pinecone
                indices, similarities, metadata_list = self.pinecone_store.query(
                    query_vector[0], 
                    top_k=top_k * 3  # Get 3x results for boost filtering
                )
                
                # Build results
                results = []
                
                if self.storage_mode == "pinecone_only":
                    # Cloud-only mode: use metadata from Pinecone
                    import json
                    for meta, similarity_score in zip(metadata_list, similarities):
                        # Deserialize JSON fields (like notes_raw)
                        deserialized_meta = dict(meta)
                        for key, value in meta.items():
                            if key.endswith('_json') and isinstance(value, str):
                                try:
                                    original_key = key[:-5]  # Remove '_json' suffix
                                    deserialized_meta[original_key] = json.loads(value)
                                    del deserialized_meta[key]  # Remove the _json version
                                except:
                                    pass  # Keep original if deserialization fails
                        
                        result = {
                            **deserialized_meta,
                            'similarity_score': float(similarity_score)
                        }
                        results.append((result, float(similarity_score)))
                else:
                    # Hybrid mode: use metadata from local cache
                    import json
                    if not self.metadata:
                        print("⚠️  No local metadata - falling back to Pinecone metadata")
                        for meta, similarity_score in zip(metadata_list, similarities):
                            # Deserialize JSON fields (like notes_raw)
                            deserialized_meta = dict(meta)
                            for key, value in meta.items():
                                if key.endswith('_json') and isinstance(value, str):
                                    try:
                                        original_key = key[:-5]  # Remove '_json' suffix
                                        deserialized_meta[original_key] = json.loads(value)
                                        del deserialized_meta[key]  # Remove the _json version
                                    except:
                                        pass  # Keep original if deserialization fails
                            
                            result = {
                                **deserialized_meta,
                                'similarity_score': float(similarity_score)
                            }
                            results.append((result, float(similarity_score)))
                    else:
                        for idx, similarity_score in zip(indices, similarities):
                            if idx < len(self.metadata):
                                result = {
                                    **self.metadata[idx],
                                    'similarity_score': float(similarity_score)
                                }
                                results.append((result, float(similarity_score)))
                
                return results
            except Exception as e:
                print(f"⚠️  Pinecone query failed: {e}")
                print(f"   Falling back to local search")
        
        # Local cosine similarity search
        if self.embeddings is None or len(self.embeddings) == 0:
            return []
        
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
        In cloud-only mode, fetches from Pinecone if local metadata is empty
        
        Returns:
            List of all vendor records
        """
        # If we have local metadata, return it
        if self.metadata:
            return self.metadata
        
        # Cloud-only mode: fetch metadata from Pinecone
        if self.storage_mode == "pinecone_only" and self.use_pinecone and self.pinecone_store:
            try:
                # Query with a dummy vector to get all metadata
                import numpy as np
                dummy_query = np.zeros(3072)  # Match embedding dimension
                
                # Get all vectors (use large top_k)
                stats = self.pinecone_store.get_stats()
                total = stats.get('total_vectors', 0)
                
                if total > 0:
                    # Fetch all vendor metadata
                    indices, similarities, metadata_list = self.pinecone_store.query(
                        dummy_query, 
                        top_k=total
                    )
                    
                    # Deserialize JSON fields
                    import json
                    deserialized_metadata = []
                    for meta in metadata_list:
                        deserialized_meta = dict(meta)
                        for key, value in meta.items():
                            if key.endswith('_json') and isinstance(value, str):
                                try:
                                    original_key = key[:-5]
                                    deserialized_meta[original_key] = json.loads(value)
                                    del deserialized_meta[key]
                                except:
                                    pass
                        deserialized_metadata.append(deserialized_meta)
                    
                    # Cache it locally for performance
                    self.metadata = deserialized_metadata
                    return deserialized_metadata
            except Exception as e:
                print(f"⚠️  Failed to fetch metadata from Pinecone: {e}")
        
        return self.metadata
    
    def get_count(self) -> int:
        """
        Get number of stored embeddings
        
        Returns:
            Count of embeddings
        """
        return len(self.metadata) if self.metadata else 0
    
    def clear(self):
        """Clear all embeddings and metadata (both local and Pinecone)"""
        self.embeddings = None
        self.metadata = []
        self.dimension = None
        
        # Clear Pinecone index if enabled
        if self.use_pinecone and self.pinecone_store:
            try:
                print("🗑️  Clearing Pinecone index...")
                self.pinecone_store.delete_all()
            except Exception as e:
                print(f"⚠️  Failed to clear Pinecone: {e}")
        
        print("✓ Vector store cleared")
    
    def save(self, file_path: str):
        """
        Save vector store to disk with database metadata for change detection
        Also syncs to Pinecone if enabled
        
        Args:
            file_path: Path to save file
        """
        # Calculate database fingerprint for change detection
        db_fingerprint = self._calculate_db_fingerprint(self.metadata)
        
        # In cloud-only mode, only sync to Pinecone (skip local cache)
        if self.storage_mode == "pinecone_only":
            if self.use_pinecone and self.pinecone_store:
                try:
                    print(f"☁️  Syncing {len(self.metadata)} embeddings to Pinecone (cloud-only mode)...")
                    # Clear existing vectors first
                    self.pinecone_store.delete_all()
                    # Upload new vectors with fingerprint
                    self.pinecone_store.upsert_embeddings(self.embeddings, self.metadata, db_fingerprint)
                    print(f"✅ Successfully synced to Pinecone (no local cache)")
                    return
                except Exception as e:
                    print(f"⚠️  Failed to sync to Pinecone: {e}")
                    print(f"   Cannot save - cloud-only mode requires Pinecone")
                    return
            else:
                print(f"⚠️  Pinecone not available but storage_mode is 'pinecone_only'")
                return
        
        # Local-only or hybrid mode: save to local cache
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        data = {
            'embeddings': self.embeddings,
            'metadata': self.metadata,
            'dimension': self.dimension,
            'db_fingerprint': db_fingerprint,
            'vendor_count': len(self.metadata)
        }
        
        # Save locally (for backup and metadata)
        with open(file_path, 'wb') as f:
            pickle.dump(data, f)
        
        print(f"✓ Saved vector store with {len(self.metadata)} items to {file_path}")
        
        # Sync to Pinecone if in hybrid mode
        if self.storage_mode == "hybrid" and self.use_pinecone and self.pinecone_store:
            try:
                print(f"☁️  Syncing {len(self.metadata)} embeddings to Pinecone (hybrid mode)...")
                # Clear existing vectors first
                self.pinecone_store.delete_all()
                # Upload new vectors with fingerprint
                self.pinecone_store.upsert_embeddings(self.embeddings, self.metadata, db_fingerprint)
                print(f"✅ Successfully synced to Pinecone")
            except Exception as e:
                print(f"⚠️  Failed to sync to Pinecone: {e}")
                print(f"   Local cache saved successfully")
    
    def _calculate_db_fingerprint(self, metadata: List[Dict[str, Any]]) -> str:
        """
        Calculate a fingerprint of the database state for change detection
        
        Args:
            metadata: List of vendor records
            
        Returns:
            Fingerprint string (hash of critical fields)
        """
        import hashlib
        import json
        
        # Create fingerprint from vendor IDs and updated_at timestamps
        fingerprint_data = []
        for vendor in metadata:
            # Include ID, updated_at, and notes_count for change detection
            fp = {
                'id': vendor.get('id'),
                'updated_at': vendor.get('updated_at', ''),
                'notes_count': vendor.get('notes_count', 0)
            }
            fingerprint_data.append(fp)
        
        # Sort by ID for consistent hashing
        fingerprint_data.sort(key=lambda x: x.get('id', 0))
        
        # Create hash
        fingerprint_str = json.dumps(fingerprint_data, sort_keys=True)
        return hashlib.md5(fingerprint_str.encode()).hexdigest()
    
    def load(self, file_path: str):
        """
        Load vector store from disk or Pinecone
        
        Args:
            file_path: Path to load from
        """
        # Cloud-only mode: load from Pinecone only (no local cache needed)
        if self.storage_mode == "pinecone_only":
            if self.use_pinecone and self.pinecone_store:
                try:
                    # Get fingerprint from Pinecone
                    db_fingerprint, vendor_count = self.pinecone_store.get_db_fingerprint()
                    
                    stats = self.pinecone_store.get_stats()
                    if stats['total_vectors'] > 0:
                        print(f"✅ Found {stats['total_vectors']} vectors in Pinecone (cloud-only mode)")
                        print(f"   No local cache needed")
                        
                        # Store fingerprint for change detection
                        self.db_fingerprint = db_fingerprint
                        self.vendor_count = vendor_count
                        
                        # We'll get metadata from Pinecone during queries
                        return True
                    else:
                        print(f"⚠️  No vectors found in Pinecone")
                        return False
                except Exception as e:
                    print(f"⚠️  Failed to check Pinecone: {e}")
                    return False
            else:
                print(f"⚠️  Pinecone not available but storage_mode is 'pinecone_only'")
                return False
        
        # Hybrid mode: load from Pinecone + local cache
        if self.storage_mode == "hybrid":
            if self.use_pinecone and self.pinecone_store:
                try:
                    if self.pinecone_store.check_exists():
                        print(f"✅ Found embeddings in Pinecone")
                        # Load local cache for metadata and fingerprinting
                        if os.path.exists(file_path):
                            with open(file_path, 'rb') as f:
                                data = pickle.load(f)
                            
                            self.embeddings = data.get('embeddings')
                            self.metadata = data.get('metadata', [])
                            self.dimension = data.get('dimension')
                            self.db_fingerprint = data.get('db_fingerprint')
                            self.vendor_count = data.get('vendor_count', len(self.metadata))
                            
                            print(f"✓ Loaded {len(self.metadata)} items (metadata from local, vectors from Pinecone)")
                            return True
                        else:
                            print(f"⚠️  Pinecone has vectors but no local cache found")
                            print(f"   Will use Pinecone metadata")
                            return True  # Can still work with Pinecone metadata
                except Exception as e:
                    print(f"⚠️  Failed to check Pinecone: {e}")
                    print(f"   Falling back to local cache")
        
        # Local-only mode: load from local cache
        if not os.path.exists(file_path):
            print(f"No vector store found at {file_path}")
            return False
        
        with open(file_path, 'rb') as f:
            data = pickle.load(f)
        
        self.embeddings = data.get('embeddings')
        self.metadata = data.get('metadata', [])
        self.dimension = data.get('dimension')
        self.db_fingerprint = data.get('db_fingerprint')
        self.vendor_count = data.get('vendor_count', len(self.metadata))
        
        print(f"✓ Loaded vector store with {len(self.metadata)} items from {file_path}")
        return True
    
    def is_stale(self, current_metadata: List[Dict[str, Any]]) -> bool:
        """
        Check if cached vector store is stale compared to current database
        
        Args:
            current_metadata: Current vendor data from database
            
        Returns:
            True if cache is stale and should be rebuilt
        """
        # If no fingerprint exists, consider it stale
        if not hasattr(self, 'db_fingerprint') or self.db_fingerprint is None:
            print("⚠ No database fingerprint found in cache - will rebuild")
            return True
        
        # Check vendor count first (quick check)
        if len(current_metadata) != self.vendor_count:
            print(f"⚠ Vendor count changed: {self.vendor_count} → {len(current_metadata)} - will rebuild")
            return True
        
        # Calculate current fingerprint
        current_fingerprint = self._calculate_db_fingerprint(current_metadata)
        
        # Compare fingerprints
        if current_fingerprint != self.db_fingerprint:
            print("⚠ Database content changed (updates/edits/notes) - will rebuild cache")
            return True
        
        print("✓ Cache is up-to-date with database")
        return False
    
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
    
    def update_embedding(self, index: int, new_embedding: List[float], new_metadata: Dict[str, Any]):
        """
        Update both embedding and metadata for a specific item
        
        Args:
            index: Index of item to update
            new_embedding: New embedding vector
            new_metadata: New metadata dictionary
        """
        if 0 <= index < len(self.metadata):
            # Update embedding
            self.embeddings[index] = np.array(new_embedding)
            # Update metadata
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
