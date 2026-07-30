# app/__init__.py

from flask import Flask, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
import os
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
mail = Mail()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///integrity.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    migrate.init_app(app, db)
    mail.init_app(app)
    csrf.init_app(app)
    
    # Register blueprints
    print("Importing auth...")
    from app.auth import auth_bp
    print("✓ auth imported")

    print("Importing students...")
    from app.students import students_bp
    print("✓ students imported")

    print("Importing lecturers...")
    from app.lecturers import lecturers_bp
    print("✓ lecturers imported")

    print("Importing admin...")
    from app.admin import admin_bp
    print("✓ admin imported")
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(students_bp, url_prefix='/students')
    app.register_blueprint(lecturers_bp, url_prefix='/lecturers')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from app.notifications import notifications_bp

    app.register_blueprint(notifications_bp)

    from app.reports import reports_bp

    app.register_blueprint(reports_bp)

    print("Importing settings...")
    from app.settings import settings_bp
    print("✓ settings imported")
    app.register_blueprint(settings_bp)
    

    #routes
    @app.route('/')
    def home():
        return render_template('index.html')
    
    # Create upload directory if not exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    return app


# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    return User.query.get(int(user_id))