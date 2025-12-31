"""
Migration script to add new scoring system fields to the database.
This adds streak tracking, monthly scores, and the monthly leaderboard table.
"""

from bemo import app, db
from bemo.models import User, MonthlyLeaderboard
from sqlalchemy import text

def migrate():
    with app.app_context():
        print("Starting migration for improved scoring system...")
        
        # Add new columns to User table
        try:
            with db.engine.connect() as conn:
                # Check if columns already exist before adding
                print("Adding streak tracking columns to User table...")
                
                # Add current_streak
                try:
                    conn.execute(text(
                        "ALTER TABLE user ADD COLUMN current_streak INTEGER NOT NULL DEFAULT 0"
                    ))
                    conn.commit()
                    print("✓ Added current_streak column")
                except Exception as e:
                    if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                        print("  - current_streak already exists, skipping")
                    else:
                        raise
                
                # Add longest_streak
                try:
                    conn.execute(text(
                        "ALTER TABLE user ADD COLUMN longest_streak INTEGER NOT NULL DEFAULT 0"
                    ))
                    conn.commit()
                    print("✓ Added longest_streak column")
                except Exception as e:
                    if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                        print("  - longest_streak already exists, skipping")
                    else:
                        raise
                
                # Add last_solve_date
                try:
                    conn.execute(text(
                        "ALTER TABLE user ADD COLUMN last_solve_date DATE"
                    ))
                    conn.commit()
                    print("✓ Added last_solve_date column")
                except Exception as e:
                    if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                        print("  - last_solve_date already exists, skipping")
                    else:
                        raise
                
                # Add monthly_score
                try:
                    conn.execute(text(
                        "ALTER TABLE user ADD COLUMN monthly_score INTEGER NOT NULL DEFAULT 0"
                    ))
                    conn.commit()
                    print("✓ Added monthly_score column")
                except Exception as e:
                    if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                        print("  - monthly_score already exists, skipping")
                    else:
                        raise
                
                # Add last_monthly_reset
                try:
                    conn.execute(text(
                        "ALTER TABLE user ADD COLUMN last_monthly_reset DATE"
                    ))
                    conn.commit()
                    print("✓ Added last_monthly_reset column")
                except Exception as e:
                    if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                        print("  - last_monthly_reset already exists, skipping")
                    else:
                        raise
                
                # Add solved_at to solves table
                print("\nAdding solved_at column to solves table...")
                try:
                    conn.execute(text(
                        "ALTER TABLE solves ADD COLUMN solved_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP"
                    ))
                    conn.commit()
                    print("✓ Added solved_at column to solves table")
                except Exception as e:
                    if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                        print("  - solved_at already exists, skipping")
                    else:
                        raise
                
                # Add submitted_at to submission table
                print("\nAdding submitted_at column to submission table...")
                try:
                    conn.execute(text(
                        "ALTER TABLE submission ADD COLUMN submitted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP"
                    ))
                    conn.commit()
                    print("✓ Added submitted_at column to submission table")
                except Exception as e:
                    if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                        print("  - submitted_at already exists, skipping")
                    else:
                        raise
        
        except Exception as e:
            print(f"Error during column addition: {e}")
            raise
        
        # Create MonthlyLeaderboard table
        print("\nCreating MonthlyLeaderboard table...")
        try:
            db.create_all()
            print("✓ MonthlyLeaderboard table created (or already exists)")
        except Exception as e:
            print(f"Error creating MonthlyLeaderboard table: {e}")
            raise
        
        print("\n✅ Migration completed successfully!")
        print("\nNew features added:")
        print("  - Streak tracking (current_streak, longest_streak, last_solve_date)")
        print("  - Monthly leaderboard system (monthly_score, MonthlyLeaderboard table)")
        print("  - Timestamp tracking for solves and submissions")

if __name__ == '__main__':
    migrate()
