from datetime import datetime, timedelta, timezone

from models import db


class Pregnancy(db.Model):
    __tablename__ = "pregnancies"

    id = db.Column(db.Integer, primary_key=True)
    cattle_id = db.Column(db.Integer, db.ForeignKey("cattle.id"), nullable=False)
    insemination_date = db.Column(db.Date, nullable=False)
    expected_calving_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    cattle = db.relationship("Cattle", back_populates="pregnancies")

    def calculate_expected_calving_date(self):
        if self.insemination_date:
            self.expected_calving_date = self.insemination_date + timedelta(days=280)
        return self.expected_calving_date

    def pregnancy_days(self):
        if not self.expected_calving_date:
            self.calculate_expected_calving_date()
        if self.expected_calving_date:
            today = datetime.now(timezone.utc).date()
            return max(0, (today - self.insemination_date).days)
        return 0

    def remaining_days(self):
        if not self.expected_calving_date:
            self.calculate_expected_calving_date()
        if self.expected_calving_date:
            today = datetime.now(timezone.utc).date()
            return max(0, (self.expected_calving_date - today).days)
        return 0

    def __repr__(self):
        return f"<Pregnancy {self.cattle_id}>"
