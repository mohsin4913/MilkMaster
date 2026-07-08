from datetime import datetime

from models import db


class MilkEntry(db.Model):
    __tablename__ = "milk_entries"

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    entry_date = db.Column(db.Date, nullable=False)
    morning_litres = db.Column(db.Float, default=0.0, nullable=False)
    evening_litres = db.Column(db.Float, default=0.0, nullable=False)
    total_litres = db.Column(db.Float, default=0.0, nullable=False)
    rate = db.Column(db.Float, default=0.0, nullable=False)
    amount = db.Column(db.Float, default=0.0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    customer = db.relationship("Customer", back_populates="milk_entries")

    __table_args__ = (
        db.UniqueConstraint("customer_id", "entry_date", name="unique_customer_entry_date"),
    )

    def __repr__(self):
        return f"<MilkEntry {self.customer_id} on {self.entry_date}>"
