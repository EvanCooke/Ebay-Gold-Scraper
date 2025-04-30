from flask import Flask
from backend.app.routes import notifications_bp, frontend_bp
import os
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key')
    app.config['DEBUG'] = os.getenv('FLASK_ENV', 'development') == 'development'

    # Register blueprints
    app.register_blueprint(notifications_bp)  # API routes
    app.register_blueprint(frontend_bp)  # Frontend routes

    return app