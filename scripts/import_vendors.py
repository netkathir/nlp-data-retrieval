#!/usr/bin/env python3
"""
Import vendor data from CSV/Excel/JSON to PostgreSQL database
Works with the actual column name schema (not field indices)
Handles JSONB notes format
"""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import POSTGRESQL_CONFIG, POSTGRES_TABLE_NAME
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_db_config():
    """Get database configuration from environment"""
    return {
        'host': os.getenv('POSTGRES_HOST'),
        'port': int(os.getenv('POSTGRES_PORT', '5432')),
        'user': os.getenv('POSTGRES_USER'),
        'password': os.getenv('POSTGRES_PASSWORD'),
        'database': os.getenv('POSTGRES_DATABASE')
    }


def create_table(connection):
    """Create vendors table with actual column names and JSONB notes"""
    
    # Drop and recreate table to ensure clean structure
    drop_table_query = f"DROP TABLE IF EXISTS {POSTGRES_TABLE_NAME};"
    
    create_table_query = f"""
    CREATE TABLE {POSTGRES_TABLE_NAME} (
        id SERIAL PRIMARY KEY,
        name VARCHAR(500),
        transport_name VARCHAR(500),
        visiting_card VARCHAR(500),
        owner_broker VARCHAR(500),
        vendor_state VARCHAR(500),
        vendor_city VARCHAR(500),
        whatsapp_number VARCHAR(500),
        alternate_number VARCHAR(500),
        vehicle_type VARCHAR(500),
        main_service_state VARCHAR(500),
        main_service_city VARCHAR(500),
        return_service VARCHAR(500),
        any_association VARCHAR(500),
        association_name VARCHAR(500),
        verification VARCHAR(500),
        notes JSONB DEFAULT '[]',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Create index on notes for faster queries
    CREATE INDEX idx_notes ON {POSTGRES_TABLE_NAME} USING GIN (notes);
    
    -- Create index on updated_at for cache invalidation checks
    CREATE INDEX idx_updated_at ON {POSTGRES_TABLE_NAME} (updated_at);
    """
    
    with connection.cursor() as cursor:
        cursor.execute(drop_table_query)
        cursor.execute(create_table_query)
        connection.commit()
        print(f"✓ Table '{POSTGRES_TABLE_NAME}' created successfully with JSONB notes support")


def import_from_csv(csv_path: str, connection):
    """Import vendors from CSV file to PostgreSQL"""
    
    print(f"📊 Reading CSV file: {csv_path}")
    df = pd.read_csv(csv_path)
    
    print(f"Found {len(df)} vendors")
    
    # Prepare data for insertion
    vendors_data = []
    for _, row in df.iterrows():
        # Parse notes from JSON string to Python object
        notes = row.get('notes', '[]')
        if isinstance(notes, str):
            try:
                notes_obj = json.loads(notes)
            except json.JSONDecodeError:
                # If it's not valid JSON, create a single note
                notes_obj = [{
                    'comment': notes,
                    'timestamp': pd.Timestamp.now().isoformat() + 'Z'
                }] if notes else []
        else:
            notes_obj = []
        
        vendor = (
            row.get('name'),
            row.get('transport_name'),
            row.get('visiting_card'),
            row.get('owner_broker'),
            row.get('vendor_state'),
            row.get('vendor_city'),
            row.get('whatsapp_number'),
            row.get('alternate_number'),
            row.get('vehicle_type'),
            row.get('main_service_state'),
            row.get('main_service_city'),
            row.get('return_service'),
            row.get('any_association'),
            row.get('association_name'),
            row.get('verification'),
            json.dumps(notes_obj)  # Convert to JSON string for JSONB
        )
        vendors_data.append(vendor)
    
    # Insert data
    insert_query = f"""
    INSERT INTO {POSTGRES_TABLE_NAME} (
        name, transport_name, visiting_card, owner_broker, vendor_state, vendor_city,
        whatsapp_number, alternate_number, vehicle_type, main_service_state,
        main_service_city, return_service, any_association, association_name,
        verification, notes
    ) VALUES %s
    """
    
    with connection.cursor() as cursor:
        execute_values(cursor, insert_query, vendors_data)
        connection.commit()
        print(f"✓ Imported {len(vendors_data)} vendors successfully")


def import_from_json(json_path: str, connection):
    """Import vendors from JSON file to PostgreSQL"""
    
    print(f"📊 Reading JSON file: {json_path}")
    with open(json_path, 'r') as f:
        vendors = json.load(f)
    
    print(f"Found {len(vendors)} vendors")
    
    # Prepare data for insertion
    vendors_data = []
    for vendor in vendors:
        # Ensure notes is in correct format
        notes = vendor.get('notes', [])
        if isinstance(notes, str):
            try:
                notes = json.loads(notes)
            except json.JSONDecodeError:
                notes = [{
                    'comment': notes,
                    'timestamp': pd.Timestamp.now().isoformat() + 'Z'
                }] if notes else []
        
        vendor_tuple = (
            vendor.get('name'),
            vendor.get('transport_name'),
            vendor.get('visiting_card'),
            vendor.get('owner_broker'),
            vendor.get('vendor_state'),
            vendor.get('vendor_city'),
            vendor.get('whatsapp_number'),
            vendor.get('alternate_number'),
            vendor.get('vehicle_type'),
            vendor.get('main_service_state'),
            vendor.get('main_service_city'),
            vendor.get('return_service'),
            vendor.get('any_association'),
            vendor.get('association_name'),
            vendor.get('verification'),
            json.dumps(notes)  # Convert to JSON string for JSONB
        )
        vendors_data.append(vendor_tuple)
    
    # Insert data
    insert_query = f"""
    INSERT INTO {POSTGRES_TABLE_NAME} (
        name, transport_name, visiting_card, owner_broker, vendor_state, vendor_city,
        whatsapp_number, alternate_number, vehicle_type, main_service_state,
        main_service_city, return_service, any_association, association_name,
        verification, notes
    ) VALUES %s
    """
    
    with connection.cursor() as cursor:
        execute_values(cursor, insert_query, vendors_data)
        connection.commit()
        print(f"✓ Imported {len(vendors_data)} vendors successfully")


def main():
    """Main import function"""
    
    print("=" * 60)
    print("PostgreSQL Vendor Import Script")
    print("=" * 60)
    
    # Connect to PostgreSQL
    print("\n🔌 Connecting to PostgreSQL...")
    try:
        config = get_db_config()
        connection = psycopg2.connect(**config)
        print(f"✓ Connected to {config['database']} on {config['host']}")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return
    
    try:
        # Create table
        print("\n📋 Creating table...")
        create_table(connection)
        
        # Import data (try multiple sources)
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        
        # Try JSON first (most complete format)
        json_path = os.path.join(data_dir, 'vendors.json')
        if os.path.exists(json_path):
            print(f"\n📥 Importing from JSON...")
            import_from_json(json_path, connection)
        
        # Alternative: Try CSV
        elif os.path.exists(os.path.join(data_dir, 'vendors_30.csv')):
            csv_path = os.path.join(data_dir, 'vendors_30.csv')
            print(f"\n📥 Importing from CSV...")
            import_from_csv(csv_path, connection)
        
        else:
            print("\n❌ No data files found in data/ directory")
            return
        
        # Show summary
        print("\n📊 Import Summary:")
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM {POSTGRES_TABLE_NAME}")
            count = cursor.fetchone()[0]
            print(f"  Total vendors in database: {count}")
            
            cursor.execute(f"""
                SELECT 
                    AVG(jsonb_array_length(notes)) as avg_notes,
                    MIN(jsonb_array_length(notes)) as min_notes,
                    MAX(jsonb_array_length(notes)) as max_notes
                FROM {POSTGRES_TABLE_NAME}
            """)
            stats = cursor.fetchone()
            print(f"  Average notes per vendor: {stats[0]:.1f}")
            print(f"  Notes range: {int(stats[1])} - {int(stats[2])}")
        
        print("\n✅ Import completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during import: {e}")
        connection.rollback()
    
    finally:
        connection.close()
        print("\n🔌 Connection closed")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
