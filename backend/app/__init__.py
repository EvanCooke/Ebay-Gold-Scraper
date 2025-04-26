from flask import Flask
from app.routes import notifications_bp
from app.config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config) # Load configuration from Config class

    # Register blueprints
    app.register_blueprint(notifications_bp)

    return app