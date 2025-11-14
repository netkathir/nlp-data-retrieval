# 🚀 QUICK START GUIDE

## Prerequisites
- Python 3.8 or higher
- MySQL Server 5.7+ or 8.0+
- OpenAI API key

## Setup (4 steps)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup MySQL Database

**Option A: Using MySQL Command Line**
```bash
# Start MySQL server (if not running)
mysql.server start   # On macOS
# or: sudo service mysql start   # On Linux

# Connect to MySQL
mysql -u root -p

# Create database and table
CREATE DATABASE warehouse_ai_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE warehouse_ai_db;

CREATE TABLE vendors (
    id INT AUTO_INCREMENT PRIMARY KEY,
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

# Exit MySQL
EXIT;
```

**Option B: Import Sample Data (Recommended)**
```bash
# First create database and table as shown above, then:
# Use Python to import from data/vendors.json
python -c "
import json
import pymysql
from config import MYSQL_CONFIG

# Load sample data
with open('data/vendors.json', 'r') as f:
    vendors = json.load(f)

# Connect and insert
conn = pymysql.connect(**MYSQL_CONFIG)
cursor = conn.cursor()

for vendor in vendors:
    fields = [vendor.get(f'field_{i}', '') for i in range(16)]
    cursor.execute('''
        INSERT INTO vendors (field_0, field_1, field_2, field_3, field_4, field_5,
                           field_6, field_7, field_8, field_9, field_10, field_11,
                           field_12, field_13, field_14, field_15)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', fields)

conn.commit()
cursor.close()
conn.close()
print('Data imported successfully!')
"
```

### 3. Configure Settings
Edit `config.py` to customize:
- **MySQL Connection**: Update `MYSQL_CONFIG` with your credentials
- **Field Mapping**: Customize `FIELD_MAP` for your field definitions
- **Field Weights**: Adjust weights in FIELD_MAP (higher = more important for search)
- **AI Behavior**: Customize `AI_SUMMARY_CONFIG`, `AI_INSIGHTS_CONFIG`, `AI_QA_CONFIG`

Add your OpenAI API key to `.env`:
```
OPENAI_API_KEY=sk-your-actual-key-here
```

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
   - State filter
   - City filter
   - Verification status
   - Similarity threshold (minimum match quality)
   - Max results count

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
        "type": "text",
        "searchable": True,
        "weight": 3,                  # Embedding weight (1-15)
        "display_in_card": True
    },
    1: {...},
    # ... fields 2-15
}
```

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
5. **Run** `python scripts/setup_mysql.py` to import your data

The system is **100% configurable** via `config.py` - no code changes needed!

## Troubleshooting

**"Import errors"**: Install packages: `pip install -r requirements.txt`

**"MySQL connection error"**: Check MYSQL_CONFIG in config.py, ensure MySQL is running

**"No API key"**: Add OPENAI_API_KEY to .env file

**"Slow first run"**: Normal - building embeddings (cached in data/embeddings/cache_mysql.pkl)

**"Low similarity scores"**: Check field weights and KEYWORD_REPETITION_COUNT in config.py

## Next Steps

- Read full documentation in README.md
- Explore PRODUCTION_HANDOVER.md for architecture details
- Customize FIELD_MAP and AI configs for your domain
- Add your own data via MySQL import or scripts/setup_mysql.py

---
Need help? Check README.md for detailed documentation.
