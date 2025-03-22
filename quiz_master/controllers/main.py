from flask import Blueprint, render_template
from flask_login import current_user

main_bp = Blueprint("main", __name__, template_folder="templates")

@main_bp.route("/")
def landing():
    return render_template("main/landing.html", user=current_user)
