from datetime import datetime, timedelta

from models import db
from models.expense import Expense
from models.milk_entry import MilkEntry
from models.payment import Payment
from models.setting import Setting


def purge_expired_records(reference_date=None):
    """Delete operational records older than the configured retention window."""
    today = reference_date or datetime.utcnow().date()
    retention_days = int(Setting.get_value("retention_days", "60") or 60)
    cutoff_date = today - timedelta(days=retention_days)

    MilkEntry.query.filter(MilkEntry.entry_date < cutoff_date).delete(synchronize_session=False)
    Payment.query.filter(Payment.payment_date < cutoff_date).delete(synchronize_session=False)
    Expense.query.filter(Expense.expense_date < cutoff_date).delete(synchronize_session=False)
    db.session.commit()
