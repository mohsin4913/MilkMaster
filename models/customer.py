from datetime import datetime

from models import db


class Customer(db.Model):
    __tablename__ = "customers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    mobile = db.Column(db.String(20), unique=True, nullable=False)
    address = db.Column(db.String(255), nullable=True)
    milk_rate = db.Column(db.Float, default=0.0, nullable=False)
    opening_balance = db.Column(db.Float, default=0.0, nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    milk_entries = db.relationship(
        "MilkEntry", back_populates="customer", cascade="all, delete-orphan"
    )
    payments = db.relationship(
        "Payment", back_populates="customer", cascade="all, delete-orphan"
    )

    def total_amount_due(self):
        total = self.opening_balance + sum(entry.amount for entry in self.milk_entries)
        return round(total, 2)

    def total_paid(self):
        return round(sum(payment.amount for payment in self.payments), 2)

    def outstanding_balance(self):
        return round(self.total_amount_due() - self.total_paid(), 2)

    def __repr__(self):
        return f"<Customer {self.name}>"
