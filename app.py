import os
import functools
from flask import (
    Flask, render_template, request, redirect, url_for, flash, session, jsonify
)
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from models import db, User, Interview, Question
from services.pdf_service import extract_text_from_pdf
from services import gemini_service

def create_app():
    app = Flask(__name__)
    
    # App configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'interviewace_secret_key_dev_2026')
    db_path = os.path.join(app.instance_path, 'interviewace.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f'sqlite:///{db_path}')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Upload folder configuration
    upload_dir = os.path.join(app.root_path, 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    os.makedirs(app.instance_path, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = upload_dir
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16 MB max limit

    db.init_app(app)

    with app.app_context():
        db.create_all()
        # Seed default demo account if table is empty
        if not User.query.first():
            demo = User(username='demo_user', email='demo@example.com')
            demo.set_password('password123')
            db.session.add(demo)
            db.session.commit()

    # Authentication Helper Decorator
    def login_required(view):
        @functools.wraps(view)
        def wrapped_view(**kwargs):
            user_id = session.get('user_id')
            if not user_id:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('login', next=request.url))
            
            user = db.session.get(User, user_id)
            if not user:
                session.pop('user_id', None)
                flash('Your session has expired. Please log in again.', 'warning')
                return redirect(url_for('login'))

            return view(**kwargs)
        return wrapped_view

    @app.context_processor
    def inject_user():
        current_user = None
        user_id = session.get('user_id')
        if user_id:
            current_user = db.session.get(User, user_id)
            if not current_user:
                session.pop('user_id', None)
        return dict(current_user=current_user, has_gemini_key=bool(os.environ.get('GEMINI_API_KEY')))

    # --- ROUTES ---

    @app.route('/')
    def index():
        if 'user_id' in session:
            return redirect(url_for('dashboard'))
        return render_template('index.html')

    # Auth: Register
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if 'user_id' in session:
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '').strip()
            confirm_password = request.form.get('confirm_password', '').strip()

            if not username or not email or not password:
                flash('All fields are required.', 'danger')
                return render_template('auth/register.html')

            if password != confirm_password:
                flash('Passwords do not match.', 'danger')
                return render_template('auth/register.html')

            if len(password) < 6:
                flash('Password must be at least 6 characters long.', 'danger')
                return render_template('auth/register.html')

            if User.query.filter_by(username=username).first():
                flash('Username already taken. Please choose another.', 'danger')
                return render_template('auth/register.html')

            if User.query.filter_by(email=email).first():
                flash('Email already registered. Please login.', 'danger')
                return render_template('auth/register.html')

            new_user = User(username=username, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()

            session['user_id'] = new_user.id
            flash(f'Account created successfully! Welcome to InterviewAce AI, {new_user.username}!', 'success')
            return redirect(url_for('dashboard'))

        return render_template('auth/register.html')

    # Auth: Login
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if 'user_id' in session:
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            email_or_user = request.form.get('email_or_user', '').strip()
            password = request.form.get('password', '').strip()

            from sqlalchemy import func
            user = User.query.filter(
                (func.lower(User.email) == email_or_user.lower()) | 
                (func.lower(User.username) == email_or_user.lower())
            ).first()

            if not user or not user.check_password(password):
                flash('Invalid email/username or password.', 'danger')
                return render_template('auth/login.html')

            session['user_id'] = user.id
            flash(f'Welcome back, {user.username}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('dashboard'))

        return render_template('auth/login.html')

    # Auth: Logout
    @app.route('/logout')
    def logout():
        session.pop('user_id', None)
        flash('You have been logged out safely.', 'info')
        return redirect(url_for('index'))

    # Dashboard
    @app.route('/dashboard')
    @login_required
    def dashboard():
        user = db.session.get(User, session['user_id'])
        interviews = Interview.query.filter_by(user_id=user.id).order_by(Interview.created_at.desc()).all()
        
        completed_interviews = [i for i in interviews if i.status == 'completed' and i.overall_score is not None]
        total_interviews = len(completed_interviews)
        avg_score = round(sum(i.overall_score for i in completed_interviews) / total_interviews) if total_interviews > 0 else 0

        # Recent 5 interviews
        recent_interviews = interviews[:5]

        return render_template('dashboard.html', 
                               total_interviews=total_interviews,
                               avg_score=avg_score,
                               recent_interviews=recent_interviews)

    # API: Dashboard Analytics Data for Chart.js
    @app.route('/api/dashboard/analytics')
    @login_required
    def dashboard_analytics():
        user_id = session['user_id']
        interviews = Interview.query.filter_by(user_id=user_id, status='completed')\
                                   .order_by(Interview.created_at.asc()).all()
        
        labels = [i.created_at.strftime('%b %d') for i in interviews]
        scores = [i.overall_score for i in interviews]
        roles = [i.role for i in interviews]

        # Role score breakdown averages
        role_scores = {}
        for i in interviews:
            if i.role not in role_scores:
                role_scores[i.role] = []
            role_scores[i.role].append(i.overall_score or 0)

        role_labels = list(role_scores.keys())
        role_averages = [round(sum(role_scores[r]) / len(role_scores[r])) for r in role_labels]

        return jsonify({
            'trend_labels': labels,
            'trend_scores': scores,
            'role_labels': role_labels,
            'role_averages': role_averages
        })

    # History Page
    @app.route('/history')
    @login_required
    def history():
        user_id = session['user_id']
        interviews = Interview.query.filter_by(user_id=user_id).order_by(Interview.created_at.desc()).all()
        return render_template('history.html', interviews=interviews)

    # Interview Setup View
    @app.route('/interview/setup')
    @login_required
    def interview_setup():
        return render_template('interview/setup.html')

    # API: Create New Interview (Role-based or Resume-based)
    @app.route('/api/interview/create', methods=['POST'])
    @login_required
    def create_interview():
        user_id = session['user_id']
        interview_type = request.form.get('interview_type', 'role') # 'role' or 'resume'

        if interview_type == 'resume':
            if 'resume_file' not in request.files:
                return jsonify({'success': False, 'error': 'No resume file uploaded.'}), 400
            file = request.files['resume_file']
            if file.filename == '':
                return jsonify({'success': False, 'error': 'No file selected.'}), 400
            if not file.filename.lower().endswith('.pdf'):
                return jsonify({'success': False, 'error': 'Only PDF files are supported.'}), 400

            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"user_{user_id}_{filename}")
            file.save(filepath)

            try:
                resume_text = extract_text_from_pdf(filepath)
                generated_qs = gemini_service.generate_resume_questions(resume_text, count=5)
                title = f"Resume Interview - {filename[:20]}"
                role = "Resume Assessment"
                difficulty = "Custom"
            except Exception as e:
                return jsonify({'success': False, 'error': f"Failed to process resume: {str(e)}"}), 400

        else: # Role-based
            role = request.form.get('role', 'Web Developer')
            difficulty = request.form.get('difficulty', 'Medium')
            title = f"{role} ({difficulty})"
            filename = None
            generated_qs = gemini_service.generate_questions(role, difficulty, count=5)

        # Create Interview record
        new_interview = Interview(
            user_id=user_id,
            title=title,
            role=role,
            difficulty=difficulty,
            interview_type=interview_type,
            resume_filename=filename,
            status='in_progress'
        )
        db.session.add(new_interview)
        db.session.flush() # get new_interview.id

        # Insert Questions
        for idx, q_item in enumerate(generated_qs, 1):
            q_record = Question(
                interview_id=new_interview.id,
                question_order=idx,
                question_text=q_item.get('question_text'),
                model_answer=q_item.get('model_answer')
            )
            db.session.add(q_record)

        db.session.commit()

        return jsonify({
            'success': True,
            'interview_id': new_interview.id,
            'redirect_url': url_for('interview_session', interview_id=new_interview.id)
        })

    # Interview Session Page
    @app.route('/interview/<int:interview_id>/session')
    @login_required
    def interview_session(interview_id):
        user_id = session['user_id']
        interview = Interview.query.filter_by(id=interview_id, user_id=user_id).first_or_404()

        if interview.status == 'completed':
            return redirect(url_for('interview_report', interview_id=interview.id))

        return render_template('interview/session.html', interview=interview)

    # API: Save Question Answer Progress
    @app.route('/api/interview/<int:interview_id>/save-answer', methods=['POST'])
    @login_required
    def save_answer(interview_id):
        user_id = session['user_id']
        interview = Interview.query.filter_by(id=interview_id, user_id=user_id).first_or_404()

        data = request.get_json() or {}
        question_id = data.get('question_id')
        user_answer = data.get('user_answer', '').strip()

        question = Question.query.filter_by(id=question_id, interview_id=interview.id).first()
        if question:
            question.user_answer = user_answer
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Question not found'}), 404

    # API: Submit & Evaluate Interview with Gemini AI
    @app.route('/api/interview/<int:interview_id>/submit', methods=['POST'])
    @login_required
    def submit_interview(interview_id):
        user_id = session['user_id']
        interview = Interview.query.filter_by(id=interview_id, user_id=user_id).first_or_404()

        data = request.get_json() or {}
        answers = data.get('answers', {}) # dict of question_id -> user_answer

        # Save answers to questions
        for q in interview.questions:
            q_str_id = str(q.id)
            if q_str_id in answers:
                q.user_answer = answers[q_str_id]

        db.session.commit()

        # Prepare payload for Gemini evaluation
        questions_payload = []
        for q in interview.questions:
            questions_payload.append({
                "question_text": q.question_text,
                "model_answer": q.model_answer or "",
                "user_answer": q.user_answer or ""
            })

        # Run AI Evaluation
        eval_result = gemini_service.evaluate_interview(interview.role, interview.difficulty, questions_payload)

        # Update Interview record with overall score & feedback
        interview.overall_score = eval_result.get('overall_score', 75)
        interview.summary_feedback = eval_result.get('summary_feedback', '')
        interview.strengths = eval_result.get('strengths', [])
        interview.weaknesses = eval_result.get('weaknesses', [])
        interview.status = 'completed'

        # Update individual question scores & feedback
        q_evals = eval_result.get('question_evaluations', [])
        for idx, q in enumerate(interview.questions):
            matching_eval = next((item for item in q_evals if item.get('question_index') == idx), None)
            if matching_eval:
                q.score = matching_eval.get('score', 70)
                q.feedback = matching_eval.get('feedback', '')
                q.improvement_tips = matching_eval.get('improvement_tips', '')

        db.session.commit()

        return jsonify({
            'success': True,
            'report_url': url_for('interview_report', interview_id=interview.id)
        })

    # Interview Evaluation Report Page
    @app.route('/interview/<int:interview_id>/report')
    @login_required
    def interview_report(interview_id):
        user_id = session['user_id']
        interview = Interview.query.filter_by(id=interview_id, user_id=user_id).first_or_404()

        return render_template('interview/report.html', interview=interview)

    # API: Delete Interview
    @app.route('/api/interview/<int:interview_id>', methods=['DELETE'])
    @login_required
    def delete_interview(interview_id):
        user_id = session['user_id']
        interview = Interview.query.filter_by(id=interview_id, user_id=user_id).first_or_404()

        db.session.delete(interview)
        db.session.commit()
        return jsonify({'success': True})

    # API: Dynamically Set/Update Gemini API Key in session or environment
    @app.route('/api/settings/update-api-key', methods=['POST'])
    @login_required
    def update_api_key():
        data = request.get_json() or {}
        api_key = data.get('api_key', '').strip()
        os.environ['GEMINI_API_KEY'] = api_key
        return jsonify({'success': True, 'message': 'Gemini API Key updated successfully!'})

    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
