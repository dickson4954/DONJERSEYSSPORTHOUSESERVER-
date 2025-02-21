from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager  
from .config import Config
from .extensions import db, migrate
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Configure CORS to allow requests from frontend
    CORS(app, resources={r"/*": {"origins": [ "https://dickson4954.github.io", "http://localhost:5000"]}},
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"],
     supports_credentials=True)

    jwt = JWTManager(app)

    # blueprint registration 
    from .auth_routes import auth_bp
    from .admin_routes import admin_bp
    from .product_routes import product_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(product_bp)

    return app
