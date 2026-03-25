import os
from dotenv import load_dotenv
from database import get_db_session
from sqlalchemy import text

load_dotenv()

def create_media_table():
    db = get_db_session()
    try:
        db.execute(text("""
        CREATE TABLE IF NOT EXISTS post_media (
            media_id SERIAL PRIMARY KEY,
            post_id INTEGER REFERENCES posts(post_id) ON DELETE CASCADE,
            media_type VARCHAR(50),
            media_url TEXT,
            local_path TEXT,
            added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """))
        db.commit()
        print("Created post_media table successfully.")
    except Exception as e:
        print(f"Error creating table: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_media_table()
