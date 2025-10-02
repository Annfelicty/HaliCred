"""
Database Cleanup Script
Deletes ALL data from ALL tables while preserving schema
Use for testing/development only - NOT for production!

Author: System
Date: 2025-10-02
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from app.config import settings
from app.db.ai_models import (
    AIEvidence, OCRResult, CVResult, EmissionResult, GreenScoreResult,
    CarbonCredit, SectorBaseline, ReviewCase, AIProcessingLog, UserGreenScoreHistory
)
from app.db.models import User, BusinessProfile, LoanApplication, Verification, GreenScore, Evidence

def print_banner():
    print("\n" + "="*70)
    print("  DATABASE CLEANUP SCRIPT")
    print("  WARNING: This will DELETE ALL DATA from the database")
    print("="*70 + "\n")

def get_table_counts(db: Session) -> dict:
    """Get current row counts for all tables"""
    counts = {}

    # AI tables
    counts['AIProcessingLog'] = db.query(AIProcessingLog).count()
    counts['UserGreenScoreHistory'] = db.query(UserGreenScoreHistory).count()
    counts['ReviewCase'] = db.query(ReviewCase).count()
    counts['CarbonCredit'] = db.query(CarbonCredit).count()
    counts['GreenScoreResult'] = db.query(GreenScoreResult).count()
    counts['EmissionResult'] = db.query(EmissionResult).count()
    counts['CVResult'] = db.query(CVResult).count()
    counts['OCRResult'] = db.query(OCRResult).count()
    counts['AIEvidence'] = db.query(AIEvidence).count()

    # Main tables
    counts['Evidence'] = db.query(Evidence).count()
    counts['GreenScore'] = db.query(GreenScore).count()
    counts['LoanApplication'] = db.query(LoanApplication).count()
    counts['Verification'] = db.query(Verification).count()
    counts['BusinessProfile'] = db.query(BusinessProfile).count()
    counts['User'] = db.query(User).count()
    counts['SectorBaseline'] = db.query(SectorBaseline).count()

    return counts

def display_counts(counts: dict):
    """Display table row counts"""
    print("Current database state:")
    print("-" * 70)
    total = 0
    for table, count in counts.items():
        if count > 0:
            print(f"  {table:30} {count:>8} rows")
            total += count
    print("-" * 70)
    print(f"  TOTAL:{' '*23} {total:>8} rows")
    print()

def clean_database(db: Session):
    """Delete all data from all tables in correct order (foreign key safe)"""

    print("Starting database cleanup...\n")

    # Delete in order to respect foreign key constraints
    tables = [
        # Dependent tables first (child → parent order)
        ('AIProcessingLog', AIProcessingLog),
        ('UserGreenScoreHistory', UserGreenScoreHistory),
        ('ReviewCase', ReviewCase),
        ('CarbonCredit', CarbonCredit),
        ('GreenScoreResult', GreenScoreResult),
        ('EmissionResult', EmissionResult),
        ('CVResult', CVResult),
        ('OCRResult', OCRResult),
        ('AIEvidence', AIEvidence),
        ('LoanApplication', LoanApplication),
        ('Verification', Verification),
        ('Evidence', Evidence),
        ('GreenScore', GreenScore),
        ('BusinessProfile', BusinessProfile),
        ('User', User),
        ('SectorBaseline', SectorBaseline),
    ]

    deleted_total = 0

    for table_name, table_class in tables:
        try:
            count = db.query(table_class).count()
            if count > 0:
                db.query(table_class).delete()
                db.commit()
                print(f"[OK] Deleted {count:>6} rows from {table_name}")
                deleted_total += count
            else:
                print(f"  Skipped {table_name:30} (already empty)")
        except Exception as e:
            print(f"[ERROR] Error deleting from {table_name}: {e}")
            db.rollback()
            raise

    print()
    print("-" * 70)
    print(f"[SUCCESS] Successfully deleted {deleted_total} total rows")
    print("-" * 70)

def reset_sequences(db: Session):
    """Reset PostgreSQL sequences (auto-increment counters)"""
    print("\nResetting database sequences...")

    # Get all sequences
    result = db.execute(text("""
        SELECT sequencename
        FROM pg_sequences
        WHERE schemaname = 'public'
    """))

    sequences = [row[0] for row in result]

    for seq in sequences:
        try:
            db.execute(text(f"ALTER SEQUENCE {seq} RESTART WITH 1"))
            print(f"  [OK] Reset sequence: {seq}")
        except Exception as e:
            print(f"  [ERROR] Error resetting {seq}: {e}")

    db.commit()
    print("[OK] Sequences reset\n")

def run_cleanup():
    """Main cleanup function"""
    print_banner()

    # Create database connection
    engine = create_engine(settings.DATABASE_URL)
    db = Session(bind=engine)

    try:
        # Show current state
        print("Analyzing current database state...\n")
        counts_before = get_table_counts(db)
        display_counts(counts_before)

        total_rows = sum(counts_before.values())

        if total_rows == 0:
            print("[OK] Database is already empty. Nothing to clean.\n")
            return

        # Confirmation prompt
        print(f"WARNING: You are about to DELETE {total_rows} rows across all tables.")
        print("This action CANNOT be undone!\n")

        response = input("Type 'DELETE ALL' to confirm (or anything else to cancel): ").strip()

        if response != "DELETE ALL":
            print("\n[CANCELLED] Cleanup cancelled by user.\n")
            return

        print("\nProceeding with cleanup...\n")

        # Perform cleanup
        clean_database(db)

        # Reset sequences
        reset_sequences(db)

        # Verify cleanup
        print("Verifying cleanup...\n")
        counts_after = get_table_counts(db)

        remaining = sum(counts_after.values())

        if remaining == 0:
            print("=" * 70)
            print("  [SUCCESS] Database is now completely clean.")
            print("  All data deleted, sequences reset.")
            print("  Ready for fresh onboarding!")
            print("=" * 70 + "\n")
        else:
            print(f"[WARNING] {remaining} rows still remaining:")
            display_counts(counts_after)

    except Exception as e:
        print(f"\n[ERROR] Error during cleanup: {e}")
        print("Database may be in an inconsistent state.")
        print("Check the error above and try again.\n")
        db.rollback()
        raise

    finally:
        db.close()

if __name__ == "__main__":
    print("\nDANGER ZONE: Database Cleanup")
    print("This script will DELETE ALL DATA from your database.")
    print("Make sure you have a backup if needed.\n")

    proceed = input("Do you want to continue? (yes/no): ").strip().lower()

    if proceed == "yes":
        run_cleanup()
    else:
        print("\n[OK] Cleanup aborted. Database unchanged.\n")
