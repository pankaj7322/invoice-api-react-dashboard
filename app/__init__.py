# app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from config import Config
from app.views import invoice_bp  # Import the blueprint from views




def create_app():
    app = Flask(__name__)
    
    # Configurations for the app
    # app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///invoice.db'  # Or your actual database URI
    # app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize db with the app
    # db.init_app(app)

    CORS(app)
    # Import and register your Blueprint
    from app.views import invoice_bp
    app.register_blueprint(invoice_bp, url_prefix='/api')

    return app