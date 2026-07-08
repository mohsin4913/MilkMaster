import json
from datetime import datetime

from flask import Blueprint, Response, flash, redirect, render_template, request, url_for
from sqlalchemy import text

from models import db
from models.cattle import Cattle
from models.customer import Customer
from models.expense import Expense
from models.milk_entry import MilkEntry
from models.payment import Payment
from models.pregnancy import Pregnancy
from models.setting import Setting
from utils.backup import build_backup_payload

settings_bp = Blueprint("settings", __name__)


def _parse_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _parse_date(value):
    if not value:
        return None
    return datetime.fromisoformat(value).date()


def _parse_datetime(value):
    if not value:
        return None
    return datetime.fromisoformat(value)


def _reset_all_tables():
    db.session.execute(text("PRAGMA foreign_keys=OFF"))
    for table_name in [
        "milk_entries",
        "payments",
        "expenses",
        "pregnancies",
        "cattle",
        "customers",
        "settings",
    ]:
        db.session.execute(text(f"DELETE FROM {table_name}"))
    try:
        db.session.execute(
            text(
                "DELETE FROM sqlite_sequence WHERE name IN ('milk_entries', 'payments', 'expenses', 'pregnancies', 'cattle', 'customers', 'settings')"
            )
        )
    except Exception:
        pass
    db.session.execute(text("PRAGMA foreign_keys=ON"))
    db.session.commit()


def _restore_backup_payload(payload):
    _reset_all_tables()

    for setting_data in payload.get("settings", []):
        db.session.add(Setting(key=setting_data["key"], value=str(setting_data["value"])))

    db.session.flush()

    for customer_data in payload.get("customers", []):
        db.session.add(
            Customer(
                id=customer_data.get("id"),
                name=customer_data.get("name", ""),
                mobile=customer_data.get("mobile", ""),
                address=customer_data.get("address"),
                milk_rate=float(customer_data.get("milk_rate", 0) or 0),
                opening_balance=float(customer_data.get("opening_balance", 0) or 0),
                active=bool(customer_data.get("active", True)),
                created_at=_parse_datetime(customer_data.get("created_at")) or datetime.utcnow(),
            )
        )

    db.session.flush()

    for cattle_data in payload.get("cattle", []):
        db.session.add(
            Cattle(
                id=cattle_data.get("id"),
                tag_number=cattle_data.get("tag_number", ""),
                name=cattle_data.get("name", ""),
                breed=cattle_data.get("breed"),
                gender=cattle_data.get("gender"),
                date_of_birth=_parse_date(cattle_data.get("date_of_birth")),
                purchase_date=_parse_date(cattle_data.get("purchase_date")),
                purchase_cost=float(cattle_data.get("purchase_cost", 0) or 0),
                current_status=cattle_data.get("current_status", "Milking"),
                created_at=_parse_datetime(cattle_data.get("created_at")) or datetime.utcnow(),
            )
        )

    db.session.flush()

    for entry_data in payload.get("milk_entries", []):
        db.session.add(
            MilkEntry(
                id=entry_data.get("id"),
                customer_id=entry_data.get("customer_id"),
                entry_date=_parse_date(entry_data.get("entry_date")),
                morning_litres=float(entry_data.get("morning_litres", 0) or 0),
                evening_litres=float(entry_data.get("evening_litres", 0) or 0),
                total_litres=float(entry_data.get("total_litres", 0) or 0),
                rate=float(entry_data.get("rate", 0) or 0),
                amount=float(entry_data.get("amount", 0) or 0),
                created_at=_parse_datetime(entry_data.get("created_at")) or datetime.utcnow(),
            )
        )

    for payment_data in payload.get("payments", []):
        db.session.add(
            Payment(
                id=payment_data.get("id"),
                customer_id=payment_data.get("customer_id"),
                payment_date=_parse_date(payment_data.get("payment_date")),
                amount=float(payment_data.get("amount", 0) or 0),
                payment_mode=payment_data.get("payment_mode", "Cash"),
                notes=payment_data.get("notes"),
                created_at=_parse_datetime(payment_data.get("created_at")) or datetime.utcnow(),
            )
        )

    for expense_data in payload.get("expenses", []):
        db.session.add(
            Expense(
                id=expense_data.get("id"),
                category=expense_data.get("category", "Other"),
                description=expense_data.get("description", ""),
                amount=float(expense_data.get("amount", 0) or 0),
                expense_date=_parse_date(expense_data.get("expense_date")),
                created_at=_parse_datetime(expense_data.get("created_at")) or datetime.utcnow(),
            )
        )

    db.session.flush()

    for pregnancy_data in payload.get("pregnancies", []):
        db.session.add(
            Pregnancy(
                id=pregnancy_data.get("id"),
                cattle_id=pregnancy_data.get("cattle_id"),
                insemination_date=_parse_date(pregnancy_data.get("insemination_date")),
                expected_calving_date=_parse_date(pregnancy_data.get("expected_calving_date")),
                created_at=_parse_datetime(pregnancy_data.get("created_at")) or datetime.utcnow(),
            )
        )

    db.session.commit()


@settings_bp.route("/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        Setting.set_value("default_milk_rate", request.form.get("default_milk_rate", ""))
        Setting.set_value("currency", request.form.get("currency", ""))
        Setting.set_value("theme", request.form.get("theme", ""))
        Setting.set_value("language", request.form.get("language", ""))
        Setting.set_value("retention_days", str(_parse_int(request.form.get("retention_days"), 60)))
        flash("Settings updated successfully.", "success")
        return redirect(url_for("settings.settings"))

    return render_template(
        "settings/index.html",
        default_milk_rate=Setting.get_value("default_milk_rate", "55"),
        currency=Setting.get_value("currency", "INR"),
        theme=Setting.get_value("theme", "light"),
        language=Setting.get_value("language", "en"),
        retention_days=Setting.get_value("retention_days", "60"),
    )


@settings_bp.route("/settings/backup.json")
def download_backup():
    payload = build_backup_payload()
    return Response(
        json.dumps(payload, indent=2),
        mimetype="application/json",
        headers={"Content-Disposition": "attachment; filename=milkmaster-backup.json"},
    )


@settings_bp.route("/settings/restore", methods=["POST"])
def restore_backup():
    backup_file = request.files.get("backup_file")
    if not backup_file or not backup_file.filename:
        flash("Please choose a backup file to restore.", "danger")
        return redirect(url_for("settings.settings"))

    try:
        payload = json.load(backup_file.stream)
        _restore_backup_payload(payload)
    except Exception:
        db.session.rollback()
        flash("The backup file could not be restored.", "danger")
        return redirect(url_for("settings.settings"))

    flash("Backup restored successfully.", "success")
    return redirect(url_for("settings.settings"))