from app import create_app
from extensions import db
from models import User
import os, sys
from sqlalchemy import text

app = create_app()

def main():
    print("== Manage: init DB and admin ==")
    try:
        with app.app_context():
            db.session.execute(text("SELECT 1"))
            print("DB connection: OK")

            db.create_all()
            print("Tables: created/verified")

            username = os.getenv("ADMIN_USERNAME", "admin")
            password = os.getenv("ADMIN_PASSWORD", "admin123")

            u = User.query.filter_by(username=username).first()
            if not u:
                u = User(username=username, role="admin")
                u.set_password(password)
                db.session.add(u)
                db.session.commit()
                print(f"Admin user created: {username}")
            else:
                print(f"Admin already exists: {username}")
    except Exception as e:
        print("ERROR:", e, file=sys.stderr)
        raise

if __name__ == "__main__":
    main()
