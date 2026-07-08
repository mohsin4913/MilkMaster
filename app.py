from dotenv import load_dotenv

load_dotenv()
from flask import Flask
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

from config import Config
from models import db
from utils.data_retention import purge_expired_records

migrate = Migrate()
csrf = CSRFProtect()


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    from routes.main import main_bp
    from routes.customers import customers_bp
    from routes.milk_entries import milk_entries_bp
    from routes.payments import payments_bp
    from routes.expenses import expenses_bp
    from routes.cattle import cattle_bp
    from routes.pregnancies import pregnancies_bp
    from routes.reports import reports_bp
    from routes.settings import settings_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(customers_bp)
    app.register_blueprint(milk_entries_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(expenses_bp)
    app.register_blueprint(cattle_bp)
    app.register_blueprint(pregnancies_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(settings_bp)

    with app.app_context():
        db.create_all()
        from models.setting import Setting

        Setting.ensure_defaults()

    @app.before_request
    def remove_expired_records():
        purge_expired_records()

    return app


app = create_app()


if __name__ == "__main__":
    app.run()
