# app/db/init_admin.py
from app.db.session import SessionLocal
from app.db.models import User  # Your SQLAlchemy User model
from app.core.security import hash_password

def create_admin():
    db = SessionLocal()
    try:
        # check if admin exists
        if not db.query(User).filter(User.username == "admin").first():
            admin = User(
                username="admin",
                email="admin@example.com",
                password_hash=hash_password("admin123"),  # Will truncate automatically
                role="admin"
            )
            db.add(admin)
            db.commit()
            print("Admin created")
        else:
            print("Admin already exists")
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()
