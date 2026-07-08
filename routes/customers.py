from io import BytesIO
from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, Response, url_for
from sqlalchemy.exc import IntegrityError
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from models import db
from models.customer import Customer
from models.milk_entry import MilkEntry
from models.payment import Payment

customers_bp = Blueprint("customers", __name__)


def _parse_float(value, error_message, redirect_endpoint):
    try:
        return float(value)
    except (TypeError, ValueError):
        flash(error_message, "danger")
        return redirect(url_for(redirect_endpoint))


def _save_customer(customer, success_message, redirect_endpoint):
    try:
        db.session.add(customer)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash("Mobile number already exists.", "danger")
        return redirect(url_for(redirect_endpoint))

    flash(success_message, "success")
    return redirect(url_for(redirect_endpoint))


@customers_bp.route("/customers")
def list_customers():
    query = request.args.get("q", "", type=str)
    if query:
        customers = Customer.query.filter(Customer.name.ilike(f"%{query}%")).all()
    else:
        customers = Customer.query.order_by(Customer.created_at.desc()).all()
    return render_template("customers/list.html", customers=customers, query=query)


@customers_bp.route("/customers/new", methods=["GET", "POST"])
def create_customer():
    if request.method == "POST":
        milk_rate = _parse_float(
            request.form.get("milk_rate", 0),
            "Milk rate must be a valid number.",
            "customers.create_customer",
        )
        if not isinstance(milk_rate, float):
            return milk_rate

        opening_balance = _parse_float(
            request.form.get("opening_balance", 0),
            "Opening balance must be a valid number.",
            "customers.create_customer",
        )
        if not isinstance(opening_balance, float):
            return opening_balance

        customer = Customer(
            name=request.form.get("name", "").strip(),
            mobile=request.form.get("mobile", "").strip(),
            address=request.form.get("address", "").strip(),
            milk_rate=milk_rate,
            opening_balance=opening_balance,
            active=request.form.get("active") == "on",
        )
        return _save_customer(customer, "Customer added successfully.", "customers.list_customers")
    return render_template("customers/form.html", customer=None)


@customers_bp.route("/customers/<int:customer_id>/edit", methods=["GET", "POST"])
def edit_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    if request.method == "POST":
        milk_rate = _parse_float(
            request.form.get("milk_rate", 0),
            "Milk rate must be a valid number.",
            "customers.edit_customer",
        )
        if not isinstance(milk_rate, float):
            return redirect(url_for("customers.edit_customer", customer_id=customer_id))

        opening_balance = _parse_float(
            request.form.get("opening_balance", 0),
            "Opening balance must be a valid number.",
            "customers.edit_customer",
        )
        if not isinstance(opening_balance, float):
            return redirect(url_for("customers.edit_customer", customer_id=customer_id))

        customer.name = request.form.get("name", "").strip()
        customer.mobile = request.form.get("mobile", "").strip()
        customer.address = request.form.get("address", "").strip()
        customer.milk_rate = milk_rate
        customer.opening_balance = opening_balance
        customer.active = request.form.get("active") == "on"
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Mobile number already exists.", "danger")
            return redirect(url_for("customers.edit_customer", customer_id=customer_id))

        flash("Customer updated successfully.", "success")
        return redirect(url_for("customers.list_customers"))
    return render_template("customers/form.html", customer=customer)


@customers_bp.route("/customers/<int:customer_id>/delete", methods=["POST"])
def delete_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    db.session.delete(customer)
    db.session.commit()
    flash("Customer deleted successfully.", "success")
    return redirect(url_for("customers.list_customers"))


@customers_bp.route("/customers/<int:customer_id>/monthly-statement.pdf")
def monthly_statement_pdf(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    month = request.args.get("month", datetime.now().strftime("%Y-%m"))
    year, month_num = map(int, month.split("-"))

    entries = (
        MilkEntry.query.filter(
            MilkEntry.customer_id == customer.id,
            MilkEntry.entry_date >= datetime(year, month_num, 1).date(),
            MilkEntry.entry_date < datetime(year + (month_num // 12), (month_num % 12) + 1, 1).date(),
        )
        .order_by(MilkEntry.entry_date.asc())
        .all()
    )
    payments = (
        Payment.query.filter(
            Payment.customer_id == customer.id,
            Payment.payment_date >= datetime(year, month_num, 1).date(),
            Payment.payment_date < datetime(year + (month_num // 12), (month_num % 12) + 1, 1).date(),
        )
        .order_by(Payment.payment_date.asc())
        .all()
    )

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("MilkMaster Monthly Milk Statement", styles["Title"]))
    story.append(Paragraph(f"Customer: {customer.name}", styles["Heading2"]))
    story.append(Paragraph(f"Mobile: {customer.mobile}", styles["BodyText"]))
    story.append(Paragraph(f"Month: {month}", styles["BodyText"]))
    story.append(Spacer(1, 12))

    table_data = [["Date", "Morning", "Evening", "Total", "Rate", "Amount"]]
    for entry in entries:
        table_data.append(
            [
                str(entry.entry_date),
                f"{entry.morning_litres:.2f}",
                f"{entry.evening_litres:.2f}",
                f"{entry.total_litres:.2f}",
                f"{entry.rate:.2f}",
                f"{entry.amount:.2f}",
            ]
        )

    table = Table(table_data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f7a4d")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.beige]),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 12))

    total_milk = sum(entry.total_litres for entry in entries)
    total_amount = sum(entry.amount for entry in entries)
    total_paid = sum(payment.amount for payment in payments)
    balance = customer.opening_balance + total_amount - total_paid

    story.append(Paragraph(f"Total milk: {total_milk:.2f} litres", styles["BodyText"]))
    story.append(Paragraph(f"Total amount: {total_amount:.2f}", styles["BodyText"]))
    story.append(Paragraph(f"Payments this month: {total_paid:.2f}", styles["BodyText"]))
    story.append(Paragraph(f"Closing balance: {balance:.2f}", styles["BodyText"]))

    doc.build(story)
    buffer.seek(0)
    return Response(buffer.getvalue(), mimetype="application/pdf", headers={"Content-Disposition": f"attachment; filename={customer.name.lower().replace(' ', '_')}_statement.pdf"})


@customers_bp.route("/customers/<int:customer_id>/message-preview")
def customer_message_preview(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    month = request.args.get("month", datetime.now().strftime("%Y-%m"))
    year, month_num = map(int, month.split("-"))
    start_date = datetime(year, month_num, 1).date()
    end_date = datetime(year + (month_num // 12), (month_num % 12) + 1, 1).date()

    entries = MilkEntry.query.filter(
        MilkEntry.customer_id == customer.id,
        MilkEntry.entry_date >= start_date,
        MilkEntry.entry_date < end_date,
    ).all()
    total_milk = sum(entry.total_litres for entry in entries)
    total_amount = sum(entry.amount for entry in entries)
    balance = customer.outstanding_balance()

    message = (
        f"Hello {customer.name}, your monthly milk statement for {month} is ready. "
        f"Milk delivered: {total_milk:.2f} litres. Total amount: {total_amount:.2f}. "
        f"Outstanding balance: {balance:.2f}. Thank you."
    )
    return render_template("customers/message_preview.html", customer=customer, month=month, message=message)
