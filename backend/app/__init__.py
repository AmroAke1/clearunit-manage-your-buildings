from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_jwt_extended import JWTManager
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()
jwt = JWTManager()


def create_app():
    app = Flask(__name__,
                template_folder='../../frontend/templates',
                static_folder='../../frontend/static')
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    jwt.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    from app.routes import register_blueprints
    register_blueprints(app)

    from app.routes.api.auth import api_auth_bp
    from app.routes.api.manager import api_manager_bp
    from app.routes.api.resident import api_resident_bp
    csrf.exempt(api_auth_bp)
    csrf.exempt(api_manager_bp)
    csrf.exempt(api_resident_bp)

    return app