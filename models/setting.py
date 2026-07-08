from models import db


class Setting(db.Model):
    __tablename__ = "settings"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.String(255), nullable=False)

    @staticmethod
    def ensure_defaults():
        defaults = {
            "default_milk_rate": "55",
            "currency": "INR",
            "theme": "light",
            "language": "en",
            "retention_days": "60",
        }
        for key, value in defaults.items():
            existing = Setting.query.filter_by(key=key).first()
            if not existing:
                db.session.add(Setting(key=key, value=value))
        db.session.commit()

    @staticmethod
    def get_value(key, default=None):
        setting = Setting.query.filter_by(key=key).first()
        return setting.value if setting else default

    @staticmethod
    def set_value(key, value):
        setting = Setting.query.filter_by(key=key).first()
        if setting:
            setting.value = value
        else:
            setting = Setting(key=key, value=value)
            db.session.add(setting)
        db.session.commit()
