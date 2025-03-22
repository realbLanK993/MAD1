from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from quiz_master.models import db, Quiz, Chapter, Subject, Question, Score
from datetime import datetime
from datetime import timedelta
from sqlalchemy import func

user_bp = Blueprint("user", __name__, url_prefix="/user", template_folder="templates")

@user_bp.route("/dashboard")
@login_required
def dashboard():
    if current_user.role == "admin":
        return redirect(url_for("admin.dashboard"))
    
    quizzes = Quiz.query.all()
    quizzes_data = []
    for idx, quiz in enumerate(quizzes, start=1):
        chapter = Chapter.query.get(quiz.chapter_id)
        subject = Subject.query.get(chapter.subject_id) if chapter else None
        quizzes_data.append({
            "sl_no": idx,
            "id": quiz.id,
            "name": quiz.name,
            "duration": quiz.time_duration or "Not set",
            "questions_count": len(quiz.questions),
            "chapter_name": chapter.name if chapter else "Unknown",
            "subject_name": subject.name if subject else "Unknown"
        })
    
    return render_template("user/dashboard.html", user=current_user, quizzes=quizzes_data)

@user_bp.route("/attempt_quiz/<int:quiz_id>", methods=["GET", "POST"])
@login_required
def attempt_quiz(quiz_id):
    if current_user.role == "admin":
        return redirect(url_for("admin.dashboard"))
    
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = quiz.questions

    if not questions:
        flash("This quiz has no questions yet.", "warning")
        return redirect(url_for("user.dashboard"))

    if request.method == "POST":
        total_correct = 0
        for question in questions:
            user_answer = request.form.get(f"question_{question.id}")
            if user_answer and int(user_answer) == question.correct_option:
                total_correct += 1
        
        # Save the score with timestamp
        score = Score(
            quiz_id=quiz.id,
            user_id=current_user.id,
            time_stamp_of_attempt=datetime.utcnow(),  # Required field
            total_scored=total_correct
        )
        db.session.add(score)
        db.session.commit()
        
        flash(f"Quiz submitted! You scored {total_correct} out of {len(questions)}.", "success")
        return redirect(url_for("user.dashboard"))

    # Serialize questions for GET request
    questions_data = []
    for question in questions:
        options = [
            question.option1,
            question.option2,
            question.option3 if question.option3 else None,
            question.option4 if question.option4 else None
        ]
        questions_data.append({
            "id": question.id,
            "question_statement": question.question_statement,  # Updated attribute
            "options": [opt for opt in options if opt is not None]  # Filter out None options
        })
    
    return render_template("user/attempt_quiz.html", quiz=quiz, questions=questions_data)
@user_bp.route("/summary")
@login_required
def summary():
    if current_user.role == "admin":
        return redirect(url_for("admin.dashboard"))
    
    # Stats
    total_attempts = Score.query.filter_by(user_id=current_user.id).count()
    avg_score = db.session.query(func.avg(Score.total_scored)).filter_by(user_id=current_user.id).scalar() or 0
    quizzes_attempted = Score.query.filter_by(user_id=current_user.id).join(Quiz).distinct(Quiz.id).count()

    # Chart: Scores Over Time
    score_data = Score.query.filter_by(user_id=current_user.id).join(Quiz).order_by(Score.time_stamp_of_attempt).all()
    chart_data = {
        "labels": [score.time_stamp_of_attempt.strftime('%Y-%m-%d') for score in score_data],
        "scores": [score.total_scored for score in score_data],
        "quiz_names": [score.quiz.name for score in score_data]  # For tooltips
    }

    return render_template("user/summary.html", 
                         user=current_user,
                         total_attempts=total_attempts,
                         avg_score=round(avg_score, 2),
                         quizzes_attempted=quizzes_attempted,
                         chart_data=chart_data)
