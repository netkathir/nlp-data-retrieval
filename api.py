"""
Flask REST API for Warehouse AI Search
Deploy this on your own website/server
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sys
import os
from openai import OpenAI
import config

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.query_engine import SemanticSearch
from core.response_generator import ResponseGenerator

app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

# Initialize search engine once
search_engine = None
response_generator = None
openai_client = None

def init_app():
    """Initialize search engine on startup"""
    global search_engine, response_generator, openai_client
    try:
        search_engine = SemanticSearch()
        response_generator = ResponseGenerator()
        openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
        print("✓ Search engine initialized successfully")
        print("✓ OpenAI client initialized successfully")
    except Exception as e:
        print(f"✗ Error initializing search engine: {e}")
        raise

# Initialize on startup
init_app()


@app.route('/')
def index():
    """Serve the main HTML page with config values"""
    # Pass field index configuration to frontend
    try:
        field_map = config.FIELD_MAP
        card_display_indices = config.CARD_DISPLAY_INDICES
        filter_indices = config.FILTER_INDICES
        primary_display_index = config.PRIMARY_DISPLAY_INDEX
        advanced_filters = config.ADVANCED_FILTERS
    except AttributeError:
        # Fallback to legacy config if FIELD_MAP not available
        field_map = {}
        card_display_indices = []
        filter_indices = {}
        primary_display_index = 0
        advanced_filters = []
    
    return render_template(
        'index.html',
        similarity_threshold=config.SIMILARITY_THRESHOLD,
        max_results=config.MAX_RESULTS,
        ui=config.UI_CONFIG,
        primary_field=getattr(config, 'PRIMARY_DISPLAY_FIELD', 'transport_name'),
        filter_fields=getattr(config, 'FILTER_FIELD_NAMES', {}),
        # New field index configuration
        field_map=field_map,
        card_display_indices=card_display_indices,
        filter_indices=filter_indices,
        primary_display_index=primary_display_index,
        advanced_filters=advanced_filters
    )


@app.route('/api/search', methods=['POST'])
def search():
    """
    Search endpoint
    
    POST /api/search
    {
        "query": "Find electronics vendors in Mumbai",
        "top_k": 5,
        "threshold": 0.25,
        "filters": {
            "vendor_state": "Maharashtra",
            "vendor_city": "Mumbai",
            "verification": "Verified"
        }
    }
    
    Returns:
    {
        "success": true,
        "results": [...],
        "count": 5
    }
    """
    try:
        data = request.json
        query = data.get('query', '')
        top_k = data.get('top_k', 5)
        threshold = data.get('threshold', 0.25)
        filters = data.get('filters', {})
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Query is required'
            }), 400
        
        # Execute search
        if filters:
            results = search_engine.query_with_filters(
                query, 
                filters, 
                top_k=top_k,
                threshold=threshold
            )
        else:
            results = search_engine.query(
                query, 
                top_k=top_k,
                threshold=threshold
            )
        
        return jsonify({
            'success': True,
            'results': results,
            'count': len(results),
            'query': query
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/summary', methods=['POST'])
def summary():
    """
    Generate AI summary of search results
    
    POST /api/summary
    {
        "query": "Find electronics vendors",
        "vendors": [...] or "results": [...]
    }
    
    Returns:
    {
        "success": true,
        "summary": "Found 3 electronics vendors..."
    }
    """
    try:
        data = request.json
        query = data.get('query', '')
        # Accept both 'vendors' (from frontend) and 'results' (for consistency)
        results = data.get('vendors') or data.get('results', [])
        
        if not results:
            return jsonify({
                'success': False,
                'error': 'No results to summarize'
            }), 400
        
        # Correct parameter order: (results, query)
        summary_text = response_generator.generate_summary(results, query)
        
        return jsonify({
            'success': True,
            'summary': summary_text
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/stats', methods=['GET'])
def stats():
    """
    Get database statistics
    
    GET /api/stats
    
    Returns:
    {
        "success": true,
        "stats": {
            "total_vendors": 12,
            "verified_vendors": 10,
            ...
        }
    }
    """
    try:
        stats = search_engine.get_statistics()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/refresh', methods=['POST'])
def refresh():
    """
    Refresh the search index
    
    POST /api/refresh
    
    Returns:
    {
        "success": true,
        "message": "Index refreshed successfully"
    }
    """
    try:
        search_engine.initialize(force_rebuild=True)
        return jsonify({
            'success': True,
            'message': 'Index refreshed successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/transcribe', methods=['POST'])
def transcribe():
    """
    Translate audio to English text using OpenAI Whisper Translation API
    Automatically detects Tamil/Hindi/other languages and translates to English
    Perfect for Tamil-English code-mixing (Tanglish)
    
    POST /api/transcribe
    Content-Type: multipart/form-data
    {
        "audio": <audio file (webm, mp3, wav, etc.)>
    }
    
    Returns:
    {
        "success": true,
        "text": "translated text in English",
        "language": "ta" or "en" (detected source language)
    }
    """
    try:
        # Check if audio file is present
        if 'audio' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No audio file provided',
                'user_message': 'No audio recorded. Please try again.'
            }), 400
        
        audio_file = request.files['audio']
        
        if audio_file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No audio file selected',
                'user_message': 'No audio recorded. Please try again.'
            }), 400
        
        # Read the file content
        audio_content = audio_file.read()
        
        # Check if audio is too short (less than 100 bytes is likely invalid)
        if len(audio_content) < 100:
            return jsonify({
                'success': False,
                'error': 'Audio file too short',
                'user_message': 'Recording too short. Please hold the button longer and speak clearly.'
            }), 400
        
        # Create a file-like object with proper filename
        from io import BytesIO
        audio_buffer = BytesIO(audio_content)
        audio_buffer.name = 'recording.webm'
        
        # Use Whisper Translation API to translate Tamil speech to English
        # This will automatically detect Tamil/other languages and translate to English
        translation = openai_client.audio.translations.create(
            model="whisper-1",
            file=audio_buffer,
            response_format="verbose_json"  # Get language detection info
        )
        
        return jsonify({
            'success': True,
            'text': translation.text,
            'language': translation.language,
            'duration': translation.duration
        })
        
    except Exception as e:
        error_message = str(e)
        user_message = 'Voice recognition failed. Please try again.'
        
        # Provide user-friendly messages for common errors
        if 'Invalid file format' in error_message:
            user_message = 'Recording format not supported. Please try again.'
        elif 'too short' in error_message.lower():
            user_message = 'Recording too short. Please hold the button longer and speak clearly.'
        elif 'no speech' in error_message.lower():
            user_message = 'No speech detected. Please speak louder and try again.'
        
        return jsonify({
            'success': False,
            'error': error_message,
            'user_message': user_message
        }), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'search_engine': search_engine is not None
    })


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Warehouse AI Search API")
    print("=" * 60)
    print()
    print("API Endpoints:")
    print("  POST   /api/search      - Search vendors")
    print("  POST   /api/summary     - Generate AI summary")
    print("  POST   /api/transcribe  - Transcribe audio (Whisper)")
    print("  GET    /api/stats       - Get database stats")
    print("  POST   /api/refresh     - Refresh search index")
    print("  GET    /health          - Health check")
    print()
    print("Frontend:")
    print("  GET    /              - Main search interface")
    print()
    print("=" * 60)
    print()
    
    # Run the app
    from config import API_HOST, API_PORT, API_DEBUG
    
    app.run(
        host=API_HOST,
        port=API_PORT,
        debug=API_DEBUG
    )
