from flask import Flask
from app.models import db
import os
import urllib.parse

def create_app(test_config=None):
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///project_v2.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = os.environ.get('SECRET_KEY', 'default-secret-key-for-dev')

    use_sqlserver = os.environ.get("USE_SQLSERVER", "0") == "1"
    if use_sqlserver:
        sqlserver_conn = (
            "Driver={ODBC Driver 17 for SQL Server};"
            "Server=(localdb)\\MSSQLLocalDB;"
            "Database=ANTE_ACADEMIC;"
            "Trusted_Connection=yes;"
        )
        app.config["SQLALCHEMY_DATABASE_URI"] = (
            "mssql+pyodbc:///?odbc_connect=" + urllib.parse.quote_plus(sqlserver_conn)
        )

    # explicit override (if user provides full SQLAlchemy URL)
    if os.environ.get("DATABASE_URL"):
        app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]

    if test_config:
        app.config.update(test_config)

    db.init_app(app)

    # Register blueprints
    from app.routes.intro import intro_bp
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.pipeline import pipeline_bp
    from app.routes.exercise import exercise_bp
    from app.routes.progress import progress_bp
    from app.routes.lecturer import lecturer_bp
    
    app.register_blueprint(intro_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(pipeline_bp)
    app.register_blueprint(exercise_bp)
    app.register_blueprint(progress_bp)
    app.register_blueprint(lecturer_bp)

    with app.app_context():
        db.create_all()
        from app.services.db_init import ensure_schema_compatibility
        from app.seed import bootstrap_database

        ensure_schema_compatibility()
        bootstrap_database()

    return app

