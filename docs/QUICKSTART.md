# 🚀 QUICK START GUIDE

## Prerequisites
- Python 3.11 or higher
- PostgreSQL database (already created with vendor data)
- OpenAI API key for embeddings
- Pinecone API key (for cloud vector storage)

## Setup (3 steps)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Your Database Connection

Create a `.env` file in the project root with your database credentials:

```bash
# OpenAI API Key (for embeddings)
OPENAI_API_KEY=sk-your-actual-key-here

# PostgreSQL Database Connection (local or cloud)
POSTGRES_HOST=localhost          # or your cloud database host
POSTGRES_PORT=5432
POSTGRES_USER=postgres           # or your username
POSTGRES_PASSWORD=your_password
POSTGRES_DATABASE=transport_vendor_db

# Pinecone (for cloud vector storage)
PINECONE_API_KEY=your-pinecone-key-here
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX=warehouse-ai

# Storage Mode (choose one)
STORAGE_MODE=pinecone_only       # Cloud-only (recommended for Docker)
# STORAGE_MODE=hybrid            # Local cache + Pinecone backup
# STORAGE_MODE=local             # Local SQLite only (for development)
```

**Database Setup:**
- ✅ The PostgreSQL `vendors` table already exists with field_0 through field_15
- ✅ 60 sample vendor records are pre-loaded in the database
- ✅ No need to create tables or import data manually

**For Local Development:**
```bash
# If using local PostgreSQL on macOS:
brew install postgresql
brew services start postgresql
psql postgres  # Connect to verify
```

### 3. Run the Application
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
   - **Advanced Filters** - Configurable in `config.py` (add as many as you want!)
   - **Similarity threshold** - Minimum match quality (0-100%)
   - **Max results count** - How many results to display

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

## Customizing Search Behavior

Edit `config.py` to customize:

### Field Mapping
```python
FIELD_MAP = {
    0: {
        "name": "transport_name",     # Logical name for code
        "label": "Transport Company",  # Display label for UI
        "icon": "truck.svg",          # SVG icon file in /static/icons/
        "weight": 3,                  # Higher = more important for search
    },
    # ... fields 1-15
}
```

### Field Weights
- **15**: Critical (notes, descriptions) - Maximum semantic importance
- **8**: High-importance (locations, categories)
- **3**: Medium-importance (names)
- **1**: Low-importance (metadata)

### AI Behavior
```python
AI_SUMMARY_CONFIG = {
    "system_prompt": "You are a helpful assistant...",
    "temperature": 0.7,
    "max_tokens": 300,
}
```

### Advanced Filters (100% Configurable)
```python
ADVANCED_FILTERS = [
    {"field_index": 3, "type": "text", "placeholder": "Filter by state..."},
    {"field_index": 2, "type": "text", "placeholder": "Filter by city..."},
    {"field_index": 14, "type": "select", "options": ["All", "Verified", "Unverified"]},
]
```

Add as many filters as you want - no code changes needed!

## Using in Your Project

```python
from core.query_engine import SemanticSearch

# Initialize
search = SemanticSearch()

# Search
results = search.query("your question here", top_k=5)

# Access results
for vendor in results:
    print(f"{vendor['transport_name']}: {vendor['similarity_score']:.1%}")
```

## Storage Modes

The system supports three storage modes (set in `.env`):

### Cloud-Only (Recommended for Docker)
```bash
STORAGE_MODE=pinecone_only
```
- ✅ No local cache needed
- ✅ Minimal disk space
- ✅ Perfect for containerized deployments
- ⚠️ First stats load slower (10-15s), then cached

### Hybrid (Local Cache + Cloud Backup)
```bash
STORAGE_MODE=hybrid
```
- ✅ Fast local searches
- ✅ Cloud backup if needed
- ⚠️ Requires more disk space

### Local Development
```bash
STORAGE_MODE=local
```
- ✅ Works offline
- ✅ No API keys needed for testing
- ⚠️ Slower than local cache mode

## Troubleshooting

**"PostgreSQL connection error"**
- Check .env file for correct credentials
- Verify PostgreSQL is running: `psql postgres`
- For cloud databases, check firewall/network access

**"API key is required"**
- Add OPENAI_API_KEY to .env file
- Verify .env is in project root

**"Embeddings not updating"**
- Delete cache: `rm data/embeddings/cache_postgresql.pkl`
- Restart: `python api.py` (will rebuild embeddings automatically)

**"Low similarity scores"**
- Increase field weights in FIELD_MAP (especially notes field)
- Add domain keywords to SPECIALIZATION_KEYWORDS

**"Docker build takes too long"**
- Docker uses layer caching automatically
- Only pip install reruns if requirements.txt changes
- First build: ~22 minutes (installs all dependencies)
- Subsequent builds: ~30 seconds (uses cache)

## Next Steps

- Read full documentation in [README.md](README.md)
- Explore [PRODUCTION_HANDOVER.md](PRODUCTION_HANDOVER.md) for architecture details
- Customize `FIELD_MAP` and AI configs in `config.py` for your domain

---
Need help? Check [README.md](README.md) for detailed documentation.
