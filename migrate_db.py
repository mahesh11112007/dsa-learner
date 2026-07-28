import os
from app import app
from database import db
from sqlalchemy import text

def migrate():
    with app.app_context():
        try:
            db.session.execute(text("ALTER TABLE questions ADD COLUMN IF NOT EXISTS question_type VARCHAR(20) DEFAULT 'code';"))
            db.session.commit()
            print("[SUCCESS] Successfully added 'question_type' column to PostgreSQL database!")
        except Exception as e:
            db.session.rollback()
            print("[MIGRATION WARNING]", e)

        # Update existing null question_types
        try:
            db.session.execute(text("UPDATE questions SET question_type = 'code' WHERE question_type IS NULL;"))
            db.session.commit()
            print("[SUCCESS] Successfully populated default 'question_type' for existing questions!")
        except Exception as e:
            db.session.rollback()
            print("[MIGRATION WARNING]", e)

if __name__ == '__main__':
    migrate()
