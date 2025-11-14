"""
Query Engine Module
Main interface for semantic search and query processing
"""

from typing import List, Dict, Any, Optional, Tuple
from core.vector_store import VectorStore
from utils.data_loader import DataLoader
from utils.text_processor import TextProcessor


class SemanticSearch:
    """Main query engine for semantic search across vendor data"""
    
    def __init__(self, data_source: Optional[str] = None, 
                 vector_store_path: Optional[str] = None,
                 auto_load: bool = True):
        """
        Initialize SemanticSearch engine
        
        Args:
            data_source: Path to vendor data file
            vector_store_path: Path to saved vector store (optional)
            auto_load: Whether to automatically load and index data
        """
        from config import EMBEDDINGS_CACHE_PATH
        from core.embeddings import EmbeddingGenerator
        
        self.data_loader = DataLoader(data_source)
        self.text_processor = TextProcessor()
        self.embedding_generator = EmbeddingGenerator()
        self.vector_store = VectorStore()
        
        self.vector_store_path = vector_store_path or EMBEDDINGS_CACHE_PATH
        self.initialized = False
        
        if auto_load:
            self.initialize()
    
    def initialize(self, force_rebuild: bool = False):
        """
        Initialize the search engine by loading or building vector store
        
        Args:
            force_rebuild: Force rebuilding embeddings even if cache exists
        """
        # If force rebuild, clear existing data first
        if force_rebuild:
            print("Clearing existing vector store...")
            self.vector_store.clear()
        
        # Try to load existing vector store
        if not force_rebuild and self.vector_store.load(self.vector_store_path):
            self.initialized = True
            print(f"✓ Search engine initialized with {self.vector_store.get_count()} vendors")
            return
        
        # Build new vector store
        print("Building vector store from data...")
        self._build_vector_store()
        
        # Save for future use
        self.vector_store.save(self.vector_store_path)
        self.initialized = True
        
        print(f"✓ Search engine initialized with {self.vector_store.get_count()} vendors")
    
    def _build_vector_store(self):
        """Build vector store from vendor data"""
        # Load vendor data
        vendors = self.data_loader.load()
        
        if not vendors:
            raise ValueError("No vendor data found")
        
        # Generate embeddings
        embeddings, processed_vendors = self.embedding_generator.embed_vendors(vendors)
        
        # Add to vector store
        self.vector_store.add_embeddings(embeddings, processed_vendors)
    
    def query(self, query_text: str, top_k: int = 5, 
              threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Search for vendors matching the query
        
        Args:
            query_text: Natural language query
            top_k: Number of results to return
            threshold: Minimum similarity threshold (None = use default)
                      Applied AFTER keyword boosting to get accurate results
            
        Returns:
            List of matching vendor records with similarity scores
        """
        from config import SIMILARITY_THRESHOLD
        
        if not self.initialized:
            self.initialize()
        
        # Generate query embedding
        query_embedding = self.embedding_generator.generate_embedding(query_text)
        
        # Set threshold
        if threshold is None:
            threshold = SIMILARITY_THRESHOLD
        
        # Get more results initially (will filter after boosting)
        results = self.vector_store.search(query_embedding, top_k=top_k, threshold=None)
        
        # Apply keyword matching boost, match percentage boost, and cap to 100%
        from config import MATCH_PERCENTAGE_BOOST
        boosted_results = []
        for result in results:
            metadata = result[0]
            base_score = metadata.get('similarity_score', 0)
            
            # Apply keyword matching boost first
            keyword_boost = self._calculate_keyword_boost(query_text, metadata)
            score_after_keywords = base_score + keyword_boost
            
            # Apply match percentage boost multiplier
            final_score = min(score_after_keywords * MATCH_PERCENTAGE_BOOST, 1.0)
            
            metadata['similarity_score'] = final_score
            
            # Apply threshold AFTER all boosting
            if final_score >= threshold:
                boosted_results.append(metadata)
        
        # Sort by similarity score (descending) after applying boost
        boosted_results.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
        
        # Return only top_k results
        return boosted_results[:top_k]
    
    def _calculate_keyword_boost(self, query: str, vendor: Dict[str, Any]) -> float:
        """
        Calculate boost score based on keyword matches using CONFIGURABLE field priorities.
        This is DATABASE-AGNOSTIC - uses field indices and FIELD_MAP from config.py
        Returns a boost value between 0.0 and 0.3 (30% max boost)
        """
        from config import FIELD_MAP, FIELD_INDEX_WEIGHTS, SEMANTIC_SEARCH_FIELDS
        
        boost = 0.0
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        # Remove common words
        stop_words = {'in', 'at', 'the', 'a', 'an', 'and', 'or', 'for', 'find', 'search'}
        query_keywords = query_words - stop_words
        
        # Check all searchable fields from config
        for field_idx in SEMANTIC_SEARCH_FIELDS:
            if field_idx not in FIELD_MAP:
                continue
            
            field_config = FIELD_MAP[field_idx]
            field_name = field_config["name"]
            field_weight = FIELD_INDEX_WEIGHTS.get(field_idx, 1)
            
            # Get field value (try both logical name and field_X format)
            field_value = vendor.get(field_name)
            if field_value is None:
                field_value = vendor.get(f"field_{field_idx}")
            
            if not field_value:
                continue
            
            field_value_lower = str(field_value).lower()
            
            # Check for keyword matches
            for keyword in query_keywords:
                if len(keyword) > 3 and keyword in field_value_lower:
                    # Weight boost by field importance (higher weight = more boost)
                    if field_weight >= 15:  # Semantic fields (notes, description)
                        boost += 0.15
                    elif field_weight >= 10:
                        boost += 0.12
                    elif field_weight >= 8:
                        boost += 0.10
                    elif field_weight >= 5:
                        boost += 0.08
                    else:
                        boost += 0.05
                    break  # One boost per field to avoid over-boosting
        
        # Cap total boost at 0.3 (30%)
        return min(boost, 0.3)
    
    def query_with_filters(self, query_text: str, filters: Dict[str, Any],
                          top_k: int = 5, threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Search with additional filters
        
        Args:
            query_text: Natural language query
            filters: Dictionary of filters (e.g., {"vendor_state": "Maharashtra"})
            top_k: Number of results to return
            threshold: Minimum similarity threshold (None = use default)
                      Applied AFTER keyword boosting to get accurate results
            
        Returns:
            Filtered search results
        """
        from config import SIMILARITY_THRESHOLD
        
        if not self.initialized:
            self.initialize()
        
        # Generate query embedding
        query_embedding = self.embedding_generator.generate_embedding(query_text)
        
        # Use threshold if provided
        if threshold is None:
            threshold = SIMILARITY_THRESHOLD
        
        # Search with filters (pass None for threshold - will apply after boost)
        results = self.vector_store.search_with_filter(
            query_embedding, 
            filters=filters, 
            top_k=top_k,
            threshold=None  # Don't filter yet - apply after boost
        )
        
        # Apply keyword matching boost, match percentage boost, and cap to 100%
        from config import MATCH_PERCENTAGE_BOOST
        boosted_results = []
        for result in results:
            metadata = result[0]
            base_score = metadata.get('similarity_score', 0)
            
            # Apply keyword matching boost first
            keyword_boost = self._calculate_keyword_boost(query_text, metadata)
            score_after_keywords = base_score + keyword_boost
            
            # Apply match percentage boost multiplier
            final_score = min(score_after_keywords * MATCH_PERCENTAGE_BOOST, 1.0)
            
            metadata['similarity_score'] = final_score
            
            # Apply threshold AFTER all boosting
            if final_score >= threshold:
                boosted_results.append(metadata)
        
        # Sort by similarity score (descending) after applying boost
        boosted_results.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
        
        # Return only top_k results
        return boosted_results[:top_k]
    
    def search_by_location(self, query_text: str, state: Optional[str] = None,
                          city: Optional[str] = None, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search vendors by location using configurable field names
        
        Args:
            query_text: Natural language query
            state: Filter by vendor state
            city: Filter by vendor city
            top_k: Number of results
            
        Returns:
            Location-filtered results
        """
        from config import FILTER_FIELD_NAMES
        
        filters = {}
        if state:
            filters[FILTER_FIELD_NAMES.get('state', 'vendor_state')] = state
        if city:
            filters[FILTER_FIELD_NAMES.get('city', 'vendor_city')] = city
        
        if filters:
            return self.query_with_filters(query_text, filters, top_k)
        else:
            return self.query(query_text, top_k)
    
    def search_by_vehicle_type(self, vehicle_type: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search vendors by vehicle type using configurable field names
        
        Args:
            vehicle_type: Type of vehicle
            top_k: Number of results
            
        Returns:
            Vendors with matching vehicle type
        """
        from config import FILTER_FIELD_NAMES
        
        vehicle_field = FILTER_FIELD_NAMES.get('vehicle_type', 'vehicle_type')
        query_text = f"vendor with {vehicle_type}"
        results = self.query(query_text, top_k=top_k * 2)  # Get more results
        
        # Filter by vehicle type in results
        filtered = []
        for vendor in results:
            if vendor.get(vehicle_field) and \
               vehicle_type.lower() in str(vendor[vehicle_field]).lower():
                filtered.append(vendor)
                if len(filtered) >= top_k:
                    break
        
        return filtered
    
    def get_verified_vendors(self, query_text: str = "vendor", 
                           top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Get only verified vendors using configurable field names
        
        Args:
            query_text: Natural language query
            top_k: Number of results
            
        Returns:
            Verified vendors only
        """
        from config import FILTER_FIELD_NAMES
        
        verification_field = FILTER_FIELD_NAMES.get('verification', 'verification')
        results = self.query(query_text, top_k=top_k * 2)
        return [v for v in results if v.get(verification_field) == 'Verified'][:top_k]
    
    def get_owners_vs_brokers(self, query_text: str, owner_broker: str,
                             top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Filter by owner or broker using configurable field names
        
        Args:
            query_text: Natural language query
            owner_broker: "Owner" or "Broker"
            top_k: Number of results
            
        Returns:
            Filtered results
        """
        from config import FILTER_FIELD_NAMES
        
        owner_broker_field = FILTER_FIELD_NAMES.get('owner_broker', 'owner_broker')
        return self.query_with_filters(query_text, {owner_broker_field: owner_broker}, top_k)
    
    def refresh_index(self):
        """Rebuild the vector store from source data"""
        print("Refreshing search index...")
        self.initialize(force_rebuild=True)
    
    def get_all_vendors(self) -> List[Dict[str, Any]]:
        """
        Get all vendors in the database
        
        Returns:
            List of all vendors
        """
        if not self.initialized:
            self.initialize()
        
        return self.vector_store.get_all_metadata()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the database using configurable field names
        
        Returns:
            Dictionary with statistics
        """
        from config import FILTER_FIELD_NAMES
        
        if not self.initialized:
            self.initialize()
        
        vendors = self.vector_store.get_all_metadata()
        
        # Get field names from config (with fallbacks)
        owner_broker_field = FILTER_FIELD_NAMES.get('owner_broker', 'owner_broker')
        state_field = FILTER_FIELD_NAMES.get('state', 'vendor_state')
        verification_field = FILTER_FIELD_NAMES.get('verification', 'verification')
        
        stats = {
            'total_vendors': len(vendors),
            'verified_vendors': len([v for v in vendors if v.get(verification_field) == 'Verified']),
            'owners': len([v for v in vendors if v.get(owner_broker_field) == 'Owner']),
            'brokers': len([v for v in vendors if v.get(owner_broker_field) == 'Broker']),
            'with_associations': len([v for v in vendors if v.get('any_association') == 'Y']),
            'return_service_available': len([v for v in vendors if v.get('return_service') == 'Y'])
        }
        
        # Count by state (using configurable field name)
        states = {}
        for v in vendors:
            state = v.get(state_field)
            if state:
                states[state] = states.get(state, 0) + 1
        stats['vendors_by_state'] = states
        
        return stats


class QueryEngine(SemanticSearch):
    """Alias for SemanticSearch for backward compatibility"""
    pass
