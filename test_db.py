from core.config import settings
from core.database import engine
import sqlalchemy

print(f"DATABASE_URL from settings: {settings.DATABASE_URL}")
print(f"Engine URL: {engine.url}")

try:
    with engine.connect() as connection:
        result = connection.execute(sqlalchemy.text("SELECT current_database();"))
        db_name = result.scalar()
        print(f"Connected to PostgreSQL database: {db_name}")
except Exception as e:
    print(f"Error connecting to PostgreSQL: {e}")
    try:
        with engine.connect() as connection:
            result = connection.execute(sqlalchemy.text("SELECT sqlite_version();"))
            sqlite_ver = result.scalar()
            print(f"Connected to SQLite version: {sqlite_ver}")
    except Exception as e2:
        print(f"Error connecting to SQLite: {e2}")
