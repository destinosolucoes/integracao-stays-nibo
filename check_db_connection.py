#!/usr/bin/env python3
"""
Database Connection Test Script

This script tests the PostgreSQL database connection without making any changes.
Useful for troubleshooting connection issues.

Usage:
    python check_db_connection.py
"""

import sys
from sqlmodel import create_engine, text
from api.constants import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME

def test_connection():
    """Test the database connection and display basic information."""
    
    # Construct the PostgreSQL connection URL
    db_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    print("PostgreSQL Connection Test")
    print("=" * 40)
    print(f"Host: {DB_HOST}:{DB_PORT}")
    print(f"Database: {DB_NAME}")
    print(f"User: {DB_USER}")
    print("-" * 40)
    
    try:
        # Create engine and test connection
        engine = create_engine(db_url)
        
        with engine.connect() as connection:
            # Test basic query
            result = connection.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            
            print("✅ Connection successful!")
            print(f"PostgreSQL Version: {version}")
            
            # Check if our tables exist
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('requests', 'logs')
                ORDER BY table_name
            """))
            
            existing_tables = [row[0] for row in result.fetchall()]
            
            print(f"\nExisting application tables: {existing_tables}")
            
            if not existing_tables:
                print("\n⚠️  No application tables found.")
                print("Run 'python create_tables.py' to create them.")
            else:
                print(f"✅ Found {len(existing_tables)} application table(s).")
                
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        print("\nTroubleshooting tips:")
        print("1. Verify PostgreSQL server is running")
        print("2. Check database name exists")
        print("3. Verify username and password")
        print("4. Ensure user has access to the database")
        print("5. Check if psycopg2-binary is installed")
        sys.exit(1)

if __name__ == "__main__":
    test_connection()