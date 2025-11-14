"""
Embeddings Module
Handles OpenAI embedding generation with caching
"""

import pickle
import os
from typing import List, Dict, Any, Optional, Tuple
import time
from openai import OpenAI


class EmbeddingGenerator:
    """Generate and cache embeddings using OpenAI API"""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize EmbeddingGenerator
        
        Args:
            api_key: OpenAI API key (loads from config if not provided)
            model: Embedding model name (loads from config if not provided)
        """
        from config import OPENAI_API_KEY, EMBEDDING_MODEL, OPENAI_API_BASE
        
        self.api_key = api_key or OPENAI_API_KEY
        self.model = model or EMBEDDING_MODEL
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY in .env file")
        
        # Initialize OpenAI client
        if OPENAI_API_BASE:
            self.client = OpenAI(api_key=self.api_key, base_url=OPENAI_API_BASE)
        else:
            self.client = OpenAI(api_key=self.api_key)
        
        self.cache = {}  # In-memory cache
        
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as list of floats
        """
        # Check cache first
        if text in self.cache:
            return self.cache[text]
        
        try:
            # Call OpenAI API
            response = self.client.embeddings.create(
                input=text,
                model=self.model
            )
            
            embedding = response.data[0].embedding
            
            # Cache the result
            self.cache[text] = embedding
            
            return embedding
            
        except Exception as e:
            print(f"Error generating embedding: {e}")
            raise
    
    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 100, 
                                  show_progress: bool = True) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches
        
        Args:
            texts: List of texts to embed
            batch_size: Number of texts to process at once
            show_progress: Whether to print progress
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        total_batches = (len(texts) + batch_size - 1) // batch_size
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            if show_progress:
                print(f"Processing batch {batch_num}/{total_batches}...")
            
            try:
                # Process batch
                response = self.client.embeddings.create(
                    input=batch,
                    model=self.model
                )
                
                # Extract embeddings
                batch_embeddings = [item.embedding for item in response.data]
                embeddings.extend(batch_embeddings)
                
                # Cache results
                for text, embedding in zip(batch, batch_embeddings):
                    self.cache[text] = embedding
                
                # Rate limiting - be nice to the API
                if i + batch_size < len(texts):
                    time.sleep(0.5)
                    
            except Exception as e:
                print(f"Error processing batch {batch_num}: {e}")
                raise
        
        if show_progress:
            print(f"✓ Generated {len(embeddings)} embeddings")
        
        return embeddings
    
    def embed_vendors(self, vendors: List[Dict[str, Any]], 
                     text_field: str = "text") -> Tuple[List[List[float]], List[Dict[str, Any]]]:
        """
        Generate embeddings for vendor records
        
        Args:
            vendors: List of vendor dictionaries
            text_field: Field name containing the text to embed
            
        Returns:
            Tuple of (embeddings list, vendors with metadata)
        """
        from utils.text_processor import TextProcessor
        
        # Prepare texts
        texts = []
        processed_vendors = []
        
        for vendor in vendors:
            # If text field exists, use it; otherwise generate it
            if text_field in vendor:
                text = vendor[text_field]
            else:
                text = TextProcessor.prepare_for_embedding(vendor)
                vendor['text'] = text  # Store for future use
            
            texts.append(text)
            processed_vendors.append(vendor)
        
        # Generate embeddings
        embeddings = self.generate_embeddings_batch(texts)
        
        return embeddings, processed_vendors
    
    def save_cache(self, cache_path: str):
        """
        Save embedding cache to disk
        
        Args:
            cache_path: Path to save cache file
        """
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        
        with open(cache_path, 'wb') as f:
            pickle.dump(self.cache, f)
        
        print(f"✓ Saved {len(self.cache)} cached embeddings to {cache_path}")
    
    def load_cache(self, cache_path: str):
        """
        Load embedding cache from disk
        
        Args:
            cache_path: Path to cache file
        """
        if os.path.exists(cache_path):
            with open(cache_path, 'rb') as f:
                self.cache = pickle.load(f)
            
            print(f"✓ Loaded {len(self.cache)} cached embeddings from {cache_path}")
        else:
            print(f"No cache file found at {cache_path}")


def generate_embeddings(texts: List[str], api_key: Optional[str] = None) -> List[List[float]]:
    """
    Convenience function to generate embeddings
    
    Args:
        texts: List of texts to embed
        api_key: Optional API key
        
    Returns:
        List of embedding vectors
    """
    generator = EmbeddingGenerator(api_key=api_key)
    return generator.generate_embeddings_batch(texts)
