"""
Migration script to add time complexity tracking to the database.
This adds:
- optimal_complexity field to Problem table
- execution_times and detected_complexity fields to Submission table
- ProblemComplexitySolve table for tracking first solves at each complexity level
"""

from bemo import app, db
from bemo.models import User, Problem, Submission, ProblemComplexitySolve
from sqlalchemy import text

def migrate():
    with app.app_context():
        print("Starting migration for time complexity tracking system...")
        
        # Add new columns to Problem table
        try:
            with db.engine.connect() as conn:
                print("\nAdding optimal_complexity column to Problem table...")
                try:
                    conn.execute(text(
                        "ALTER TABLE problem ADD COLUMN optimal_complexity VARCHAR(20)"
                    ))
                    conn.commit()
                    print("✓ Added optimal_complexity column")
                except Exception as e:
                    if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                        print("  - optimal_complexity already exists, skipping")
                    else:
                        raise
                
                # Add execution_times to Submission table
                print("\nAdding execution_times column to Submission table...")
                try:
                    conn.execute(text(
                        "ALTER TABLE submission ADD COLUMN execution_times TEXT DEFAULT '[]'"
                    ))
                    conn.commit()
                    print("✓ Added execution_times column")
                except Exception as e:
                    if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                        print("  - execution_times already exists, skipping")
                    else:
                        raise
                
                # Add detected_complexity to Submission table
                print("\nAdding detected_complexity column to Submission table...")
                try:
                    conn.execute(text(
                        "ALTER TABLE submission ADD COLUMN detected_complexity VARCHAR(20)"
                    ))
                    conn.commit()
                    print("✓ Added detected_complexity column")
                except Exception as e:
                    if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                        print("  - detected_complexity already exists, skipping")
                    else:
                        raise
        
        except Exception as e:
            print(f"Error during column addition: {e}")
            raise
        
        # Create ProblemComplexitySolve table
        print("\nCreating ProblemComplexitySolve table...")
        try:
            db.create_all()
            print("✓ ProblemComplexitySolve table created (or already exists)")
        except Exception as e:
            print(f"Error creating ProblemComplexitySolve table: {e}")
            raise
        
        print("\n✅ Migration completed successfully!")
        print("\nNew features added:")
        print("  - Time complexity tracking per submission")
        print("  - Complexity-based scoring (only first solve at each complexity gets bonus)")
        print("  - Cascading complexity closing (solving O(n) closes O(1) and O(log n))")
        print("\nHow it works:")
        print("  - Each submission's time complexity is estimated from execution time")
        print("  - First solver at each complexity level gets bonus points")
        print("  - Easier complexities are automatically closed when a complexity is solved")
        print("  - Example: If you solve at O(n), O(1) and O(log n) are closed, but O(n^2) stays open")

if __name__ == '__main__':
    migrate()
