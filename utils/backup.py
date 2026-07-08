from datetime import date, datetime
from decimal import Decimal

from models.cattle import Cattle
from models.customer import Customer
from models.expense import Expense
from models.milk_entry import MilkEntry
from models.payment import Payment
from models.pregnancy import Pregnancy
from models.setting import Setting


def _serialize_value(value):
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def _serialize_model(model, fields):
    return {field: _serialize_value(getattr(model, field)) for field in fields}


def build_backup_payload():
    return {
        "customers": [
            _serialize_model(
                customer,
                [
                    "id",
                    "name",
                    "mobile",
                    "address",
                    "milk_rate",
                    "opening_balance",
                    "active",
                    "created_at",
                ],
            )
            for customer in Customer.query.order_by(Customer.id.asc()).all()
        ],
        "milk_entries": [
            _serialize_model(
                entry,
                [
                    "id",
                    "customer_id",
                    "entry_date",
                    "morning_litres",
                    "evening_litres",
                    "total_litres",
                    "rate",
                    "amount",
                    "created_at",
                ],
            )
            for entry in MilkEntry.query.order_by(MilkEntry.id.asc()).all()
        ],
        "payments": [
            _serialize_model(
                payment,
                [
                    "id",
                    "customer_id",
                    "payment_date",
                    "amount",
                    "payment_mode",
                    "notes",
                    "created_at",
                ],
            )
            for payment in Payment.query.order_by(Payment.id.asc()).all()
        ],
        "expenses": [
            _serialize_model(
                expense,
                ["id", "category", "description", "amount", "expense_date", "created_at"],
            )
            for expense in Expense.query.order_by(Expense.id.asc()).all()
        ],
        "cattle": [
            _serialize_model(
                cattle,
                [
                    "id",
                    "tag_number",
                    "name",
                    "breed",
                    "gender",
                    "date_of_birth",
                    "purchase_date",
                    "purchase_cost",
                    "current_status",
                    "created_at",
                ],
            )
            for cattle in Cattle.query.order_by(Cattle.id.asc()).all()
        ],
        "pregnancies": [
            _serialize_model(
                pregnancy,
                ["id", "cattle_id", "insemination_date", "expected_calving_date", "created_at"],
            )
            for pregnancy in Pregnancy.query.order_by(Pregnancy.id.asc()).all()
        ],
        "settings": [
            _serialize_model(setting, ["id", "key", "value"]) for setting in Setting.query.order_by(Setting.id.asc()).all()
        ],
        "exported_at": datetime.utcnow().isoformat(),
    }