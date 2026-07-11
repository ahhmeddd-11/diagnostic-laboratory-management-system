from flask import Flask, render_template
from config import Config
from .routes.auth_routes import auth_bp
from .routes.patient_routes import patient_bp
from .routes.test_routes import test_bp
from .routes.report_routes import report_bp
from .routes.user_routes import user_bp
from .routes.log_routes import log_bp
from .routes.setup_routes import setup_bp
from flask import request, redirect, url_for

def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(Config)

    # Register blueprints for REST endpoints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(patient_bp, url_prefix='/api/patients')
    app.register_blueprint(test_bp, url_prefix='/api/tests')
    app.register_blueprint(report_bp, url_prefix='/api/reports')
    app.register_blueprint(user_bp, url_prefix='/api/users')
    app.register_blueprint(log_bp, url_prefix='/api/logs')
    app.register_blueprint(setup_bp, url_prefix='/api/setup')

    @app.before_request
    def check_setup():
        # Allow static files and setup routes
        if request.path.startswith('/static') or request.path.startswith('/api/setup') or request.path == '/setup':
            return
            
        if not Config.IS_CONFIGURED:
            return redirect('/setup')

    # Frontend routes
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/dashboard')
    def dashboard():
        return render_template('dashboard.html')

    @app.route('/print')
    def print_page():
        return render_template('print_report.html')

    @app.route('/setup')
    def setup_page():
        if Config.IS_CONFIGURED:
            return redirect('/')
        return render_template('setup.html')

    return app
