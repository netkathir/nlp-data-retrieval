"""
Configuration module for Warehouse AI Tool
Loads environment variables and defines global constants
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenAI API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", None)

# Model Configuration
EMBEDDING_MODEL = "text-embedding-3-large"  # Higher quality embeddings (3072 dimensions)
CHAT_MODEL = "gpt-4o-mini"  # Good balance of quality and speed
# Alternative: "text-embedding-3-small" for cheaper/faster (1536 dimensions)
# Alternative: "gpt-4" for better quality, "gpt-3.5-turbo" for faster/cheaper

# Search Configuration
DEFAULT_TOP_K = 5  # Number of results to return by default
SIMILARITY_THRESHOLD = 0.35  # Minimum similarity score (0-1) - CHANGE THIS to adjust minimum match quality
# Note: Semantic embeddings typically score 30-60% for good matches!
# Scores: 50-100% = Excellent, 30-50% = Good, 10-30% = Fair, 0-10% = Poor
MAX_RESULTS = 5  # Maximum number of results - CHANGE THIS to limit total results shown

# Data Configuration
# ==================
# CHANGE THIS to switch between different data sources
# Supported formats: JSON, CSV, Excel (.xlsx), PostgreSQL Database, MySQL Database

# Option 1: PostgreSQL Database (Default - Cloud-hosted on Render)
DATA_TYPE = "postgresql"
POSTGRESQL_CONFIG = {
    "host": os.getenv("POSTGRES_HOST"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "database": os.getenv("POSTGRES_DATABASE"),
}
POSTGRES_TABLE_NAME = "vendors"

# Option 2: MySQL Database (Uncomment to use)
# DATA_TYPE = "mysql"
# MYSQL_CONFIG = {
#     "host": os.getenv("MYSQL_HOST", "localhost"),
#     "user": os.getenv("MYSQL_USER", "root"),
#     "password": os.getenv("MYSQL_PASSWORD", "root"),
#     "database": os.getenv("MYSQL_DATABASE", "warehouse_ai_db"),
#     "charset": "utf8mb4"
# }
# MYSQL_TABLE_NAME = "vendors"

# Option 3: JSON File (Uncomment to use)
# DATA_TYPE = "json"
# DATA_PATH = os.getenv("DATA_PATH", "data/vendors.json")

# Option 4: CSV File (Uncomment to use)
# DATA_TYPE = "csv"
# DATA_PATH = "data/vendors.csv"

# Option 5: Excel File (Uncomment to use)
# DATA_TYPE = "excel"
# DATA_PATH = "data/vendors.xlsx"

EMBEDDINGS_CACHE_PATH = os.getenv("EMBEDDINGS_CACHE_PATH", "data/embeddings/cache_postgresql.pkl")

# Flask API Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")  # 0.0.0.0 allows external connections, 127.0.0.1 for local only
API_PORT = int(os.getenv("API_PORT", "5001"))
API_DEBUG = os.getenv("API_DEBUG", "False").lower() == "true"  # Set to False in production!

# ============================================================================
# FIELD INDEX CONFIGURATION - Pure Database-Agnostic Architecture
# ============================================================================
"""
FIELD_MAP: Define database schema using pure field indices (field_0, field_1, etc.)
This makes the system work with ANY database without assumptions about field semantics.

Each field index maps to:
- name: Logical identifier (for internal use)
- label: Display label in UI
- type: Data type (text, number, boolean)
- searchable: Include in semantic search embeddings
- weight: Importance in search (higher = more important)
- display_in_card: Show in result cards
- display_in_table: Show in table view
- display_in_brief: Show in brief format
- icon: Optional icon for UI display

Note: Filterable fields are defined separately in ADVANCED_FILTERS configuration.
"""

# Define how many total fields exist in database
TOTAL_FIELDS = 16

# Define which field indices are active (exist in database)
# ACTIVE_FIELD_INDICES = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
# Active field indices (0-based) - these map to field_0, field_1, etc. in the database
# Only these fields will be loaded from the database
# ACTIVE_FIELD_INDICES = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
ACTIVE_FIELD_INDICES = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]

# ====================
# FIELD WEIGHT MULTIPLIERS (Higher = Better Matching)
# ====================
SEMANTIC_WEIGHT = 20      # For notes, description, specialization (ULTRA CRITICAL)
LOCATION_WEIGHT = 12      # For city, state, vehicle type (CRITICAL)
SECONDARY_WEIGHT = 6      # For names, verification, services (IMPORTANT)
METADATA_WEIGHT = 2       # For contact info (NORMAL)

# Map each field index to its configuration
FIELD_MAP = {
    0: {
        "name": "transport_name",
        "label": "Transport Company",
        "type": "text",
        "searchable": True,
        "weight": SECONDARY_WEIGHT,
        "display_in_card": True,
        "display_in_table": True,
        "display_in_brief": True,
        "icon": "truck.svg"
    },
    1: {
        "name": "name",
        "label": "Contact Person",
        "type": "text",
        "searchable": True,
        "weight": METADATA_WEIGHT,
        "display_in_card": True,
        "display_in_table": True,
        "display_in_brief": False,
        "icon": "user.svg"
    },
    2: {
        "name": "vendor_city",
        "label": "City",
        "type": "text",
        "searchable": True,
        "weight": LOCATION_WEIGHT,
        "display_in_card": True,
        "display_in_table": True,
        "display_in_brief": True,
        "icon": "map-pin.svg"
    },
    3: {
        "name": "vendor_state",
        "label": "State",
        "type": "text",
        "searchable": True,
        "weight": LOCATION_WEIGHT,
        "display_in_card": True,
        "display_in_table": True,
        "display_in_brief": True,
        "icon": "map.svg"
    },
    4: {
        "name": "visiting_card",
        "label": "Brief Description",
        "type": "text",
        "searchable": True,
        "weight": SECONDARY_WEIGHT,
        "display_in_card": True,
        "display_in_table": False,
        "display_in_brief": False,
        "icon": "briefcase.svg"
    },
    5: {
        "name": "vehicle_type",
        "label": "Vehicle Type",
        "type": "text",
        "searchable": True,
        "weight": LOCATION_WEIGHT,
        "display_in_card": True,
        "display_in_table": True,
        "display_in_brief": True,
        "icon": "truck.svg"
    },
    6: {
        "name": "main_service_city",
        "label": "Service Areas",
        "type": "text",
        "searchable": True,
        "weight": SECONDARY_WEIGHT,
        "display_in_card": True,
        "display_in_table": False,
        "display_in_brief": False,
        "icon": "globe.svg"
    },
    7: {
        "name": "owner_broker",
        "label": "Type",
        "type": "text",
        "searchable": True,
        "weight": SECONDARY_WEIGHT,
        "display_in_card": True,
        "display_in_table": True,
        "display_in_brief": True,
        "icon": "building.svg"
    },
    8: {
        "name": "whatsapp_number",
        "label": "WhatsApp",
        "type": "text",
        "searchable": False,
        "weight": METADATA_WEIGHT,
        "display_in_card": True,
        "display_in_table": False,
        "display_in_brief": False,
        "icon": "smartphone.svg"
    },
    9: {
        "name": "alternate_number",
        "label": "Alternate Phone",
        "type": "text",
        "searchable": False,
        "weight": METADATA_WEIGHT,
        "display_in_card": False,
        "display_in_table": False,
        "display_in_brief": False,
        "icon": "smartphone.svg"
    },
    10: {
        "name": "main_service_state",
        "label": "Service State",
        "type": "text",
        "searchable": True,
        "weight": SECONDARY_WEIGHT,
        "display_in_card": False,
        "display_in_table": False,
        "display_in_brief": False,
        "icon": "map.svg"
    },
    11: {
        "name": "return_service",
        "label": "Return Service",
        "type": "text",
        "searchable": True,
        "weight": SECONDARY_WEIGHT,
        "display_in_card": True,
        "display_in_table": False,
        "display_in_brief": False,
        "icon": "repeat.svg"
    },
    12: {
        "name": "any_association",
        "label": "Has Association",
        "type": "text",
        "searchable": True,
        "weight": METADATA_WEIGHT,
        "display_in_card": False,
        "display_in_table": False,
        "display_in_brief": False,
        "icon": "users.svg"
    },
    13: {
        "name": "association_name",
        "label": "Association",
        "type": "text",
        "searchable": True,
        "weight": METADATA_WEIGHT,
        "display_in_card": True,
        "display_in_table": False,
        "display_in_brief": False,
        "icon": "users.svg"
    },
    14: {
        "name": "verification",
        "label": "Verification",
        "type": "text",
        "searchable": True,
        "weight": SECONDARY_WEIGHT,
        "display_in_card": True,
        "display_in_table": True,
        "display_in_brief": False,
        "icon": "check-square.svg"
    },
    15: {
        "name": "notes",
        "label": "Notes & Comments",
        "type": "text",
        "searchable": True,
        "weight": SEMANTIC_WEIGHT,
        "display_in_card": True,
        "display_in_table": False,
        "display_in_brief": False,
        "icon": "file-text.svg"
    }
}

# Display Configuration - Which field indices to show in each view
CARD_DISPLAY_INDICES = [0, 1, 2, 3, 4, 5, 6, 7, 8, 11, 13, 14, 15]  # Fields shown in result cards
TABLE_COLUMN_INDICES = [0, 1, 2, 3, 5, 7, 14]  # Fields shown as table columns
BRIEF_DISPLAY_INDICES = [0, 2, 3, 5, 7]  # Fields shown in brief format

# Search Configuration - Which field indices to include in embeddings
SEMANTIC_SEARCH_FIELDS = [0, 1, 2, 3, 4, 5, 6, 7, 10, 11, 12, 13, 14, 15]  # Searchable fields

# Advanced Filters Configuration (for UI generation)
# =======================================================
# COMPLETELY CONFIGURABLE - Add/remove/reorder filters as needed
# The system automatically generates UI elements and handles filtering
# 
# Each filter configuration:
#   - field_index: Which field from FIELD_MAP to filter by (e.g., 3 = vendor_state)
#   - type: 'text' (text input), 'select' (dropdown), or 'checkbox' (boolean)
#   - placeholder: Placeholder text for text inputs (optional)
#   - options: List of options for select dropdowns (first option is default)
#
# EXAMPLES:
# ---------
# Text filter:
#   {"field_index": 2, "type": "text", "placeholder": "Search by field..."}
#
# Dropdown filter:
#   {"field_index": 14, "type": "select", "options": ["All", "Option1", "Option2"]}
#
# Checkbox filter:
#   {"field_index": 11, "type": "checkbox"}
#
# TO CUSTOMIZE FOR YOUR DATABASE:
# 1. Change field_index to match your FIELD_MAP indices
# 2. Add/remove filters as needed (can have 0, 1, 5, 10+ filters!)
# 3. Labels are automatically pulled from FIELD_MAP[field_index]["label"]
# 4. Field names are automatically pulled from FIELD_MAP[field_index]["name"]
#
# Example: To add a vehicle type filter, just add:
# {"field_index": 5, "type": "select", "options": ["All", "Truck", "Tempo", "Van"]}

ADVANCED_FILTERS = [
    {
        "field_index": 3,  # field_3 = vendor_state (auto-labeled "State" from FIELD_MAP)
        "type": "text",
        "placeholder": "Filter by this field..."
    },
    {
        "field_index": 2,  # field_2 = vendor_city (auto-labeled "City" from FIELD_MAP)
        "type": "text",
        "placeholder": "Filter by this field..."
    },
    {
        "field_index": 14,  # field_14 = verification (auto-labeled "Verification" from FIELD_MAP)
        "type": "select",
        "options": ["All", "Verified", "Unverified", "Pending"]
    },
    {
        "field_index": 7,  # owner_broker
        "type": "select",
        "options": ["All", "Owner", "Broker"]
    }
]

# TO ADD MORE FILTERS (just append to the list):
# {
#     "field_index": 5,  # vehicle_type
#     "type": "select",
#     "options": ["All", "Truck", "Tempo", "Van", "Container"]
# },
# {
#     "field_index": 7,  # owner_broker
#     "type": "select",
#     "options": ["All", "Owner", "Broker"]
# }

# Primary Display Index (used as card title)
PRIMARY_DISPLAY_INDEX = 0  # field_0 = transport_name

# Brief Format Template (uses field indices as placeholders)
BRIEF_FORMAT_TEMPLATE = "{field[0]} - {field[2]}, {field[3]} ({field[7]})"

# Field Weight Map (for embeddings) - based on field indices
FIELD_INDEX_WEIGHTS = {idx: FIELD_MAP[idx]["weight"] for idx in SEMANTIC_SEARCH_FIELDS if idx in FIELD_MAP}

# Vendor Data Schema (Legacy - for backward compatibility with JSON/CSV)
VENDOR_FIELDS = [
    "name",
    "transport_name",
    "visiting_card",
    "owner_broker",
    "vendor_state",
    "vendor_city",
    "whatsapp_number",
    "alternate_number",
    "vehicle_type",
    "main_service_state",
    "main_service_city",
    "return_service",
    "any_association",
    "association_name",
    "verification",
    # "notes"
]

# Field descriptions for better context
FIELD_DESCRIPTIONS = {
    "name": "Vendor or contact person name",
    "transport_name": "Name of the transport company",
    "owner_broker": "Whether the vendor is an owner or broker",
    "vendor_state": "State where vendor is located",
    "vendor_city": "City where vendor is located",
    "vehicle_type": "Type of vehicle (truck, tempo, etc.)",
    "main_service_state": "Primary state where service is provided",
    "main_service_city": "Primary city where service is provided",
    "return_service": "Whether return service is available (Y/N)",
    "any_association": "Whether vendor has any association (Y/N)",
    "verification": "Verification status of the vendor"
}

# ============================================================================
# EMBEDDING FIELD CONFIGURATION (Scalable & Configurable)
# ============================================================================
"""
Configure how fields are weighted in embeddings for semantic search.
Higher weight = more importance in similarity matching.

This configuration is DATABASE-AGNOSTIC - just update field names and weights
for different datasets without changing code!
"""

# ====================
# MATCH PERCENTAGE DISPLAY BOOST (Set to 1.0 for raw scores)
# ====================
MATCH_PERCENTAGE_BOOST = 1.2  # 20% boost to displayed match percentages

# Keyword Extraction Rules (Extract specializations from text fields)
# Format: {"keyword_to_find": ["synonym1", "synonym2", "variation3"]}
SPECIALIZATION_KEYWORDS = {
    # Electronics & IT
    "electronic": ["electronics transport", "IT equipment", "electronic goods", "electronics specialist"],
    "it equipment": ["IT transport", "technology equipment", "computer hardware"],
    "computer": ["computers", "IT hardware", "technology devices"],
    
    # Pharmaceutical & Medical
    "pharma": ["pharmaceutical transport", "medical supplies", "medicine delivery", "healthcare products"],
    "medical": ["medical equipment", "healthcare supplies", "hospital equipment"],
    
    # Textiles & Fashion
    "textile": ["textiles", "fabric transport", "garment delivery", "clothing transport"],
    "fabric": ["fabrics", "textile goods", "garment materials"],
    "garment": ["garments", "clothing", "apparel transport"],
    
    # Fragile & Delicate
    "fragile": ["fragile items", "delicate goods", "breakable items", "careful handling"],
    "delicate": ["delicate items", "sensitive goods", "fragile materials"],
    
    # Food & Perishables
    "perishable": ["perishables", "perishable goods", "food transport", "fresh produce"],
    "food": ["food products", "edible goods", "food delivery"],
    "fresh": ["fresh produce", "fresh goods", "refrigerated transport"],
    
    # Heavy Machinery & Industrial
    "machinery": ["heavy machinery", "industrial equipment", "large machines", "factory equipment"],
    "heavy": ["heavy goods", "heavy equipment", "oversized cargo"],
    "industrial": ["industrial goods", "factory equipment", "manufacturing materials"],
    
    # Agricultural
    "agricultural": ["farm products", "agriculture goods", "farming equipment", "crop transport"],
    "farm": ["farm produce", "agricultural products", "farming goods"],
    
    # Port & Coastal
    "port": ["port deliveries", "port to city", "harbor transport", "shipping port"],
    "coastal": ["coastal transport", "seaside delivery", "port services"],
    
    # Speed & Time-Sensitive
    "fast": ["fast delivery", "quick turnaround", "express service", "speedy transport"],
    "quick": ["quick delivery", "rapid service", "fast turnaround"],
    "express": ["express delivery", "urgent transport", "fast service"],
    
    # Reliability & Trust
    "reliable": ["reliable service", "dependable transport", "trustworthy vendor"],
    "trusted": ["trusted vendor", "reliable partner", "dependable service"]
}

# ====================
# KEYWORD REPETITION MULTIPLIER
# ====================
KEYWORD_REPETITION_COUNT = 10  # Boost keyword-specific matches (electronics, IT, etc.)
# This makes vendors with matching specialization keywords score higher


# ====================
# UI CONFIGURATION (Customizable Labels & Text)
# ====================
"""
Configure all UI text here to make the system fully customizable for different use cases.
Change these values to rebrand for different industries (vendors, suppliers, products, etc.)
"""

UI_CONFIG = {
    # Page Title & Branding
    "page_title": "AI Vendor Search",
    "main_heading": "AI Vendor Search",
    "subtitle": "Find the perfect transport vendor using AI-powered semantic search",
    
    # Entity Name (describes what records represent in this database)
    "entity_name": "vendors",
    "entity_name_singular": "vendor",
    
    # Search Interface
    "search_placeholder": "Ask in natural language: e.g., Find electronics vendors in Mumbai...",
    "search_button": "Search",
    "voice_button_tooltip": "Voice Search",
    
    # Results Display
    "results_heading": "Search Results",
    "no_results_title": "No vendors found",
    "no_results_message": "Try adjusting your filters or search query",
    "loading_message": "Searching for vendors...",
    
    # Statistics Labels
    "stat_total": "Total Vendors",
    "stat_verified": "Verified",
    "stat_with_associations": "With Associations",
    
    # Filter Labels
    "filter_state_label": "State",
    "filter_city_label": "City",
    "filter_verification_label": "Verification Status",
    "filter_threshold_label": "Similarity Threshold",
    "filter_max_results_label": "Maximum Results",
    
    # Card Field Labels (maps to actual field names)
    "field_labels": {
        "transport_name": "Transport Company",
        "name": "Contact Person",
        "owner_broker": "Type",
        "vendor_state": "State",
        "vendor_city": "City",
        "vehicle_type": "Vehicle Type",
        "main_service_city": "Service Area",
        "main_service_state": "Service State",
        "return_service": "Return Service",
        "verification": "Verification",
        "any_association": "Association",
        "association_name": "Association Name",
        "whatsapp_number": "WhatsApp",
        "alternate_number": "Alternate",
        # "notes": "Notes"
    },
    
    # Summary Section
    "summary_heading": "AI Summary",
    "generate_summary_button": "Generate AI Summary",
    
    # Filter Placeholders
    "state_all": "All States",
    "city_all": "All Cities",
    "verification_all": "All",
    "verification_verified": "Verified Only",
    "verification_unverified": "Unverified Only",
    
    # SVG Icon Paths (relative to /static/icons/)
    "icons": {
        "main_logo": "warehouse.svg",
        "search": "search.svg",
        "microphone": "microphone.svg",
        "pause": "pause.svg",
        "refresh": "refresh.svg",
        "lightbulb": "lightbulb.svg",
        "filter": "filter.svg",
        "chevron_down": "chevron-down.svg",
        "alert_circle": "alert-circle.svg",
        "check_circle": "check-circle.svg",
        "search_x": "search-x.svg",
        "alert_triangle": "alert-triangle.svg",
        "recording_dot": "recording-dot.svg"
    }
}

# Primary display field (shown as card title)
PRIMARY_DISPLAY_FIELD = "transport_name"

# Field names used for filtering (make configurable for different schemas)
FILTER_FIELD_NAMES = {
    "state": "vendor_state",
    "city": "vendor_city",
    "verification": "verification",
    "owner_broker": "owner_broker",
    "vehicle_type": "vehicle_type"
}

# ============================================================================
# AI SUMMARY CONFIGURATION (GPT Prompts & Behavior)
# ============================================================================
"""
Configure how GPT generates summaries of search results.
Customize these to match your business domain and desired output style.
"""

# AI Summary Settings
AI_SUMMARY_CONFIG = {
    # Model parameters
    "temperature": 0.7,  # 0.0 = deterministic, 1.0 = creative
    "max_tokens": 300,   # Maximum length of summary
    "top_results_limit": 10,  # How many top results to include in summary
    
    # System prompt (defines AI's role and expertise)
    "system_prompt": "You are a helpful assistant summarizing transport vendor search results. Provide clear, actionable insights based on the search results.",
    
    # User prompt template (use {query}, {vendor_summaries}, {count} as placeholders)
    "user_prompt_template": """Based on the user's query: "{query}"

Here are the top {count} matching results:

{vendor_summaries}

Please provide a concise, helpful summary of these results. Your response should:
1. Identify the BEST matching results that most closely match the user's query
2. Explain WHY these specific results are the best matches based on query relevance
3. For the relevant top match(es), include the contact person's name and phone number in a natural way (e.g., "Contact Ramesh Iyer at +91-9876543210") at the end.
4. Highlight key characteristics (location, specializations, vehicle types) of the top matches
5. Note any patterns or recommendations for the user
6. If there are no suitable match, politely inform the user so, and recommend the next best matches.

Keep the summary conversational and under 150 words.""",
    
    # Fields to include in vendor summaries for GPT (uses field indices)
    # "summary_field_indices": [0, 1, 2, 3, 4, 5, 7, 8, 9, 13, 14, 15],  # Transport name, contact name, location, phones (WhatsApp & alternate), vehicle, verification, notes
    "summary_field_indices": [0, 1, 2, 3, 4, 5, 7, 8, 9, 13, 14],  # Transport name, contact name, location, phones (WhatsApp & alternate), vehicle, verification, notes

    # Fallback message when no results found
    "no_results_message": "No vendors were found matching your query. Try broadening your search criteria or adjusting filters.",
    
    # Error fallback message
    "error_message": "Unable to generate AI summary at this time. Please view the search results above."
}

# Alternative: E-commerce product search system prompt
# "system_prompt": "You are a helpful shopping assistant summarizing product search results. Focus on key features, prices, and recommendations."

# Alternative: Job search system prompt  
# "system_prompt": "You are a career advisor summarizing job search results. Highlight key roles, requirements, and opportunities."

# Alternative: Real estate system prompt
# "system_prompt": "You are a real estate advisor summarizing property listings. Focus on locations, prices, and property features."

# ============================================================================
# AI INSIGHTS CONFIGURATION (Analytics & Statistics)
# ============================================================================
"""
Configure which fields to analyze for insights/statistics.
Uses field indices for database-agnostic operation.
"""

AI_INSIGHTS_CONFIG = {
    # Which field index to use for location distribution analysis
    "location_field_index": 3,  # field_3 = vendor_state
    
    # Which field index to use for category/type distribution
    "category_field_index": 5,  # field_5 = vehicle_type
    
    # Which field index to use for verification analysis
    "verification_field_index": 14,  # field_14 = verification
    
    # Which field index to analyze for binary features (Y/N)
    "binary_feature_indices": {
        11: "Return Service",  # field_11 = return_service
    },
    
    # Which field index for owner/broker split
    "owner_broker_field_index": 7,  # field_7 = owner_broker
    
    # Labels for insights
    "labels": {
        "top_locations": "Top States",
        "common_categories": "Common Vehicle Types",
        "verification_rate": "Verification Rate",
        "owner_broker_split": "Owner vs Broker"
    }
}

# ============================================================================
# AI QUESTION ANSWERING CONFIGURATION
# ============================================================================
"""
Configure GPT behavior for answering specific questions about results.
"""

AI_QA_CONFIG = {
    # Model parameters
    "temperature": 0.5,  # Lower for more factual answers
    "max_tokens": 250,
    "top_results_for_qa": 5,  # How many results to include in context
    
    # System prompt
    "system_prompt": "You are a knowledgeable assistant helping with transport vendor queries. Provide accurate, helpful answers based on the data provided.",
    
    # User prompt template
    "user_prompt_template": """Question: {query}
{context}

Available vendor information:
{vendor_data}

Please answer the question based on the vendor data provided. Identify which vendors in the list are the BEST matches for the query and explain why they are most relevant. Be specific and helpful.""",
    
    # Field indices to include when answering questions
    # "qa_field_indices": [0, 1, 2, 3, 5, 6, 7, 11, 14, 15],  # Key fields for context
    "qa_field_indices": [0, 1, 2, 3, 5, 6, 7, 11, 14],  # Key fields for context


    # Fallback message
    "no_results_message": "I couldn't find any relevant vendors to answer your question.",
    "error_message": "Unable to answer the question at this time."
}

# Alternative: E-commerce Q&A system prompt
# "system_prompt": "You are a shopping assistant helping customers find the right products. Answer questions about features, prices, and availability."

# Alternative: Job search Q&A system prompt
# "system_prompt": "You are a career advisor helping job seekers. Answer questions about roles, requirements, salaries, and opportunities."

