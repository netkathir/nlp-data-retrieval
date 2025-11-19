# 🚀 Production Handover Guide

**For: DevOps/System Admin/Client Technical Team**  
**From: Development Team**  
**Project: AI-Powered Semantic Search System**

---

## 📋 Table of Contents
1. [Quick Overview](#quick-overview)
2. [Understanding config.py](#understanding-configpy)
3. [Changing Database/Data Source](#changing-database)
4. [Customizing UI & Branding](#customizing-ui)
5. [Deployment Checklist](#deployment-checklist)
6. [Performance Tuning](#performance-tuning)
7. [Troubleshooting](#troubleshooting)

---

## 🎯 Quick Overview

This is a **100% template-based system** designed to work with ANY database schema. Everything is configurable through `config.py` - no code changes needed.

**What this system does:**
- Semantic search using OpenAI embeddings (understands meaning, not just keywords)
- Voice search with auto-translation (Tamil/Hindi → English)
- AI-powered result summaries
- Real-time filtering and scoring

**Tech Stack:**
- Backend: Flask (Python 3.8+)
- AI: OpenAI API (GPT-4o-mini + text-embedding-3-large)
- Frontend: Pure HTML/CSS/JS with Jinja2 templates
- Storage: Pickle cache for embeddings (fast reload)

---

## ⚙️ Understanding config.py

**THIS IS THE ONLY FILE YOUR CLIENT NEEDS TO EDIT**

`config.py` has 8 main sections:

### 1. **API Configuration** (Lines 12-19)
```python
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Load from .env file
EMBEDDING_MODEL = "text-embedding-3-large"     # OpenAI embedding model
CHAT_MODEL = "gpt-4o-mini"                     # For AI summaries
```

**Client Action:** Add their OpenAI API key to `.env` file

---

### 2. **Search Configuration** (Lines 21-27)
```python
SIMILARITY_THRESHOLD = 0.35  # Min score to show results (0-1 scale)
MAX_RESULTS = 5              # Max results per search
```

**What to adjust:**
- **SIMILARITY_THRESHOLD**: Higher = stricter matching (fewer results)
  - 0.25 = Very permissive (shows many results)
  - 0.35 = Balanced (recommended)
  - 0.50 = Strict (only very close matches)
  
- **MAX_RESULTS**: How many results to show by default

---

### 3. **Data Configuration** (Lines 29-56) ⭐ CRITICAL

```python
# Option 1: JSON File (Default)
DATA_PATH = "data/vendors.json"
DATA_TYPE = "json"

# Option 2: CSV File
# DATA_PATH = "data/vendors.csv"
# DATA_TYPE = "csv"

# Option 3: Excel File
# DATA_PATH = "data/vendors.xlsx"
# DATA_TYPE = "excel"

# Option 4: PostgreSQL Database (Default)
# DATA_TYPE = "postgresql"
# POSTGRES_TABLE_NAME = "vendors"
```

**Client Action:** 
1. Choose ONE data source
2. Uncomment relevant lines
3. Update path/connection string

**Supported Formats:**
- ✅ PostgreSQL (Cloud or Local) - requires `psycopg2-binary`
- ✅ JSON (.json)
- ✅ CSV (.csv)
- ✅ Excel (.xlsx, .xls) - requires `openpyxl`

---

### 4. **Database Schema Mapping** (Lines 58-76) ⭐ CRITICAL

**Purpose:** Tell the system what columns exist in the client's database

```python
VENDOR_FIELDS = [
    "name",           # ← Replace with client's column names
    "company_name",
    "location",
    "phone",
    # ... add all their columns here
]
```

**Example:** If client has a products database:
```python
VENDOR_FIELDS = [
    "product_id",
    "product_name",
    "description",
    "category",
    "price",
    "stock_location",
    "manufacturer"
]
```

---

### 5. **Field Weights** (Lines 115-149) ⭐ CRITICAL FOR SEARCH QUALITY

**Purpose:** Tell the AI which fields are most important for matching

```python
FIELD_WEIGHTS = {
    "notes": 15,              # Ultra critical - detailed descriptions
    "vendor_city": 8,         # Critical - location info
    "transport_name": 3,      # Important - main identifier
    "phone": 1,               # Normal - just metadata
}
```

**How weights work:**
- Higher number = more important for search
- Field content is repeated N times in the embedding
- Example: If `notes` has weight 15, its content counts 15x more than `phone` (weight 1)

**Client Action:** Adjust weights based on their search priorities
- Product search? Make `description`, `category`, `specifications` high weight
- Service directory? Make `services_offered`, `expertise`, `location` high weight

---

### 6. **Specialization Keywords** (Lines 151-195) ⭐ OPTIONAL BUT POWERFUL

**Purpose:** Boost scores when query matches specific industry terms

```python
SPECIALIZATION_KEYWORDS = {
    "electronics": ["electronics", "IT equipment", "computers"],
    "pharma": ["pharmaceutical", "medical supplies", "medicine"],
    # Add client's industry terms here
}
```

**Example for E-commerce:**
```python
SPECIALIZATION_KEYWORDS = {
    "clothing": ["apparel", "fashion", "garments", "wear"],
    "footwear": ["shoes", "sandals", "boots", "sneakers"],
    "electronics": ["gadgets", "devices", "tech", "appliances"]
}
```

---

### 7. **UI Configuration** (Lines 217-290) ⭐ FOR BRANDING

**Purpose:** Change all text/labels without touching HTML

```python
UI_CONFIG = {
    "page_title": "AI Vendor Search",          # Browser tab title
    "main_heading": "AI Vendor Search",        # Main page heading
    "subtitle": "Find the perfect vendor...",  # Subheading
    "search_placeholder": "Search...",         # Input placeholder
    # ... 20+ more UI labels
}
```

**Client Action:** Replace with their brand/terminology
- Vendor → Product / Supplier / Property / Candidate
- Transport Company → Business Name / Company / Organization

---

### 8. **Advanced Filters Configuration** ⭐ CRITICAL - NOW 100% GENERIC

**Purpose:** Configure which fields appear as UI filters - completely database-agnostic

```python
# Filters are defined by field_index (from FIELD_MAP)
# System automatically pulls labels and field names from FIELD_MAP
# NO hardcoded assumptions - works with ANY database!

ADVANCED_FILTERS = [
    {
        "field_index": 3,                  # Points to FIELD_MAP[3] (auto-labeled)
        "type": "text",                    # Input type: text, select, or checkbox
        "placeholder": "Filter by this field..."
    },
    {
        "field_index": 2,                  # Points to FIELD_MAP[2] (auto-labeled)
        "type": "text",
        "placeholder": "Filter by this field..."
    },
    {
        "field_index": 14,                 # Points to FIELD_MAP[14] (auto-labeled)
        "type": "select",                  # Dropdown with options
        "options": ["All", "Verified", "Unverified", "Pending"]
    }
    # Add as many filters as you want - system adapts automatically!
]

# System automatically generates:
# - Filter IDs: filter_0, filter_1, filter_2, etc.
# - Labels: from FIELD_MAP[field_index]["label"]
# - Field names: from FIELD_MAP[field_index]["name"]
# - HTML form elements
# - Filtering logic
```

**Filter Types Available:**
- `"text"` - Text input field (for states, cities, names, etc.)
- `"select"` - Dropdown menu (requires `options` array)
- `"checkbox"` - Boolean yes/no toggle

**How Filters Work:**
1. Filter values **augment the search query** (e.g., "electronics" + state filter "Tamil Nadu" → "electronics Tamil Nadu")
2. This ensures filters contribute to **both semantic similarity AND keyword boost**
3. Exact matching is applied post-search to filter results
4. **Result:** Using filters gives same high scores as typing the filter values in the query!

**Client Action:** 
- Add/remove unlimited filters by updating `ADVANCED_FILTERS`
- Simply specify `field_index` from FIELD_MAP
- Labels and field names are pulled automatically
- Choose appropriate input types (text/select/checkbox)
- No code changes needed - 100% configuration-driven!

**Examples:**
```python
# Add a vehicle type filter:
{"field_index": 5, "type": "select", "options": ["All", "Truck", "Van"]}

# Add an owner/broker filter:
{"field_index": 7, "type": "select", "options": ["All", "Owner", "Broker"]}

# Add a checkbox filter:
{"field_index": 11, "type": "checkbox"}
```

---

### 9. **Filter Configuration - REMOVED** ✅

**Legacy configurations removed:**
- ❌ `FILTER_FIELD_NAMES` - No longer needed
- ❌ `FILTER_INDICES` - No longer needed
- ❌ Hardcoded filter IDs/labels - Auto-generated now

**Everything is now controlled by:**
- ✅ `ADVANCED_FILTERS` (field_index based)
- ✅ `FIELD_MAP` (provides labels and field names)

The system is now 100% database-agnostic!

---

## 🗄️ Changing Database

### Scenario 1: Client has JSON data

1. Place JSON file in `data/` folder
2. Update `config.py`:
```python
DATA_PATH = "data/their_data.json"
DATA_TYPE = "json"
```
3. Update `VENDOR_FIELDS` to match their JSON structure
4. Restart server - it will auto-build embeddings

### Scenario 2: Client has CSV/Excel

1. Place file in `data/` folder
2. Update `config.py`:
```python
DATA_PATH = "data/their_data.csv"
DATA_TYPE = "csv"
```
3. Update field mappings
4. Restart server

### Scenario 3: Client has PostgreSQL Database

1. Install dependencies:
```bash
pip install psycopg2-binary
```

2. Configure credentials in `.env`:
```bash
POSTGRES_HOST=your-postgres-host.com
POSTGRES_PORT=5432
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
POSTGRES_DATABASE=your_database_name
```

3. Update `config.py`:
```python
DATA_TYPE = "postgresql"
POSTGRES_TABLE_NAME = "products"
```

4. Update field mappings to match your PostgreSQL table columns
5. Restart server

**Note:** The system only READS from the database. No write operations (INSERT, UPDATE, DELETE) are performed during normal operation. Data import is handled separately via `scripts/import_vendors.py`.

---

## 🎨 Customizing UI & Branding

**All in `config.py` - No HTML editing needed!**

### Example: Rebranding for E-commerce

```python
UI_CONFIG = {
    "page_title": "AI Product Finder",
    "main_heading": "Smart Product Search",
    "subtitle": "Find products using intelligent AI search",
    "search_placeholder": "Search for products: e.g., red sneakers size 10",
    "stat_total": "Total Products",
    "stat_verified": "In Stock",
    "no_results_title": "No products found",
    
    # Update field labels
    "field_labels": {
        "product_name": "Product",
        "category": "Category",
        "price": "Price",
        "stock_location": "Warehouse",
    }
}

# Update primary display field
PRIMARY_DISPLAY_FIELD = "product_name"

# Filters are now automatically derived from ADVANCED_FILTERS + FIELD_MAP
# No need for FILTER_FIELD_NAMES anymore!
```

**Result:** Entire UI now talks about "products" instead of "vendors"!

---

## ✅ Deployment Checklist

### Pre-Deployment

- [ ] **1. OpenAI API Key set in `.env` file**
  ```bash
  echo "OPENAI_API_KEY=sk-your-key-here" > .env
  ```

- [ ] **2. Update `config.py` with client's data:**
  - [ ] `DATA_PATH` / `DATA_TYPE` configured
  - [ ] `FIELD_MAP` matches their schema
  - [ ] `FIELD_INDEX_WEIGHTS` adjusted for their use case
  - [ ] `UI_CONFIG` branded for their business
  - [ ] `ADVANCED_FILTERS` configured (optional - for UI filters)

- [ ] **3. Test with sample data:**
  ```bash
  python api.py
  # Visit http://localhost:5001
  # Try 3-5 test searches
  ```

- [ ] **4. Generate embeddings cache:**
  - First run will take 1-2 minutes to build cache
  - Cache saves to `data/embeddings/cache.pkl`
  - Subsequent runs load instantly from cache

### Production Setup

- [ ] **5. Install production dependencies:**
  ```bash
  pip install -r requirements.txt
  pip install gunicorn  # Production server
  ```

- [ ] **6. Set environment variables:**
  ```bash
  export FLASK_ENV=production
  export OPENAI_API_KEY=sk-your-key
  ```

- [ ] **7. Run with production server:**
  ```bash
  gunicorn -w 4 -b 0.0.0.0:5001 api:app
  ```

- [ ] **8. Set up reverse proxy (Nginx):**
  ```nginx
  server {
      listen 80;
      server_name your-domain.com;
      
      location / {
          proxy_pass http://localhost:5001;
          proxy_set_header Host $host;
      }
  }
  ```

- [ ] **9. Enable HTTPS (Let's Encrypt):**
  ```bash
  certbot --nginx -d your-domain.com
  ```

- [ ] **10. Set up systemd service:**
  ```ini
  [Unit]
  Description=AI Search Service
  After=network.target
  
  [Service]
  User=www-data
  WorkingDirectory=/path/to/warehouse-ai-tool
  ExecStart=/path/to/.venv/bin/gunicorn -w 4 api:app
  Restart=always
  
  [Install]
  WantedBy=multi-user.target
  ```

---

## 🚀 Performance Tuning

### 1. **Embedding Cache**
- Cache is automatically created on first run
- Stored in `data/embeddings/cache.pkl`
- **Important:** Delete cache when data changes!
  ```bash
  rm data/embeddings/cache.pkl
  # Restart server to rebuild
  ```

### 2. **Search Performance**
```python
# config.py adjustments:

# Faster searches, less accurate
EMBEDDING_MODEL = "text-embedding-3-small"  # 1536 dims vs 3072

# Show fewer results for speed
MAX_RESULTS = 3

# Higher threshold = fewer candidates to score
SIMILARITY_THRESHOLD = 0.40
```

### 3. **Cost Optimization**
- Embeddings are cached - only paid once per data update
- ~$0.00013 per 1000 tokens for embeddings
- Example: 1000 products × 200 words = $0.026 total (one-time)
- AI summaries: ~$0.15 per 1000 requests

---

## 🐛 Troubleshooting

### Issue: "No results found" for valid queries

**Cause:** Threshold too high or field weights wrong

**Fix:**
1. Lower `SIMILARITY_THRESHOLD` to 0.25
2. Increase weights for searchable fields:
   ```python
   FIELD_WEIGHTS = {
       "description": 15,  # Make sure high-weight fields have content!
       "notes": 15,
   }
   ```

---

### Issue: Wrong results appearing

**Cause:** Keyword boost too aggressive or wrong field weights

**Fix:**
1. Check `SPECIALIZATION_KEYWORDS` - remove irrelevant terms
2. Reduce `KEYWORD_REPETITION_COUNT` from 10 to 5
3. Adjust field weights - ensure metadata fields have low weight

---

### Issue: Embeddings taking too long

**Cause:** Large dataset or slow API

**Fix:**
1. Use `text-embedding-3-small` instead of `large`
2. Reduce field repetitions:
   ```python
   SEMANTIC_WEIGHT = 10  # Instead of 15
   LOCATION_WEIGHT = 5   # Instead of 8
   ```

---

### Issue: API key errors

**Cause:** Missing or invalid OpenAI key

**Fix:**
1. Check `.env` file exists: `cat .env`
2. Verify key format: starts with `sk-`
3. Test key:
   ```bash
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer $OPENAI_API_KEY"
   ```

---

### Issue: Threshold not working correctly

**Cause:** Threshold was applied BEFORE keyword boosting, filtering out results that would have passed after boosting.

**Fix:** Threshold now applies AFTER keyword boosting. System gets 3x candidates, applies boost, then filters by threshold.

---

### Issue: Refresh creates duplicate results

**Cause:** Refresh appended new embeddings to old ones instead of replacing them.

**Fix:** Refresh now clears existing embeddings before rebuilding the cache.

---

### Issue: Voice recording errors

**Cause:** Very short recordings or silence caused technical error messages.

**Fix:** 
- Added 0.5 second minimum duration check
- User-friendly error messages with "Try Again" button
- Empty transcript detection shows "No Speech Detected" message

---

### Issue: AI Summary formatting

**Cause:** Markdown syntax (`**bold**`, `* bullets`) displayed as raw text instead of formatted HTML.

**Fix:** Added markdown-to-HTML converter that properly formats bold, italic, lists, headers, and links. AI summary now displays inline above search results for easy comparison.

---

## 📊 Monitoring & Logs

### Key Metrics to Watch

1. **Search latency:** Should be <2 seconds
2. **API costs:** Track OpenAI usage in dashboard
3. **Cache hit rate:** Embeddings should load from cache instantly

### Logging

```python
# Check application logs
tail -f /var/log/search-app.log

# Key log messages to watch for:
# ✓ "Loaded vector store with X items" - Cache loaded
# ✓ "Building vector store from data..." - First run or cache miss
# ✗ "Error generating embedding" - API issue
```

---

## 🔐 Security Notes

1. **Never commit `.env` to git** - it contains API keys
2. **API key rotation:** Change keys every 90 days
3. **CORS:** Currently allows all origins - restrict in production:
   ```python
   # api.py
   CORS(app, origins=['https://yourdomain.com'])
   ```
4. **Rate limiting:** Add in production:
   ```bash
   pip install flask-limiter
   ```

---

## 📞 Support Contact

**For technical issues:**
- Developer: [Your contact info]
- Documentation: See `/docs/` folder
- Data format guide: `/docs/DATA_SOURCE_GUIDE.md`

**For OpenAI API issues:**
- Dashboard: https://platform.openai.com
- Support: https://help.openai.com

---

## 🔄 Using the Refresh Embeddings Feature

### What is it?
The "Refresh Embeddings" button rebuilds the search index from your database. This process takes **1-2 minutes**.

### When to use it:
✅ **After updating your database** - Added/modified/deleted records  
✅ **Results seem outdated** - Search not finding new entries  
✅ **After changing field weights** - New scoring priorities need to be cached

### How to use it:
1. Click the **"Refresh Embeddings"** button (pink/red button near top)
2. Read the confirmation modal explaining what will happen
3. Click **"Yes, Refresh"** to proceed
4. Wait for the success message (1-2 minutes)
5. Search functionality automatically resumes

**Note:** During refresh, search will be temporarily unavailable. Plan refreshes during low-traffic periods.

---

## 💡 Using the AI Summary Feature

### What is it?
The "Generate AI Summary" button creates an intelligent overview of your search results using GPT-4.

### When to use it:
- You have many search results and want a quick overview
- You need to understand patterns across multiple vendors
- You want key highlights extracted from detailed data

### How it works:
1. Perform any search (with or without filters)
2. Click the **"Generate AI Summary"** button (purple/blue button)
3. Wait 2-5 seconds for AI to analyze results
4. Read the generated summary with key insights
5. Click "Back to Results" to return to detailed view

**Note:** The AI Summary button automatically hides when you're already viewing an AI summary (no redundancy).

### Customizing AI Summaries:
Edit the prompt in `config.py` at `SUMMARY_PROMPT_TEMPLATE` (lines 170-215) to change what information the AI focuses on.

---

## 🎓 Quick Reference

| Task | Location | What to Change |
|------|----------|----------------|
| Change database | `config.py` lines 29-56 | `DATA_PATH`, `DATA_TYPE` |
| Update field names | `config.py` lines 58-76 | `VENDOR_FIELDS` |
| Adjust search quality | `config.py` lines 115-149 | `FIELD_WEIGHTS` |
| Rebrand UI | `config.py` lines 217-290 | `UI_CONFIG` |
| Change threshold | `config.py` line 24 | `SIMILARITY_THRESHOLD` |
| Configure filters | `config.py` ADVANCED_FILTERS | Field-index based (100% generic) |
| Refresh embeddings | Web UI | Click "Refresh Embeddings" button |
| Get AI summary | Web UI | Click "Generate AI Summary" button |

**Remember:** Only edit `config.py` - never touch the code! System is now 100% database-agnostic.

---

**Last Updated:** November 19, 2025  
**Version:** 3.0 (100% Generic & Database-Agnostic)

