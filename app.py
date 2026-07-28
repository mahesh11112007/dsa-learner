import os
import csv
import io
import json
from functools import wraps
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, abort, send_from_directory, Response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename

from config import Config
from database import db
from models import User, Question, Submission, Notice, StudyNote

app = Flask(__name__)
app.config.from_object(Config)
app.url_map.strict_slashes = False

# Initialize extensions
db.init_app(app)

_db_initialized = False

def ensure_db_initialized():
    global _db_initialized
    if _db_initialized:
        return
    _db_initialized = True
    
    try:
        os.makedirs(app.config['QUESTION_UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(app.config['SUBMISSION_UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(app.config['NOTE_UPLOAD_FOLDER'], exist_ok=True)
    except Exception:
        pass

    try:
        db.create_all()
        if not User.query.filter_by(role='admin').first():
            mahesh = User(username='mahesh', full_name='Mahesh', role='admin')
            mahesh.set_password('12341234')
            db.session.add(mahesh)
            
            admin_user = User(username='admin', full_name='System Administrator', role='admin')
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            
            db.session.commit()
            print("[INFO] Auto-seeded default admin users into database.")
    except Exception as e:
        print(f"[Warning] DB initialization note: {e}")

@app.before_request
def before_request():
    ensure_db_initialized()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except Exception:
        return None

# Admin Access Decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Access denied. Administrator privileges required.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Upload Helper
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def save_file(file, target_folder):
    if file and file.filename != '' and allowed_file(file.filename):
        os.makedirs(target_folder, exist_ok=True)
        filename = secure_filename(file.filename)
        # Add timestamp prefix to avoid filename collisions
        unique_filename = f"{int(datetime.utcnow().timestamp())}_{filename}"
        filepath = os.path.join(target_folder, unique_filename)
        file.save(filepath)
        return unique_filename
    return None

# ==================== MAIN ROUTES ====================

@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('student_dashboard'))
    return redirect(url_for('login'))

# Auth Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash(f'Welcome, {user.full_name}!', 'success')
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password. Please try again.', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

# ==================== ADMIN ROUTES ====================

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    total_users = User.query.filter_by(role='student').count()
    total_questions = Question.query.count()
    pending_submissions = Submission.query.filter_by(status='submitted').count()
    graded_submissions = Submission.query.filter_by(status='graded').count()
    
    recent_submissions = Submission.query.order_by(Submission.submitted_at.desc()).limit(5).all()
    notices = Notice.query.order_by(Notice.created_at.desc()).all()
    
    return render_template('admin/dashboard.html',
                           total_users=total_users,
                           total_questions=total_questions,
                           pending_submissions=pending_submissions,
                           graded_submissions=graded_submissions,
                           recent_submissions=recent_submissions,
                           notices=notices)

@app.route('/admin/notices/add', methods=['POST'])
@login_required
@admin_required
def add_notice():
    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    category = request.form.get('category', 'General')
    
    if not title or not content:
        flash('Title and notice content are required.', 'danger')
    else:
        notice = Notice(
            title=title,
            content=content,
            category=category,
            created_by_id=current_user.id
        )
        db.session.add(notice)
        db.session.commit()
        flash('Announcement posted to Notice Board successfully!', 'success')
        
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/notices/<int:notice_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_notice(notice_id):
    notice = db.session.get(Notice, notice_id) or abort(404)
    db.session.delete(notice)
    db.session.commit()
    flash('Notice deleted from Notice Board.', 'info')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/users', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_users():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        full_name = request.form.get('full_name', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', 'student')
        
        if not username or not full_name or not password:
            flash('All fields (username, full name, password) are required.', 'danger')
        elif User.query.filter_by(username=username).first():
            flash('An account with this username already exists.', 'warning')
        else:
            new_user = User(username=username, full_name=full_name, role=role)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash(f'Account for "{full_name}" ({username}) created successfully!', 'success')
            return redirect(url_for('admin_users'))
            
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot delete your own admin account.', 'danger')
        return redirect(url_for('admin_users'))
        
    db.session.delete(user)
    db.session.commit()
    flash(f'User "{user.username}" deleted successfully.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/questions', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_questions():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        try:
            max_marks = float(request.form.get('max_marks', 10.0))
        except ValueError:
            max_marks = 10.0
            
        due_date_str = request.form.get('due_date', '').strip()
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                pass

        category = request.form.get('category', 'General').strip()
        solution_hint = request.form.get('solution_hint', '').strip()

        file = request.files.get('image')
        image_filename = save_file(file, app.config['QUESTION_UPLOAD_FOLDER'])
        
        if not title or not description:
            flash('Title and question description are required.', 'danger')
        else:
            question = Question(
                title=title,
                description=description,
                image_filename=image_filename,
                max_marks=max_marks,
                due_date=due_date,
                category=category,
                solution_hint=solution_hint,
                created_by_id=current_user.id
            )
            db.session.add(question)
            db.session.commit()
            flash(f'Question "{title}" created successfully!', 'success')
            return redirect(url_for('admin_questions'))

    questions = Question.query.order_by(Question.created_at.desc()).all()
    return render_template('admin/questions.html', questions=questions)

@app.route('/admin/questions/bulk_import', methods=['POST'])
@login_required
@admin_required
def bulk_import_questions():
    json_text = request.form.get('json_text', '').strip()
    json_file = request.files.get('json_file')
    
    raw_content = ""
    if json_file and json_file.filename:
        try:
            raw_content = json_file.read().decode('utf-8')
        except Exception as e:
            flash(f'Error reading JSON file: {e}', 'danger')
            return redirect(url_for('admin_questions'))
    elif json_text:
        raw_content = json_text
        
    if not raw_content:
        flash('Please paste JSON text or upload a .json file.', 'warning')
        return redirect(url_for('admin_questions'))
        
    try:
        # Clean markdown codeblocks if AI returned ```json ... ```
        cleaned = raw_content.replace('```json', '').replace('```', '').strip()
        data = json.loads(cleaned)
        
        questions_list = []
        if isinstance(data, list):
            questions_list = data
        elif isinstance(data, dict):
            questions_list = data.get('questions', data.get('data', [data]))
            
        if not questions_list or not isinstance(questions_list, list):
            flash('No valid questions array found in JSON payload.', 'warning')
            return redirect(url_for('admin_questions'))
            
        count = 0
        for item in questions_list:
            if not isinstance(item, dict):
                continue
            title = str(item.get('title', '')).strip()
            description = str(item.get('description', '')).strip()
            if not title or not description:
                continue
                
            category = str(item.get('category', 'General')).strip()
            try:
                max_marks = float(item.get('max_marks', 10.0))
            except (ValueError, TypeError):
                max_marks = 10.0
                
            solution_hint = str(item.get('solution_hint') or item.get('sample_answer_key') or item.get('solution') or '').strip()
            
            q = Question(
                title=title,
                description=description,
                max_marks=max_marks,
                category=category,
                solution_hint=solution_hint,
                created_by_id=current_user.id
            )
            db.session.add(q)
            count += 1
            
        db.session.commit()
        flash(f'Successfully bulk-imported {count} questions!', 'success')
    except json.JSONDecodeError as e:
        flash(f'Invalid JSON format: {e}', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Bulk import error: {e}', 'danger')
        
    return redirect(url_for('admin_questions'))

@app.route('/admin/questions/<int:question_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_question(question_id):
    question = Question.query.get_or_404(question_id)
    db.session.delete(question)
    db.session.commit()
    flash(f'Question "{question.title}" deleted.', 'success')
    return redirect(url_for('admin_questions'))

@app.route('/admin/submissions')
@login_required
@admin_required
def admin_submissions():
    status_filter = request.args.get('status', 'all')
    query = Submission.query.order_by(Submission.submitted_at.desc())
    
    if status_filter == 'pending':
        query = query.filter_by(status='submitted')
    elif status_filter == 'graded':
        query = query.filter_by(status='graded')
        
    submissions = query.all()
    return render_template('admin/grade_list.html', submissions=submissions, status_filter=status_filter)

@app.route('/admin/submissions/<int:submission_id>/grade', methods=['GET', 'POST'])
@login_required
@admin_required
def grade_submission(submission_id):
    submission = Submission.query.get_or_404(submission_id)
    question = submission.question
    
    if request.method == 'POST':
        try:
            marks = float(request.form.get('marks_awarded', 0))
            if marks < 0 or marks > question.max_marks:
                flash(f'Marks awarded must be between 0 and {question.max_marks}.', 'warning')
                return redirect(url_for('grade_submission', submission_id=submission_id))
        except ValueError:
            flash('Please enter a valid numeric value for marks.', 'danger')
            return redirect(url_for('grade_submission', submission_id=submission_id))
            
        feedback = request.form.get('feedback', '').strip()
        
        submission.marks_awarded = marks
        submission.feedback = feedback
        submission.status = 'graded'
        submission.graded_at = datetime.utcnow()
        
        db.session.commit()
        flash(f'Graded submission for {submission.student.full_name}: {marks}/{question.max_marks} marks awarded.', 'success')
        return redirect(url_for('admin_submissions'))
        
    return render_template('admin/grade_item.html', submission=submission, question=question)

# ==================== STUDENT ROUTES ====================

@app.route('/student')
@login_required
def student_dashboard():
    if current_user.is_admin():
        return redirect(url_for('admin_dashboard'))
        
    questions = Question.query.order_by(Question.created_at.desc()).all()
    student_submissions = Submission.query.filter_by(student_id=current_user.id).all()
    submissions_by_q = {sub.question_id: sub for sub in student_submissions}
    
    total_earned = sum(sub.marks_awarded for sub in student_submissions if sub.marks_awarded is not None)
    total_possible = sum(sub.question.max_marks for sub in student_submissions if sub.marks_awarded is not None)
    
    notices = Notice.query.order_by(Notice.created_at.desc()).all()
    
    return render_template('student/dashboard.html',
                           questions=questions,
                           submissions_by_q=submissions_by_q,
                           total_earned=total_earned,
                           total_possible=total_possible,
                           notices=notices)

# Settings Route (Profile & Security)
@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        action = request.form.get('action', 'change_password')
        
        if action == 'update_profile':
            full_name = request.form.get('full_name', '').strip()
            if not full_name:
                flash('Full name cannot be empty.', 'danger')
            else:
                current_user.full_name = full_name
                db.session.commit()
                flash('Profile information updated successfully!', 'success')
                return redirect(url_for('settings'))
                
        elif action == 'change_password':
            current_pwd = request.form.get('current_password', '')
            new_pwd = request.form.get('new_password', '')
            confirm_pwd = request.form.get('confirm_password', '')
            
            if not current_user.check_password(current_pwd):
                flash('Incorrect current password.', 'danger')
            elif not new_pwd or len(new_pwd) < 6:
                flash('New password must be at least 6 characters long.', 'warning')
            elif new_pwd != confirm_pwd:
                flash('New passwords do not match.', 'danger')
            else:
                current_user.set_password(new_pwd)
                db.session.commit()
                flash('Your password has been updated successfully!', 'success')
                return redirect(url_for('settings'))
                
    return render_template('settings.html')

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_pwd = request.form.get('current_password', '')
        new_pwd = request.form.get('new_password', '')
        confirm_pwd = request.form.get('confirm_password', '')
        
        if not current_user.check_password(current_pwd):
            flash('Incorrect current password.', 'danger')
        elif not new_pwd or len(new_pwd) < 6:
            flash('New password must be at least 6 characters long.', 'warning')
        elif new_pwd != confirm_pwd:
            flash('New passwords do not match.', 'danger')
        else:
            current_user.set_password(new_pwd)
            db.session.commit()
            flash('Your password has been updated successfully!', 'success')
            return redirect(url_for('settings'))
            
        return redirect(url_for('settings'))
    return redirect(url_for('settings'))

# Admin Student Password Reset
@app.route('/admin/users/<int:user_id>/reset_password', methods=['POST'])
@login_required
@admin_required
def admin_reset_password(user_id):
    user = db.session.get(User, user_id) or abort(404)
    new_pwd = request.form.get('new_password', '').strip()
    if not new_pwd or len(new_pwd) < 6:
        flash('Password must be at least 6 characters.', 'warning')
    else:
        user.set_password(new_pwd)
        db.session.commit()
        flash(f'Password for student "{user.full_name}" (@{user.username}) reset successfully!', 'success')
        
    return redirect(url_for('admin_users'))

# CSV Grade Report Export
@app.route('/admin/export_csv')
@login_required
@admin_required
def export_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'Student Username', 'Student Name', 'Question Title',
        'Max Marks', 'Marks Awarded', 'Status',
        'Submitted At', 'Graded At', 'Teacher Feedback'
    ])
    
    submissions = Submission.query.order_by(Submission.submitted_at.desc()).all()
    for sub in submissions:
        writer.writerow([
            sub.student.username,
            sub.student.full_name,
            sub.question.title,
            sub.question.max_marks,
            sub.marks_awarded if sub.marks_awarded is not None else 'N/A',
            sub.status,
            sub.submitted_at.strftime('%Y-%m-%d %H:%M:%S') if sub.submitted_at else '',
            sub.graded_at.strftime('%Y-%m-%d %H:%M:%S') if sub.graded_at else '',
            sub.feedback or ''
        ])
        
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=dsa_qa_grades_report.csv'}
    )

@app.route('/student/questions/<int:question_id>', methods=['GET', 'POST'])
@login_required
def question_detail(question_id):
    if current_user.is_admin():
        flash('Admins do not submit test answers.', 'info')
        return redirect(url_for('admin_questions'))
        
    question = Question.query.get_or_404(question_id)
    existing_submission = Submission.query.filter_by(question_id=question_id, student_id=current_user.id).first()
    
    if request.method == 'POST':
        if question.is_past_due():
            flash('The deadline for this question has passed. Submissions are closed.', 'danger')
            return redirect(url_for('question_detail', question_id=question_id))

        answer_text = request.form.get('answer_text', '').strip()
        file = request.files.get('image')
        image_filename = save_file(file, app.config['SUBMISSION_UPLOAD_FOLDER'])
        
        if not answer_text and not image_filename:
            flash('You must provide either a text answer or upload an answer image/diagram.', 'danger')
            return redirect(url_for('question_detail', question_id=question_id))
            
        if existing_submission:
            # Update existing submission
            existing_submission.answer_text = answer_text
            if image_filename:
                existing_submission.image_filename = image_filename
            existing_submission.status = 'submitted'
            existing_submission.submitted_at = datetime.utcnow()
            flash('Your submission has been updated!', 'success')
        else:
            # Create new submission
            new_sub = Submission(
                question_id=question_id,
                student_id=current_user.id,
                answer_text=answer_text,
                image_filename=image_filename,
                status='submitted'
            )
            db.session.add(new_sub)
            flash('Your answer has been submitted successfully!', 'success')
            
        db.session.commit()
        return redirect(url_for('student_dashboard'))
        
    return render_template('student/question_detail.html', question=question, submission=existing_submission)

@app.route('/student/submissions')
@login_required
def my_submissions():
    if current_user.is_admin():
        return redirect(url_for('admin_submissions'))
        
    submissions = Submission.query.filter_by(student_id=current_user.id).order_by(Submission.submitted_at.desc()).all()
    return render_template('student/my_submissions.html', submissions=submissions)

# Study Notes Routes
@app.route('/notes')
@login_required
def notes_index():
    category = request.args.get('category', '').strip()
    search = request.args.get('search', '').strip()
    
    query = StudyNote.query
    if category:
        query = query.filter_by(category=category)
    if search:
        query = query.filter(StudyNote.title.ilike(f'%{search}%') | StudyNote.content.ilike(f'%{search}%'))
        
    notes = query.order_by(StudyNote.created_at.desc()).all()
    categories = [r[0] for r in db.session.query(StudyNote.category).distinct().all() if r[0]]
    
    return render_template('notes/index.html', notes=notes, categories=categories, selected_category=category, search=search)

@app.route('/notes/<int:note_id>')
@login_required
def note_detail(note_id):
    note = StudyNote.query.get_or_404(note_id)
    return render_template('notes/detail.html', note=note)

@app.route('/admin/notes', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_notes():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        category = request.form.get('category', 'General').strip()
        
        file = request.files.get('attachment')
        attachment_filename = save_file(file, app.config['NOTE_UPLOAD_FOLDER'])
        
        if not title or not content:
            flash('Title and note content are required.', 'danger')
        else:
            note = StudyNote(
                title=title,
                content=content,
                category=category,
                attachment_filename=attachment_filename,
                created_by_id=current_user.id
            )
            db.session.add(note)
            db.session.commit()
            flash(f'Study Note "{title}" published successfully!', 'success')
            return redirect(url_for('admin_notes'))
            
    notes = StudyNote.query.order_by(StudyNote.created_at.desc()).all()
    return render_template('admin/manage_notes.html', notes=notes)

@app.route('/admin/notes/<int:note_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_note(note_id):
    note = StudyNote.query.get_or_404(note_id)
    db.session.delete(note)
    db.session.commit()
    flash(f'Study Note "{note.title}" deleted.', 'success')
    return redirect(url_for('admin_notes'))

@app.route('/admin/notes/bulk_import', methods=['POST'])
@login_required
@admin_required
def bulk_import_notes():
    json_text = request.form.get('json_text', '').strip()
    json_file = request.files.get('json_file')
    
    raw_content = ""
    if json_file and json_file.filename:
        try:
            raw_content = json_file.read().decode('utf-8')
        except Exception as e:
            flash(f'Error reading JSON file: {e}', 'danger')
            return redirect(url_for('admin_notes'))
    elif json_text:
        raw_content = json_text
        
    if not raw_content:
        flash('Please paste JSON text or upload a .json file.', 'warning')
        return redirect(url_for('admin_notes'))
        
    try:
        cleaned = raw_content.replace('```json', '').replace('```', '').strip()
        data = json.loads(cleaned)
        
        notes_list = []
        if isinstance(data, list):
            notes_list = data
        elif isinstance(data, dict):
            notes_list = data.get('notes', data.get('data', [data]))
            
        if not notes_list or not isinstance(notes_list, list):
            flash('No valid notes array found in JSON payload.', 'warning')
            return redirect(url_for('admin_notes'))
            
        count = 0
        for item in notes_list:
            if not isinstance(item, dict):
                continue
            title = str(item.get('title', '')).strip()
            content = str(item.get('content', '')).strip()
            if not title or not content:
                continue
                
            category = str(item.get('category', 'General')).strip()
            
            note = StudyNote(
                title=title,
                content=content,
                category=category,
                created_by_id=current_user.id
            )
            db.session.add(note)
            count += 1
            
        db.session.commit()
        flash(f'Successfully bulk-imported {count} study notes!', 'success')
    except json.JSONDecodeError as e:
        flash(f'Invalid JSON format: {e}', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Bulk import error: {e}', 'danger')
        
    return redirect(url_for('admin_notes'))

# Upload File Serving Helpers
@app.route('/uploads/questions/<filename>')
@login_required
def uploaded_question_file(filename):
    return send_from_directory(app.config['QUESTION_UPLOAD_FOLDER'], filename)

@app.route('/uploads/submissions/<filename>')
@login_required
def uploaded_submission_file(filename):
    return send_from_directory(app.config['SUBMISSION_UPLOAD_FOLDER'], filename)

@app.route('/uploads/notes/<filename>')
@login_required
def uploaded_note_file(filename):
    return send_from_directory(app.config['NOTE_UPLOAD_FOLDER'], filename)

# Run app
if __name__ == '__main__':
    os.makedirs(app.config['QUESTION_UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['SUBMISSION_UPLOAD_FOLDER'], exist_ok=True)
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
