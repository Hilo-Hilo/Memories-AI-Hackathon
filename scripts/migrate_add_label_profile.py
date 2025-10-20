"""
Database migration script: Add label_profile_name column to sessions table.

Run this to migrate existing databases to support label profiles.
"""

import sqlite3
import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.focus_guardian.utils.logger import setup_logger, get_logger

logger = setup_logger("migration")


def migrate_database(db_path: Path) -> bool:
    """
    Add label_profile_name column to existing sessions table.
    
    Args:
        db_path: Path to database file
        
    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Starting database migration: {db_path}")
    
    if not db_path.exists():
        logger.error(f"Database not found: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(sessions)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'label_profile_name' in columns:
            logger.info("Column 'label_profile_name' already exists - skipping migration")
            conn.close()
            return True
        
        # Add column with default value
        logger.info("Adding column 'label_profile_name' to sessions table...")
        cursor.execute("""
            ALTER TABLE sessions
            ADD COLUMN label_profile_name TEXT NOT NULL DEFAULT 'Default'
        """)
        
        # Update any NULL values (shouldn't happen due to DEFAULT, but safe)
        cursor.execute("""
            UPDATE sessions
            SET label_profile_name = 'Default'
            WHERE label_profile_name IS NULL
        """)
        
        conn.commit()
        
        # Verify migration
        cursor.execute("SELECT COUNT(*) FROM sessions")
        total_sessions = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM sessions
            WHERE label_profile_name = 'Default'
        """)
        migrated_sessions = cursor.fetchone()[0]
        
        conn.close()
        
        logger.info(f"✅ Migration successful:")
        logger.info(f"   Total sessions: {total_sessions}")
        logger.info(f"   Migrated to Default profile: {migrated_sessions}")
        
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        return False


def main():
    """Run migration on default database."""
    # Find database
    project_root = Path(__file__).parent.parent
    db_path = project_root / "data" / "focus_guardian.db"
    
    print(f"Focus Guardian - Database Migration")
    print(f"Adding label_profile_name column to sessions table")
    print(f"Database: {db_path}")
    print()
    
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        print("No migration needed (will be created with new schema on first run)")
        return 0
    
    # Confirm with user
    response = input("Proceed with migration? (y/n): ")
    if response.lower() != 'y':
        print("Migration cancelled")
        return 0
    
    # Run migration
    success = migrate_database(db_path)
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("All existing sessions now use 'Default' label profile")
        return 0
    else:
        print("\n❌ Migration failed - check logs for details")
        return 1


if __name__ == "__main__":
    sys.exit(main())

