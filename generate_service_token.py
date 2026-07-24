import sys
import os
from datetime import timedelta

# Ensure the backend directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.security import create_access_token
from core.database import SessionLocal
from models.user import User

def generate_permanent_token(email: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"Error: User with email '{email}' not found.")
            return

        # 100 years from now
        expires = timedelta(days=36500)
        token = create_access_token(data={"sub": user.email}, expires_delta=expires)
        
        print("\n" + "="*80)
        print("SUCCESS! Generated 100-year non-expiring Service Token")
        print("="*80)
        print(f"User: {user.email}")
        print("Token:")
        print(f"\n{token}\n")
        print("="*80)
        print("Copy the token above and use it as PMTOOL_API_TOKEN in your Render environment variables.")
    finally:
        db.close()

if __name__ == "__main__":
    generate_permanent_token("kandpalkartik.13@gmail.com")
