from flask import Flask
from backend.app.routes import notifications_bp, frontend_bp
from backend.instance.config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config) # Load configuration from Config class

    # Register blueprints
    app.register_blueprint(notifications_bp)  # API routes
    app.register_blueprint(frontend_bp)  # Frontend routes

    return app