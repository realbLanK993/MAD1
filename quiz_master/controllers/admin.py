# quiz_master/admin.py
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from quiz_master.models import db, User, Subject, Score, Chapter, Quiz, Question
from sqlalchemy import func
from datetime import datetime, timedelta

admin_bp = Blueprint("admin", __name__, url_prefix="/admin", template_folder="templates")

@admin_bp.route("/dashboard")
@login_required
def dashboard():
    if current_user.role != "admin":
        return redirect(url_for("user.dashboard"))
    
    # Total users (unchanged)
    total_users = User.query.filter_by(role="user").count()

    # Chart 1: Average Score per Quiz
    quiz_scores = db.session.query(
        Quiz.id, Quiz.name, func.avg(Score.total_scored).label('avg_score'), func.count(Score.id).label('attempts')
    ).outerjoin(Score, Quiz.id == Score.quiz_id).group_by(Quiz.id, Quiz.name).all()
    quiz_chart_data = {
        "labels": [quiz.name for quiz in quiz_scores],
        "avg_scores": [float(quiz.avg_score or 0) for quiz in quiz_scores],  # Convert None to 0
        "attempts": [quiz.attempts for quiz in quiz_scores]  # For tooltip or secondary metric
    }

    # Chart 2: User Activity Over Time (last 7 days)
    last_week = datetime.utcnow() - timedelta(days=7)
    activity_data = db.session.query(
        func.date(Score.time_stamp_of_attempt).label('date'),
        func.count(Score.id).label('attempts')
    ).filter(Score.time_stamp_of_attempt >= last_week).group_by(func.date(Score.time_stamp_of_attempt)).all()
    activity_chart_data = {
        "labels": [row.date for row in activity_data],  # Use string directly
        "attempts": [row.attempts for row in activity_data]
    }

    return render_template("admin/dashboard.html", 
                         total_users=total_users, 
                         quiz_chart_data=quiz_chart_data,
                         activity_chart_data=activity_chart_data)

@admin_bp.route("/subjects", methods=["GET", "POST"])
@login_required
def subjects():
    if current_user.role != "admin":
        return redirect(url_for("user.dashboard"))
    
    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")
        
        if not name:
            flash("Subject name is required.", "error")
            return redirect(url_for("admin.subjects"))
        
        new_subject = Subject(name=name, description=description)
        db.session.add(new_subject)
        db.session.commit()
        flash("Subject added successfully!", "success")
        return redirect(url_for("admin.subjects"))
    
    subjects = Subject.query.all()
    subjects_data = []
    for subject in subjects:
        enrolled_count = (
            db.session.query(User)
            .join(Score)
            .join(Quiz)
            .join(Chapter)
            .filter(Chapter.subject_id == subject.id)
            .distinct()
            .count()
        )
        subjects_data.append({
            "id": subject.id,
            "name": subject.name,
            "description": subject.description,
            "chapters_count": len(subject.chapters),
            "enrolled": enrolled_count
        })
    
    return render_template("admin/subjects.html", subjects=subjects_data)

@admin_bp.route("/subject/<int:subject_id>")
@login_required
def subject_detail(subject_id):
    if current_user.role != "admin":
        return redirect(url_for("user.dashboard"))
    
    subject = Subject.query.get_or_404(subject_id)
    chapters = subject.chapters
    return render_template("admin/subject_detail.html", subject=subject, chapters=chapters)

@admin_bp.route("/subject/<int:subject_id>/chapter/add", methods=["POST"])
@login_required
def add_chapter(subject_id):
    if current_user.role != "admin":
        return redirect(url_for("user.dashboard"))
    
    name = request.form.get("name")
    description = request.form.get("description")
    
    if not name:
        flash("Chapter name is required.", "error")
        return redirect(url_for("admin.subject_detail", subject_id=subject_id))
    
    new_chapter = Chapter(name=name, description=description, subject_id=subject_id)
    db.session.add(new_chapter)
    db.session.commit()
    flash("Chapter added successfully!", "success")
    return redirect(url_for("admin.subject_detail", subject_id=subject_id))

@admin_bp.route("/subject/<int:subject_id>/chapter/<int:chapter_id>/edit", methods=["POST"])
@login_required
def edit_chapter(subject_id, chapter_id):
    if current_user.role != "admin":
        return redirect(url_for("user.dashboard"))
    
    chapter = Chapter.query.get_or_404(chapter_id)
    name = request.form.get("name")
    description = request.form.get("description")
    
    if not name:
        flash("Chapter name is required.", "error")
        return redirect(url_for("admin.subject_detail", subject_id=subject_id))
    
    chapter.name = name
    chapter.description = description
    db.session.commit()
    flash("Chapter updated successfully!", "success")
    return redirect(url_for("admin.subject_detail", subject_id=subject_id))

@admin_bp.route("/subject/<int:subject_id>/chapter/<int:chapter_id>/delete", methods=["POST"])
@login_required
def delete_chapter(subject_id, chapter_id):
    if current_user.role != "admin":
        return redirect(url_for("user.dashboard"))
    
    chapter = Chapter.query.get_or_404(chapter_id)
    db.session.delete(chapter)
    db.session.commit()
    flash("Chapter deleted successfully!", "success")
    return redirect(url_for("admin.subject_detail", subject_id=subject_id))

@admin_bp.route("/quizzes", methods=["GET", "POST"])
@login_required
def quizzes():
    if current_user.role != "admin":
        return redirect(url_for("user.dashboard"))
    
    if request.method == "POST":
        name = request.form.get("name")
        chapter_id = request.form.get("chapter_id")
        time_duration = request.form.get("time_duration")
        
        if not name or not chapter_id:
            flash("Quiz name and chapter are required.", "error")
            return redirect(url_for("admin.quizzes"))
        
        # Optional: Validate time_duration format (HH:MM)
        if time_duration and not (len(time_duration) == 5 and time_duration[2] == ':' and time_duration[:2].isdigit() and time_duration[3:].isdigit()):
            flash("Time duration must be in HH:MM format (e.g., 01:30).", "error")
            return redirect(url_for("admin.quizzes"))
        
        new_quiz = Quiz(name=name, chapter_id=chapter_id, time_duration=time_duration)
        db.session.add(new_quiz)
        db.session.commit()
        flash("Quiz added successfully!", "success")
        return redirect(url_for("admin.quizzes"))
    
    # Fetch and serialize quizzes
    quizzes = Quiz.query.all()
    quizzes_data = []
    for quiz in quizzes:
        chapter = Chapter.query.get(quiz.chapter_id)  # Explicitly fetch chapter
        subject = Subject.query.get(chapter.subject_id)
        quizzes_data.append({
            "id": quiz.id,
            "name": quiz.name,
            "chapter_name": chapter.name if chapter else "Unknown",
            "subject_name": subject.name if subject else "Unknown",
            "time_duration": quiz.time_duration,
            "questions_count": len(quiz.questions)
        })
    
    subjects = Subject.query.all()
    return render_template("admin/quizzes.html", quizzes=quizzes_data, subjects=subjects)

@admin_bp.route("/quiz/<int:quiz_id>")
@login_required
def quiz_detail(quiz_id):
    if current_user.role != "admin":
        return redirect(url_for("user.dashboard"))
    
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = quiz.questions
    return render_template("admin/quiz_detail.html", quiz=quiz, questions=questions)

@admin_bp.route("/quiz/<int:quiz_id>/question/add", methods=["POST"])
@login_required
def add_question(quiz_id):
    if current_user.role != "admin":
        return redirect(url_for("user.dashboard"))
    
    text = request.form.get("text")
    option1 = request.form.get("option1")
    option2 = request.form.get("option2")
    option3 = request.form.get("option3")
    option4 = request.form.get("option4")
    correct_option = request.form.get("correct_option")
    
    if not all([text, option1, option2, correct_option]):
        flash("Question text, at least two options, and correct option are required.", "error")
        return redirect(url_for("admin.quiz_detail", quiz_id=quiz_id))
    
    correct_option = int(correct_option)
    if correct_option not in [1, 2, 3, 4]:
        flash("Correct option must be 1, 2, 3, or 4.", "error")
        return redirect(url_for("admin.quiz_detail", quiz_id=quiz_id))
    
    new_question = Question(
        question_statement=text,
        option1=option1,
        option2=option2,
        option3=option3,
        option4=option4,
        correct_option=correct_option,
        quiz_id=quiz_id
    )
    db.session.add(new_question)
    db.session.commit()
    flash("Question added successfully!", "success")
    return redirect(url_for("admin.quiz_detail", quiz_id=quiz_id))
