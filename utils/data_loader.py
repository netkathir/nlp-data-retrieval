"""
Data Loader Module
Handles loading vendor data from various sources (JSON, CSV, Excel, SQL Database)
"""

import json
import pandas as pd
from typing import List, Dict, Any, Optional
import os


class DataLoader:
    """Load and validate vendor data from different sources"""
    
    def __init__(self, data_source: str = None):
        """
        Initialize DataLoader with data source path
        
        Args:
            data_source: Path to data file (JSON, CSV, or Excel)
        """
        from config import DATA_TYPE
        
        # Try to import DATA_PATH for backward compatibility
        try:
            from config import DATA_PATH
            self.data_source = data_source or DATA_PATH
        except ImportError:
            self.data_source = data_source or "data/vendors.json"
        
        self.data_type = DATA_TYPE.lower()
        
    def load_from_json(self, file_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Load vendor data from JSON file
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            List of vendor dictionaries
        """
        path = file_path or self.data_source
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"Data file not found: {path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle both list and dict with 'vendors' key
        if isinstance(data, dict) and 'vendors' in data:
            return data['vendors']
        elif isinstance(data, list):
            return data
        else:
            return data
    
    def load_from_csv(self, file_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Load vendor data from CSV file
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            List of vendor dictionaries
        """
        path = file_path or self.data_source
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"Data file not found: {path}")
        
        df = pd.read_csv(path)
        
        # Convert NaN to None for consistency
        df = df.where(pd.notna(df), None)
        
        return df.to_dict('records')
    
    def load_from_excel(self, file_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Load vendor data from Excel file (.xlsx, .xls)
        
        Args:
            file_path: Path to Excel file
            
        Returns:
            List of vendor dictionaries
        """
        path = file_path or self.data_source
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"Data file not found: {path}")
        
        df = pd.read_excel(path)
        
        # Convert NaN to None for consistency
        df = df.where(pd.notna(df), None)
        
        return df.to_dict('records')
    
    def load_from_sql(self, database_url: str = None, table_name: str = None) -> List[Dict[str, Any]]:
        """
        Load vendor data from SQL database
        
        Args:
            database_url: Database connection URL
            table_name: Name of the table to load
            
        Returns:
            List of vendor dictionaries
        """
        try:
            from sqlalchemy import create_engine
        except ImportError:
            raise ImportError("sqlalchemy is required for SQL support. Install it with: pip install sqlalchemy")
        
        from config import SQL_DATABASE_URL, SQL_TABLE_NAME
        
        db_url = database_url or SQL_DATABASE_URL
        table = table_name or SQL_TABLE_NAME
        
        # Create database connection
        engine = create_engine(db_url)
        
        # Load data from table
        query = f"SELECT * FROM {table}"
        df = pd.read_sql(query, engine)
        
        # Convert NaN to None for consistency
        df = df.where(pd.notna(df), None)
        
        return df.to_dict('records')
    
    def load_from_mysql(self) -> List[Dict[str, Any]]:
        """
        Load vendor data from MySQL database using pure field index architecture
        
        Returns:
            List of vendor dictionaries with field indices mapped to logical names
        """
        try:
            import pymysql
            from pymysql.cursors import DictCursor
        except ImportError:
            raise ImportError("pymysql is required for MySQL support. Install it with: pip install pymysql")
        
        from config import MYSQL_CONFIG, MYSQL_TABLE_NAME, FIELD_MAP, ACTIVE_FIELD_INDICES
        
        # Create MySQL connection
        try:
            connection = pymysql.connect(**MYSQL_CONFIG, cursorclass=DictCursor)
        except pymysql.Error as e:
            raise ConnectionError(f"Failed to connect to MySQL: {e}")
        
        try:
            with connection.cursor() as cursor:
                # Build SELECT query with all active field indices
                field_columns = ", ".join([f"field_{i}" for i in ACTIVE_FIELD_INDICES])
                query = f"SELECT id, {field_columns} FROM {MYSQL_TABLE_NAME}"
                
                cursor.execute(query)
                rows = cursor.fetchall()
                
                # Convert field indices to logical names using FIELD_MAP
                vendors = []
                for row in rows:
                    vendor = {"id": row.get("id")}
                    
                    # Map field_0, field_1, ... to logical names
                    for idx in ACTIVE_FIELD_INDICES:
                        field_key = f"field_{idx}"
                        field_value = row.get(field_key, "")
                        
                        # Get logical name from FIELD_MAP
                        if idx in FIELD_MAP:
                            logical_name = FIELD_MAP[idx]["name"]
                            vendor[logical_name] = field_value if field_value else None
                        
                        # Also keep field index access for pure index operations
                        vendor[f"field_{idx}"] = field_value if field_value else None
                    
                    vendors.append(vendor)
                
                return vendors
                
        finally:
            connection.close()
    
    def load_from_dataframe(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Load vendor data from pandas DataFrame
        
        Args:
            df: pandas DataFrame with vendor data
            
        Returns:
            List of vendor dictionaries
        """
        return df.to_dict('records')
    
    def validate_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate and clean vendor data
        
        Args:
            data: List of vendor dictionaries
            
        Returns:
            Validated and cleaned data
        """
        from config import VENDOR_FIELDS
        
        validated_data = []
        
        for idx, record in enumerate(data):
            # Ensure all required fields exist (fill with None if missing)
            validated_record = {}
            
            for field in VENDOR_FIELDS:
                validated_record[field] = record.get(field, None)
            
            # Keep the original ID if present
            if 'id' in record:
                validated_record['id'] = record['id']
            else:
                validated_record['id'] = idx + 1
            
            # Convert empty strings to None
            for key, value in validated_record.items():
                if value == "" or value == "null":
                    validated_record[key] = None
            
            validated_data.append(validated_record)
        
        return validated_data
    
    def load(self, validate: bool = True) -> List[Dict[str, Any]]:
        """
        Load data from configured source (auto-detects format)
        
        Args:
            validate: Whether to validate the data
            
        Returns:
            List of vendor dictionaries
        """
        # Load based on DATA_TYPE config
        if self.data_type == 'mysql':
            data = self.load_from_mysql()
            # MySQL data is pre-validated with field mapping, skip legacy validation
            print(f"✓ Loaded {len(data)} vendors from MySQL source")
            return data
        elif self.data_type == 'json' or self.data_source.endswith('.json'):
            data = self.load_from_json()
        elif self.data_type == 'csv' or self.data_source.endswith('.csv'):
            data = self.load_from_csv()
        elif self.data_type == 'excel' or self.data_source.endswith(('.xlsx', '.xls')):
            data = self.load_from_excel()
        elif self.data_type == 'sql':
            data = self.load_from_sql()
        else:
            raise ValueError(f"Unsupported data type: {self.data_type} or file: {self.data_source}")
        
        if validate:
            data = self.validate_data(data)
        
        print(f"✓ Loaded {len(data)} vendors from {self.data_type.upper()} source")
        return data
    
    def get_sample_data(self, n: int = 5) -> List[Dict[str, Any]]:
        """
        Get a sample of vendor data
        
        Args:
            n: Number of records to return
            
        Returns:
            Sample of vendor data
        """
        data = self.load()
        return data[:n]


def load_vendors(data_source: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Convenience function to load vendor data
    
    Args:
        data_source: Optional path to data file
        
    Returns:
        List of vendor dictionaries
    """
    loader = DataLoader(data_source)
    return loader.load()
