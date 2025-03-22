from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, current_user, logout_user  # Added Flask-Login functions
from quiz_master.models import db, User  # Adjust import based on your package
from datetime import datetime

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# Register route (from previous response)
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        role = "user"  # Default to "user" since admin shouldn’t register
        username = request.form.get("username")
        email = request.form.get("email")
        full_name = request.form.get("full_name")
        qualification = request.form.get("qualification")
        dob = request.form.get("dob")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if not all([username, email, full_name, qualification, dob, password, confirm_password]):
            flash("All fields are required.", "error")
            return render_template("auth/register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("auth/register.html")

        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "error")
            return render_template("auth/register.html")

        try:
            new_user = User(
                role=role,
                username=username,
                email=email,
                full_name=full_name,
                qualification=qualification,
                dob=dob,
                password=password
            )
            db.session.add(new_user)
            db.session.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("auth.login"))
        except ValueError as e:
            flash(f"Invalid date of birth format: {str(e)}. Use YYYY-MM-DD.", "error")
            return render_template("auth/register.html")
        except Exception as e:
            flash(f"An error occurred: {str(e)}", "error")
            return render_template("auth/register.html")
    return render_template("auth/register.html")

# Login route
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # If user is already logged in, redirect to appropriate dashboard
    if current_user.is_authenticated:
        if current_user.role == "admin":
            return redirect(url_for("admin.dashboard"))  # Assumes an admin blueprint/route
        return redirect(url_for("user.dashboard"))  # Assumes a user blueprint/route

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # Basic validation
        if not email or not password:
            flash("Email and password are required.", "error")
            return render_template("auth/login.html")

        # Find user by email
        user = User.query.filter_by(email=email).first()

        # Check credentials
        if user and user.check_password(password):
            login_user(user)  # Log the user in with Flask-Login
            flash("Logged in successfully!", "success")
            # Redirect based on role
            if user.role == "admin":
                return redirect(url_for("admin.dashboard"))
            return redirect(url_for("user.dashboard"))
        else:
            flash("Invalid email or password.", "danger")
            return render_template("auth/login.html")

    # GET request: Render the login form
    return render_template("auth/login.html")

# Optional: Logout route
@auth_bp.route("/logout")
def logout():
    logout_user()  # Clear the user session
    flash("Logged out successfully.", "success")
    return redirect(url_for("main.landing"))
