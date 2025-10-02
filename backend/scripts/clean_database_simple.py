"""
Simple Database Cleanup Script - Uses Raw SQL
Deletes ALL data from ALL tables while preserving schema
Use for testing/development only - NOT for production!
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.config import settings

def print_banner():
    print("\n" + "="*70)
    print("  DATABASE CLEANUP SCRIPT (Simple SQL Version)")
    print("  WARNING: This will DELETE ALL DATA from the database")
    print("="*70 + "\n")

def get_all_tables(engine):
    """Get list of all tables in the database"""
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
        """))
        return [row[0] for row in result]

def get_table_count(engine, table_name):
    """Get row count for a specific table"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"'))
            return result.scalar()
    except Exception:
        return 0

def truncate_all_tables(engine):
    """Truncate all tables in the database"""
    print("Getting list of tables...\n")

    tables = get_all_tables(engine)

    if not tables:
        print("[OK] No tables found in database.\n")
        return

    print(f"Found {len(tables)} tables\n")

    # Show current state
    print("Current row counts:")
    print("-" * 70)
    total_before = 0
    for table in tables:
        count = get_table_count(engine, table)
        if count > 0:
            print(f"  {table:30} {count:>8} rows")
            total_before += count
    print("-" * 70)
    print(f"  TOTAL:{' '*23} {total_before:>8} rows\n")

    if total_before == 0:
        print("[OK] Database is already empty. Nothing to clean.\n")
        return

    # Confirmation
    print(f"WARNING: You are about to DELETE {total_before} rows across {len(tables)} tables.")
    print("This action CANNOT be undone!\n")

    response = input("Type 'DELETE ALL' to confirm (or anything else to cancel): ").strip()

    if response != "DELETE ALL":
        print("\n[CANCELLED] Cleanup cancelled by user.\n")
        return

    print("\nProceeding with cleanup...\n")

    # Disable foreign key checks and truncate all tables
    try:
        with engine.begin() as conn:
            # Build list of tables to truncate
            table_list = ', '.join([f'"{t}"' for t in tables])

            # TRUNCATE CASCADE will handle foreign key constraints
            print(f"Truncating all tables...")
            conn.execute(text(f"TRUNCATE TABLE {table_list} RESTART IDENTITY CASCADE"))

        print("[SUCCESS] All tables truncated\n")

        # Verify cleanup
        print("Verifying cleanup...\n")
        print("Row counts after cleanup:")
        print("-" * 70)
        total_after = 0
        for table in tables:
            count = get_table_count(engine, table)
            if count > 0:
                print(f"  {table:30} {count:>8} rows")
                total_after += count

        if total_after == 0:
            print("  All tables empty")
        print("-" * 70)
        print(f"  TOTAL:{' '*23} {total_after:>8} rows\n")

        if total_after == 0:
            print("=" * 70)
            print("  [SUCCESS] Database is now completely clean.")
            print("  All data deleted, sequences reset.")
            print("  Ready for fresh onboarding!")
            print("=" * 70 + "\n")
        else:
            print(f"[WARNING] {total_after} rows still remaining\n")

    except Exception as e:
        print(f"\n[ERROR] Error during cleanup: {e}")
        print("Database may be in an inconsistent state.\n")
        raise

def run_cleanup():
    """Main cleanup function"""
    print_banner()

    # Create database connection
    engine = create_engine(settings.DATABASE_URL)

    try:
        truncate_all_tables(engine)
    finally:
        engine.dispose()

if __name__ == "__main__":
    print("\nDANGER ZONE: Database Cleanup")
    print("This script will DELETE ALL DATA from your database.")
    print("Make sure you have a backup if needed.\n")

    proceed = input("Do you want to continue? (yes/no): ").strip().lower()

    if proceed == "yes":
        run_cleanup()
    else:
        print("\n[OK] Cleanup aborted. Database unchanged.\n")
