#!/usr/bin/env python3
"""
Script to update the image_path column in the articles table
with the existing image filenames from the filtered_images directory.
"""

import os
import sys
from sqlalchemy import create_engine, text

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.db.database import SQLALCHEMY_DATABASE_URL

def update_image_paths():
    # Create database engine
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    try:
        # Get the path to the filtered_images directory
        filtered_images_path = os.path.join(os.path.dirname(__file__), 'filtered_images')
        
        if not os.path.exists(filtered_images_path):
            print(f"Error: {filtered_images_path} directory not found")
            return
            
        # Get list of image files
        image_files = [f for f in os.listdir(filtered_images_path) if f.endswith('.jpg')]
        print(f"Found {len(image_files)} image files")
        
        # Update the database for each image file
        updated_count = 0
        for image_file in image_files:
            # Extract article_id from filename (remove .jpg extension)
            article_id = image_file[:-4]  # Remove .jpg extension
            
            # Update the article record with the image path
            with engine.connect() as conn:
                trans = conn.begin()
                try:
                    result = conn.execute(
                        text("UPDATE niche_data.articles SET image_path = :image_path WHERE article_id = :article_id"),
                        {"image_path": image_file, "article_id": article_id}
                    )
                    if result.rowcount > 0:
                        updated_count += 1
                    trans.commit()
                except Exception as e:
                    trans.rollback()
                    print(f"Error updating article {article_id}: {e}")
                
        print(f"Successfully updated {updated_count} articles with image paths")
        
    except Exception as e:
        print(f"Error updating image paths: {e}")
    finally:
        engine.dispose()

if __name__ == "__main__":
    update_image_paths()