from datetime import datetime

from models import db


class Cattle(db.Model):
    __tablename__ = "cattle"

    id = db.Column(db.Integer, primary_key=True)
    tag_number = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    breed = db.Column(db.String(80), nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    purchase_date = db.Column(db.Date, nullable=True)
    purchase_cost = db.Column(db.Float, default=0.0)
    current_status = db.Column(db.String(30), default="Milking")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    pregnancies = db.relationship(
        "Pregnancy", back_populates="cattle", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Cattle {self.tag_number}>"
