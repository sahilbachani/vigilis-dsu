#!/usr/bin/env python
"""
Quick script to create or reset admin user credentials
Run this once after setting up the database
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.db.models import User
from app.core.security import hash_password

def create_or_reset_admin():
    db = SessionLocal()
    try:
        # Check if admin exists
        admin = db.query(User).filter(User.username == "admin").first()
        
        if admin:
            print("✅ Admin user already exists")
            print(f"   Username: {admin.username}")
            print(f"   Email: {admin.email}")
            
            # Option to reset password
            reset = input("\nReset admin password? (y/n): ").lower() == 'y'
            if reset:
                admin.hashed_password = hash_password("admin123")
                db.commit()
                print("✅ Admin password reset to: admin123")
        else:
            # Create new admin
            admin = User(
                username="admin",
                email="admin@vigilis.local",
                hashed_password=hash_password("admin123"),
                is_active=True,
                is_superuser=True
            )
            db.add(admin)
            db.commit()
            print("✅ Admin user created successfully!")
            print(f"   Username: admin")
            print(f"   Password: admin123")
            print(f"   Email: admin@vigilis.local")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_or_reset_admin()
