import os
from app import app
from database import db
from sqlalchemy import text

def migrate():
    with app.app_context():
        # Ensure all database tables exist first
        db.create_all()
        print("[INFO] Database tables verified and created successfully.")

        try:
            db.session.execute(text("ALTER TABLE questions ADD COLUMN IF NOT EXISTS question_type VARCHAR(20) DEFAULT 'code';"))
            db.session.commit()
            print("[SUCCESS] Successfully verified 'question_type' column in database!")
        except Exception as e:
            db.session.rollback()
            # In SQLite, IF NOT EXISTS in ALTER TABLE is not supported; try simple ALTER TABLE
            try:
                db.session.execute(text("ALTER TABLE questions ADD COLUMN question_type VARCHAR(20) DEFAULT 'code';"))
                db.session.commit()
                print("[SUCCESS] Successfully added 'question_type' column!")
            except Exception:
                db.session.rollback()

        # Update existing null question_types
        try:
            db.session.execute(text("UPDATE questions SET question_type = 'code' WHERE question_type IS NULL;"))
            db.session.commit()
            print("[SUCCESS] Successfully set default 'question_type' for existing questions!")
        except Exception as e:
            db.session.rollback()

if __name__ == '__main__':
    migrate()
