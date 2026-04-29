def register_blueprints(app):
    from app.routes.auth import auth_bp
    from app.routes.manager import manager_bp
    from app.routes.resident import resident_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(manager_bp, url_prefix='/manager')
    app.register_blueprint(resident_bp, url_prefix='/resident')