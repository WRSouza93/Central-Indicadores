def register_blueprints(app):
    """Registrar todos os blueprints da aplicação"""
    
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.indicadores import indicadores_bp
    from app.routes.api import api_bp
    from app.routes.setores import setores_bp
    
    # Registrar blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(indicadores_bp, url_prefix='/indicadores')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(setores_bp, url_prefix='/setores')
    
    # Rota principal
    @app.route('/')
    def index():
        from flask import redirect, url_for
        from flask_login import current_user
        
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.home'))
        return redirect(url_for('auth.login'))
