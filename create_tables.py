#!/usr/bin/env python3
"""
Database Table Creation Script

This script creates all necessary tables for the Stays-Nibo integration application.
Run this script after setting up your PostgreSQL database and environment variables.

Usage:
    python create_tables.py

Make sure your .env file is properly configured with PostgreSQL connection details:
- DB_HOST
- DB_PORT  
- DB_NAME
- DB_USER
- DB_PASSWORD
"""

import sys
from sqlmodel import SQLModel, create_engine
from api.constants import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME
from api.utils import Requests, Logs

def create_database_tables():
    """Create all database tables defined in the application."""
    
    # Construct the PostgreSQL connection URL
    db_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    print(f"Connecting to PostgreSQL database...")
    print(f"Host: {DB_HOST}:{DB_PORT}")
    print(f"Database: {DB_NAME}")
    print(f"User: {DB_USER}")
    print("-" * 50)
    
    try:
        # Create the engine
        engine = create_engine(db_url, echo=True)  # echo=True shows SQL commands
        
        print("Creating tables...")
        
        # Create all tables defined in SQLModel classes
        SQLModel.metadata.create_all(engine)
        
        print("\n✅ Tables created successfully!")
        print("\nTables created:")
        print("- requests: Stores incoming webhook requests")
        print("- logs: Stores processing logs and tracking information")
        
        # Test the connection by trying to connect
        with engine.connect() as connection:
            print("\n✅ Database connection test successful!")
            
    except Exception as e:
        print(f"\n❌ Error creating tables: {str(e)}")
        print("\nPlease check:")
        print("1. PostgreSQL server is running")
        print("2. Database exists and is accessible")
        print("3. Connection credentials are correct in your .env file")
        print("4. psycopg2-binary is installed (pip install psycopg2-binary)")
        sys.exit(1)

def check_environment():
    """Check if all required environment variables are set."""
    required_vars = [
        ("DB_HOST", DB_HOST),
        ("DB_PORT", DB_PORT), 
        ("DB_NAME", DB_NAME),
        ("DB_USER", DB_USER),
        ("DB_PASSWORD", DB_PASSWORD)
    ]
    
    missing_vars = []
    for var_name, var_value in required_vars:
        if not var_value:
            missing_vars.append(var_name)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease create a .env file with the required variables.")
        print("You can use .env-example as a template.")
        sys.exit(1)
    
    print("✅ All required environment variables are set.")

if __name__ == "__main__":
    print("Database Table Creation Script")
    print("=" * 50)
    
    # Check environment variables
    check_environment()
    
    # Create tables
    create_database_tables()
    
    print("\n" + "=" * 50)
    print("Setup complete! You can now start your FastAPI application.")
    print("\nTo start the server:")
    print("uvicorn api.index:app --reload --host 0.0.0.0 --port 8000")