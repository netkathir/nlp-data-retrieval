"""
Text Processor Module
Handles text preprocessing and conversion of vendor records to searchable text
"""

from typing import Dict, Any, List, Optional


class TextProcessor:
    """Process and prepare vendor data for embedding generation"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean and normalize text
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text
        """
        # Remove extra whitespace
        text = " ".join(text.split())
        
        # Remove special characters (keep basic punctuation)
        # text = re.sub(r'[^\w\s\-,.|()]', '', text)
        
        return text.strip()
    
    @staticmethod
    def prepare_for_embedding(vendor: Dict[str, Any]) -> str:
        """
        Prepare vendor data for embedding generation using pure field index architecture
        
        This method constructs a weighted text representation where high-priority fields
        (like notes, locations, specializations) appear multiple times to boost their
        semantic importance in the embedding.
        
        Additionally detects specialization keywords (e.g., "electronics", "pharma", "fragile")
        and repeats them with synonyms for enhanced semantic matching.
        
        Args:
            vendor: Vendor dictionary with field_X keys and logical name mappings
            
        Returns:
            Weighted text ready for embedding
        """
        try:
            from config import (
                FIELD_MAP, 
                SEMANTIC_SEARCH_FIELDS, 
                FIELD_INDEX_WEIGHTS,
                SPECIALIZATION_KEYWORDS,
                KEYWORD_REPETITION_COUNT
            )
            
            parts = []
            specialization_text = ""  # Collect text for keyword detection
            
            # Process each field configured for semantic search
            for field_idx in SEMANTIC_SEARCH_FIELDS:
                if field_idx not in FIELD_MAP:
                    continue
                
                field_config = FIELD_MAP[field_idx]
                field_name = field_config["name"]
                label = field_config["label"]
                
                # Get value from vendor (try both logical name and field_X format)
                value = vendor.get(field_name)
                if value is None:
                    value = vendor.get(f"field_{field_idx}")
                
                # Skip empty values
                if not value or str(value).lower() in ['none', 'null', '']:
                    continue
                
                value = str(value)
                
                # Collect high-weight fields for keyword detection
                # (notes, description, services, etc. - fields with weight >= 10)
                weight = FIELD_INDEX_WEIGHTS.get(field_idx, 1)
                if weight >= 10:
                    specialization_text += " " + value.lower()
                
                # Format text with label for better semantic understanding
                formatted_text = f"{label}: {value}"
                
                # Repeat the text based on its weight
                parts.extend([formatted_text] * weight)
            
            # Step 2: Detect and boost specialization keywords
            # This is crucial for matching queries like "electronics transport in Mumbai"
            if specialization_text and SPECIALIZATION_KEYWORDS:
                for keyword, synonyms in SPECIALIZATION_KEYWORDS.items():
                    if keyword.lower() in specialization_text:
                        # Add the keyword and all its synonyms, repeated for emphasis
                        parts.extend(synonyms * KEYWORD_REPETITION_COUNT)
            
            # Join all parts with period separator
            text = ". ".join(parts)
            
            # Clean up the text
            text = TextProcessor.clean_text(text)
            
            return text
            
        except ImportError:
            # Should not happen - config is always available
            return ""
    
    @staticmethod
    def batch_prepare(vendors: List[Dict[str, Any]]) -> List[str]:
        """
        Prepare multiple vendors for embedding
        
        Args:
            vendors: List of vendor dictionaries
            
        Returns:
            List of prepared texts
        """
        return [TextProcessor.prepare_for_embedding(v) for v in vendors]
    
    @staticmethod
    def format_for_display(vendor: Dict[str, Any]) -> str:
        """
        Format vendor data for user-friendly display using field indices
        
        Args:
            vendor: Vendor dictionary
            
        Returns:
            Formatted display text
        """
        try:
            from config import FIELD_MAP, CARD_DISPLAY_INDICES
            
            lines = []
            
            for field_idx in CARD_DISPLAY_INDICES:
                if field_idx not in FIELD_MAP:
                    continue
                
                field_config = FIELD_MAP[field_idx]
                field_name = field_config["name"]
                label = field_config["label"]
                icon = field_config.get("icon", "")
                
                # Get value from vendor
                value = vendor.get(field_name) or vendor.get(f"field_{field_idx}")
                
                if value and str(value).lower() not in ['none', 'null', '']:
                    lines.append(f"{icon} {label}: {value}")
            
            return "\n".join(lines) if lines else "No data available"
            
        except ImportError:
            # Fallback to legacy method
            return TextProcessor.format_for_display_legacy(vendor)
    
    @staticmethod
    def format_for_display_legacy(vendor: Dict[str, Any]) -> str:
        """
        Legacy format vendor data for user-friendly display
        
        Args:
            vendor: Vendor dictionary
            
        Returns:
            Formatted display text
        """
        lines = []
        
        lines.append(f"🚛 {vendor.get('transport_name', 'N/A')}")
        
        if vendor.get('name'):
            lines.append(f"   Contact: {vendor['name']}")
        
        if vendor.get('vendor_city') and vendor.get('vendor_state'):
            lines.append(f"   Location: {vendor['vendor_city']}, {vendor['vendor_state']}")
        
        if vendor.get('vehicle_type'):
            lines.append(f"   Vehicles: {vendor['vehicle_type']}")
        
        if vendor.get('main_service_city'):
            lines.append(f"   Services: {vendor['main_service_city']}")
        
        if vendor.get('owner_broker'):
            lines.append(f"   Type: {vendor['owner_broker']}")
        
        if vendor.get('verification'):
            lines.append(f"   Status: {vendor['verification']}")
        
        if vendor.get('notes'):
            lines.append(f"   Notes: {vendor['notes']}")
        
        return "\n".join(lines)


def prepare_vendor_text(vendor: Dict[str, Any]) -> str:
    """
    Convenience function to prepare vendor for embedding
    
    Args:
        vendor: Vendor dictionary
        
    Returns:
        Prepared text
    """
    return TextProcessor.prepare_for_embedding(vendor)
