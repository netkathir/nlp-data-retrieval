# 🚀 QUICK START GUIDE

## Prerequisites
- Python 3.8 or higher
- PostgreSQL database (local or cloud-hosted)
- OpenAI API key

## Setup (4 steps)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup PostgreSQL Database

**Option A: Using PostgreSQL Command Line**
```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE transport_vendor_db;

# Connect to the database
\c transport_vendor_db

# Create table
CREATE TABLE vendors (
    id SERIAL PRIMARY KEY,
    field_0 VARCHAR(500),
    field_1 VARCHAR(500),
    field_2 VARCHAR(500),
    field_3 VARCHAR(500),
    field_4 VARCHAR(500),
    field_5 VARCHAR(500),
    field_6 VARCHAR(500),
    field_7 VARCHAR(500),
    field_8 VARCHAR(500),
    field_9 VARCHAR(500),
    field_10 TEXT,
    field_11 TEXT,
    field_12 VARCHAR(500),
    field_13 VARCHAR(500),
    field_14 VARCHAR(500),
    field_15 TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

# Exit PostgreSQL
\q
```

**Option B: Import Sample Data (Recommended)**
```bash
# Import 60 sample vendors from JSON
python scripts/import_vendors.py
```

This will create the table and import 60 diverse vendor records from `data/vendors.json`.

**Option C: Cloud-Hosted PostgreSQL**
If using a cloud provider (Render, AWS RDS, etc.), get your connection details and configure the environment variables in step 3.

### 3. Configure Settings

Add your credentials to `.env`:
```bash
# OpenAI API Key
OPENAI_API_KEY=sk-your-actual-key-here

# PostgreSQL Database Connection
POSTGRES_HOST=your-postgres-host.com
POSTGRES_PORT=5432
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
POSTGRES_DATABASE=transport_vendor_db
```

Edit `config.py` to customize:
- **Field Mapping**: Customize `FIELD_MAP` for your field definitions
- **Field Icons**: Update icon filenames in FIELD_MAP (SVG files in `/static/icons/`)
- **Field Weights**: Adjust weights in FIELD_MAP (higher = more important for search)
- **UI Text**: Customize `UI_CONFIG` for page titles, entity names, and labels
- **Advanced Filters**: Configure `ADVANCED_FILTERS` to customize UI filter fields (see below)
- **AI Behavior**: Customize `AI_SUMMARY_CONFIG`, `AI_INSIGHTS_CONFIG`, `AI_QA_CONFIG`

### 4. Run the Application
```bash
python api.py
```

The API will run at http://127.0.0.1:5001

Open your browser and visit the URL to access the web interface.

## Using the Web Interface

### Search & Results
1. **Enter your query** in natural language (e.g., "transport vendors in Mumbai with trucks")
2. **Choose a response format** from the dropdown:
   - **AI Summary** (Default) - Conversational GPT summary with detailed cards
   - **Detailed Cards** - Full vendor information with icons
   - **Brief Summary** - Quick text overview
   - **Table View** - Compact tabular format

3. **Adjust filters** (optional):
   - **Advanced Filters** (State, City, Verification, etc.) - Now fully configurable via `config.py`
   - **Similarity threshold** - Minimum match quality (0-100%)
   - **Max results count** - How many results to display

**Note:** Advanced filters are configured in `config.py` using `ADVANCED_FILTERS`. You can add/remove/modify filters without touching HTML:

```python
ADVANCED_FILTERS = [
    {
        "id": "filterState",
        "label": "State",
        "field_name": "vendor_state",
        "type": "text",  # or "select" or "checkbox"
        "placeholder": "e.g., Maharashtra"
    },
    # Add more filters as needed
]
```

Filter values **augment the search query** for better semantic matching. Searching "electronics" with state filter "Tamil Nadu" gives the same high scores as typing "electronics in Tamil Nadu"!

4. **View results** - The page auto-scrolls to show matching vendors

### Voice Search
Click the microphone button and speak your query naturally. The system will transcribe and search automatically.

### Understanding Match Scores
- **70-100%** 🟢 Excellent match (green badge)
- **50-70%** 🔵 Good match (blue badge)  
- **35-50%** 🟠 Fair match (orange badge)

Scores below 35% are filtered out by default (configurable via threshold slider).

## Test the System

Example queries to try:
- "Find transport vendors in Mumbai with trucks"
- "Which vendors serve Maharashtra and have associations?"
- "Show me brokers with return service available"
- "List all verified vendors handling electronics"

## Configuration Architecture

The system uses a **pure field index architecture** for database compatibility:

### Field Mapping (config.py)
```python
FIELD_MAP = {
    0: {
        "name": "transport_name",     # Logical name for code
        "label": "Transport Company",  # Display label for UI
        "icon": "truck.svg",          # SVG icon file in /static/icons/
        "type": "text",
        "searchable": True,
        "weight": 3,                  # Embedding weight (1-15)
        "display_in_card": True
    },
    1: {...},
    # ... fields 2-15
}
```

**Note**: Icons are now SVG files stored in `/static/icons/`. Change any icon by editing the SVG file or updating the "icon" field in FIELD_MAP.

### Active Fields
```python
ACTIVE_FIELD_INDICES = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]
```

### Search Configuration
```python
SEMANTIC_SEARCH_FIELDS = [0,1,2,3,4,5,6,7,10,11,12,13,14,15]  # Exclude phone numbers
FIELD_INDEX_WEIGHTS = {0: 3, 1: 1, 2: 8, 3: 8, 5: 8, 15: 15}  # Auto-generated from FIELD_MAP
```

### Field Weights
- **20**: Ultra critical fields (notes, descriptions, specializations) - Maximum semantic importance
- **12**: High-importance (cities, states, vehicle types) - Critical for location/type searches
- **6**: Medium-importance (service areas, verification, company names) - Important context
- **2**: Low-importance (contact info, associations) - Metadata

Higher weights make fields more influential in similarity scoring and matching.

### Keyword Boosting
The system detects specialization keywords (electronics, pharma, fragile, etc.) and boosts them:
```python
SPECIALIZATION_KEYWORDS = {
    "electronic": ["electronics transport", "IT equipment", ...],
    "fragile": ["fragile items", "delicate goods", ...],
    # ... more categories
}
KEYWORD_REPETITION_COUNT = 10  # Repeat detected keywords 10x
```

## Using in Your Project

```python
from core.query_engine import SemanticSearch

# Initialize
search = SemanticSearch()

# Search
results = search.query("your question here", top_k=5)

# Access results using logical names
for vendor in results:
    print(vendor['transport_name'])  # Mapped from field_0
    print(vendor['vendor_city'])     # Mapped from field_2
    print(vendor['notes'])           # Mapped from field_15
```

## Customizing for Your Database

1. **Update FIELD_MAP** in `config.py` with your field definitions
2. **Adjust weights** based on field importance for your use case
3. **Configure AI prompts** in AI_SUMMARY_CONFIG, AI_INSIGHTS_CONFIG, AI_QA_CONFIG
4. **Update SPECIALIZATION_KEYWORDS** with your domain-specific keywords
5. **Run** `python scripts/import_vendors.py` to import your data

The system is **100% configurable** via `config.py` - no code changes needed!

## Troubleshooting

**"Import errors"**: Install packages: `pip install -r requirements.txt`

**"PostgreSQL connection error"**: Check .env file for correct credentials, ensure PostgreSQL is accessible

**"No API key"**: Add OPENAI_API_KEY to .env file

**"Slow first run"**: Normal - building embeddings (cached in data/embeddings/cache_postgresql.pkl)

**"Low similarity scores"**: Check field weights and KEYWORD_REPETITION_COUNT in config.py

## Next Steps

- Read full documentation in README.md
- Explore PRODUCTION_HANDOVER.md for architecture details
- Customize FIELD_MAP and AI configs for your domain
- Add your own data via MySQL import or scripts/setup_mysql.py

---
Need help? Check README.md for detailed documentation.
