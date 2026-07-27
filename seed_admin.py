import os
from app import app
from database import db
from models import User

def init_db_and_admin():
    with app.app_context():
        db.create_all()
        
        # Ensure user 'mahesh' exists with password '12341234'
        mahesh = User.query.filter_by(username='mahesh').first()
        if not mahesh:
            mahesh = User(username='mahesh', full_name='Mahesh', role='admin')
            mahesh.set_password('12341234')
            db.session.add(mahesh)
            print("[SUCCESS] Created admin user 'mahesh' (password: 12341234)")
        else:
            mahesh.role = 'admin'
            mahesh.set_password('12341234')
            print("[SUCCESS] Updated admin user 'mahesh' (password: 12341234)")

        # Ensure user 'admin' also exists with password 'admin123'
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(username='admin', full_name='System Administrator', role='admin')
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            print("[SUCCESS] Created admin user 'admin' (password: admin123)")
        else:
            admin_user.role = 'admin'
            admin_user.set_password('admin123')
            print("[SUCCESS] Updated admin user 'admin' (password: admin123)")

        db.session.commit()
        print("[SUCCESS] All admin credentials successfully updated in database!")

if __name__ == '__main__':
    os.makedirs(app.config['QUESTION_UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['SUBMISSION_UPLOAD_FOLDER'], exist_ok=True)
    init_db_and_admin()
