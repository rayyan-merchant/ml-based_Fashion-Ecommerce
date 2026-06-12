#!/usr/bin/env python3
"""
Script to check if articles exist in the database.
"""

import os
import sys
from sqlalchemy import create_engine, text

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.db.database import SQLALCHEMY_DATABASE_URL

def check_articles():
    # Create database engine
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    try:
        # Check total number of articles
        with engine.connect() as conn:
            result = conn.execute(text('SELECT COUNT(*) FROM niche_data.articles'))
            count = result.fetchone()[0]
            print(f"Total articles in database: {count}")
            
            # Check a few sample articles
            result = conn.execute(text('SELECT article_id FROM niche_data.articles LIMIT 5'))
            print("Sample article IDs:")
            for row in result.fetchall():
                print(f"  {row[0]}")
                
            # Check if any articles already have image_path
            result = conn.execute(text('SELECT COUNT(*) FROM niche_data.articles WHERE image_path IS NOT NULL'))
            count_with_images = result.fetchone()[0]
            print(f"Articles with image_path: {count_with_images}")
        
    except Exception as e:
        print(f"Error checking articles: {e}")
    finally:
        engine.dispose()

if __name__ == "__main__":
    check_articles()