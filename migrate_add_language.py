"""
Migration script to add language_id column to Submission table
Run this if you have an existing database that needs the new column
"""
from bemo import app, db
from sqlalchemy import text

def migrate_add_language_column():
    with app.app_context():
        try:
            # Check if column exists
            with db.engine.begin() as conn:  # Use begin() for automatic transaction management
                result = conn.execute(text("PRAGMA table_info(submission)"))
                columns = [row[1] for row in result]
                
                if 'language_id' not in columns:
                    print("Adding language_id column to submission table...")
                    conn.execute(text("ALTER TABLE submission ADD COLUMN language_id VARCHAR(10) DEFAULT '54'"))
                    print("Column added successfully!")
                else:
                    print("Column language_id already exists in submission table.")
        except Exception as e:
            print(f"Error during migration: {e}")
            print("If you see 'duplicate column name' error, the column already exists.")

if __name__ == '__main__':
    migrate_add_language_column()
