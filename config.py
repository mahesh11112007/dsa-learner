import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dsa-qa-super-secret-key-2026'
    
    # Database URL configuration for Local (SQLite) and Online Cloud DBs (PostgreSQL, MySQL)
    db_url = os.environ.get('DATABASE_URL')
    if db_url and db_url.startswith("postgres://"):
        # Fix legacy Heroku/Render/ElephantSQL postgres:// prefix to postgresql:// for SQLAlchemy 2.0
        db_url = db_url.replace("postgres://", "postgresql://", 1)
        
    SQLALCHEMY_DATABASE_URI = db_url or ('sqlite:///' + os.path.join(BASE_DIR, 'dsa_qa.db'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Connection Pool settings optimized for Vercel Serverless & Neon DB
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }
    
    # Handle read-only filesystem on Vercel / serverless deployments
    if os.environ.get('VERCEL'):
        UPLOAD_FOLDER = '/tmp/uploads'
    else:
        UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
        
    QUESTION_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, 'questions')
    SUBMISSION_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, 'submissions')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max limit
