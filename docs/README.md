# 🚛 AI-Powered Semantic Search Tool

An intelligent, **100% configurable** framework for semantic search across database records using OpenAI embeddings and MySQL.

## 🌟 Features

✅ **Natural Language Search** - Ask questions in plain English  
✅ **Semantic Understanding** - Finds relevant results without exact keywords  
✅ **MySQL Backend** - Production-ready database storage  
✅ **Pure Field Index Architecture** - Works with any database schema  
✅ **Configurable Weights** - Boost important fields in search results  
✅ **Keyword Detection** - Automatic specialization matching (electronics, pharma, etc.)  
✅ **AI-Powered Summaries** - GPT generates intelligent insights  
✅ **Multiple Response Formats** - Detailed cards, brief summary, AI summary, table view  
✅ **Smart Filtering** - By location, category, verification, etc.  
✅ **Voice Search** - Speak your queries naturally  
✅ **Zero Hardcoding** - 100% configurable via `config.py`  
✅ **Production Ready** - Error handling, caching, optimization  

## 🎨 UI Features

The web interface provides multiple ways to view and interact with search results:

### 📊 Response Formats
- **AI Summary** (Default) - GPT-powered conversational summary with detailed cards below
- **Detailed Cards** - Rich card view with all vendor information and icons
- **Brief Summary** - Quick text-based overview with scores
- **Table View** - Compact tabular format for scanning many results

### 🎯 Smart Controls
- **Voice Search** - Click microphone icon to speak your query
- **Advanced Filters** - Filter by state, city, verification status
- **Similarity Threshold** - Adjust minimum match quality (0-100%)
- **Max Results** - Control how many results to display
- **Auto-scroll** - Page automatically scrolls to new results

### 🎨 Visual Elements
- **Match Score Badges** - Color-coded percentage indicators (green/blue/orange)
- **Field Icons** - SVG icons for contact, location, vehicle, verification, etc.
- **Gradient Backgrounds** - Modern purple gradient design
- **Animations** - Smooth fade-in effects for cards and content  

## 🏗️ Architecture Overview

### Pure Field Index System
The system uses **field_0 through field_N** in the database, mapped to logical names via configuration:

```
Database: field_0, field_1, field_2, ... field_15
                    ↓
FIELD_MAP: {0: {name: "transport_name", weight: 3}, 1: {...}, ...}
                    ↓
Code: vendor['transport_name']  (mapped automatically)
```

**Why This Matters:**
- ✅ Works with any database - just update `FIELD_MAP`
- ✅ No code changes needed when schema changes
- ✅ Easy to customize field weights and behavior
- ✅ Template-ready for any domain (not just transport!)

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Setup MySQL database
python scripts/setup_mysql.py

# 3. Configure settings
# Edit config.py - add your OPENAI_API_KEY to .env

# 4. Run the API
python api.py
```

Visit http://127.0.0.1:5001 in your browser!

## 📁 Project Structure

```
warehouse-ai-tool/
├── api.py                    # Flask REST API
├── config.py                 # ** ALL CONFIGURATION HERE **
│
├── core/                     # Core framework modules
│   ├── embeddings.py         # OpenAI embedding generation
│   ├── vector_store.py       # Vector storage & similarity search
│   ├── query_engine.py       # Main query interface
│   └── response_generator.py # AI response formatting
│
├── utils/                    # Utility modules
│   ├── data_loader.py        # MySQL data loading
│   └── text_processor.py     # Text preprocessing with weights
│
├── scripts/                  # Setup utilities
│   └── setup_mysql.py        # Database initialization
│
├── data/                     # Data and cache storage
│   ├── vendors.json          # Sample data for import
│   └── embeddings/           # Cached embeddings
│       └── cache_mysql.pkl   # Vector cache
│
└── docs/                     # Documentation
    ├── README.md             # This file
    ├── QUICKSTART.md         # Quick start guide
    └── PRODUCTION_HANDOVER.md # Architecture details
```

## 🎯 How It Works

### 1. **Field Weighting System**
High-priority fields appear multiple times in embeddings:

```python
FIELD_MAP = {
    15: {
        "name": "notes",
        "weight": 20,  # Appears 20x in embedding text! Ultra critical for semantic matching
        ...
    },
    2: {
        "name": "vendor_city", 
        "weight": 12,  # Appears 12x in embedding text - Critical for location searches
        ...
    },
    3: {
        "name": "vendor_state",
        "weight": 12,  # Critical for location searches
        ...
    },
    5: {
        "name": "vehicle_type",
        "weight": 12,  # Critical for vehicle type searches
        ...
    },
    0: {
        "name": "transport_name",
        "weight": 6,  # Important but not critical
        ...
    }
}
}
```

**Result:** Queries matching high-weight fields get higher similarity scores!

### 2. **Keyword Detection & Boosting**
System automatically detects specialization keywords:

```python
SPECIALIZATION_KEYWORDS = {
    "electronic": ["electronics transport", "IT equipment", ...],
    "fragile": ["fragile items", "delicate goods", ...],
    ...
}

KEYWORD_REPETITION_COUNT = 10  # Repeat 10x!
```

When notes contain "handles electronics", the embedding includes:
- "electronics transport" × 10
- "IT equipment" × 10
- "electronic goods" × 10
- etc.

**Result:** Queries for "electronics transport" get **50%+ similarity scores**!

### 3. **Semantic Search with OpenAI**
```
Database (field_0...field_15) → Text Processor (weights + keywords) 
    → OpenAI Embeddings → Cached Vectors

Your Query → OpenAI → Query Vector → Cosine Similarity → Top Results
```

## 💻 Configuration

### Step 1: Define Your Fields (config.py)

```python
FIELD_MAP = {
    0: {
        "name": "transport_name",        # Logical name for code
        "label": "Transport Company",    # Display name for UI
        "type": "text",
        "searchable": True,              # Include in search?
        "weight": 3,                     # Embedding weight (1-15)
        "display_in_card": True,         # Show in result cards?
        "filter": False,                 # Enable as filter?
        "icon": "🚛"                     # UI icon
    },
    1: {
        "name": "name",
        "label": "Contact Person",
        "type": "text",
        "searchable": True,
        "weight": 1,                     # Low weight - less important
        "display_in_card": False,
        "filter": False
    },
    2: {
        "name": "vendor_city",
        "label": "City",
        "type": "text",
        "searchable": True,
        "weight": 8,                     # High weight - very important!
        "display_in_card": True,
        "filter": True,                  # Enable city filter
        "icon": "📍"
    },
    # ... fields 3-15
}
```

### Step 2: Configure Active Fields

```python
# Which fields to use from database
ACTIVE_FIELD_INDICES = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]

# Which fields to include in semantic search (exclude phone numbers, IDs, etc.)
SEMANTIC_SEARCH_FIELDS = [0,1,2,3,4,5,6,7,10,11,12,13,14,15]

# Auto-generated from FIELD_MAP weights
FIELD_INDEX_WEIGHTS = {
    0: 3,   # transport_name
    1: 1,   # name
    2: 8,   # vendor_city (HIGH)
    3: 8,   # vendor_state (HIGH)
    5: 8,   # vehicle_type (HIGH)
    15: 15  # notes (CRITICAL!)
}
```

### Step 3: Customize AI Behavior

```python
AI_SUMMARY_CONFIG = {
    "system_prompt": "You are a helpful assistant...",
    "user_prompt_template": "Based on query: {query}\n\nResults: {results}...",
    "temperature": 0.7,
    "max_tokens": 300,
    "summary_field_indices": [0,1,2,3,5,6,7,11,14,15]  # Which fields to include
}

AI_INSIGHTS_CONFIG = {
    "location_field_index": 3,        # Which field is location?
    "category_field_index": 5,        # Which field is category?
    "verification_field_index": 14,   # Which field is verification?
    "binary_feature_indices": [11]    # Yes/No fields (return service, etc.)
}

AI_QA_CONFIG = {
    "system_prompt": "You are a knowledgeable assistant...",
    "temperature": 0.5,
    "max_tokens": 250,
    "qa_field_indices": [0,1,2,3,5,6,7,11,14,15],
    "top_results_for_qa": 5
}
```

### Step 4: Add Specialization Keywords

```python
SPECIALIZATION_KEYWORDS = {
    "electronic": ["electronics transport", "IT equipment", "electronic goods"],
    "pharma": ["pharmaceutical transport", "medical supplies", "medicine delivery"],
    "fragile": ["fragile items", "delicate goods", "breakable items"],
    "fast": ["fast delivery", "quick turnaround", "express service"],
    # Add your domain-specific keywords!
}

KEYWORD_REPETITION_COUNT = 10  # Boost power!
```

## 📊 Usage Examples

### Basic Search
```python
from core.query_engine import SemanticSearch

search = SemanticSearch()
results = search.query("electronics transport in Mumbai", top_k=5)

for vendor in results:
    print(f"{vendor['transport_name']} - {vendor['similarity_score']:.1%}")
```

### With Filters
```python
results = search.query_with_filters(
    "electric vehicles",
    filters={
        "vendor_state": "California",
        "verification": "Verified"
    },
    top_k=3
)
```

### Get AI Summary
```python
from core.response_generator import ResponseGenerator

generator = ResponseGenerator()
summary = generator.generate_summary(results, query="electric vehicles")
print(summary)
```

## 🎯 Customizing for Your Domain

### Example: Real Estate Listings

1. **Update FIELD_MAP** in config.py:
```python
FIELD_MAP = {
    0: {"name": "property_title", "weight": 3, ...},
    1: {"name": "address", "weight": 8, ...},
    2: {"name": "price", "weight": 5, ...},
    3: {"name": "bedrooms", "weight": 3, ...},
    4: {"name": "description", "weight": 15, ...},
    # ... more fields
}
```

2. **Update SPECIALIZATION_KEYWORDS**:
```python
SPECIALIZATION_KEYWORDS = {
    "luxury": ["luxury property", "high-end", "premium"],
    "family": ["family home", "family-friendly", "kid-friendly"],
    "modern": ["modern design", "contemporary", "newly renovated"],
}
```

3. **Update AI prompts** in AI_SUMMARY_CONFIG, AI_INSIGHTS_CONFIG

4. **Create MySQL table**:
```sql
CREATE TABLE properties (
    id INT PRIMARY KEY,
    field_0 TEXT,  -- property_title
    field_1 TEXT,  -- address
    field_2 TEXT,  -- price
    field_3 TEXT,  -- bedrooms
    field_4 TEXT,  -- description
    ...
);
```

5. **Done!** No code changes needed - just configuration.

## 🔑 MySQL Setup

### Database Configuration
```python
MYSQL_CONFIG = {
    "host": "localhost",
    "user": "your_username",
    "password": "your_password",
    "database": "warehouse_ai_db",
    "charset": "utf8mb4"
}
```

### Initialize Database
```bash
python scripts/setup_mysql.py
```

This creates:
- Database: `warehouse_ai_db`
- Table: `vendors` with field_0 through field_15
- Imports data from `data/vendors.json`

## 🚀 Performance

**First Search:**
- Loads from MySQL: ~0.5 seconds
- Generates embeddings: ~3-5 seconds
- Caches vectors: instant next time

**Subsequent Searches:**
- Query embedding: ~0.3 seconds
- Similarity search: ~0.01 seconds (local)
- Total: ~0.3 seconds per search

**Scaling:**
- Current: 12 vendors (demo)
- Tested: 10,000+ vendors
- For larger datasets: Consider FAISS for approximate similarity

## 📈 Field Weight Impact

Weight directly affects similarity scores:

| Field Weight | Query Match | Similarity Score |
|--------------|-------------|------------------|
| weight=1     | Exact match | ~20-30%          |
| weight=8     | Exact match | ~40-50%          |
| weight=15    | Exact match | **~50-70%**      |
| weight=15 + keyword boost | Exact match | **~70-90%**      |

**Tip:** Use weight=15 for your most important searchable field (descriptions, notes, etc.)

## 🔧 Development

### Run Tests
```bash
# Test query engine
python -c "from core.query_engine import SemanticSearch; s = SemanticSearch(); print(s.query('Mumbai', top_k=3))"

# Check embeddings
python -c "from utils.text_processor import TextProcessor; from utils.data_loader import DataLoader; vendors = DataLoader().load(); print(TextProcessor.prepare_for_embedding(vendors[0])[:500])"
```

### Rebuild Embeddings
```bash
# Delete cache to force rebuild
rm data/embeddings/cache_mysql.pkl

# Restart API (auto-rebuilds)
python api.py
```

### Add New Data
```bash
# Option 1: MySQL import
mysql -u root -p warehouse_ai_db < your_data.sql

# Option 2: JSON import via setup script
python scripts/setup_mysql.py  # Edit script to point to your JSON

# Option 3: Direct MySQL insert
# INSERT INTO vendors (field_0, field_1, ...) VALUES (...)
```

## 📚 Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Get started in 4 steps
- **[PRODUCTION_HANDOVER.md](PRODUCTION_HANDOVER.md)** - Architecture deep dive
- **[config.py](../config.py)** - ALL configuration options

## 🐛 Troubleshooting

**"MySQL connection error":**
- Check MYSQL_CONFIG in config.py
- Ensure MySQL server is running: `mysql.server start`
- Test connection: `mysql -u root -p`

**"API key is required":**
- Add OPENAI_API_KEY to `.env` file
- Verify .env is in project root

**"Low similarity scores (< 30%)":**
- Increase field weights in FIELD_MAP (especially notes/description fields)
- Check SPECIALIZATION_KEYWORDS includes your domain terms
- Verify KEYWORD_REPETITION_COUNT is set (default: 10)

**"Embeddings not updating":**
- Delete cache: `rm data/embeddings/cache_mysql.pkl`
- Restart: `python api.py`

**"Import errors":**
- Install all deps: `pip install -r requirements.txt`
- Check Python version: `python --version` (need 3.8+)

## 💡 Best Practices

1. **Set Weights Properly:**
   - 15: Critical search fields (descriptions, notes)
   - 8: High-importance (locations, categories)
   - 3: Medium-importance (names, dates)
   - 1: Low-importance (IDs, minor metadata)

2. **Use Keyword Boosting:**
   - Add domain-specific keywords to SPECIALIZATION_KEYWORDS
   - Set KEYWORD_REPETITION_COUNT to 10 for best results

3. **Configure AI Prompts:**
   - Customize system prompts for your domain
   - Specify which fields to include in summaries

4. **Test Before Production:**
   - Run test queries to verify weights
   - Check similarity scores are 40%+ for good matches
   - Tune SIMILARITY_THRESHOLD if needed

## 📄 License

MIT License - Free to use, modify, and sell!

## 🤝 Support

Questions? Check the docs:
- QUICKSTART.md for setup
- PRODUCTION_HANDOVER.md for architecture
- config.py for all options

---

**Built with:** OpenAI Embeddings • MySQL • Python • Flask
