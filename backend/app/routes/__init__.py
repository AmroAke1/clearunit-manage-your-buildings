def register_blueprints(app):
    from app.routes.auth import auth_bp
    from app.routes.manager import manager_bp
    from app.routes.resident import resident_bp
    from app.routes.api.auth import api_auth_bp
    from app.routes.api.manager import api_manager_bp
    from app.routes.api.resident import api_resident_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(manager_bp, url_prefix='/manager')
    app.register_blueprint(resident_bp, url_prefix='/resident')
    app.register_blueprint(api_auth_bp, url_prefix='/api/auth')
    app.register_blueprint(api_manager_bp, url_prefix='/api/manager')
    app.register_blueprint(api_resident_bp, url_prefix='/api/resident')