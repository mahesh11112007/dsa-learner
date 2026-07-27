# DSA Learner - Question Answering & Evaluation Platform

An enterprise-grade Flask web application designed for interactive DSA problem solving, diagram attachments, notice boards, automated grading workflows, and score tracking.

## Features
- 🔒 **Controlled Account Management**: Admin creates student user credentials (public self-registration disabled).
- ⚙️ **Account Settings Portal**: Profile customization & self-service password changes.
- 🔑 **Admin Student Password Reset**: Admins can reset student passwords directly from directory.
- 📝 **Question Bank with Diagram Support**: Post questions with text prompts, reference diagrams, max marks, and deadlines.
- ✍️ **Student Answer Submission**: Submit step-by-step code solutions + attach solution photos/diagrams.
- ⭐ **Admin Evaluation Dashboard**: Split-screen grading workspace with preset feedback chips.
- 📢 **Notice Board Banner**: Announcements with category tags.
- 📊 **CSV Grade Sheet Export**: Export class grades in `.csv` format.
- ⏰ **Deadline Expiration Locking**: Automatic submission locking when question deadlines pass.
- 🎨 **Code Syntax Highlighting**: Prism.js dark syntax highlighting.

## Quick Start (Local)

1. Clone repository:
   ```bash
   git clone https://github.com/mahesh11112007/dsa-learner.git
   cd dsa-learner
   ```

2. Create virtual environment & install requirements:
   ```bash
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

3. Initialize database & seed admin accounts:
   ```bash
   python seed_admin.py
   ```

4. Run local server:
   ```bash
   python app.py
   ```
   Open `http://127.0.0.1:5000` in browser.

### Admin Credentials:
- **Username**: `mahesh` | **Password**: `12341234`
- **Username**: `admin`  | **Password**: `admin123`

---

## Deployment (Vercel + Neon Cloud DB)

See detailed deployment instructions in `vercel.json` and project documentation.
