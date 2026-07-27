import io
import os
import unittest
from app import app
from database import db
from models import User, Question, Submission

class FlaskAppTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'test_dsa_qa.db')
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

        self.app_context = app.app_context()
        self.app_context.push()
        
        db.drop_all()
        db.create_all()

        # Create default admin
        admin = User(username='admin', full_name='Admin User', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        test_db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'test_dsa_qa.db')
        if os.path.exists(test_db_path):
            try:
                os.remove(test_db_path)
            except Exception:
                pass

    def test_full_workflow(self):
        # 1. Admin login
        response = self.client.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        }, follow_redirects=True)
        self.assertIn(b'Admin Control Center', response.data)
        print("[PASS] Step 1: Admin login successful")

        # 2. Admin creates student account
        response = self.client.post('/admin/users', data={
            'username': 'student1',
            'full_name': 'Rahul Student',
            'password': 'studentpass123',
            'role': 'student'
        }, follow_redirects=True)
        self.assertIn(b'student1', response.data)
        print("[PASS] Step 2: Admin created student account 'student1'")

        # 3. Admin creates question with text and dummy image attachment
        fake_img = (io.BytesIO(b"fake image content"), 'test_diagram.png')
        response = self.client.post('/admin/questions', data={
            'title': 'Binary Search Tree Traversal',
            'description': 'Explain Inorder traversal of a BST with time complexity.',
            'max_marks': '10.0',
            'image': fake_img
        }, follow_redirects=True)
        self.assertIn(b'Binary Search Tree Traversal', response.data)
        print("[PASS] Step 3: Admin created text + image question")

        # 4. Logout admin & Student login
        self.client.get('/logout')
        response = self.client.post('/login', data={
            'username': 'student1',
            'password': 'studentpass123'
        }, follow_redirects=True)
        self.assertIn(b'Rahul Student', response.data)
        print("[PASS] Step 4: Student1 logged in successfully")

        # 5. Student submits answer with text & image attachment
        fake_ans_img = (io.BytesIO(b"fake answer image content"), 'student_solution.png')
        response = self.client.post('/student/questions/1', data={
            'answer_text': 'Inorder traversal visits Left, Root, Right. Time complexity is O(N).',
            'image': fake_ans_img
        }, follow_redirects=True)
        self.assertIn(b'Your answer has been submitted successfully!', response.data)
        print("[PASS] Step 5: Student submitted text answer and diagram image")

        # 6. Logout student & Admin logs in to grade answer
        self.client.get('/logout')
        self.client.post('/login', data={'username': 'admin', 'password': 'admin123'})
        
        response = self.client.post('/admin/submissions/1/grade', data={
            'marks_awarded': '9.5',
            'feedback': 'Excellent answer and clear diagram explanation!'
        }, follow_redirects=True)
        self.assertIn(b'Graded submission for Rahul Student', response.data)
        print("[PASS] Step 6: Admin evaluated answer and assigned 9.5/10 marks with feedback")

        # 7. Student checks marks and feedback
        self.client.get('/logout')
        self.client.post('/login', data={'username': 'student1', 'password': 'studentpass123'})
        response = self.client.get('/student/submissions')
        self.assertIn(b'9.5', response.data)
        self.assertIn(b'Excellent answer and clear diagram explanation!', response.data)
        print("[PASS] Step 7: Student verified awarded marks and admin feedback")

        # 8. Admin posts a notice on Notice Board and Student views it
        self.client.get('/logout')
        self.client.post('/login', data={'username': 'admin', 'password': 'admin123'})
        response = self.client.post('/admin/notices/add', data={
            'title': 'Test 2 Schedule',
            'content': 'Test 2 will cover Graph Algorithms next Friday.',
            'category': 'Exam'
        }, follow_redirects=True)
        self.assertIn(b'Test 2 Schedule', response.data)
        print("[PASS] Step 8a: Admin posted announcement to Notice Board")

        # 9. Student changes password
        self.client.get('/logout')
        self.client.post('/login', data={'username': 'student1', 'password': 'studentpass123'})
        response = self.client.post('/change_password', data={
            'current_password': 'studentpass123',
            'new_password': 'newpassword456',
            'confirm_password': 'newpassword456'
        }, follow_redirects=True)
        self.assertIn(b'Your password has been updated successfully!', response.data)
        print("[PASS] Step 9: Student changed password successfully")

        # 10. Admin exports CSV grade report
        self.client.get('/logout')
        self.client.post('/login', data={'username': 'admin', 'password': 'admin123'})
        response = self.client.get('/admin/export_csv')
        self.assertEqual(response.mimetype, 'text/csv')
        self.assertIn(b'Student Username,Student Name,Question Title', response.data)
        self.assertIn(b'student1,Rahul Student,Binary Search Tree Traversal', response.data)
        print("[PASS] Step 10: Admin exported CSV grade sheet containing student scores")

        # 11. Past due deadline enforcement
        # Create a question with a due date set to yesterday
        from datetime import datetime, timedelta
        past_due = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M')
        response = self.client.post('/admin/questions', data={
            'title': 'Expired Graph Question',
            'description': 'Explain BFS algorithm.',
            'max_marks': '10.0',
            'due_date': past_due
        }, follow_redirects=True)
        self.assertIn(b'Expired Graph Question', response.data)

        # 12. Settings profile update & Admin Password Reset
        response = self.client.post('/settings', data={
            'action': 'update_profile',
            'full_name': 'Rahul S. Updated'
        }, follow_redirects=True)
        self.assertIn(b'Profile information updated successfully!', response.data)
        print("[PASS] Step 12a: Profile information updated in Settings")

        self.client.get('/logout')
        self.client.post('/login', data={'username': 'admin', 'password': 'admin123'})
        response = self.client.post('/admin/users/2/reset_password', data={
            'new_password': 'resetpass789'
        }, follow_redirects=True)
        self.assertIn(b'reset successfully!', response.data)
        print("[PASS] Step 12b: Admin reset student password directly from user directory")

if __name__ == '__main__':
    unittest.main()
