from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for

from models import db
from models.customer import Customer
from models.milk_entry import MilkEntry

milk_entries_bp = Blueprint("milk_entries", __name__)


@milk_entries_bp.route("/milk-entries")
def list_milk_entries():
    entries = MilkEntry.query.order_by(MilkEntry.entry_date.desc()).all()
    return render_template("milk_entries/list.html", entries=entries)


@milk_entries_bp.route("/milk-entries/new", methods=["GET", "POST"])
def create_milk_entry():
    customers = Customer.query.order_by(Customer.name).all()
    if request.method == "POST":
        customer_id = int(request.form.get("customer_id"))
        entry_date = request.form.get("entry_date")
        morning_raw = request.form.get("morning_litres", "")
        evening_raw = request.form.get("evening_litres", "")
        morning_litres = float(morning_raw) if morning_raw not in ("", None) else 0.0
        evening_litres = float(evening_raw) if evening_raw not in ("", None) else 0.0
        if morning_litres < 0 or evening_litres < 0:
            flash("Milk litres cannot be negative.", "danger")
            return redirect(url_for("milk_entries.create_milk_entry"))
        if morning_litres == 0 and evening_litres == 0:
            flash("Please enter at least one milk value.", "danger")
            return redirect(url_for("milk_entries.create_milk_entry"))
        customer = Customer.query.get_or_404(customer_id)
        existing = MilkEntry.query.filter_by(customer_id=customer_id, entry_date=datetime.strptime(entry_date, "%Y-%m-%d").date()).first()
        if existing:
            flash("This customer already has a milk entry for that date.", "danger")
            return redirect(url_for("milk_entries.create_milk_entry"))
        total_litres = morning_litres + evening_litres
        rate = customer.milk_rate or 0
        amount = round(total_litres * rate, 2)
        entry = MilkEntry(
            customer_id=customer_id,
            entry_date=datetime.strptime(entry_date, "%Y-%m-%d").date(),
            morning_litres=morning_litres,
            evening_litres=evening_litres,
            total_litres=total_litres,
            rate=rate,
            amount=amount,
        )
        db.session.add(entry)
        db.session.commit()
        flash("Milk entry recorded successfully.", "success")
        return redirect(url_for("milk_entries.list_milk_entries"))
    return render_template("milk_entries/form.html", customers=customers, entry=None)


@milk_entries_bp.route("/milk-entries/<int:entry_id>/edit", methods=["GET", "POST"])
def edit_milk_entry(entry_id):
    entry = MilkEntry.query.get_or_404(entry_id)
    customers = Customer.query.order_by(Customer.name).all()
    if request.method == "POST":
        customer_id = int(request.form.get("customer_id"))
        entry_date = datetime.strptime(request.form.get("entry_date"), "%Y-%m-%d").date()
        morning_raw = request.form.get("morning_litres", "")
        evening_raw = request.form.get("evening_litres", "")
        morning_litres = float(morning_raw) if morning_raw not in ("", None) else 0.0
        evening_litres = float(evening_raw) if evening_raw not in ("", None) else 0.0
        if morning_litres < 0 or evening_litres < 0:
            flash("Milk litres cannot be negative.", "danger")
            return redirect(url_for("milk_entries.edit_milk_entry", entry_id=entry_id))
        if morning_litres == 0 and evening_litres == 0:
            flash("Please enter at least one milk value.", "danger")
            return redirect(url_for("milk_entries.edit_milk_entry", entry_id=entry_id))
        customer = Customer.query.get_or_404(customer_id)
        entry.customer_id = customer_id
        entry.entry_date = entry_date
        entry.morning_litres = morning_litres
        entry.evening_litres = evening_litres
        entry.total_litres = morning_litres + evening_litres
        entry.rate = customer.milk_rate or 0
        entry.amount = round(entry.total_litres * entry.rate, 2)
        db.session.commit()
        flash("Milk entry updated successfully.", "success")
        return redirect(url_for("milk_entries.list_milk_entries"))
    return render_template("milk_entries/form.html", customers=customers, entry=entry)


@milk_entries_bp.route("/milk-entries/<int:entry_id>/delete", methods=["POST"])
def delete_milk_entry(entry_id):
    entry = MilkEntry.query.get_or_404(entry_id)
    db.session.delete(entry)
    db.session.commit()
    flash("Milk entry deleted successfully.", "success")
    return redirect(url_for("milk_entries.list_milk_entries"))
