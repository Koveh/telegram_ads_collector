#!/usr/bin/env python3
"""
Test script to verify database connection and basic functionality.
"""
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collect_stats import get_postgres_config
from postgres_manager import PostgresManager

load_dotenv()

def test_database_connection() -> bool:
    """Test database connection."""
    try:
        postgres_config = get_postgres_config()
        db_manager = PostgresManager(postgres_config)
        campaigns = db_manager.get_active_campaigns()
        all_campaigns = db_manager.get_all_campaigns()
        print(f"✓ Database connection successful.")
        print(f"  Active campaigns: {len(campaigns)}")
        print(f"  Total campaigns: {len(all_campaigns)}")
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_database_connection()
    sys.exit(0 if success else 1)

