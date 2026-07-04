import sys
from datetime import date
from .database import SessionLocal
from .scheduler import process_scheduled_insertions

def main():
    print(f"==> Starting automated scheduled insertions job for date: {date.today()}...")
    db = SessionLocal()
    try:
        inserted = process_scheduled_insertions(db)
        print(f"==> Job completed successfully. Processed and inserted {len(inserted)} expenses:")
        for exp in inserted:
            print(f"  - {exp.date.strftime('%Y-%m-%d')} | {exp.description} | {exp.user} | £{abs(exp.amount):.2f}")
    except Exception as e:
        print(f"==> ERROR executing scheduler job: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
