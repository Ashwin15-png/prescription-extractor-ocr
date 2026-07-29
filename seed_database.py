import os
import sys

# Add backend directory to sys.path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "backend")))

from app.database import SessionLocal, engine, auto_migrate
from app.seeder import seed_data_logic

def main():
    print("Auto-migrating database schema...")
    auto_migrate()
    
    print("Seeding database (running seed_data_logic)...")
    db = SessionLocal()
    try:
        inserted = seed_data_logic(db)
        if inserted == 0:
            print("Database already contains data or seeding was skipped.")
        else:
            print(f"Success! Seeded {inserted} medical prescription records.")
    except Exception as e:
        print(f"Error during seeding execution: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
