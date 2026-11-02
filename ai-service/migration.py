"""Apply the same schema upgrades and preset seeds used by AUTO_CREATE_TABLES."""
from database import init_db

if __name__ == "__main__":
    init_db()
    print("Database schema and presets are up to date.")
