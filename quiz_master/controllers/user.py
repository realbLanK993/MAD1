# quiz_master/user.py
from flask import Blueprint, render_template
from flask_login import login_required

user_bp = Blueprint("user", __name__, url_prefix="/user", template_folder="templates")

@user_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("user/dashboard.html")