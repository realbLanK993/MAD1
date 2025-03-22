from flask import Flask
from flask_login import LoginManager
from .models import db, User
from .controllers.auth import auth_bp
from .controllers.admin import admin_bp
from .controllers.user import user_bp
from .controllers.main import main_bp
def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.sqlite3"  # Point to instance folder
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "your_secret_key_here"  # Required for sessions/Flask-Login

    # Initialize extensions
    db.init_app(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login" 

    #Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(main_bp)
    # Create tables and admin user
    with app.app_context():
        db.create_all()
        # Add admin if not exists
        if not User.query.filter_by(email="admin@example.com").first():
            admin = User(
                role="admin",
                username="admin",
                email="admin@example.com",
                full_name="Quiz Master",
                qualification="Admin",
                dob="1990-01-01",  # String for simplicity, parsed in model
                password="admin123"  # Will be hashed in set_password_hash
            )
            db.session.add(admin)
            db.session.commit()

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app
